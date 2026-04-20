"""
Funciones auxiliares para procesamiento de Excel
"""
from datetime import timedelta


def generate_ticket_parts(ticket_code):
    """Divide el código del ticket en partes para mostrar en el desglose"""
    parts = ticket_code.split('-')
    
    if len(parts) < 7:
        default_parts = ['BID', 'PRU', 'F&REG', '10', 'TEL', 'OTR', '001']
        for i in range(7):
            if i >= len(parts) or not parts[i]:
                parts.append(default_parts[i])
    
    return parts


def calcular_dias_habiles(fecha_inicio, fecha_fin):
    """
    Calcula el número de días hábiles entre dos fechas (excluyendo sábados y domingos)
    """
    if not fecha_inicio or not fecha_fin:
        return 0
    
    if hasattr(fecha_inicio, 'date'):
        fecha_inicio = fecha_inicio.date()
    if hasattr(fecha_fin, 'date'):
        fecha_fin = fecha_fin.date()
    
    if fecha_inicio > fecha_fin:
        return 0
    
    dias_habiles = 0
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() < 5:
            dias_habiles += 1
        fecha_actual += timedelta(days=1)
    
    return dias_habiles


def sanitizar_public_id(nombre):
    """Limpia caracteres inválidos para Cloudinary"""
    import re
    nombre = re.sub(r'[&<>#%{}|\\^~\[\]`;?:@=$,/]', '_', nombre)
    nombre = re.sub(r'\s+', '_', nombre)
    nombre = nombre.encode('ascii', 'ignore').decode('ascii')
    nombre = re.sub(r'[^a-zA-Z0-9_-]', '_', nombre)
    return nombre


def extraer_public_id_cloudinary(url):
    """
    Extrae el public_id de una URL de Cloudinary
    """
    import re
    try:
        pattern = r'/upload/(?:v\d+/)?(.+?)\.\w+$'
        match = re.search(pattern, url)
        
        if match:
            public_id = match.group(1)
            public_id = public_id.split('?')[0]
            return public_id
        
        return None
    except Exception:
        return None