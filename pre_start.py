# pre_start.py
import os
import django
import psycopg2
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

def fix_solicitudpruebas_pk():
    """Asegurar que extractor_solicitudpruebas tiene PRIMARY KEY"""
    try:
        with connection.cursor() as cursor:
            # Verificar si la tabla tiene PK
            cursor.execute("""
                SELECT conname 
                FROM pg_constraint 
                WHERE conrelid = 'extractor_solicitudpruebas'::regclass 
                AND contype = 'p'
            """)
            has_pk = cursor.fetchone()
            
            if not has_pk:
                print("⚠️ No se encontró PRIMARY KEY en extractor_solicitudpruebas")
                print("🔧 Agregando PRIMARY KEY...")
                cursor.execute("ALTER TABLE extractor_solicitudpruebas ADD PRIMARY KEY (id);")
                print("✅ PRIMARY KEY agregada exitosamente")
            else:
                print("✅ PRIMARY KEY ya existe en extractor_solicitudpruebas")
                
    except Exception as e:
        print(f"⚠️ Error al verificar PK: {e}")
        print("Continuando con la ejecución...")

if __name__ == "__main__":
    print("=== PRE-START: Verificando estructura de base de datos ===")
    fix_solicitudpruebas_pk()
    print("=== PRE-START completado ===")