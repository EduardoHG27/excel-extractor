#!/usr/bin/env python
# pre_start.py

import os
import django
import sys

print("🔧 VERIFICANDO ESTADO DE MIGRACIONES...")
print("="*50)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

try:
    with connection.cursor() as cursor:
        # 1. Verificar tabla extractor_solicitudpruebas
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'extractor_solicitudpruebas'
            );
        """)
        tabla_existe = cursor.fetchone()[0]
        
        if tabla_existe:
            print("✅ La tabla 'extractor_solicitudpruebas' YA EXISTE")
            
            # 2. VERIFICAR Y CREAR COLUMNAS FALTANTES EN extractor_ticket
            print("🔍 Verificando columnas en extractor_ticket...")
            
            # Lista de columnas que deben existir
            columnas_necesarias = [
                ('jira_issue_key', 'VARCHAR(50)'),
                ('jira_issue_url', 'VARCHAR(200)'),
                ('fecha_sincronizacion_jira', 'TIMESTAMP')
            ]
            
            for columna, tipo in columnas_necesarias:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'extractor_ticket' 
                        AND column_name = %s
                    );
                """, [columna])
                
                columna_existe = cursor.fetchone()[0]
                
                if not columna_existe:
                    print(f"⚠️ Columna '{columna}' no existe. Creándola...")
                    cursor.execute(f'ALTER TABLE extractor_ticket ADD COLUMN {columna} {tipo} NULL;')
                    print(f"✅ Columna '{columna}' creada exitosamente")
                else:
                    print(f"✅ Columna '{columna}' ya existe")
            
            # 3. Ahora sí, marcar migraciones como aplicadas
            print("🔄 Marcando migraciones como aplicadas...")
            call_command('migrate', 'extractor', '--fake')
            print("✅ Migraciones marcadas como aplicadas")
            
        else:
            print("⚠️ Tabla 'extractor_solicitudpruebas' NO existe")
            print("➡️ Se ejecutarán las migraciones normalmente")
    
    print("="*50)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("="*50)
    
except Exception as e:
    print(f"❌ Error durante la verificación: {e}")
    import traceback
    traceback.print_exc()