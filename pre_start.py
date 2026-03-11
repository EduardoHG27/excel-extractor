#!/usr/bin/env python
# pre_start.py - Colocar al mismo nivel que manage.py

import os
import django
import sys

print("🔧 VERIFICANDO ESTADO DE MIGRACIONES...")
print("="*50)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

try:
    # Verificar si la tabla extractor_solicitudpruebas existe
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'extractor_solicitudpruebas'
            );
        """)
        tabla_existe = cursor.fetchone()[0]
        
        if tabla_existe:
            print("✅ La tabla 'extractor_solicitudpruebas' YA EXISTE en la BD")
            print("🔄 Marcando migraciones como aplicadas (--fake)...")
            
            # Marcar TODAS las migraciones de extractor como aplicadas
            call_command('migrate', 'extractor', '--fake')
            
            print("✅ Migraciones marcadas como aplicadas exitosamente")
        else:
            print("⚠️ La tabla 'extractor_solicitudpruebas' NO existe")
            print("➡️ Se ejecutarán las migraciones normalmente")
    
    print("="*50)
    print("✅ VERIFICACIÓN COMPLETADA - Continuando con migrate normal...")
    print("="*50)
    
except Exception as e:
    print(f"❌ Error durante la verificación: {e}")
    # No detenemos el proceso, dejamos que migrate intente