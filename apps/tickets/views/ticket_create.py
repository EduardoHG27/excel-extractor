"""
Vistas para creación manual de tickets
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse

from extractor.models import Ticket, Cliente, Proyecto, TipoServicio, ExcelData
from django.conf import settings


@login_required
def ticket_create(request):
    """Crear un nuevo ticket manualmente (versión completa)"""
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente')
            proyecto_id = request.POST.get('proyecto')
            tipo_prueba_id = request.POST.get('tipo_prueba')
            tipo_servicio_code = request.POST.get('tipo_servicio_code')
            
            # Validaciones
            campos_faltantes = []
            if not cliente_id:
                campos_faltantes.append("Cliente")
            if not proyecto_id:
                campos_faltantes.append("Proyecto")
            if not tipo_prueba_id:
                campos_faltantes.append("Tipo de Prueba")
            if not tipo_servicio_code:
                campos_faltantes.append("Tipo de Servicio")
            
            if campos_faltantes:
                messages.error(request, f"Campos obligatorios: {', '.join(campos_faltantes)}")
                return redirect('extractor:ticket_create')
            
            cliente = Cliente.objects.get(id=cliente_id, activo=True)
            proyecto = Proyecto.objects.get(id=proyecto_id, activo=True)
            tipo_prueba = TipoServicio.objects.get(id=tipo_prueba_id, activo=True)
            
            if proyecto.cliente_id != cliente.id:
                messages.error(request, 'El proyecto no pertenece al cliente')
                return redirect('extractor:ticket_create')
            
            # Consecutivo
            consecutivo_manual = request.POST.get('consecutivo', '').strip()
            
            if consecutivo_manual:
                try:
                    consecutivo_num = int(consecutivo_manual)
                    if consecutivo_num < 1 or consecutivo_num > 999:
                        messages.error(request, 'El consecutivo debe estar entre 1 y 999')
                        return redirect('extractor:ticket_create')
                    
                    existe = Ticket.objects.filter(
                        empresa_code="BID",
                        tipo_servicio_code=tipo_servicio_code,
                        funcion_code=tipo_prueba.nomenclatura,
                        version_code=str(tipo_prueba.id),
                        cliente_code=cliente.nomenclatura,
                        proyecto_code=proyecto.codigo,
                        consecutivo=consecutivo_num
                    ).exists()
                    
                    if existe:
                        messages.error(request, f'Ya existe un ticket con consecutivo {consecutivo_num:03d}')
                        return redirect('extractor:ticket_create')
                    
                except ValueError:
                    messages.error(request, 'El consecutivo debe ser un número válido')
                    return redirect('extractor:ticket_create')
            else:
                tickets_existentes = Ticket.objects.filter(
                    empresa_code="BID",
                    tipo_servicio_code=tipo_servicio_code,
                    funcion_code=tipo_prueba.nomenclatura,
                    version_code=str(tipo_prueba.id),
                    cliente_code=cliente.nomenclatura,
                    proyecto_code=proyecto.codigo
                )
                
                if tickets_existentes.exists():
                    max_consecutivo = tickets_existentes.aggregate(models.Max('consecutivo'))['consecutivo__max']
                    consecutivo_num = (max_consecutivo or 0) + 1
                else:
                    consecutivo_num = 1
            
            consecutivo_str = f"{consecutivo_num:03d}"
            ticket_code = f"BID-{tipo_servicio_code}-{tipo_prueba.nomenclatura}-{tipo_prueba.id}-{cliente.nomenclatura}-{proyecto.codigo}-{consecutivo_str}"
            
            ticket = Ticket.objects.create(
                codigo=ticket_code,
                empresa_code="BID",
                tipo_servicio_code=tipo_servicio_code,
                funcion_code=tipo_prueba.nomenclatura,
                version_code=str(tipo_prueba.id),
                cliente_code=cliente.nomenclatura,
                proyecto_code=proyecto.codigo,
                consecutivo=consecutivo_num,
                cliente=cliente,
                proyecto=proyecto,
                tipo_servicio=tipo_prueba,
                responsable_solicitud=request.POST.get('responsable_solicitud', '')[:255],
                lider_proyecto=request.POST.get('lider_proyecto', '')[:255],
                numero_version=request.POST.get('numero_version', '')[:255],
                estado='GENERADO'
            )
            
            # Crear ExcelData si hay información adicional
            if any([
                request.POST.get('funcionalidad_liberacion'),
                request.POST.get('detalle_cambios'),
                request.POST.get('justificacion_cambio')
            ]):
                excel_data = ExcelData.objects.create(
                    cliente=str(cliente.id),
                    proyecto=str(proyecto.id),
                    tipo_pruebas=str(tipo_prueba.id),
                    tipo_servicio=tipo_servicio_code,
                    responsable_solicitud=request.POST.get('responsable_solicitud', ''),
                    lider_proyecto=request.POST.get('lider_proyecto', ''),
                    numero_version=request.POST.get('numero_version', ''),
                    funcionalidad_liberacion=request.POST.get('funcionalidad_liberacion', ''),
                    detalle_cambios=request.POST.get('detalle_cambios', ''),
                    justificacion_cambio=request.POST.get('justificacion_cambio', ''),
                    ticket_code=ticket_code
                )
                ticket.excel_data = excel_data
                ticket.save()
            
            messages.success(request, f'✅ Ticket creado exitosamente: {ticket_code}')
            return redirect('extractor:ticket_detail', id=ticket.id)
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f'Error al crear ticket: {str(e)}')
            return redirect('extractor:ticket_create')
    
    # GET request
    context = {
        'clientes': Cliente.objects.filter(activo=True).order_by('nombre'),
        'tipos_servicio': TipoServicio.objects.filter(activo=True).order_by('nombre'),
        'proyectos': [],
        'ultimo_consecutivo': Ticket.objects.order_by('-consecutivo').first().consecutivo if Ticket.objects.exists() else 0,
        'debug': settings.DEBUG,
    }
    return render(request, 'catalogos/new_ticket_form.html', context)


@login_required
def ticket_create_simple(request):
    """Versión simplificada - Crear un nuevo ticket manualmente"""
    
    if request.method == 'GET':
        context = {
            'clientes': Cliente.objects.filter(activo=True).order_by('nombre'),
            'tipos_servicio': TipoServicio.objects.filter(activo=True).order_by('nombre'),
            'debug': settings.DEBUG,
        }
        return render(request, 'catalogos/new_ticket_form_simple.html', context)
    
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente')
            proyecto_id = request.POST.get('proyecto')
            tipo_servicio_code = request.POST.get('tipo_servicio_code', '').strip().upper()
            tipo_prueba_id = request.POST.get('tipo_prueba')
            consecutivo_manual = request.POST.get('consecutivo', '').strip()
            
            # Validaciones
            campos_faltantes = []
            if not cliente_id:
                campos_faltantes.append("Cliente")
            if not proyecto_id:
                campos_faltantes.append("Proyecto")
            if not tipo_servicio_code:
                campos_faltantes.append("Tipo de Servicio")
            if not tipo_prueba_id:
                campos_faltantes.append("Tipo de Prueba")
            
            if campos_faltantes:
                messages.error(request, f'Campos obligatorios faltantes: {", ".join(campos_faltantes)}')
                return redirect('extractor:ticket_create_simple')
            
            cliente = Cliente.objects.get(id=cliente_id, activo=True)
            proyecto = Proyecto.objects.get(id=proyecto_id, activo=True)
            tipo_prueba = TipoServicio.objects.get(id=tipo_prueba_id, activo=True)
            
            if proyecto.cliente_id != cliente.id:
                messages.error(request, 'El proyecto no pertenece al cliente seleccionado')
                return redirect('extractor:ticket_create_simple')
            
            # Consecutivo
            if consecutivo_manual:
                try:
                    consecutivo_num = int(consecutivo_manual)
                    if consecutivo_num < 1 or consecutivo_num > 999:
                        messages.error(request, 'El consecutivo debe ser entre 1 y 999')
                        return redirect('extractor:ticket_create_simple')
                    
                    existe = Ticket.objects.filter(
                        empresa_code="BID",
                        tipo_servicio_code=tipo_servicio_code,
                        funcion_code=tipo_prueba.nomenclatura,
                        version_code=str(tipo_prueba.id),
                        cliente_code=cliente.nomenclatura,
                        proyecto_code=proyecto.codigo,
                        consecutivo=consecutivo_num
                    ).exists()
                    
                    if existe:
                        messages.error(request, f'Ya existe un ticket con consecutivo {consecutivo_num:03d}')
                        return redirect('extractor:ticket_create_simple')
                    
                except ValueError:
                    messages.error(request, 'El consecutivo debe ser un número válido')
                    return redirect('extractor:ticket_create_simple')
            else:
                tickets_existentes = Ticket.objects.filter(
                    empresa_code="BID",
                    tipo_servicio_code=tipo_servicio_code,
                    funcion_code=tipo_prueba.nomenclatura,
                    version_code=str(tipo_prueba.id),
                    cliente_code=cliente.nomenclatura,
                    proyecto_code=proyecto.codigo
                )
                
                if tickets_existentes.exists():
                    max_consecutivo = tickets_existentes.aggregate(models.Max('consecutivo'))['consecutivo__max']
                    consecutivo_num = (max_consecutivo or 0) + 1
                else:
                    consecutivo_num = 1
            
            consecutivo_str = f"{consecutivo_num:03d}"
            ticket_code = f"BID-{tipo_servicio_code}-{tipo_prueba.nomenclatura}-{tipo_prueba.id}-{cliente.nomenclatura}-{proyecto.codigo}-{consecutivo_str}"
            
            ticket = Ticket.objects.create(
                codigo=ticket_code,
                empresa_code="BID",
                tipo_servicio_code=tipo_servicio_code,
                funcion_code=tipo_prueba.nomenclatura,
                version_code=str(tipo_prueba.id),
                cliente_code=cliente.nomenclatura,
                proyecto_code=proyecto.codigo,
                consecutivo=consecutivo_num,
                cliente=cliente,
                proyecto=proyecto,
                tipo_servicio=tipo_prueba,
                responsable_solicitud=request.POST.get('responsable_solicitud', '')[:255],
                lider_proyecto=request.POST.get('lider_proyecto', '')[:255],
                numero_version=request.POST.get('numero_version', '')[:255],
                estado='GENERADO',
                creado_por=request.user,
                asignado_a=request.user,
                comentarios_seguimiento=f"Ticket creado manualmente por {request.user.get_full_name() or request.user.username}"
            )
            
            if any([
                request.POST.get('funcionalidad_liberacion'),
                request.POST.get('detalle_cambios'),
                request.POST.get('justificacion_cambio')
            ]):
                excel_data = ExcelData.objects.create(
                    cliente=str(cliente.id),
                    proyecto=str(proyecto.id),
                    tipo_pruebas=str(tipo_prueba.id),
                    tipo_servicio=tipo_servicio_code,
                    responsable_solicitud=request.POST.get('responsable_solicitud', ''),
                    lider_proyecto=request.POST.get('lider_proyecto', ''),
                    numero_version=request.POST.get('numero_version', ''),
                    funcionalidad_liberacion=request.POST.get('funcionalidad_liberacion', ''),
                    detalle_cambios=request.POST.get('detalle_cambios', ''),
                    justificacion_cambio=request.POST.get('justificacion_cambio', ''),
                    ticket_code=ticket_code
                )
                ticket.excel_data = excel_data
                ticket.save()
            
            messages.success(request, f'✅ Ticket creado exitosamente: {ticket_code}')
            return redirect('extractor:ticket_detail', id=ticket.id)
            
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f'Error al crear ticket: {str(e)}')
            return redirect('extractor:ticket_create_simple')


@login_required
def crear_ticket_manual(request):
    """Vista para crear solicitud de pruebas manualmente"""
    from django.utils import timezone
    
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente')
            proyecto_id = request.POST.get('proyecto')
            tipo_servicio_code = request.POST.get('tipo_servicio_code')
            tipo_prueba_id = request.POST.get('tipo_prueba')
            
            if not cliente_id or not proyecto_id or not tipo_servicio_code or not tipo_prueba_id:
                messages.error(request, 'Todos los campos obligatorios deben estar llenos')
                return redirect('extractor:crear_ticket_manual')
            
            cliente = Cliente.objects.get(id=cliente_id, activo=True)
            proyecto = Proyecto.objects.get(id=proyecto_id, activo=True)
            tipo_prueba = TipoServicio.objects.get(id=tipo_prueba_id, activo=True)
            
            if proyecto.cliente_id != cliente.id:
                messages.error(request, 'El proyecto no pertenece al cliente seleccionado')
                return redirect('extractor:crear_ticket_manual')
            
            tickets_existentes = Ticket.objects.filter(
                empresa_code="BID",
                tipo_servicio_code=tipo_servicio_code,
                funcion_code=tipo_prueba.nomenclatura,
                version_code=str(tipo_prueba.id),
                cliente_code=cliente.nomenclatura,
                proyecto_code=proyecto.codigo
            )
            
            if tickets_existentes.exists():
                max_consecutivo = tickets_existentes.aggregate(models.Max('consecutivo'))['consecutivo__max']
                consecutivo_num = (max_consecutivo or 0) + 1
            else:
                consecutivo_num = 1
            
            consecutivo_str = f"{consecutivo_num:03d}"
            ticket_code = f"BID-{tipo_servicio_code}-{tipo_prueba.nomenclatura}-{tipo_prueba.id}-{cliente.nomenclatura}-{proyecto.codigo}-{consecutivo_str}"
            
            ticket = Ticket.objects.create(
                codigo=ticket_code,
                empresa_code="BID",
                tipo_servicio_code=tipo_servicio_code,
                funcion_code=tipo_prueba.nomenclatura,
                version_code=str(tipo_prueba.id),
                cliente_code=cliente.nomenclatura,
                proyecto_code=proyecto.codigo,
                consecutivo=consecutivo_num,
                cliente=cliente,
                proyecto=proyecto,
                tipo_servicio=tipo_prueba,
                responsable_solicitud=request.POST.get('responsable_solicitud', '')[:255],
                lider_proyecto=request.POST.get('lider_proyecto', '')[:255],
                numero_version=request.POST.get('numero_version', '')[:255],
                estado='GENERADO'
            )
            
            excel_data = ExcelData.objects.create(
                cliente=str(cliente.id),
                proyecto=str(proyecto.id),
                tipo_pruebas=str(tipo_prueba.id),
                tipo_servicio=tipo_servicio_code,
                responsable_solicitud=request.POST.get('responsable_solicitud', ''),
                lider_proyecto=request.POST.get('lider_proyecto', ''),
                tipo_aplicacion=request.POST.get('tipo_aplicacion', ''),
                numero_version=request.POST.get('numero_version', ''),
                funcionalidad_liberacion=request.POST.get('funcionalidad_liberacion', ''),
                detalle_cambios=request.POST.get('detalle_cambios', ''),
                justificacion_cambio=request.POST.get('justificacion_cambio', ''),
                ticket_code=ticket_code
            )
            
            ticket.excel_data = excel_data
            ticket.save()
            
            messages.success(request, f'✅ Solicitud creada exitosamente. Ticket: {ticket_code}')
            return redirect('extractor:ticket_detail', id=ticket.id)
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f'Error al crear solicitud: {str(e)}')
            return redirect('extractor:crear_ticket_manual')
    
    context = {
        'clientes': Cliente.objects.filter(activo=True).order_by('nombre'),
        'tipos_servicio': TipoServicio.objects.filter(activo=True).order_by('nombre'),
        'today': timezone.now().date(),
        'now': timezone.now(),
        'debug': settings.DEBUG,
    }
    return render(request, 'extractor/crear_solicitud.html', context)