"""
Vistas públicas (sin autenticación)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from calendar import monthrange
from django.db.models import Count, Q

from extractor.models import Ticket


def consultar_ticket(request):
    """Vista pública para consultar tickets (sin autenticación)"""
    ticket = None
    error = None
    
    # ========== 1. ESTADÍSTICAS SOLO DEL MES ACTUAL ==========
    hoy = timezone.now()
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    
    # Obtener el último día del mes actual
    ultimo_dia = monthrange(hoy.year, hoy.month)[1]
    fin_mes = datetime(hoy.year, hoy.month, ultimo_dia, 23, 59, 59)
    
    # Aplicar timezone si es necesario
    if timezone.is_aware(inicio_mes):
        inicio_mes = timezone.make_aware(inicio_mes)
        fin_mes = timezone.make_aware(fin_mes)
    
    # Filtrar tickets del mes actual
    tickets_mes = Ticket.objects.filter(
        fecha_creacion__gte=inicio_mes,
        fecha_creacion__lte=fin_mes
    )
    
    # ========== ESTADÍSTICAS CORREGIDAS ==========
    total_tickets_mes = tickets_mes.count()
    
    # Tickets abiertos (en proceso)
    tickets_abiertos_mes = tickets_mes.filter(
        estado__in=['GENERADO', 'ABIERTO', 'EN_PROCESO', 'PENDIENTE']
    ).count()
    
    # Tickets completados exitosamente
    tickets_completados_mes = tickets_mes.filter(
        estado='COMPLETADO'
    ).count()
    
    # ✅ NUEVO: Tickets NO EXITOSOS
    tickets_no_exitosos_mes = tickets_mes.filter(
        estado='NO_EXITOSO'
    ).count()
    
    # ✅ NUEVO: Tickets CANCELADOS (opcional)
    tickets_cancelados_mes = tickets_mes.filter(
        estado='CANCELADO'
    ).count()
    
    # Estadísticas detalladas por estado (YA INCLUYE NO_EXITOSO automáticamente)
    estadisticas_estados = tickets_mes.values('estado').annotate(
        cantidad=Count('estado')
    ).order_by('estado')  # Ordenar para consistencia
    
    # Mapear estados a nombres legibles (incluyendo NO_EXITOSO)
    estados_map = dict(Ticket.ESTADOS_TICKET)
    for stat in estadisticas_estados:
        stat['estado_nombre'] = estados_map.get(stat['estado'], stat['estado'])
    
    # ========== 2. NOMBRE DEL MES EN ESPAÑOL ==========
    meses_espanol = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    mes_actual = f"{meses_espanol[hoy.month]} {hoy.year}"
    
    if request.method == 'POST':
        codigo_ticket = request.POST.get('codigo_ticket', '').strip().upper()
        
        if not codigo_ticket:
            error = 'Por favor ingresa un código de ticket'
        else:
            try:
                # ========== 3. CARGAR ASIGNADO_A con select_related ==========
                ticket = Ticket.objects.select_related(
                    'cliente', 'proyecto', 'tipo_servicio', 'asignado_a', 'creado_por'
                ).filter(codigo=codigo_ticket).first()
                
                if not ticket:
                    error = f'No se encontró ningún ticket con el código "{codigo_ticket}"'
                else:
                    if ticket.estado in ['CANCELADO']:
                        error = 'Este ticket no está disponible para consulta pública'
                        ticket = None
                    else:
                        if ticket.estado == 'COMPLETADO':
                            ticket.archivos = []
                            
                            if ticket.dictamen_pdf and str(ticket.dictamen_pdf):
                                url_dictamen = str(ticket.dictamen_pdf.url) if hasattr(ticket.dictamen_pdf, 'url') else str(ticket.dictamen_pdf)
                                nombre_dictamen = url_dictamen.split('/')[-1].split('?')[0]
                                extension = nombre_dictamen.split('.')[-1].lower() if '.' in nombre_dictamen else 'pdf'
                                
                                ticket.archivos.append({
                                    'nombre': f"Dictamen - {nombre_dictamen}",
                                    'tipo': extension,
                                    'tamanio': None,
                                    'fecha_subida': ticket.fecha_subida_dictamen,
                                    'url_descarga': reverse('extractor:descargar_archivo_publico', kwargs={
                                        'ticket_id': ticket.id, 
                                        'tipo': 'dictamen'
                                    })
                                })
                            
                            if ticket.evidencia_pdf and str(ticket.evidencia_pdf):
                                url_evidencia = str(ticket.evidencia_pdf.url) if hasattr(ticket.evidencia_pdf, 'url') else str(ticket.evidencia_pdf)
                                nombre_evidencia = url_evidencia.split('/')[-1].split('?')[0]
                                extension = nombre_evidencia.split('.')[-1].lower() if '.' in nombre_evidencia else 'pdf'
                                
                                ticket.archivos.append({
                                    'nombre': f"Evidencia - {nombre_evidencia}",
                                    'tipo': extension,
                                    'tamanio': None,
                                    'fecha_subida': ticket.fecha_subida_evidencia,
                                    'url_descarga': reverse('extractor:descargar_archivo_publico', kwargs={
                                        'ticket_id': ticket.id, 
                                        'tipo': 'evidencia'
                                    })
                                })
                        
            except Exception as e:
                error = f'Error al buscar el ticket: {str(e)}'
    
    # ========== 4. CONTEXTO CON LAS NUEVAS VARIABLES ==========
    context = {
        'ticket': ticket,
        'error': error,
        # Estadísticas del mes actual (NO globales)
        'total_tickets': total_tickets_mes,
        'tickets_abiertos': tickets_abiertos_mes,
        'tickets_completados': tickets_completados_mes,
        'tickets_no_exitosos': tickets_no_exitosos_mes,  # ✅ NUEVO
        'tickets_cancelados': tickets_cancelados_mes,     # ✅ NUEVO (opcional)
        'estadisticas_estados': estadisticas_estados,
        'mes_actual': mes_actual,
        'debug': settings.DEBUG,
        'codigo_buscado': request.POST.get('codigo_ticket', '') if request.method == 'POST' else '',
    }
    
    return render(request, 'extractor/consultar_ticket.html', context)


def descargar_archivo_publico(request, ticket_id, tipo):
    """Vista pública para descargar archivos de un ticket completado"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if ticket.estado != 'COMPLETADO':
        raise Http404("Este ticket no tiene archivos disponibles para descarga")
    
    if tipo == 'dictamen':
        archivo = ticket.dictamen_pdf
        nombre_base = "Dictamen"
    elif tipo == 'evidencia':
        archivo = ticket.evidencia_pdf
        nombre_base = "Evidencia"
    else:
        raise Http404("Tipo de archivo no válido")
    
    if not archivo:
        raise Http404("Archivo no encontrado")
    
    url = archivo.url
    if '?' in url:
        url += '&flags=attachment'
    else:
        url += '?flags=attachment'
    
    return redirect(url)