"""
Dashboard para Líder de Pruebas - Versión con gráficos por período
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
from collections import defaultdict
import calendar

from extractor.models import Ticket, Cliente, Proyecto, Usuario


def es_lider_pruebas(user):
    """Verifica si el usuario es líder de pruebas"""
    return user.is_authenticated and (user.is_superuser or getattr(user, 'es_lider_pruebas', False))


@login_required
@user_passes_test(es_lider_pruebas, login_url='extractor:ticket_list')
def dashboard_lider(request):
    """
    Dashboard para líder de pruebas.
    Versión compatible con SQLite.
    """
    
    # ========== OBTENER PARÁMETROS ==========
    cliente_id = request.GET.get('cliente')
    proyecto_id = request.GET.get('proyecto')
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    periodo = request.GET.get('periodo', 'mes_actual')  # mes_actual, mes_anterior, trimestre, semestre, año
    
    # ========== OBTENER TODOS LOS TICKETS ==========
    tickets = Ticket.objects.all().select_related('cliente', 'proyecto', 'tipo_servicio', 'asignado_a')
    
    # ========== APLICAR FILTROS MANUALMENTE ==========
    tickets_list = list(tickets)
    
    # Filtro por cliente
    if cliente_id and cliente_id != '':
        tickets_list = [t for t in tickets_list if t.cliente_id == int(cliente_id)]
    
    # Filtro por proyecto
    if proyecto_id and proyecto_id != '':
        tickets_list = [t for t in tickets_list if t.proyecto_id == int(proyecto_id)]
    
    # Filtro por estado
    if estado and estado != '':
        tickets_list = [t for t in tickets_list if t.estado == estado]
    
    # Filtro por fecha desde
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        tickets_list = [t for t in tickets_list if t.fecha_creacion and t.fecha_creacion.date() >= fecha_desde_obj]
    
    # Filtro por fecha hasta
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        tickets_list = [t for t in tickets_list if t.fecha_creacion and t.fecha_creacion.date() <= fecha_hasta_obj]
    
    ahora = timezone.now()
    
    # ========== CALCULAR PERÍODOS ==========
    fechas_periodo = calcular_fechas_periodo(periodo, ahora)
    
    # ========== FILTRAR TICKETS POR PERÍODO ==========
    tickets_generales = tickets_list  # Todos los tickets (con filtros aplicados)
    tickets_periodo = [t for t in tickets_list if t.fecha_creacion and fechas_periodo['fecha_inicio'] <= t.fecha_creacion.date() <= fechas_periodo['fecha_fin']]
    
    # ========== MÉTRICAS PRINCIPALES ==========
    total_tickets = len(tickets_generales)
    
    tickets_abiertos = len([t for t in tickets_generales if t.estado in ['ABIERTO', 'GENERADO']])
    tickets_proceso = len([t for t in tickets_generales if t.estado == 'EN_PROCESO'])
    tickets_sin_asignar = len([t for t in tickets_generales if t.asignado_a is None])
    
    # Tickets completados en el período seleccionado
    tickets_completados_periodo = len([t for t in tickets_periodo if t.estado == 'COMPLETADO'])
    
    usuarios_activos = Usuario.objects.filter(is_active=True).count()
    
    # ========== GRÁFICO 1: TICKETS POR ESTADO (GENERAL) ==========
    conteo_estados_general = defaultdict(int)
    for ticket in tickets_generales:
        for codigo, nombre in Ticket.ESTADOS_TICKET:
            if ticket.estado == codigo:
                conteo_estados_general[nombre] += 1
                break
    
    tickets_por_estado_general = [{'estado': k, 'total': v} for k, v in conteo_estados_general.items()]
    
    # ========== GRÁFICO 2: TICKETS POR ESTADO (PERÍODO) ==========
    conteo_estados_periodo = defaultdict(int)
    for ticket in tickets_periodo:
        for codigo, nombre in Ticket.ESTADOS_TICKET:
            if ticket.estado == codigo:
                conteo_estados_periodo[nombre] += 1
                break
    
    tickets_por_estado_periodo = [{'estado': k, 'total': v} for k, v in conteo_estados_periodo.items()]
    
    # ========== GRÁFICO: TICKETS POR CLIENTE ==========
    conteo_clientes = defaultdict(int)
    for ticket in tickets_generales:
        if ticket.cliente and ticket.cliente.nombre:
            conteo_clientes[ticket.cliente.nombre] += 1
    
    tickets_por_cliente = [{'cliente__nombre': k, 'total': v} for k, v in sorted(conteo_clientes.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    # ========== GRÁFICO: TENDENCIA ÚLTIMOS 30 DÍAS ==========
    fecha_limite = ahora - timedelta(days=30)
    conteo_por_dia = defaultdict(int)
    
    for ticket in tickets_generales:
        if ticket.fecha_creacion and ticket.fecha_creacion >= fecha_limite:
            fecha_str = ticket.fecha_creacion.date().isoformat()
            conteo_por_dia[fecha_str] += 1
    
    tickets_por_dia = [{'dia_str': k, 'total': v} for k, v in sorted(conteo_por_dia.items())]
    
    # ========== TABLA: ÚLTIMOS 10 TICKETS ==========
    ultimos_tickets = sorted(tickets_generales, key=lambda x: x.fecha_creacion if x.fecha_creacion else timezone.make_aware(datetime.min), reverse=True)[:10]
    
    # ========== TICKETS POR TIPO DE SERVICIO ==========
    conteo_servicio = defaultdict(int)
    for ticket in tickets_generales:
        if ticket.tipo_servicio and ticket.tipo_servicio.nombre:
            conteo_servicio[ticket.tipo_servicio.nombre] += 1
    
    tickets_por_servicio = [{'tipo_servicio__nombre': k, 'total': v} for k, v in sorted(conteo_servicio.items(), key=lambda x: x[1], reverse=True)]
    
    # ========== TICKETS POR PROYECTO ==========
    conteo_proyecto = defaultdict(int)
    for ticket in tickets_generales:
        if ticket.proyecto and ticket.proyecto.nombre:
            conteo_proyecto[ticket.proyecto.nombre] += 1
    
    tickets_por_proyecto = [{'proyecto__nombre': k, 'total': v} for k, v in sorted(conteo_proyecto.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    # ========== DATOS PARA GRÁFICOS (JSON) ==========
    chart_data = {
        # Gráfico general
        'estados_general_labels': json.dumps([item['estado'] for item in tickets_por_estado_general]),
        'estados_general_data': json.dumps([item['total'] for item in tickets_por_estado_general]),
        # Gráfico por período
        'estados_periodo_labels': json.dumps([item['estado'] for item in tickets_por_estado_periodo]),
        'estados_periodo_data': json.dumps([item['total'] for item in tickets_por_estado_periodo]),
        # Clientes
        'clientes_labels': json.dumps([item['cliente__nombre'] for item in tickets_por_cliente]),
        'clientes_data': json.dumps([item['total'] for item in tickets_por_cliente]),
        # Tendencia
        'tendencias_labels': json.dumps([item['dia_str'] for item in tickets_por_dia]),
        'tendencias_data': json.dumps([item['total'] for item in tickets_por_dia]),
    }
    
    context = {
        # Métricas
        'total_tickets': total_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_proceso': tickets_proceso,
        'tickets_activos': tickets_abiertos + tickets_proceso,
        'tickets_completados_periodo': tickets_completados_periodo,
        'tickets_sin_asignar': tickets_sin_asignar,
        'usuarios_activos': usuarios_activos,
        
        # Información del período
        'periodo_actual': periodo,
        'periodo_nombre': fechas_periodo['nombre'],
        'periodo_fecha_inicio': fechas_periodo['fecha_inicio'].strftime('%d/%m/%Y'),
        'periodo_fecha_fin': fechas_periodo['fecha_fin'].strftime('%d/%m/%Y'),
        'total_tickets_periodo': len(tickets_periodo),
        
        # Tablas
        'ultimos_tickets': ultimos_tickets,
        'tickets_por_servicio': tickets_por_servicio,
        'tickets_por_proyecto': tickets_por_proyecto,
        
        # Datos para gráficos (JSON)
        'chart_data': chart_data,
        
        # Filtros
        'clientes': Cliente.objects.filter(activo=True),
        'proyectos': Proyecto.objects.filter(activo=True).select_related('cliente'),
        'estados_disponibles': Ticket.ESTADOS_TICKET,
        
        # Opciones de período
        'periodos_disponibles': [
            ('mes_actual', 'Mes Actual'),
            ('mes_anterior', 'Mes Anterior'),
            ('trimestre', 'Trimestre Actual'),
            ('semestre', 'Semestre Actual'),
            ('anio', 'Año Actual'),
        ],
        
        # Valores seleccionados
        'cliente_selected': cliente_id or '',
        'proyecto_selected': proyecto_id or '',
        'estado_selected': estado or '',
        'fecha_desde': fecha_desde or '',
        'fecha_hasta': fecha_hasta or '',
    }
    
    return render(request, 'extractor/dashboard_lider.html', context)


def calcular_fechas_periodo(periodo, fecha_referencia):
    """Calcula las fechas de inicio y fin según el período seleccionado"""
    
    if periodo == 'mes_actual':
        fecha_inicio = fecha_referencia.replace(day=1)
        # Último día del mes
        ultimo_dia = calendar.monthrange(fecha_referencia.year, fecha_referencia.month)[1]
        fecha_fin = fecha_referencia.replace(day=ultimo_dia)
        nombre = f"{fecha_referencia.strftime('%B %Y')}"
        
    elif periodo == 'mes_anterior':
        if fecha_referencia.month == 1:
            fecha_inicio = fecha_referencia.replace(year=fecha_referencia.year - 1, month=12, day=1)
        else:
            fecha_inicio = fecha_referencia.replace(month=fecha_referencia.month - 1, day=1)
        # Último día del mes anterior
        ultimo_dia = calendar.monthrange(fecha_inicio.year, fecha_inicio.month)[1]
        fecha_fin = fecha_inicio.replace(day=ultimo_dia)
        nombre = f"{fecha_inicio.strftime('%B %Y')}"
        
    elif periodo == 'trimestre':
        trimestre = (fecha_referencia.month - 1) // 3 + 1
        mes_inicio = (trimestre - 1) * 3 + 1
        fecha_inicio = fecha_referencia.replace(month=mes_inicio, day=1)
        if trimestre == 1:
            fecha_fin = fecha_referencia.replace(month=3, day=31)
        elif trimestre == 2:
            fecha_fin = fecha_referencia.replace(month=6, day=30)
        elif trimestre == 3:
            fecha_fin = fecha_referencia.replace(month=9, day=30)
        else:
            fecha_fin = fecha_referencia.replace(month=12, day=31)
        nombre = f"Trimestre {trimestre} - {fecha_referencia.year}"
        
    elif periodo == 'semestre':
        semestre = 1 if fecha_referencia.month <= 6 else 2
        if semestre == 1:
            fecha_inicio = fecha_referencia.replace(month=1, day=1)
            fecha_fin = fecha_referencia.replace(month=6, day=30)
        else:
            fecha_inicio = fecha_referencia.replace(month=7, day=1)
            fecha_fin = fecha_referencia.replace(month=12, day=31)
        nombre = f"Semestre {semestre} - {fecha_referencia.year}"
        
    else:  # año
        fecha_inicio = fecha_referencia.replace(month=1, day=1)
        fecha_fin = fecha_referencia.replace(month=12, day=31)
        nombre = f"Año {fecha_referencia.year}"
    
    return {
        'nombre': nombre,
        'fecha_inicio': fecha_inicio.date() if hasattr(fecha_inicio, 'date') else fecha_inicio,
        'fecha_fin': fecha_fin.date() if hasattr(fecha_fin, 'date') else fecha_fin,
    }