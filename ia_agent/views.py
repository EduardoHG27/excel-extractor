import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

from extractor.models import Ticket, SolicitudPruebas, Proyecto
from .models import Requerimiento, CasoPrueba, EjecucionPrueba
from .services.ia_service import IAService

logger = logging.getLogger(__name__)
ia_service = IAService()

@login_required
def generar_desde_ticket(request, ticket_id):
    """Vista para generar casos de prueba desde un ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        try:
            # Obtener configuraciones del formulario
            incluir_negativos = request.POST.get('incluir_negativos') == 'on'
            detallado = request.POST.get('detallado') == 'on'
            
            # Leer número de casos del formulario
            num_casos = int(request.POST.get('num_casos', 8))
            # Limitar entre 3 y 20 casos
            num_casos = max(3, min(num_casos, 20))
            
            logger.info(f"Configuración: incluir_negativos={incluir_negativos}, detallado={detallado}, num_casos={num_casos}")
            
            # Construir requerimiento
            requerimiento_texto = f"""
=== INFORMACIÓN DEL TICKET ===
Código: {ticket.codigo}
Estado: {ticket.get_estado_display()}
Fecha Creación: {ticket.fecha_creacion.strftime('%d/%m/%Y %H:%M') if ticket.fecha_creacion else 'No especificada'}
Fecha Actualización: {ticket.fecha_actualizacion.strftime('%d/%m/%Y %H:%M') if ticket.fecha_actualizacion else 'No especificada'}

=== RESPONSABLES ===
Responsable Solicitud: {ticket.responsable_solicitud or 'No especificado'}
Líder Proyecto: {ticket.lider_proyecto or 'No especificado'}
Versión: {ticket.numero_version or 'No especificado'}

=== DATOS DEL PROYECTO ===
Proyecto: {ticket.proyecto.nombre if ticket.proyecto else 'No especificado'}
Cliente: {ticket.cliente.nombre if ticket.cliente else 'No especificado'}
Tipo Servicio: {ticket.tipo_servicio.nombre if ticket.tipo_servicio else 'No especificado'}
"""
            
            # Agregar datos del Excel asociado
            if ticket.excel_data:
                requerimiento_texto += f"""

=== DATOS DEL EXCEL ASOCIADO ===
Tipo de Pruebas: {ticket.excel_data.tipo_pruebas or 'No especificado'}
Tipo de Aplicación: {ticket.excel_data.tipo_aplicacion or 'No especificado'}

=== REQUERIMIENTO FUNCIONAL ===
Funcionalidad a Liberar:
{ticket.excel_data.funcionalidad_liberacion or 'No especificado'}

=== CAMBIOS REALIZADOS ===
Detalle de Cambios:
{ticket.excel_data.detalle_cambios or 'No especificado'}

