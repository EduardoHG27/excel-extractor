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
from django.db import connections
from django.db.utils import ProgrammingError
from extractor.models import Ticket, Cliente, Proyecto, Usuario


def es_lider_pruebas(user):
    """Verifica si el usuario es líder de pruebas"""
    if not user.is_authenticated:
        return False
    
    try:
        return user.is_superuser or getattr(user, 'es_lider_pruebas', False) or user.groups.filter(name='Lideres').exists()
    except ProgrammingError as e:
        if 'relation "extractor_usuario_groups" does not exist' in str(e):
            return user.is_superuser or getattr(user, 'es_lider_pruebas', False)
        raise

@login_required
@user_passes_test(es_lider_pruebas, login_url='extractor:ticket_list')
def dashboard_lider(request):
    """
    Dashboard para líder de pruebas.
    Versión compatible con SQLite.
    """
    usuario = request.user
    
    # Verificar si existe la tabla antes de usarla
    es_lider = getattr(usuario, 'es_lider_pruebas', False)
    
    if not es_lider:
        try:
            # Intenta usar la relación groups
            es_lider = usuario.groups.filter(name='Lideres').exists()
        except ProgrammingError as e:
            # Si la tabla no existe, intenta verificar por nombre de usuario o flag
            if 'relation "extractor_usuario_groups" does not exist' in str(e):
                # Fallback: verificar si es admin o tiene flag en el perfil
                es_lider = usuario.is_superuser or getattr(usuario, 'es_lider', False)
            else:
                raise
    # ========== OBTENER PARÁMETROS ==========
    cliente_id = request.GET.get('cliente')
    proyecto_id = request.GET.get('proyecto')
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    periodo = request.GET.get('periodo', 'mes_actual')  # mes_actual, mes_anterior, trimestre, semestre, año
    
    # ========== OBTENER TODOS LOS TICKETS ==========
    tickets = Ticket.objects.all().select_related('cliente', 'proyecto', 'tipo_servicio', 'asignado_a', 'creado_por')
    
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
    estado_codigos = {}  # Para mapear nombre a código
    
    for ticket in tickets_generales:
        for codigo, nombre in Ticket.ESTADOS_TICKET:
            if ticket.estado == codigo:
                conteo_estados_general[nombre] += 1
                estado_codigos[nombre] = codigo
                break
    
    tickets_por_estado_general = [{'estado': k, 'total': v, 'codigo': estado_codigos.get(k, k)} 
                                   for k, v in conteo_estados_general.items()]
    
    # ========== GRÁFICO 2: TICKETS POR ESTADO (PERÍODO) ==========
    conteo_estados_periodo = defaultdict(int)
    estado_codigos_periodo = {}
    
    for ticket in tickets_periodo:
        for codigo, nombre in Ticket.ESTADOS_TICKET:
            if ticket.estado == codigo:
                conteo_estados_periodo[nombre] += 1
                estado_codigos_periodo[nombre] = codigo
                break
    
    tickets_por_estado_periodo = [{'estado': k, 'total': v, 'codigo': estado_codigos_periodo.get(k, k)} 
                                   for k, v in conteo_estados_periodo.items()]
    
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
    
    # ========== NUEVO: DATOS PARA TABLAS DE GRÁFICAS ==========
    # Datos para gráfica general
    datos_graficas_general = []
    total_general = sum(item['total'] for item in tickets_por_estado_general)
    
    for item in tickets_por_estado_general:
        porcentaje = (item['total'] / total_general * 100) if total_general > 0 else 0
        datos_graficas_general.append({
            'nombre': item['estado'],
            'codigo': item['codigo'],
            'cantidad': item['total'],
            'porcentaje': porcentaje
        })
    
    # Datos para gráfica por período
    datos_graficas_periodo = []
    total_periodo = sum(item['total'] for item in tickets_por_estado_periodo)
    
    for item in tickets_por_estado_periodo:
        porcentaje = (item['total'] / total_periodo * 100) if total_periodo > 0 else 0
        datos_graficas_periodo.append({
            'nombre': item['estado'],
            'codigo': item['codigo'],
            'cantidad': item['total'],
            'porcentaje': porcentaje
        })
    
    # ========== NUEVO: RESUMEN DE USUARIOS CON TICKETS POR MES ==========
    from django.db.models import Count, Q
    from django.db.models.functions import TruncMonth
    
    resumen_usuarios = []
    top_usuarios_por_mes = {}
    
    # Obtener todos los usuarios activos
    usuarios_activos_qs = Usuario.objects.filter(is_active=True)
    
    for usuario in usuarios_activos_qs:
        # Tickets del usuario (asignados o creados por él)
        tickets_usuario = Ticket.objects.filter(
            Q(asignado_a=usuario) | Q(creado_por=usuario)
        )
        
        # Aplicar los mismos filtros de cliente, proyecto, etc. a los tickets del usuario
        tickets_usuario_list = list(tickets_usuario)
        
        if cliente_id and cliente_id != '':
            tickets_usuario_list = [t for t in tickets_usuario_list if t.cliente_id == int(cliente_id)]
        
        if proyecto_id and proyecto_id != '':
            tickets_usuario_list = [t for t in tickets_usuario_list if t.proyecto_id == int(proyecto_id)]
        
        if estado and estado != '':
            tickets_usuario_list = [t for t in tickets_usuario_list if t.estado == estado]
        
        if fecha_desde:
            tickets_usuario_list = [t for t in tickets_usuario_list if t.fecha_creacion and t.fecha_creacion.date() >= fecha_desde_obj] if 'fecha_desde_obj' in locals() else tickets_usuario_list
        
        if fecha_hasta:
            tickets_usuario_list = [t for t in tickets_usuario_list if t.fecha_creacion and t.fecha_creacion.date() <= fecha_hasta_obj] if 'fecha_hasta_obj' in locals() else tickets_usuario_list
        
        # Tickets por mes (usando los tickets filtrados)
        tickets_por_mes = defaultdict(int)
        for ticket in tickets_usuario_list:
            if ticket.fecha_creacion:
                mes_key = ticket.fecha_creacion.strftime('%B %Y')
                tickets_por_mes[mes_key] += 1
        
        # Obtener últimos 6 meses
        meses_ordenados = sorted(tickets_por_mes.items(), key=lambda x: datetime.strptime(x[0], '%B %Y'), reverse=True)[:6]
        
        tickets_mes_list = []
        for mes_nombre, cantidad in meses_ordenados:
            tickets_mes_list.append({
                'mes_nombre': mes_nombre,
                'cantidad': cantidad
            })
        
        total_tickets_usuario = len(tickets_usuario_list)
        promedio = total_tickets_usuario / 6 if len(tickets_por_mes) > 0 else 0
        
        # Verificar si el usuario es líder (ajusta según tu modelo)
        try:
            es_lider = getattr(usuario, 'es_lider_pruebas', False) or usuario.groups.filter(name='Lideres').exists()
        except ProgrammingError as e:
            if 'relation "extractor_usuario_groups" does not exist' in str(e):
                es_lider = getattr(usuario, 'es_lider_pruebas', False) or usuario.is_superuser
            else:
                raise
        resumen_usuarios.append({
            'id': usuario.id,
            'nombre_completo': usuario.get_full_name() or usuario.username,
            'es_lider': es_lider,
            'total_tickets': total_tickets_usuario,
            'tickets_por_mes': tickets_mes_list,
            'promedio_mensual': promedio
        })
        
        # Para top usuarios por mes
        for ticket in tickets_usuario_list:
            if ticket.fecha_creacion:
                mes_key = ticket.fecha_creacion.strftime('%B %Y')
                if mes_key not in top_usuarios_por_mes:
                    top_usuarios_por_mes[mes_key] = {}
                
                nombre_usuario = usuario.get_full_name() or usuario.username
                if nombre_usuario not in top_usuarios_por_mes[mes_key]:
                    top_usuarios_por_mes[mes_key][nombre_usuario] = {
                        'nombre': nombre_usuario,
                        'total': 0,
                        'es_lider': es_lider
                    }
                top_usuarios_por_mes[mes_key][nombre_usuario]['total'] += 1
    
    # Convertir top usuarios por mes a lista ordenada
    top_usuarios_por_mes_ordenado = {}
    for mes, usuarios_dict in top_usuarios_por_mes.items():
        usuarios_list = list(usuarios_dict.values())
        usuarios_list.sort(key=lambda x: x['total'], reverse=True)
        top_usuarios_por_mes_ordenado[mes] = usuarios_list[:5]
    
    # Ordenar resumen de usuarios por total de tickets
    resumen_usuarios.sort(key=lambda x: x['total_tickets'], reverse=True)
    



    resumen_estados_usuarios = []
    
    for usuario in usuarios_activos_qs:
        # Tickets del usuario (asignados o creados por él)
        tickets_usuario = Ticket.objects.filter(
            Q(asignado_a=usuario) | Q(creado_por=usuario)
        )
        
        # Aplicar filtros
        tickets_usuario_list = list(tickets_usuario)
        
        if cliente_id and cliente_id != '':
            tickets_usuario_list = [t for t in tickets_usuario_list if t.cliente_id == int(cliente_id)]
        
        if proyecto_id and proyecto_id != '':
            tickets_usuario_list = [t for t in tickets_usuario_list if t.proyecto_id == int(proyecto_id)]
        
        # Contar por estado
        abiertos = len([t for t in tickets_usuario_list if t.estado in ['ABIERTO', 'GENERADO']])
        en_proceso = len([t for t in tickets_usuario_list if t.estado == 'EN_PROCESO'])
        completados = len([t for t in tickets_usuario_list if t.estado == 'COMPLETADO'])
        cancelados = len([t for t in tickets_usuario_list if t.estado == 'CANCELADO'])
        total = len(tickets_usuario_list)
        
        # Tasa de éxito (completados / total de no cancelados)
        tickets_evaluables = total - cancelados
        tasa_exito = (completados / tickets_evaluables * 100) if tickets_evaluables > 0 else 0
        
        try:
            es_lider = getattr(usuario, 'es_lider_pruebas', False) or usuario.groups.filter(name='Lideres').exists()
        except ProgrammingError as e:
            if 'relation "extractor_usuario_groups" does not exist' in str(e):
                es_lider = getattr(usuario, 'es_lider_pruebas', False) or usuario.is_superuser
            else:
                raise
        # Determinar rol
        rol = "Líder de Pruebas" if es_lider else "Tester"
        
        resumen_estados_usuarios.append({
            'id': usuario.id,
            'nombre_completo': usuario.get_full_name() or usuario.username,
            'es_lider': es_lider,
            'rol': rol,
            'total_tickets': total,
            'abiertos': abiertos,
            'en_proceso': en_proceso,
            'completados': completados,
            'cancelados': cancelados,
            'tasa_exito': tasa_exito
        })
    
    # Ordenar por total de tickets
    resumen_estados_usuarios.sort(key=lambda x: x['total_tickets'], reverse=True)

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
        
        # NUEVOS DATOS PARA TABLAS
        'datos_graficas_general': datos_graficas_general,
        'datos_graficas_periodo': datos_graficas_periodo,
        'resumen_usuarios': resumen_usuarios,
        'top_usuarios_por_mes': top_usuarios_por_mes_ordenado,
        
         # NUEVO: Resumen de estados por usuario
        'resumen_estados_usuarios': resumen_estados_usuarios,
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