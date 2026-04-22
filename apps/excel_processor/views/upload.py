# ============ upload.py - VERSIÓN SIN MAGIC ============

"""
Vistas para procesamiento de archivos Excel
"""
import os
import re
import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.forms import ValidationError
from django.utils import timezone
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from extractor.models import Cliente, Proyecto, TipoServicio, ExcelData, Ticket, SolicitudPruebas
from ..services.extractor_service import extract_excel_data, find_object_by_name_or_id
from ..services.ticket_generator import generate_and_save_ticket

import logging
logger = logging.getLogger('security')

# Configuración de seguridad
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILENAME_LENGTH = 100

def validate_file_security(uploaded_file: UploadedFile) -> tuple[bool, str]:
    """
    Validación exhaustiva de seguridad para archivos subidos
    
    Returns:
        (is_valid, error_message)
    """
    
    # 1. Validar tamaño
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // 1024 // 1024}MB"
    
    if uploaded_file.size == 0:
        return False, "El archivo está vacío"
    
    # 2. Validar nombre del archivo (prevenir path traversal)
    filename = uploaded_file.name
    if not filename:
        return False, "Nombre de archivo inválido"
    
    # Prevenir caracteres peligrosos
    dangerous_chars = ['..', '/', '\\', '%00', '\x00', ';', '&', '$', '`', '|']
    for char in dangerous_chars:
        if char in filename:
            return False, f"El nombre del archivo contiene caracteres no permitidos: {char}"
    
    # Limitar longitud
    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"El nombre del archivo es demasiado largo (máximo {MAX_FILENAME_LENGTH} caracteres)"
    
    # 3. Validar extensión
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension not in ['.xlsx', '.xls']:
        return False, "Formato no válido. Solo se permiten archivos .xlsx o .xls"
    
    # 4. Leer primeros bytes para verificar firma de archivo Excel
    try:
        file_content = uploaded_file.read(1024)
        uploaded_file.seek(0)  # Reiniciar puntero
        
        # Verificar firma de archivo Excel
        # Para .xlsx (PK signature - ZIP)
        if file_extension == '.xlsx':
            if not (file_content[:4] == b'PK\x03\x04' or file_content[:4] == b'PK\x05\x06'):
                return False, "El archivo .xlsx no parece ser un Excel válido"
        
        # Para .xls (D0 CF 11 E0 signature - OLE)
        elif file_extension == '.xls':
            if not (file_content[:4] == b'\xD0\xCF\x11\xE0'):
                return False, "El archivo .xls no parece ser un Excel válido"
                
    except Exception as e:
        logger.error(f"Error validando firma del archivo: {e}")
        return False, "No se pudo validar el tipo de archivo"
    
    # 5. Detectar macros maliciosas
    if b'vbaProject' in file_content or b'_VBA_PROJECT' in file_content:
        logger.warning(f"Archivo con macros detectado: {filename}")
        return False, "Los archivos con macros no están permitidos por razones de seguridad"
    
    # 6. Generar hash del archivo (opcional, para detección de duplicados)
    uploaded_file.seek(0)
    file_hash = hashlib.sha256(uploaded_file.read()).hexdigest()
    uploaded_file.seek(0)
    
    # 7. Verificar si es un archivo Excel válido
    try:
        import openpyxl
        from openpyxl import load_workbook
        
        # Intentar cargar para validar estructura
        wb = load_workbook(uploaded_file, data_only=True, read_only=True)
        wb.close()
        uploaded_file.seek(0)  # Reiniciar puntero después de la validación
        
    except Exception as e:
        return False, f"El archivo Excel parece estar dañado o corrupto: {str(e)[:100]}"
    
    return True, ""