=== JUSTIFICACIÓN ===
Justificación del Cambio:
{ticket.excel_data.justificacion_cambio or 'No especificado'}
"""
            
            # Contexto completo
            contexto = {
                'proyecto': ticket.proyecto.nombre if ticket.proyecto else 'No especificado',
                'cliente': ticket.cliente.nombre if ticket.cliente else 'No especificado',
                'tipo_servicio': ticket.tipo_servicio.nombre if ticket.tipo_servicio else 'No especificado',
                'responsable': ticket.responsable_solicitud or 'No especificado',
                'lider': ticket.lider_proyecto or 'No especificado',
                'version': ticket.numero_version or 'No especificado',
                'funcionalidad': ticket.excel_data.funcionalidad_liberacion if ticket.excel_data else '',
                'detalle_cambios': ticket.excel_data.detalle_cambios if ticket.excel_data else '',
                'justificacion': ticket.excel_data.justificacion_cambio if ticket.excel_data else ''
            }
            
            # Configuración para la IA - ✅ CORREGIDO: usa num_casos del formulario
            config = {
                'incluir_negativos': incluir_negativos,
                'detallado': detallado,
                'num_casos': num_casos,  # ✅ AHORA USA EL VALOR DEL FORMULARIO
                'alto_riesgo_pct': 70,
                'medio_riesgo_pct': 20,
                'bajo_riesgo_pct': 10,
            }
            
            # Crear requerimiento
            requerimiento = Requerimiento.objects.create(
                ticket=ticket,
                proyecto=ticket.proyecto,
                cliente=ticket.cliente,
                tipo_servicio=ticket.tipo_servicio,
                titulo=f"Requerimiento de Ticket: {ticket.codigo}",
                descripcion=requerimiento_texto[:500],
                fuente='ticket',
                contenido_extraido=requerimiento_texto,
                estado='procesando'
            )
            
            # Generar casos con IA usando configuraciones
            casos_generados = ia_service.generar_casos_prueba(
                requerimiento_texto,
                contexto,
                config
            )
            
            logger.info(f"IA generó {len(casos_generados)} casos")
            
            # Guardar casos generados
            casos_creados = []
            for idx, caso_data in enumerate(casos_generados):
                # Convertir nivel_riesgo a prioridad si es necesario
                prioridad = caso_data.get('prioridad', 'media')
                nivel_riesgo = caso_data.get('nivel_riesgo', '')
                if nivel_riesgo == 'alto':
                    prioridad = 'alta'
                elif nivel_riesgo == 'medio':
                    prioridad = 'media'
                elif nivel_riesgo == 'bajo':
                    prioridad = 'baja'
                
                caso = CasoPrueba.objects.create(
                    requerimiento=requerimiento,
                    ticket=ticket,
                    proyecto=ticket.proyecto,
                    cliente=ticket.cliente,
                    identificador=caso_data.get('identificador', f"TC-{len(casos_creados)+1:03d}"),
                    titulo=caso_data.get('titulo', ''),
                    descripcion=caso_data.get('descripcion', ''),
                    precondiciones='\n'.join(caso_data.get('precondiciones', [])),
                    pasos=caso_data.get('pasos', []),
                    resultados_esperados=caso_data.get('resultados_esperados', []),
                    datos_prueba=caso_data.get('datos_prueba', {}),
                    prioridad=prioridad,
                    estado='borrador',
                    created_by=request.user
                )
                casos_creados.append(caso)
            
            requerimiento.estado = 'completado'
            requerimiento.save()
            
            messages.success(request, f'✅ Se generaron {len(casos_creados)} casos de prueba con IA')
            return redirect('ia_agent:ver_casos_ticket', ticket_id=ticket.id)
            
        except Exception as e:
            logger.error(f"Error generando casos: {str(e)}", exc_info=True)
            messages.error(request, f'❌ Error generando casos: {str(e)}')
            return redirect('extractor:ticket_detail', id=ticket.id)
    
    # GET request - mostrar formulario
    context = {
        'ticket': ticket,
        'tipo': 'ticket',
        'tiene_excel': bool(ticket.excel_data),
        'funcionalidad': ticket.excel_data.funcionalidad_liberacion if ticket.excel_data else None,
        'detalle_cambios': ticket.excel_data.detalle_cambios if ticket.excel_data else None,
        'justificacion': ticket.excel_data.justificacion_cambio if ticket.excel_data else None
    }
    return render(request, 'ia_agent/generar_casos.html', context)


@login_required
def generar_desde_solicitud(request, solicitud_id):
    """Vista para generar casos de prueba desde una solicitud de pruebas"""
    solicitud = get_object_or_404(SolicitudPruebas, id=solicitud_id)
    
    if request.method == 'POST':
        try:
            # Extraer requerimiento de la solicitud
            requerimiento_texto = f"""
            Título: {solicitud.nombre_archivo}
            Descripción: {solicitud.descripcion or 'Sin descripción'}
            Archivo: {solicitud.nombre_archivo}
            Fecha Solicitud: {solicitud.fecha_solicitud}
            """
            
            # Contexto adicional
            contexto = {
                'proyecto': solicitud.proyecto.nombre if solicitud.proyecto else 'No especificado',
                'cliente': solicitud.cliente.nombre if solicitud.cliente else 'No especificado',
                'tipo_servicio': solicitud.tipo_servicio.nombre if solicitud.tipo_servicio else 'No especificado'
            }
            
            # Crear requerimiento
            requerimiento = Requerimiento.objects.create(
                solicitud=solicitud,
                titulo=f"Requerimiento de Solicitud: {solicitud.nombre_archivo}",
                descripcion=requerimiento_texto,
                fuente='solicitud',
                contenido_extraido=requerimiento_texto,
                estado='procesando'
            )
            
            # Generar casos con IA
            casos_generados = ia_service.generar_casos_prueba(
                requerimiento_texto,
                contexto
            )
            
            # Guardar casos generados
            casos_creados = []
            for caso_data in casos_generados:
                caso = CasoPrueba.objects.create(
                    requerimiento=requerimiento,
                    solicitud=solicitud,
                    proyecto=solicitud.proyecto,
                    cliente=solicitud.cliente,
                    identificador=caso_data.get('identificador', f"TC-{len(casos_creados)+1:03d}"),
                    titulo=caso_data.get('titulo', ''),
                    descripcion=caso_data.get('descripcion', ''),
                    precondiciones='\n'.join(caso_data.get('precondiciones', [])),
                    pasos=caso_data.get('pasos', []),
                    resultados_esperados=caso_data.get('resultados_esperados', []),
                    datos_prueba=caso_data.get('datos_prueba', {}),
                    prioridad=caso_data.get('prioridad', 'media'),
                    estado='borrador',
                    created_by=request.user
                )
                casos_creados.append(caso)
            
            requerimiento.estado = 'completado'
            requerimiento.save()
            
            messages.success(request, f'Se generaron {len(casos_creados)} casos de prueba exitosamente')
            return redirect('ia_agent:ver_casos_solicitud', solicitud_id=solicitud.id)
            
        except Exception as e:
            logger.error(f"Error generando casos desde solicitud {solicitud_id}: {str(e)}")
            messages.error(request, f'Error generando casos: {str(e)}')
            return redirect('ia_agent:ver_casos_solicitud', solicitud_id=solicitud.id)
    
    context = {
        'solicitud': solicitud,
        'tipo': 'solicitud'
    }
    return render(request, 'ia_agent/generar_casos.html', context)


@login_required
def generar_desde_url(request):
    """Vista para generar casos de prueba desde una URL"""
    if request.method == 'POST':
        url = request.POST.get('url')
        if not url:
            messages.error(request, 'Por favor ingrese una URL válida')
            return redirect('ia_agent:generar_url')
        
        try:
            # Extraer contenido de la URL
            resultado = ia_service.extraer_requerimiento_url(url)
            
            if 'error' in resultado:
                messages.error(request, f'Error extrayendo URL: {resultado["error"]}')
                return redirect('ia_agent:generar_url')
            
            # Crear requerimiento
            requerimiento = Requerimiento.objects.create(
                titulo=resultado['titulo'],
                descripcion=resultado['contenido'][:500],
                fuente='url',
                url_origen=url,
                contenido_extraido=resultado['contenido'],
                estado='procesando'
            )
            
            # Generar casos con IA
            casos_generados = ia_service.generar_casos_prueba(
                resultado['contenido']
            )
            
            # Guardar casos generados
            casos_creados = []
            for caso_data in casos_generados:
                caso = CasoPrueba.objects.create(
                    requerimiento=requerimiento,
                    identificador=caso_data.get('identificador', f"TC-{len(casos_creados)+1:03d}"),
                    titulo=caso_data.get('titulo', ''),
                    descripcion=caso_data.get('descripcion', ''),
                    precondiciones='\n'.join(caso_data.get('precondiciones', [])),
                    pasos=caso_data.get('pasos', []),
                    resultados_esperados=caso_data.get('resultados_esperados', []),
                    datos_prueba=caso_data.get('datos_prueba', {}),
                    prioridad=caso_data.get('prioridad', 'media'),
                    estado='borrador',
                    created_by=request.user
                )
                casos_creados.append(caso)
            
            requerimiento.estado = 'completado'
            requerimiento.save()
            
            messages.success(request, f'Se generaron {len(casos_creados)} casos de prueba desde la URL')
            return redirect('ia_agent:ver_casos_requerimiento', requerimiento_id=requerimiento.id)
            
        except Exception as e:
            logger.error(f"Error procesando URL {url}: {str(e)}")
            messages.error(request, f'Error procesando URL: {str(e)}')
            return redirect('ia_agent:generar_url')
    
    return render(request, 'ia_agent/generar_url.html')


@login_required
def ver_casos(request, ticket_id=None, solicitud_id=None, requerimiento_id=None):
    casos = CasoPrueba.objects.all()
    ticket = None
    solicitud = None
    requerimiento = None
    
    if ticket_id:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        casos = casos.filter(ticket_id=ticket_id)
        titulo = f"Casos de Prueba - Ticket {ticket.codigo}"
    elif solicitud_id:
        solicitud = get_object_or_404(SolicitudPruebas, id=solicitud_id)
        casos = casos.filter(solicitud_id=solicitud_id)
        titulo = f"Casos de Prueba - Solicitud {solicitud.nombre_archivo}"
    elif requerimiento_id:
        requerimiento = get_object_or_404(Requerimiento, id=requerimiento_id)
        casos = casos.filter(requerimiento_id=requerimiento_id)
        titulo = f"Casos de Prueba - {requerimiento.titulo}"
    else:
        titulo = "Todos los Casos de Prueba"
    
    context = {
        'casos': casos,
        'titulo': titulo,
        'ticket': ticket,
        'solicitud': solicitud,
        'requerimiento': requerimiento,
        'ticket_id': ticket_id,
        'solicitud_id': solicitud_id
    }
    return render(request, 'ia_agent/ver_casos.html', context)


@login_required
def detalle_caso(request, caso_id):
    """Vista para ver detalle de un caso de prueba"""
    caso = get_object_or_404(CasoPrueba, id=caso_id)
    ejecuciones = caso.ejecuciones.all()
    
    if request.method == 'POST':
        # Registrar ejecución
        resultado = request.POST.get('resultado')
        observaciones = request.POST.get('observaciones')
        
        EjecucionPrueba.objects.create(
            caso_prueba=caso,
            ejecutado_por=request.user,
            resultado=resultado,
            observaciones=observaciones,
            entorno=request.POST.get('entorno', '')
        )
        
        messages.success(request, 'Ejecución registrada exitosamente')
        return redirect('ia_agent:detalle_caso', caso_id=caso.id)
    
    context = {
        'caso': caso,
        'ejecuciones': ejecuciones,
        'RESULTADO_CHOICES': EjecucionPrueba.RESULTADO_CHOICES
    }
    return render(request, 'ia_agent/detalle_caso.html', context)


@login_required
def editar_caso(request, caso_id):
    """Vista para editar un caso de prueba"""
    caso = get_object_or_404(CasoPrueba, id=caso_id)
    
    if request.method == 'POST':
        caso.titulo = request.POST.get('titulo', caso.titulo)
        caso.descripcion = request.POST.get('descripcion', caso.descripcion)
        caso.precondiciones = request.POST.get('precondiciones', caso.precondiciones)
        caso.prioridad = request.POST.get('prioridad', caso.prioridad)
        caso.estado = request.POST.get('estado', caso.estado)
        
        # Procesar pasos como JSON
        pasos = request.POST.getlist('pasos[]')
        if pasos:
            caso.pasos = pasos
        
        resultados = request.POST.getlist('resultados[]')
        if resultados:
            caso.resultados_esperados = resultados
        
        caso.save()
        messages.success(request, 'Caso de prueba actualizado exitosamente')
        return redirect('ia_agent:detalle_caso', caso_id=caso.id)
    
    context = {
        'caso': caso
    }
    return render(request, 'ia_agent/editar_caso.html', context)


@login_required
@require_POST
def eliminar_caso(request, caso_id):
    """Vista para eliminar un caso de prueba"""
    caso = get_object_or_404(CasoPrueba, id=caso_id)
    caso.delete()
    messages.success(request, 'Caso de prueba eliminado exitosamente')
    return JsonResponse({'success': True})


@login_required
def api_generar_casos(request):
    """API endpoint para generar casos de prueba vía AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            texto = data.get('texto', '')
            
            if not texto:
                return JsonResponse({'error': 'Texto requerido'}, status=400)
            
            casos = ia_service.generar_casos_prueba(texto)
            return JsonResponse({'casos': casos})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)