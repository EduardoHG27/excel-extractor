"""
Vistas para manejo de archivos de tickets (Cloudinary)
"""
import re
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import cloudinary.uploader

from extractor.models import Ticket


# ============================================================
# FUNCIÓN MEJORADA PARA EXTRAER PUBLIC_ID DE CLOUDINARY
# ============================================================
def extraer_public_id_cloudinary(archivo_field):
    """
    Extrae el public_id de un campo CloudinaryStorage
    Maneja tanto URLs completas como public_ids directos
    """
    if not archivo_field:
        return None
    
    # Convertir a string para procesamiento
    valor = str(archivo_field)
    print(f"[DEBUG] Valor del campo: {valor}")
    
    # 🔹 CASO 1: El campo tiene atributo public_id (CloudinaryStorage)
    if hasattr(archivo_field, 'public_id') and archivo_field.public_id:
        public_id = archivo_field.public_id
        print(f"[DEBUG] ✅ Public ID desde atributo: {public_id}")
        return public_id
    
    # 🔹 CASO 2: Es solo un public_id (sin http, sin extensión)
    if not valor.startswith('http') and '/' in valor:
        # Limpiar extensiones comunes
        for ext in ['.pdf', '.jpg', '.png', '.doc', '.docx']:
            if valor.endswith(ext):
                valor = valor[:-len(ext)]
                break
        print(f"[DEBUG] ✅ Usando como public_id directo: {valor}")
        return valor
    
    # 🔹 CASO 3: Es una URL completa de Cloudinary
    if 'cloudinary.com' in valor or 'res.cloudinary.com' in valor:
        try:
            # Patrón para /upload/v123456/public_id.pdf
            pattern = r'/(?:image|raw|video)/upload/(?:v\d+/)?(.+?)(?:\.\w+)?$'
            match = re.search(pattern, valor)
            
            if match:
                public_id = match.group(1)
                # Limpiar parámetros de query string
                public_id = public_id.split('?')[0]
                # Eliminar extensión si quedó
                if public_id.endswith('.pdf'):
                    public_id = public_id[:-4]
                print(f"[DEBUG] ✅ Public ID desde URL: {public_id}")
                return public_id
        except Exception as e:
            print(f"[DEBUG] Error parseando URL: {e}")
    
    # 🔹 CASO 4: Intentar limpiar el valor como último recurso
    valor_limpio = valor.split('/')[-1]  # Tomar última parte
    for ext in ['.pdf', '.jpg', '.png']:
        if valor_limpio.endswith(ext):
            valor_limpio = valor_limpio[:-len(ext)]
            break
    
    print(f"[DEBUG] ⚠️ Usando último recurso: {valor_limpio}")
    return valor_limpio if valor_limpio else None


