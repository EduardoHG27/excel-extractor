"""
Generador de tickets a partir de datos extraídos de Excel
"""
from django.utils import timezone
from extractor.models import Ticket, ExcelData


def generate_and_save_ticket(extracted_data, tipo_servicio_form, nomenclaturas, objetos_encontrados, request):
    """
    Genera y guarda un ticket basado en los datos extraídos
    
    Args:
        extracted_data (dict): Datos extraídos del Excel
        tipo_servicio_form (str): Tipo de servicio (PRU, EST, G&A)
        nomenclaturas (dict): Diccionario con nomenclaturas
        objetos_encontrados (dict): Objetos de BD encontrados
        request: Request de Django
    
    Returns:
        tuple: (ticket_code, ticket_obj)
    """
    
    # Extraer objetos del diccionario
    cliente_obj = objetos_encontrados.get('cliente_obj')
    proyecto_obj = objetos_encontrados.get('proyecto_obj')
    tipo_servicio_obj = objetos_encontrados.get('tipo_servicio_obj')
    
    # Extraer nomenclaturas
    cliente_nomenclatura = nomenclaturas.get('cliente_nomenclatura', '')
    proyecto_nomenclatura = nomenclaturas.get('proyecto_nomenclatura', '')
    tipo_servicio_nomenclatura = nomenclaturas.get('tipo_servicio_nomenclatura', '')
    
    # Obtener el consecutivo
    ultimo_ticket = Ticket.objects.filter(
        empresa_code="BID",
        tipo_servicio_code=tipo_servicio_form,
        cliente_code=cliente_nomenclatura,
        proyecto_code=proyecto_nomenclatura
    ).order_by('-consecutivo').first()
    
    if ultimo_ticket:
        consecutivo = ultimo_ticket.consecutivo + 1
    else:
        consecutivo = 1
    
    # Generar el código del ticket
    ticket_code = f"BID-{tipo_servicio_form}-{tipo_servicio_obj.nomenclatura}-{tipo_servicio_obj.id}-{cliente_nomenclatura}-{proyecto_nomenclatura}-{consecutivo:03d}"
    
    # Crear el ExcelData PRIMERO (guarda toda la información de la solicitud)
    excel_data = ExcelData.objects.create(
        cliente=str(cliente_obj.id),
        proyecto=str(proyecto_obj.id),
        tipo_pruebas=str(tipo_servicio_obj.id),
        tipo_servicio=tipo_servicio_form,
        responsable_solicitud=extracted_data.get('responsable_solicitud', ''),
        lider_proyecto=extracted_data.get('lider_proyecto', ''),
        tipo_aplicacion=extracted_data.get('tipo_aplicacion', ''),
        numero_version=extracted_data.get('numero_version', ''),
        funcionalidad_liberacion=extracted_data.get('funcionalidad_liberacion', ''),
        detalle_cambios=extracted_data.get('detalle_cambios', ''),
        justificacion_cambio=extracted_data.get('justificacion_cambio', ''),
        ticket_code=ticket_code
    )
    
    # Crear el ticket y asociarlo con ExcelData
    ticket_obj = Ticket.objects.create(
        codigo=ticket_code,
        empresa_code="BID",
        tipo_servicio_code=tipo_servicio_form,
        funcion_code=tipo_servicio_obj.nomenclatura,
        version_code=str(tipo_servicio_obj.id),
        cliente_code=cliente_nomenclatura,
        proyecto_code=proyecto_nomenclatura,
        consecutivo=consecutivo,
        cliente=cliente_obj,
        proyecto=proyecto_obj,
        tipo_servicio=tipo_servicio_obj,
        responsable_solicitud=extracted_data.get('responsable_solicitud', ''),
        lider_proyecto=extracted_data.get('lider_proyecto', ''),
        numero_version=extracted_data.get('numero_version', ''),
        estado='GENERADO',
        creado_por=request.user if request.user.is_authenticated else None,
        excel_data=excel_data  # Asociar el ExcelData
    )
    
    return ticket_code, ticket_obj