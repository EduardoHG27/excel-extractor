# reset_tiposervicio.py
import os
import sys
import django

# Configuración EXACTA para tu proyecto
BASE_DIR = r'C:\Users\BID-eduardo.hernande\Desktop\extractor\excel_extractor'
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')

django.setup()

from extractor.models import TipoServicio
from django.db import connection

def resetear_tiposervicio():
    """Limpia la tabla TipoServicio y reinicia el ID a 1"""
    
    print("=" * 50)
    print("REINICIO DE TABLA TipoServicio")
    print("=" * 50)
    
    # Estado actual
    total = TipoServicio.objects.count()
    
    if total > 0:
        ultimo = TipoServicio.objects.order_by('-id').first()
        print(f"📊 Estado actual: {total} registros")
        print(f"🆔 Último ID en uso: {ultimo.id}")
    else:
        print("📊 Estado actual: Tabla vacía")
    
    print("\n⚠️  ATENCIÓN: Esta acción NO se puede deshacer")
    print("Se eliminarán TODOS los tipos de servicio")
    print("y el ID volverá a empezar desde 1")
    
    confirm = input("\n¿Continuar? (escribe 'SI' para confirmar): ")
    
    if confirm.upper() != 'SI':
        print("\n❌ Operación cancelada")
        return
    
    # 1. Eliminar todos los registros
    print("\n🔄 Eliminando registros...")
    eliminados, _ = TipoServicio.objects.all().delete()
    print(f"✅ {eliminados} registros eliminados")
    
    # 2. Reiniciar el contador del ID (SQLite)
    print("🔄 Reiniciando contador de ID...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='extractor_tiposervicio'")
        print("✅ Contador reiniciado a 1")
    except Exception as e:
        print(f"⚠️  No se pudo reiniciar contador: {e}")
    
    # 3. Verificación
    print("\n" + "=" * 30)
    print("VERIFICACIÓN FINAL")
    print("=" * 30)
    
    print(f"📊 Registros en tabla: {TipoServicio.objects.count()}")
    
    # Crea uno para verificar el ID
    try:
        nuevo = TipoServicio.objects.create(
            nombre="[VERIFICACIÓN] Puedes borrarme",
            nomenclatura="CHECK",
            activo=False
        )
        print(f"🆔 Nuevo registro creado con ID: {nuevo.id}")
        
        if nuevo.id == 1:
            print("✅ ¡ÉXITO! El ID se reinició correctamente a 1")
        else:
            print(f"⚠️  El ID empezó en {nuevo.id} en lugar de 1")
        
        # Opción para borrar el de verificación
        borrar = input("\n¿Borrar registro de verificación? (si/no): ")
        if borrar.lower() == 'si':
            nuevo.delete()
            print("✅ Registro de verificación eliminado")
    
    except Exception as e:
        print(f"❌ Error en verificación: {e}")

if __name__ == '__main__':
    resetear_tiposervicio()