@login_required
@csrf_protect
@never_cache
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def upload_excel(request):
    """Procesa la carga de archivos Excel y genera tickets"""
    
    # Log de seguridad
    logger.info(f"Intento de carga de archivo por usuario {request.user.username} desde IP {request.META.get('REMOTE_ADDR')}")
    
    if request.method == 'POST':
        fs = FileSystemStorage()
        file_path = None
        
        try:
            tipo_servicio_form = request.POST.get('tipo_servicio', '').strip()
            excel_file = request.FILES.get('excel_file')
            
            # Validaciones básicas
            if not tipo_servicio_form:
                messages.error(request, 'Por favor selecciona un tipo de servicio')
                return render(request, 'extractor/upload.html')
            
            if not excel_file:
                messages.error(request, 'Por favor selecciona un archivo Excel')
                return render(request, 'extractor/upload.html')
            
            # Validación de seguridad avanzada
            is_valid, error_msg = validate_file_security(excel_file)
            if not is_valid:
                logger.warning(f"Archivo rechazado para usuario {request.user.username}: {error_msg}")
                messages.error(request, f'Archivo inválido: {error_msg}')
                return render(request, 'extractor/upload.html')
            
            # Sanitizar nombre del archivo
            safe_filename = re.sub(r'[^\w\-_\.]', '_', excel_file.name)
            
            # Validar solicitud existente
            solicitud = SolicitudPruebas.objects.filter(
                nombre_archivo=excel_file.name,
                tiene_ticket=False
            ).first()
            solicitud_encontrada = solicitud is not None
            
            # Guardar archivo temporal con nombre seguro
            filename = fs.save(safe_filename, excel_file)
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            
            # Extraer datos
            extracted_data = extract_excel_data(file_path)
            
            # Validar y sanitizar datos extraídos
            extracted_data = sanitize_extracted_data(extracted_data)
            
            # Validar campos obligatorios
            campos_obligatorios = ['cliente', 'proyecto', 'tipo_pruebas']
            campos_faltantes = [c for c in campos_obligatorios if not extracted_data.get(c)]
            
            if campos_faltantes:
                raise ValidationError(f"Faltan campos en el Excel: {', '.join(campos_faltantes)}")
            
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
                raise ValidationError(f"No se encontraron en la base de datos: {', '.join(objetos_no_encontrados)}")
            
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
            
            # Actualizar solicitud
            if solicitud_encontrada and solicitud:
                solicitud.ticket = ticket_obj
                solicitud.tiene_ticket = True
                solicitud.fecha_asociacion_ticket = timezone.now()
                solicitud.save()
            
            # Log de éxito
            logger.info(f"Ticket generado exitosamente: {ticket_code} por usuario {request.user.username}")
            
            messages.success(request, f'✅ Ticket generado: {ticket_code}')
            return redirect('extractor:ticket_detail', id=ticket_obj.id)
            
        except ValidationError as e:
            logger.warning(f"Error de validación para usuario {request.user.username}: {e}")
            messages.error(request, str(e))
            return render(request, 'extractor/upload.html')
            
        except Exception as e:
            logger.error(f"Error inesperado en upload_excel para usuario {request.user.username}: {str(e)}")
            messages.error(request, f'Error procesando el archivo: {str(e)}')
            return render(request, 'extractor/upload.html')
            
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.error(f"Error al eliminar archivo temporal: {e}")
    
    return render(request, 'extractor/upload.html')


def sanitize_extracted_data(data: dict) -> dict:
    """
    Sanitizar y validar datos extraídos del Excel
    """
    dangerous_patterns = [
        r'<script.*?>.*?</script>',  # XSS
        r'javascript:',  # JavaScript injection
        r'on\w+\s*=',  # Event handlers
        r'&#\d+;',  # HTML entities
    ]
    
    sanitized = {}
    for key, value in data.items():
        if value and isinstance(value, str):
            # Limitar longitud
            value = value[:500]  # Máximo 500 caracteres
            
            # Remover patrones peligrosos
            for pattern in dangerous_patterns:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
            
            # Escapar caracteres especiales
            value = value.replace('\x00', '')  # Null byte
            
            sanitized[key] = value.strip()
        else:
            sanitized[key] = value
    
    return sanitized


def _create_jira_issue(ticket_obj, extracted_data, cliente_obj, proyecto_obj, tipo_servicio_form, request):
    """Helper para crear issue en Jira"""
    try:
        from extractor.jira_helper import JiraClient
        
        # Sanitizar datos para Jira
        jira_data = {
            'codigo': ticket_obj.codigo,
            'cliente': cliente_obj.nombre[:100],
            'proyecto': proyecto_obj.nombre[:100],
            'tipo_servicio': tipo_servicio_form[:50],
            'responsable_solicitud': extracted_data.get('responsable_solicitud', '')[:100],
            'lider_proyecto': extracted_data.get('lider_proyecto', '')[:100],
            'numero_version': extracted_data.get('numero_version', '')[:50],
            'funcionalidad_liberacion': extracted_data.get('funcionalidad_liberacion', '')[:500],
            'detalle_cambios': extracted_data.get('detalle_cambios', '')[:1000],
            'justificacion_cambio': extracted_data.get('justificacion_cambio', '')[:500],
            'fecha': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'usuario': request.user.username[:50] if request.user.is_authenticated else 'Sistema',
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
        logger.error(f"Error en integración Jira para ticket {ticket_obj.codigo}: {e}")