# ============================================================
# VISTA CORREGIDA PARA ELIMINAR ARCHIVO
# ============================================================
@login_required
@require_http_methods(["POST"])
def eliminar_archivo_cloudinary(request, ticket_id, tipo_archivo):
    """Elimina un archivo de Cloudinary y actualiza el modelo Ticket"""
    import traceback
    
    print(f"\n{'='*60}")
    print(f"[DEBUG] Iniciando eliminación - Ticket: {ticket_id}, Tipo: {tipo_archivo}")
    print(f"[DEBUG] Usuario: {request.user}")
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Obtener el campo correspondiente
    if tipo_archivo == 'dictamen':
        campo_archivo = ticket.dictamen_pdf
    elif tipo_archivo == 'evidencia':
        campo_archivo = ticket.evidencia_pdf
    else:
        return JsonResponse({'success': False, 'error': 'Tipo de archivo no válido'}, status=400)
    
    if not campo_archivo:
        return JsonResponse({'success': False, 'error': f'No hay {tipo_archivo} para eliminar'}, status=404)
    
    # 📋 DEPURACIÓN: Mostrar información del campo
    print(f"[DEBUG] Tipo de campo: {type(campo_archivo)}")
    print(f"[DEBUG] Valor string: {str(campo_archivo)}")
    if hasattr(campo_archivo, 'public_id'):
        print(f"[DEBUG] Atributo public_id: {campo_archivo.public_id}")
    if hasattr(campo_archivo, 'url'):
        print(f"[DEBUG] Atributo url: {campo_archivo.url}")
    
    try:
        # Obtener el public_id usando la función mejorada
        public_id = extraer_public_id_cloudinary(campo_archivo)
        
        if not public_id:
            return JsonResponse({
                'success': False, 
                'error': f'No se pudo identificar el archivo. Valor: {str(campo_archivo)[:100]}...',
                'debug_valor': str(campo_archivo)
            }, status=400)
        
        print(f"[DEBUG] Public ID final para eliminar: {public_id}")
        
        # Intentar eliminar con diferentes resource_types
        # IMPORTANTE: Para PDFs subidos con CloudinaryStorage, usar 'raw'
        eliminado = False
        resource_types = ["raw", "image", "auto"]
        ultimo_resultado = None
        
        for resource_type in resource_types:
            try:
                print(f"[DEBUG] Intentando eliminar con resource_type='{resource_type}'")
                result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
                print(f"[DEBUG] Resultado Cloudinary: {result}")
                ultimo_resultado = result
                
                if result.get('result') == 'ok':
                    eliminado = True
                    print(f"[DEBUG] ✅ Eliminado exitosamente con resource_type='{resource_type}'")
                    break
                elif result.get('result') == 'not found':
                    print(f"[DEBUG] Archivo no encontrado con resource_type='{resource_type}'")
                else:
                    print(f"[DEBUG] Falló con resource_type='{resource_type}': {result.get('result')}")
            except Exception as e:
                print(f"[DEBUG] Excepción con resource_type='{resource_type}': {str(e)}")
                continue
        
        if eliminado:
            # Limpiar el campo en el modelo
            if tipo_archivo == 'dictamen':
                ticket.dictamen_pdf = None
                ticket.fecha_subida_dictamen = None
            else:
                ticket.evidencia_pdf = None
                ticket.fecha_subida_evidencia = None
            
            ticket.subido_por = None
            
            # Registrar en comentarios de seguimiento
            usuario = request.user.get_full_name() or request.user.username
            ahora_local = timezone.localtime(timezone.now())
            fecha_hora = ahora_local.strftime('%d/%m/%Y %H:%M')
            comentario = f"[{fecha_hora}] {usuario} eliminó el {tipo_archivo}"
            
            if ticket.comentarios_seguimiento:
                ticket.comentarios_seguimiento += f"\n{comentario}"
            else:
                ticket.comentarios_seguimiento = comentario
            
            ticket.save()
            print(f"[DEBUG] ✅ Ticket actualizado correctamente")
            
            return JsonResponse({
                'success': True, 
                'message': f'{tipo_archivo.capitalize()} eliminado exitosamente'
            })
        else:
            print(f"[DEBUG] ❌ No se pudo eliminar. Último resultado: {ultimo_resultado}")
            return JsonResponse({
                'success': False, 
                'error': 'No se pudo eliminar el archivo de Cloudinary',
                'cloudinary_response': ultimo_resultado,
                'public_id': public_id
            }, status=500)
            
    except Exception as e:
        print(f"[DEBUG] ❌ Excepción general: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'error': str(e),
        }, status=500)


# ============================================================
# REST O VISTAS (sin cambios, se mantienen igual)
# ============================================================

@login_required
def subir_dictamen(request, id):
    """Subir archivo PDF del dictamen a Cloudinary"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if ticket.estado not in ['COMPLETADO', 'NO EXITOSO']:
        messages.error(request, 'Solo se pueden subir archivos cuando el ticket está COMPLETADO o NO EXITOSO')
        return redirect('extractor:ticket_detail', id=ticket.id)
    
    if request.method == 'POST' and request.FILES.get('dictamen_pdf'):
        archivo = request.FILES['dictamen_pdf']
        
        if not archivo.name.endswith('.pdf'):
            messages.error(request, 'Solo se permiten archivos PDF')
            return redirect('extractor:ticket_detail', id=ticket.id)
        
        if archivo.size > 10 * 1024 * 1024:
            messages.error(request, 'El archivo no puede superar los 10MB')
            return redirect('extractor:ticket_detail', id=ticket.id)
        
        try:
            ticket.dictamen_pdf = archivo
            ticket.fecha_subida_dictamen = timezone.now()
            ticket.subido_por = request.user
            ticket.save()
            
            usuario = request.user.get_full_name() or request.user.username
            ahora_local = timezone.localtime(timezone.now())
            fecha_hora = ahora_local.strftime('%d/%m/%Y %H:%M')
            comentario = f"[{fecha_hora}] {usuario} subió el dictamen: {archivo.name}"
            
            if ticket.comentarios_seguimiento:
                ticket.comentarios_seguimiento += f"\n{comentario}"
            else:
                ticket.comentarios_seguimiento = comentario
            ticket.save()
            
            messages.success(request, f'✅ Dictamen subido exitosamente: {archivo.name}')
            
        except Exception as e:
            messages.error(request, f'Error al subir: {str(e)}')
    
    return redirect('extractor:ticket_detail', id=ticket.id)


@login_required
def subir_evidencia(request, id):
    """Subir archivo PDF de evidencia a Cloudinary"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if ticket.estado not in ['COMPLETADO', 'NO EXITOSO']:
        messages.error(request, 'Solo se pueden subir archivos cuando el ticket está COMPLETADO o NO EXITOSO')
        return redirect('extractor:ticket_detail', id=ticket.id)
    
    if request.method == 'POST' and request.FILES.get('evidencia_pdf'):
        archivo = request.FILES['evidencia_pdf']
        
        if not archivo.name.endswith('.pdf'):
            messages.error(request, 'Solo se permiten archivos PDF')
            return redirect('extractor:ticket_detail', id=ticket.id)
        
        if archivo.size > 10 * 1024 * 1024:
            messages.error(request, 'El archivo no puede superar los 10MB')
            return redirect('extractor:ticket_detail', id=ticket.id)
        
        try:
            ticket.evidencia_pdf = archivo
            ticket.fecha_subida_evidencia = timezone.now()
            ticket.subido_por = request.user
            ticket.save()
            
            usuario = request.user.get_full_name() or request.user.username
            ahora_local = timezone.localtime(timezone.now())
            fecha_hora = ahora_local.strftime('%d/%m/%Y %H:%M')
            comentario = f"[{fecha_hora}] {usuario} subió evidencia: {archivo.name}"
            
            if ticket.comentarios_seguimiento:
                ticket.comentarios_seguimiento += f"\n{comentario}"
            else:
                ticket.comentarios_seguimiento = comentario
            ticket.save()
            
            messages.success(request, f'✅ Evidencia subida exitosamente: {archivo.name}')
            
        except Exception as e:
            messages.error(request, f'Error al subir: {str(e)}')
    
    return redirect('extractor:ticket_detail', id=ticket.id)


