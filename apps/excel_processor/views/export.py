"""
Vistas para exportaciones generales (CSV, ZIP backups)
"""
import csv
import zipfile
import io
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import logging

from extractor.models import Cliente, Proyecto, TipoServicio, Ticket, ExcelData, SolicitudPruebas, Usuario

logger = logging.getLogger(__name__)


@login_required
def export_table_csv(request, table_name):
    """
    Exporta una tabla específica a formato CSV
    """
    try:
        models_map = {
            'cliente': Cliente,
            'proyecto': Proyecto,
            'tiposervicio': TipoServicio,
            'ticket': Ticket,
            'exceldata': ExcelData,
            'solicitudpruebas': SolicitudPruebas,
            'usuario': Usuario,
        }
        
        if table_name.lower() not in models_map:
            return HttpResponse("Tabla no encontrada", status=404)
        
        model = models_map[table_name.lower()]
        queryset = model.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        filename = f"{table_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        headers = [field.name for field in model._meta.fields]
        writer.writerow(headers)
        
        for obj in queryset:
            row = []
            for field in headers:
                value = getattr(obj, field)
                if value is None:
                    row.append('')
                elif hasattr(value, 'strftime'):
                    row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                elif hasattr(value, 'pk'):
                    row.append(value.pk)
                else:
                    row.append(str(value))
            writer.writerow(row)
        
        logger.info(f"Usuario {request.user} exportó tabla {table_name} - {queryset.count()} registros")
        return response
        
    except Exception as e:
        logger.error(f"ERROR en export_table_csv: {str(e)}", exc_info=True)
        return HttpResponseServerError(f"Error al exportar: {str(e)}")


@login_required
def export_all_tables_backup(request):
    """
    Exporta todas las tablas como CSV en un archivo ZIP
    """
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            models_to_export = {
                'clientes': Cliente,
                'proyectos': Proyecto,
                'tipos_servicio': TipoServicio,
                'tickets': Ticket,
                'datos_excel': ExcelData,
                'solicitudes_pruebas': SolicitudPruebas,
                'usuarios': Usuario,
            }
            
            for filename, model in models_to_export.items():
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                
                queryset = model.objects.all()
                
                headers = [field.name for field in model._meta.fields]
                writer.writerow(headers)
                
                for obj in queryset:
                    row = []
                    for field in headers:
                        value = getattr(obj, field)
                        if value is None:
                            row.append('')
                        elif hasattr(value, 'strftime'):
                            row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                        elif hasattr(value, 'pk'):
                            row.append(value.pk)
                        else:
                            row.append(str(value))
                    writer.writerow(row)
                
                csv_content = csv_buffer.getvalue().encode('utf-8-sig')
                zip_file.writestr(f"{filename}.csv", csv_content)
        
        zip_buffer.seek(0)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="backup_completo_{timestamp}.zip"'
        
        logger.info(f"Usuario {request.user} realizó backup completo de la base de datos")
        return response
        
    except Exception as e:
        logger.error(f"ERROR en export_all_tables_backup: {str(e)}", exc_info=True)
        return HttpResponseServerError(f"Error al crear backup: {str(e)}")


@login_required
def export_clientes_csv(request):
    """Exporta clientes a CSV"""
    try:
        clientes = Cliente.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clientes_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Nomenclatura', 'Activo', 'Fecha Creación'])
        
        for cliente in clientes:
            writer.writerow([
                cliente.id,
                cliente.nombre,
                cliente.nomenclatura,
                'Sí' if cliente.activo else 'No',
                cliente.fecha_creacion.strftime('%d/%m/%Y %H:%M') if cliente.fecha_creacion else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando clientes: {str(e)}")
        from django.contrib import messages
        messages.error(request, "Error al exportar clientes")
        return redirect('extractor:clientes_list')


@login_required
def export_proyectos_csv(request):
    """Exporta proyectos a CSV"""
    try:
        proyectos = Proyecto.objects.all().select_related('cliente')
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"proyectos_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Cliente', 'Nombre', 'Código', 'Descripción', 'Activo', 'Fecha Inicio', 'Fecha Fin'])
        
        for proyecto in proyectos:
            writer.writerow([
                proyecto.id,
                proyecto.cliente.nombre if proyecto.cliente else '',
                proyecto.nombre,
                proyecto.codigo,
                proyecto.descripcion or '',
                'Sí' if proyecto.activo else 'No',
                proyecto.fecha_inicio.strftime('%d/%m/%Y') if proyecto.fecha_inicio else '',
                proyecto.fecha_fin.strftime('%d/%m/%Y') if proyecto.fecha_fin else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando proyectos: {str(e)}")
        from django.contrib import messages
        messages.error(request, "Error al exportar proyectos")
        return redirect('extractor:proyectos_list')


@login_required
def export_tipos_servicio_csv(request):
    """Exporta tipos de servicio a CSV"""
    try:
        tipos = TipoServicio.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tipos_servicio_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Nomenclatura', 'Activo', 'Fecha Creación'])
        
        for tipo in tipos:
            writer.writerow([
                tipo.id,
                tipo.nombre,
                tipo.nomenclatura,
                'Sí' if tipo.activo else 'No',
                tipo.fecha_creacion.strftime('%d/%m/%Y %H:%M') if tipo.fecha_creacion else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando tipos de servicio: {str(e)}")
        from django.contrib import messages
        messages.error(request, "Error al exportar tipos de servicio")
        return redirect('extractor:tipos_servicio_list')