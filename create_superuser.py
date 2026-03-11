# run_migrations.py
import os
import django
import subprocess
import sys

print("🚀 Iniciando script de migraciones...")

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def check_and_run_migrations():
    """Verifica y ejecuta migraciones pendientes"""
    
    print("🔍 Verificando tablas existentes...")
    
    # Verificar si la columna existe
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='extractor_ticket' AND column_name='jira_issue_key'
            """)
            exists = cursor.fetchone()
            
            if not exists:
                print("⚠️  Columna jira_issue_key NO existe. Creando migración...")
                
                # Crear migración manual
                call_command('makemigrations', 'extractor', name='add_jira_fields_manual')
                print("✅ Migración creada")
                
                # Aplicar migración
                call_command('migrate', 'extractor')
                print("✅ Migración aplicada")
            else:
                print("✅ La columna jira_issue_key ya existe")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            # Aplicar todas las migraciones por si acaso
            print("🔄 Aplicando todas las migraciones...")
            call_command('migrate')

if __name__ == '__main__':
    check_and_run_migrations()
    print("🏁 Script de migraciones completado")