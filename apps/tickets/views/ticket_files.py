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
# FUNCIÓN PARA EXTRAER PUBLIC_ID DE CLOUDINARY
# ============================================================
def extraer_public_id_cloudinary(url):
    """Extrae el public_id de una URL de Cloudinary"""
    if not url:
        return None
        
    try:
        # Patrón principal: maneja image/upload/, raw/upload/, video/upload/
        pattern = r'/(?:image|raw|video)/upload/(?:v\d+/)?(.+?)\.\w+$'
        match = re.search(pattern, url)
        
        if match:
            public_id = match.group(1)
            public_id = public_id.split('?')[0]
            return public_id
        
        # FALLBACK: patrón simple para URLs sin el tipo de recurso explícito
        pattern_fallback = r'/upload/(?:v\d+/)?(.+?)\.\w+$'
        match_fallback = re.search(pattern_fallback, url)
        
        if match_fallback:
            public_id = match_fallback.group(1)
            public_id = public_id.split('?')[0]
            return public_id
        
        return None
        
    except Exception:
        return None


# ============================================================
# VISTAS
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
@require_http_methods(["POST"])
def eliminar_archivo_cloudinary(request, ticket_id, tipo_archivo):
    """Elimina un archivo de Cloudinary y actualiza el modelo Ticket"""
    import traceback
    import json
    
    print(f"\n{'='*60}")
    print(f"[DEBUG] Iniciando eliminación - Ticket: {ticket_id}, Tipo: {tipo_archivo}")
    print(f"[DEBUG] Usuario: {request.user}")
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if tipo_archivo == 'dictamen':
        campo_url = ticket.dictamen_pdf
    elif tipo_archivo == 'evidencia':
        campo_url = ticket.evidencia_pdf
    else:
        return JsonResponse({'success': False, 'error': 'Tipo de archivo no válido'}, status=400)
    
    if not campo_url:
        return JsonResponse({'success': False, 'error': f'No hay {tipo_archivo} para eliminar'}, status=404)
    
    try:
        url_str = str(campo_url)
        print(f"[DEBUG] URL del archivo: {url_str}")
        
        public_id = extraer_public_id_cloudinary(url_str)
        print(f"[DEBUG] Public ID extraído: {public_id}")
        
        if not public_id:
            return JsonResponse({
                'success': False, 
                'error': f'No se pudo identificar el archivo. URL: {url_str[:100]}...',
                'debug_url': url_str
            }, status=400)
        
        # Intentar eliminar con diferentes resource_types
        eliminado = False
        resource_types = ["image", "raw", "auto"]
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
                else:
                    print(f"[DEBUG] ❌ Falló con resource_type='{resource_type}': {result}")
            except Exception as e:
                print(f"[DEBUG] ❌ Excepción con resource_type='{resource_type}': {str(e)}")
                continue
        
        if eliminado:
            # Actualizar el ticket
            if tipo_archivo == 'dictamen':
                ticket.dictamen_pdf = None
                ticket.fecha_subida_dictamen = None
            else:
                ticket.evidencia_pdf = None
                ticket.fecha_subida_evidencia = None
            
            ticket.subido_por = None
            
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
            
            return JsonResponse({'success': True, 'message': f'{tipo_archivo.capitalize()} eliminado exitosamente'})
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
            'traceback': traceback.format_exc()
        }, status=500)


@login_required
def ver_archivo_cloudinary(request, id, tipo):
    """Ver archivo de Cloudinary (redirige a la URL pública)"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if tipo == 'dictamen' and ticket.dictamen_pdf:
        return redirect(ticket.dictamen_pdf.url)
    elif tipo == 'evidencia' and ticket.evidencia_pdf:
        return redirect(ticket.evidencia_pdf.url)
    else:
        messages.error(request, 'Archivo no encontrado')
        return redirect('extractor:ticket_detail', id=ticket.id)


@login_required
def descargar_archivo_cloudinary(request, id, tipo):
    """Descargar archivo de Cloudinary (forzar descarga)"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if tipo == 'dictamen' and ticket.dictamen_pdf:
        url = ticket.dictamen_pdf.url
        if '?' in url:
            url += '&flags=attachment'
        else:
            url += '?flags=attachment'
        return redirect(url)
    elif tipo == 'evidencia' and ticket.evidencia_pdf:
        url = ticket.evidencia_pdf.url
        if '?' in url:
            url += '&flags=attachment'
        else:
            url += '?flags=attachment'
        return redirect(url)
    else:
        messages.error(request, 'Archivo no encontrado')
        return redirect('extractor:ticket_detail', id=ticket.id)


@login_required
def verificar_archivo_cloudinary(request, id, tipo):
    """Vista de debug para ver información del archivo en Cloudinary"""
    ticket = get_object_or_404(Ticket, id=id)
    
    info = {}
    if tipo == 'dictamen' and ticket.dictamen_pdf:
        info = {
            'tiene_archivo': True,
            'url': ticket.dictamen_pdf.url if ticket.dictamen_pdf else None,
            'tiene_public_id': hasattr(ticket.dictamen_pdf, 'public_id'),
            'public_id': ticket.dictamen_pdf.public_id if hasattr(ticket.dictamen_pdf, 'public_id') else None,
        }
    elif tipo == 'evidencia' and ticket.evidencia_pdf:
        info = {
            'tiene_archivo': True,
            'url': ticket.evidencia_pdf.url if ticket.evidencia_pdf else None,
            'tiene_public_id': hasattr(ticket.evidencia_pdf, 'public_id'),
            'public_id': ticket.evidencia_pdf.public_id if hasattr(ticket.evidencia_pdf, 'public_id') else None,
        }
    else:
        info = {'tiene_archivo': False}
    
    return JsonResponse(info)