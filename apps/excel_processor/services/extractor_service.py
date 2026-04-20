"""
Servicios para extracción de datos de Excel
"""
import pandas as pd


def extract_excel_data(file_path):
    """
    Extrae las celdas específicas según las reglas dadas
    """
    try:
        df = pd.read_excel(file_path, sheet_name='Solicitud de Pruebas V4', header=None)
    except ValueError as e:
        if "No sheet named" in str(e):
            raise Exception("El archivo no contiene la hoja 'Solicitud de Pruebas V4'")
        else:
            raise Exception(f"Error al leer el archivo: {str(e)}")
    
    def clean_value(value):
        if pd.isna(value):
            return ""
        return str(value).strip()
    
    extracted_data = {}
    
    # Mapeo de celdas
    cells_mapping = {
        'cliente': (4, 2),
        'proyecto': (4, 7),
        'tipo_pruebas': (7, 3),
        'responsable_solicitud': (11, 3),
        'lider_proyecto': (11, 9),
        'tipo_aplicacion': (16, 3),
        'numero_version': (16, 12),
        'funcionalidad_liberacion': (19, 3),
        'detalle_cambios': (21, 3),
        'justificacion_cambio': (23, 3),
    }
    
    for key, (row, col) in cells_mapping.items():
        try:
            extracted_data[key] = clean_value(df.iat[row, col])
            print(f"📌 {key}: '{extracted_data[key][:100]}...'")
        except Exception as e:
            print(f"⚠️ Error extrayendo {key}: {e}")
            extracted_data[key] = ""
    
    return extracted_data


def find_object_by_name_or_id(model, value, field_name="nombre"):
    """
    Busca un objeto por nombre o ID
    """
    if not value or value == "":
        return None
    
    value_str = str(value).strip()
    
    # Buscar por ID
    try:
        id_value = int(float(value_str))
        obj = model.objects.filter(id=id_value).first()
        if obj:
            print(f"✅ Encontrado por ID: {model.__name__} ID={id_value}")
            return obj
    except (ValueError, TypeError):
        pass
    
    # Buscar por nombre exacto
    obj = model.objects.filter(**{field_name: value_str}).first()
    if obj:
        print(f"✅ Encontrado por nombre: {model.__name__} '{value_str}'")
        return obj
    
    # Buscar por nombre que contiene
    obj = model.objects.filter(**{f"{field_name}__icontains": value_str}).first()
    if obj:
        print(f"✅ Encontrado por coincidencia: {model.__name__} '{value_str}'")
        return obj
    
    # Buscar por nomenclatura
    if hasattr(model, 'nomenclatura'):
        obj = model.objects.filter(nomenclatura=value_str).first()
        if obj:
            print(f"✅ Encontrado por nomenclatura: {model.__name__} '{value_str}'")
            return obj
    
    print(f"❌ No encontrado: {model.__name__} con valor '{value_str}'")
    return None