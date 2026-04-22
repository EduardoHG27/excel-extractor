#!/usr/bin/env python
"""
Script para ofuscar archivos JavaScript en producción
Ejecutar antes de collectstatic: python obfuscate_js_production.py
"""

import os
import subprocess
import sys
from pathlib import Path
from shutil import copy2

def install_npm_packages():
    """Instala javascript-obfuscator si no está instalado"""
    try:
        subprocess.run(['javascript-obfuscator', '--version'], 
                      capture_output=True, check=True)
        print("✅ javascript-obfuscator ya está instalado")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 Instalando javascript-obfuscator...")
        try:
            subprocess.run(['npm', 'install', '-g', 'javascript-obfuscator'], 
                         check=True, capture_output=True)
            print("✅ javascript-obfuscator instalado")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando: {e}")
            return False

def obfuscate_with_javascript_obfuscator(input_file, output_file):
    """Ofusca usando javascript-obfuscator"""
    # Configuración más segura para producción
    cmd = [
        'javascript-obfuscator',
        str(input_file),
        '--output', str(output_file),
        '--compact', 'true',
        '--self-defending', 'true',  # Esto puede causar problemas en algunos navegadores
        '--dead-code-injection', 'false',  # Cambiado a false para evitar errores
        '--debug-protection', 'false',  # Cambiado a false
        '--disable-console-output', 'false',  # Permite logs para debugging
        '--identifier-names-generator', 'mangled',  # Más seguro que hexadecimal
        '--rename-globals', 'false',
        '--rename-properties', 'false',
        '--rotate-string-array', 'true',
        '--shuffle-string-array', 'true',
        '--string-array', 'true',
        '--string-array-encoding', 'none',  # Base64 puede causar problemas
        '--string-array-threshold', '0.5',
        '--unicode-escape-sequence', 'false'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout ofuscando {input_file}")
        return False
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def find_js_files():
    """Encuentra todos los archivos JS en las apps de Django"""
    js_files = []
    
    # Patrones de búsqueda comunes en Django
    search_paths = [
        'extractor/static/js/',
        'ia_agent/static/js/',
        'static/js/',
        '*/static/js/',  # Cualquier app
    ]
    
    for path_pattern in search_paths:
        for path in Path('.').glob(path_pattern):
            if path.exists() and path.is_dir():
                js_files.extend(path.glob('*.js'))
    
    # Filtrar archivos que no deben ofuscarse
    js_files = [f for f in js_files if not any(
        skip in str(f) for skip in ['obfuscated', '.min', 'vendor', 'lib', 'external']
    )]
    
    return list(set(js_files))  # Eliminar duplicados

def obfuscate_js_files():
    """Ofusca todos los archivos JS encontrados"""
    
    js_files = find_js_files()
    
    if not js_files:
        print("⚠️ No se encontraron archivos JS para ofuscar")
        print("📁 Buscando en: extractor/static/js/, ia_agent/static/js/, static/js/")
        return False
    
    print(f"\n🔒 Ofuscando {len(js_files)} archivos JavaScript...")
    print("=" * 50)
    
    success_count = 0
    
    for js_file in js_files:
        print(f"\n📄 Procesando: {js_file}")
        
        # Crear backup
        backup_file = js_file.with_suffix('.js.bak')
        copy2(js_file, backup_file)
        
        # Archivo temporal
        temp_file = js_file.with_suffix('.temp.js')
        
        # Ofuscar
        if obfuscate_with_javascript_obfuscator(js_file, temp_file):
            # Verificar que el archivo ofuscado no esté vacío
            if temp_file.exists() and temp_file.stat().st_size > 0:
                temp_file.replace(js_file)
                print(f"  ✅ Ofuscado correctamente")
                
                # Crear versión .min.js (misma que el ofuscado)
                min_file = js_file.parent / f"{js_file.stem}.min.js"
                copy2(js_file, min_file)
                print(f"  📦 Versión min creada: {min_file.name}")
                success_count += 1
            else:
                print(f"  ❌ Archivo ofuscado vacío")
                backup_file.replace(js_file)
        else:
            print(f"  ❌ Falló ofuscación")
            backup_file.replace(js_file)
    
    print("=" * 50)
    print(f"✅ Ofuscación completada: {success_count}/{len(js_files)} archivos")
    
    return success_count == len(js_files)

def restore_backups():
    """Restaura backups si es necesario"""
    print("\n🔄 Restaurando backups...")
    restored = 0
    
    for backup_file in Path('.').rglob('*.js.bak'):
        original = backup_file.with_suffix('')
        backup_file.replace(original)
        print(f"  ✅ Restaurado: {original.name}")
        restored += 1
    
    print(f"✅ {restored} backups restaurados\n")

def verify_obfuscation():
    """Verifica que los archivos ofuscados existen"""
    js_files = find_js_files()
    missing_min = []
    
    for js_file in js_files:
        min_file = js_file.parent / f"{js_file.stem}.min.js"
        if not min_file.exists():
            missing_min.append(min_file)
    
    if missing_min:
        print("⚠️ Advertencia: Faltan archivos .min.js:")
        for f in missing_min:
            print(f"  - {f}")
        return False
    
    print("✅ Verificación: Todos los .min.js existen")
    return True

if __name__ == '__main__':
    # Detectar entorno de producción
    is_production = (
        os.environ.get('DEBUG', 'True').lower() == 'false' or
        os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or
        os.environ.get('RENDER') == 'true' or
        len(sys.argv) > 1 and sys.argv[1] == 'force'
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_backups()
    elif is_production:
        print("🚀 Iniciando ofuscación para producción...")
        if install_npm_packages():
            if obfuscate_js_files():
                verify_obfuscation()
                print("\n💡 Ejecuta ahora: python manage.py collectstatic --noinput")
            else:
                print("\n❌ Falló la ofuscación. Restaurando backups...")
                restore_backups()
                sys.exit(1)
        else:
            print("❌ No se pudo instalar javascript-obfuscator")
            sys.exit(1)
    else:
        print("⚠️ Modo DEBUG activado. No se ofuscarán los JS.")
        print("Para forzar ofuscación: python obfuscate_js_production.py force")
        print("Para restaurar backups: python obfuscate_js_production.py restore")