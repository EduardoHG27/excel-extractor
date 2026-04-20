"""
Vistas para procesamiento de archivos Excel
"""
import os
import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.forms import ValidationError
from django.utils import timezone
from django.conf import settings  
from extractor.models import Cliente, Proyecto, TipoServicio, ExcelData, Ticket, SolicitudPruebas
from ..services.extractor_service import extract_excel_data, find_object_by_name_or_id
from ..services.ticket_generator import generate_and_save_ticket


@login_required
def upload_excel(request):
    """Procesa la carga de archivos Excel y genera tickets"""
    if request.method == 'POST':
        fs = FileSystemStorage()
        file_path = None
        
        try:
            tipo_servicio_form = request.POST.get('tipo_servicio', '').strip()
            excel_file = request.FILES.get('excel_file')
            
            # Validaciones
            if not tipo_servicio_form:
                messages.error(request, 'Por favor selecciona un tipo de servicio')
                return render(request, 'extractor/upload.html')
            
            if not excel_file:
                messages.error(request, 'Por favor selecciona un archivo Excel')
                return render(request, 'extractor/upload.html')
            
            # Validar extensión
            file_extension = os.path.splitext(excel_file.name)[1].lower()
            if file_extension not in ['.xlsx', '.xls']:
                messages.error(request, 'Formato no válido. Solo .xlsx y .xls')
                return render(request, 'extractor/upload.html')
            
            # Validar nombre con SolicitudPruebas
            nombre_archivo_subido = excel_file.name
            solicitud = SolicitudPruebas.objects.filter(
                nombre_archivo=nombre_archivo_subido,
                tiene_ticket=False
            ).first()
            solicitud_encontrada = solicitud is not None
            
            # Guardar archivo temporal
            filename = fs.save(excel_file.name, excel_file)
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            
            # Extraer datos
            extracted_data = extract_excel_data(file_path)
            
            # Validar campos obligatorios
            campos_obligatorios = ['cliente', 'proyecto', 'tipo_pruebas']
            campos_faltantes = [c for c in campos_obligatorios if not extracted_data.get(c)]
            
            if campos_faltantes:
                raise ValidationError(f"Faltan campos: {', '.join(campos_faltantes)}")
            
            # Buscar objetos
            cliente_obj = find_object_by_name_or_id(Cliente, extracted_data.get('cliente', ''), 'nombre')
            proyecto_obj = find_object_by_name_or_id(Proyecto, extracted_data.get('proyecto', ''), 'nombre')
            tipo_prueba_obj = find_object_by_name_or_id(TipoServicio, extracted_data.get('tipo_pruebas', ''), 'nombre')
            
            # Validar objetos encontrados
            objetos_no_encontrados = []
            if not cliente_obj:
                objetos_no_encontrados.append(f"Cliente '{extracted_data.get('cliente', '')}'")
            if not proyecto_obj:
                objetos_no_encontrados.append(f"Proyecto '{extracted_data.get('proyecto', '')}'")
            if not tipo_prueba_obj:
                objetos_no_encontrados.append(f"Tipo de Pruebas '{extracted_data.get('tipo_pruebas', '')}'")
            
            if objetos_no_encontrados:
                raise ValidationError(f"No se encontraron: {', '.join(objetos_no_encontrados)}")
            
            # Validar pertenencia
            if proyecto_obj.cliente_id != cliente_obj.id:
                raise ValidationError(f'El proyecto "{proyecto_obj.nombre}" no pertenece al cliente "{cliente_obj.nombre}"')
            
            # Generar ticket
            nomenclaturas = {
                'cliente_nomenclatura': cliente_obj.nomenclatura,
                'proyecto_nomenclatura': proyecto_obj.codigo,
                'tipo_pruebas_nomenclatura': tipo_prueba_obj.nomenclatura,
                'tipo_servicio_nomenclatura': tipo_servicio_form
            }
            
            objetos_encontrados = {
                'cliente_obj': cliente_obj,
                'proyecto_obj': proyecto_obj,
                'tipo_servicio_obj': tipo_prueba_obj
            }
            
            ticket_code, ticket_obj = generate_and_save_ticket(
                extracted_data,
                tipo_servicio_form,
                nomenclaturas,
                objetos_encontrados,
                request
            )
            
            # Crear Jira issue
            if ticket_obj:
                _create_jira_issue(ticket_obj, extracted_data, cliente_obj, proyecto_obj, tipo_servicio_form, request)
            
           ###cosa comentada
            
            # Actualizar solicitud
            if solicitud_encontrada and solicitud:
                solicitud.ticket = ticket_obj
                solicitud.tiene_ticket = True
                solicitud.fecha_asociacion_ticket = timezone.now()
                solicitud.save()
            
            messages.success(request, f'✅ Ticket generado: {ticket_code}')
            return redirect('extractor:ticket_detail', id=ticket_obj.id)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'extractor/upload.html')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'extractor/upload.html')
            
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error al eliminar archivo: {e}")
    
    return render(request, 'extractor/upload.html')


def _create_jira_issue(ticket_obj, extracted_data, cliente_obj, proyecto_obj, tipo_servicio_form, request):
    """Helper para crear issue en Jira"""
    try:
        from extractor.jira_helper import JiraClient
        
        jira_data = {
            'codigo': ticket_obj.codigo,
            'cliente': cliente_obj.nombre,
            'proyecto': proyecto_obj.nombre,
            'tipo_servicio': tipo_servicio_form,
            'responsable_solicitud': extracted_data.get('responsable_solicitud', ''),
            'lider_proyecto': extracted_data.get('lider_proyecto', ''),
            'numero_version': extracted_data.get('numero_version', ''),
            'funcionalidad_liberacion': extracted_data.get('funcionalidad_liberacion', ''),
            'detalle_cambios': extracted_data.get('detalle_cambios', ''),
            'justificacion_cambio': extracted_data.get('justificacion_cambio', ''),
            'fecha': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'usuario': request.user.username if request.user.is_authenticated else 'Sistema',
        }
        
        jira_client = JiraClient()
        jira_issue = jira_client.create_issue(jira_data)
        
        if jira_issue:
            ticket_obj.jira_issue_key = jira_issue.key
            ticket_obj.jira_issue_url = jira_issue.permalink()
            ticket_obj.fecha_sincronizacion_jira = timezone.now()
            ticket_obj.save()
            messages.info(request, f'📋 Incidencia creada en Jira: {jira_issue.key}')
            
    except Exception as e:
        print(f"⚠️ Error en integración Jira: {e}")