"""
Vistas para CRUD de Tickets
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
import json
from datetime import datetime
from django.conf import settings 
from extractor.models import Ticket, Cliente, Proyecto, TipoServicio

@login_required
def ticket_list(request):
    """Listado de tickets con filtros y paginación"""

    from_dashboard = request.GET.get('from_dashboard') == 'true'
    
    # Si viene del dashboard, guardarlo en sesión para mantenerlo en navegación
    if from_dashboard:
        request.session['from_dashboard'] = True
    else:
        # Limpiar la sesión si no viene del dashboard
        request.session.pop('from_dashboard', None)

    # ✅ SOLO UNA DEFINICIÓN - QUERYSET NORMAL
    tickets = Ticket.objects.all().select_related('cliente', 'proyecto', 'tipo_servicio')

    # Filtros
    estado = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    proyecto_id = request.GET.get('proyecto')
    busqueda = request.GET.get('q')
    por_pagina = request.GET.get('por_pagina', 20)
    
    # Filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Filtro por nombre de cliente
    cliente_nombre = request.GET.get('cliente_nombre')

    # Aplicar filtros
    if estado:
        tickets = tickets.filter(estado=estado)
    
    if cliente_id:
        tickets = tickets.filter(cliente_id=cliente_id)
    
    if cliente_nombre:
        tickets = tickets.filter(cliente__nombre__icontains=cliente_nombre)
    
    if proyecto_id:
        tickets = tickets.filter(proyecto_id=proyecto_id)
    
    if busqueda:
        tickets = tickets.filter(
            Q(codigo__icontains=busqueda) |
            Q(nombre__icontains=busqueda) |
            Q(responsable_solicitud__icontains=busqueda) |
            Q(lider_proyecto__icontains=busqueda)
        )
    
    # Aplicar filtros de fecha
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            tickets = tickets.filter(fecha_creacion__date__gte=fecha_desde_obj)
        except (ValueError, TypeError):
            pass

    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            tickets = tickets.filter(fecha_creacion__date__lte=fecha_hasta_obj)
        except (ValueError, TypeError):
            pass

    orden = request.GET.get('orden', '-fecha_creacion')
    tickets = tickets.order_by(orden)

    # Paginación
    try:
        por_pagina = int(por_pagina)
        if por_pagina not in [10, 20, 50, 100]:
            por_pagina = 20
    except ValueError:
        por_pagina = 20
    
    paginator = Paginator(tickets, por_pagina)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estadísticas (considerando también los filtros de fecha para mostrar en tarjetas)
    tickets_generados = Ticket.objects.filter(estado='GENERADO').count()
    tickets_abiertos = Ticket.objects.filter(estado='ABIERTO').count()
    tickets_proceso = Ticket.objects.filter(estado='EN_PROCESO').count()
    tickets_completados = Ticket.objects.filter(estado='COMPLETADO').count()
    tickets_cancelados = Ticket.objects.filter(estado='CANCELADO').count()
    
    # 🆕 Estadísticas filtradas por fecha (para mostrar en el indicador)
    tickets_filtrados_count = tickets.count()
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'total_tickets': Ticket.objects.count(),
        'tickets_filtrados': tickets_filtrados_count,  # 🆕 Total con filtros aplicados
        'tickets_generados': tickets_generados + tickets_abiertos,
        'tickets_proceso': tickets_proceso,
        'tickets_completados': tickets_completados,
        'tickets_cancelados': tickets_cancelados,
        'clientes': Cliente.objects.filter(activo=True),
        'tipos_servicio': TipoServicio.objects.filter(activo=True),
        'proyectos': Proyecto.objects.filter(activo=True).select_related('cliente'),
        'estados_disponibles': Ticket.ESTADOS_TICKET,
        'estado_selected': estado,
        'cliente_selected': int(cliente_id) if cliente_id else 0,
        'proyecto_selected': int(proyecto_id) if proyecto_id else 0,
        'busqueda': busqueda or '',
        'orden_actual': orden,
        'por_pagina': por_pagina,
        'tickets_count': tickets.count(),
        'fecha_desde': fecha_desde or '',
        'fecha_hasta': fecha_hasta or '',
        'cliente_nombre': cliente_nombre or '',
        'from_dashboard': from_dashboard or request.session.get('from_dashboard', False),
        
    }
    return render(request, 'catalogos/ticket_list.html', context)


@login_required
def ticket_detail(request, id):
    """Detalle de un ticket"""
    ticket = get_object_or_404(Ticket, id=id)
    
    comentarios_lista = []
    if ticket.comentarios_seguimiento:
        comentarios_lista = ticket.comentarios_seguimiento.split('\n')
        comentarios_lista = [c for c in comentarios_lista if c.strip()]
    
    from extractor.models import Usuario
    usuarios_disponibles = Usuario.objects.filter(is_active=True).order_by('first_name', 'username')
    
    context = {
        'ticket': ticket,
        'comentarios_lista': comentarios_lista,
        'usuarios_disponibles': usuarios_disponibles,
    }
    return render(request, 'catalogos/ticket_detail.html', context)


@login_required
def ticket_delete(request, id):
    """Eliminar un ticket"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if request.method == 'POST':
        try:
            codigo = ticket.codigo
            ticket.delete()
            messages.success(request, f'✅ Ticket "{codigo}" eliminado exitosamente')
            return redirect('extractor:ticket_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar ticket: {str(e)}')
            return redirect('extractor:ticket_list')
    
    return render(request, 'catalogos/ticket_confirm_delete.html', {'ticket': ticket})

@login_required
def ticket_delete(request, id):
    """Eliminar un ticket"""
    ticket = get_object_or_404(Ticket, id=id)
    
    if request.method == 'POST':
        try:
            codigo = ticket.codigo
            ticket.delete()
            messages.success(request, f'✅ Ticket "{codigo}" eliminado exitosamente')
            return redirect('extractor:ticket_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar ticket: {str(e)}')
            return redirect('extractor:ticket_list')
    
    return render(request, 'catalogos/ticket_confirm_delete.html', {'ticket': ticket})