@login_required
def ver_archivo_cloudinary(request, id, tipo):
    """Ver archivo de Cloudinary (redirige a la URL pública)"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if tipo == 'dictamen' and ticket.dictamen_pdf:
        # CloudinaryStorage tiene atributo url
        if hasattr(ticket.dictamen_pdf, 'url'):
            return redirect(ticket.dictamen_pdf.url)
        else:
            return redirect(str(ticket.dictamen_pdf))
    elif tipo == 'evidencia' and ticket.evidencia_pdf:
        if hasattr(ticket.evidencia_pdf, 'url'):
            return redirect(ticket.evidencia_pdf.url)
        else:
            return redirect(str(ticket.evidencia_pdf))
    else:
        messages.error(request, 'Archivo no encontrado')
        return redirect('extractor:ticket_detail', id=ticket.id)


@login_required
def descargar_archivo_cloudinary(request, id, tipo):
    """Descargar archivo de Cloudinary (forzar descarga)"""
    ticket = get_object_or_404(Ticket, id=id)
    
    # Obtener la URL base
    if tipo == 'dictamen' and ticket.dictamen_pdf:
        if hasattr(ticket.dictamen_pdf, 'url'):
            url = ticket.dictamen_pdf.url
        else:
            url = str(ticket.dictamen_pdf)
    elif tipo == 'evidencia' and ticket.evidencia_pdf:
        if hasattr(ticket.evidencia_pdf, 'url'):
            url = ticket.evidencia_pdf.url
        else:
            url = str(ticket.evidencia_pdf)
    else:
        messages.error(request, 'Archivo no encontrado')
        return redirect('extractor:ticket_detail', id=ticket.id)
    
    # Agregar flag de descarga
    if '?' in url:
        url += '&flags=attachment'
    else:
        url += '?flags=attachment'
    
    return redirect(url)


@login_required
def verificar_archivo_cloudinary(request, id, tipo):
    """Vista de debug para ver información del archivo en Cloudinary"""
    ticket = get_object_or_404(Ticket, id=id)
    
    info = {'tiene_archivo': False}
    
    if tipo == 'dictamen' and ticket.dictamen_pdf:
        info = {
            'tiene_archivo': True,
            'tipo_campo': str(type(ticket.dictamen_pdf)),
            'valor_str': str(ticket.dictamen_pdf),
            'tiene_public_id': hasattr(ticket.dictamen_pdf, 'public_id'),
            'public_id': ticket.dictamen_pdf.public_id if hasattr(ticket.dictamen_pdf, 'public_id') else None,
            'tiene_url': hasattr(ticket.dictamen_pdf, 'url'),
            'url': ticket.dictamen_pdf.url if hasattr(ticket.dictamen_pdf, 'url') else None,
        }
    elif tipo == 'evidencia' and ticket.evidencia_pdf:
        info = {
            'tiene_archivo': True,
            'tipo_campo': str(type(ticket.evidencia_pdf)),
            'valor_str': str(ticket.evidencia_pdf),
            'tiene_public_id': hasattr(ticket.evidencia_pdf, 'public_id'),
            'public_id': ticket.evidencia_pdf.public_id if hasattr(ticket.evidencia_pdf, 'public_id') else None,
            'tiene_url': hasattr(ticket.evidencia_pdf, 'url'),
            'url': ticket.evidencia_pdf.url if hasattr(ticket.evidencia_pdf, 'url') else None,
        }
    
    return JsonResponse(info)