"""
Vistas para visualización de datos extraídos de Excel
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv
from django.utils import timezone
import logging
from django.conf import settings 

from extractor.models import ExcelData, Cliente, Proyecto, TipoServicio

logger = logging.getLogger(__name__)


@login_required
def data_list(request):
    """
    Listado de datos extraídos de archivos Excel
    """
    data = ExcelData.objects.all().order_by('-extracted_date')
    
    # Filtros
    cliente_id = request.GET.get('cliente')
    proyecto_id = request.GET.get('proyecto')
    tipo_prueba_id = request.GET.get('tipo_prueba')
    tipo_servicio = request.GET.get('tipo_servicio')
    busqueda = request.GET.get('q')
    
    if cliente_id:
        data = data.filter(cliente=cliente_id)
    if proyecto_id:
        data = data.filter(proyecto=proyecto_id)
    if tipo_prueba_id:
        data = data.filter(tipo_pruebas=tipo_prueba_id)
    if tipo_servicio:
        data = data.filter(tipo_servicio=tipo_servicio)
    if busqueda:
        data = data.filter(
            Q(responsable_solicitud__icontains=busqueda) |
            Q(lider_proyecto__icontains=busqueda) |
            Q(numero_version__icontains=busqueda) |
            Q(funcionalidad_liberacion__icontains=busqueda) |
            Q(ticket_code__icontains=busqueda)
        )
    
    # Paginación
    por_pagina = request.GET.get('por_pagina', 20)
    try:
        por_pagina = int(por_pagina)
        if por_pagina not in [10, 20, 50, 100]:
            por_pagina = 20
    except ValueError:
        por_pagina = 20
    
    paginator = Paginator(data, por_pagina)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener listas para filtros
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    proyectos = Proyecto.objects.filter(activo=True).order_by('nombre')
    tipos_prueba = TipoServicio.objects.filter(activo=True).order_by('nombre')
    tipos_servicio_opciones = ExcelData.objects.values_list('tipo_servicio', flat=True).distinct().order_by('tipo_servicio')
    
    context = {
        'data_list': page_obj,
        'page_obj': page_obj,
        'total_registros': ExcelData.objects.count(),
        'clientes': clientes,
        'proyectos': proyectos,
        'tipos_prueba': tipos_prueba,
        'tipos_servicio_opciones': [t for t in tipos_servicio_opciones if t],
        'filtro_cliente': cliente_id,
        'filtro_proyecto': proyecto_id,
        'filtro_tipo_prueba': tipo_prueba_id,
        'filtro_tipo_servicio': tipo_servicio,
        'busqueda': busqueda or '',
        'por_pagina': por_pagina,
        'debug': settings.DEBUG,
    }
    return render(request, 'extractor/list.html', context)


@login_required
def export_data_csv(request):
    """
    Exporta los datos de Excel a CSV
    """
    try:
        data = ExcelData.objects.all().order_by('-extracted_date')
        
        # Aplicar filtros si vienen en GET
        cliente_id = request.GET.get('cliente')
        proyecto_id = request.GET.get('proyecto')
        tipo_prueba_id = request.GET.get('tipo_prueba')
        tipo_servicio = request.GET.get('tipo_servicio')
        busqueda = request.GET.get('q')
        
        if cliente_id:
            data = data.filter(cliente=cliente_id)
        if proyecto_id:
            data = data.filter(proyecto=proyecto_id)
        if tipo_prueba_id:
            data = data.filter(tipo_pruebas=tipo_prueba_id)
        if tipo_servicio:
            data = data.filter(tipo_servicio=tipo_servicio)
        if busqueda:
            data = data.filter(
                Q(responsable_solicitud__icontains=busqueda) |
                Q(lider_proyecto__icontains=busqueda) |
                Q(numero_version__icontains=busqueda) |
                Q(ticket_code__icontains=busqueda)
            )
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"datos_excel_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Cliente', 'Proyecto', 'Tipo Pruebas', 'Tipo Servicio',
            'Responsable Solicitud', 'Líder Proyecto', 'Tipo Aplicación',
            'Número Versión', 'Funcionalidad Liberación', 'Detalle Cambios',
            'Justificación Cambio', 'Ticket Code', 'Fecha Extracción'
        ])
        
        for item in data:
            # Obtener nombres en lugar de IDs
            cliente_nombre = ""
            try:
                if item.cliente and item.cliente.isdigit():
                    cliente = Cliente.objects.filter(id=int(item.cliente)).first()
                    cliente_nombre = cliente.nombre if cliente else item.cliente
                else:
                    cliente_nombre = item.cliente
            except:
                cliente_nombre = item.cliente
            
            proyecto_nombre = ""
            try:
                if item.proyecto and item.proyecto.isdigit():
                    proyecto = Proyecto.objects.filter(id=int(item.proyecto)).first()
                    proyecto_nombre = proyecto.nombre if proyecto else item.proyecto
                else:
                    proyecto_nombre = item.proyecto
            except:
                proyecto_nombre = item.proyecto
            
            tipo_pruebas_nombre = ""
            try:
                if item.tipo_pruebas and item.tipo_pruebas.isdigit():
                    tipo = TipoServicio.objects.filter(id=int(item.tipo_pruebas)).first()
                    tipo_pruebas_nombre = tipo.nombre if tipo else item.tipo_pruebas
                else:
                    tipo_pruebas_nombre = item.tipo_pruebas
            except:
                tipo_pruebas_nombre = item.tipo_pruebas
            
            writer.writerow([
                item.id,
                cliente_nombre,
                proyecto_nombre,
                tipo_pruebas_nombre,
                item.tipo_servicio,
                item.responsable_solicitud,
                item.lider_proyecto,
                item.tipo_aplicacion,
                item.numero_version,
                item.funcionalidad_liberacion,
                item.detalle_cambios,
                item.justificacion_cambio,
                item.ticket_code,
                item.extracted_date.strftime('%d/%m/%Y %H:%M:%S') if item.extracted_date else ''
            ])
        
        logger.info(f"Usuario {request.user} exportó datos Excel - {data.count()} registros")
        return response
        
    except Exception as e:
        logger.error(f"Error exportando datos Excel: {str(e)}", exc_info=True)
        from django.contrib import messages
        messages.error(request, "Error al exportar datos")
        return redirect('extractor:data_list')


@login_required
def data_detail(request, id):
    """
    Ver detalle de un registro de datos extraído
    """
    from django.shortcuts import get_object_or_404
    
    data_item = get_object_or_404(ExcelData, id=id)
    
    # Obtener nombres en lugar de IDs para mostrar
    cliente_nombre = ""
    try:
        if data_item.cliente and data_item.cliente.isdigit():
            cliente = Cliente.objects.filter(id=int(data_item.cliente)).first()
            cliente_nombre = cliente.nombre if cliente else data_item.cliente
        else:
            cliente_nombre = data_item.cliente
    except:
        cliente_nombre = data_item.cliente
    
    proyecto_nombre = ""
    try:
        if data_item.proyecto and data_item.proyecto.isdigit():
            proyecto = Proyecto.objects.filter(id=int(data_item.proyecto)).first()
            proyecto_nombre = proyecto.nombre if proyecto else data_item.proyecto
        else:
            proyecto_nombre = data_item.proyecto
    except:
        proyecto_nombre = data_item.proyecto
    
    tipo_pruebas_nombre = ""
    try:
        if data_item.tipo_pruebas and data_item.tipo_pruebas.isdigit():
            tipo = TipoServicio.objects.filter(id=int(data_item.tipo_pruebas)).first()
            tipo_pruebas_nombre = tipo.nombre if tipo else data_item.tipo_pruebas
        else:
            tipo_pruebas_nombre = data_item.tipo_pruebas
    except:
        tipo_pruebas_nombre = data_item.tipo_pruebas
    
    context = {
        'data': data_item,
        'cliente_nombre': cliente_nombre,
        'proyecto_nombre': proyecto_nombre,
        'tipo_pruebas_nombre': tipo_pruebas_nombre,
        'debug': settings.DEBUG,
    }
    return render(request, 'extractor/data_detail.html', context)