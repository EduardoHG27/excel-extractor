# test_gemini_simple.py
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')

import django
django.setup()

from django.conf import settings
import google.generativeai as genai

print("=" * 60)
print("🔍 DIAGNÓSTICO DE GEMINI")
print("=" * 60)

# Verificar API Key
api_key = getattr(settings, 'GEMINI_API_KEY', None)
print(f"1. API Key: {'✅ Presente' if api_key else '❌ No encontrada'}")
if api_key:
    print(f"   Valor: {api_key[:15]}...{api_key[-5:] if len(api_key) > 20 else ''}")

# Verificar versión de la librería
print(f"\n2. Versión de google-generativeai:")
try:
    import google.generativeai
    version = google.generativeai.__version__ if hasattr(google.generativeai, '__version__') else 'desconocida'
    print(f"   Versión: {version}")
except Exception as e:
    print(f"   Error: {e}")

# Configurar Gemini
print(f"\n3. Configurando Gemini...")
try:
    genai.configure(api_key=api_key)
    print("   ✅ Configuración exitosa")
except Exception as e:
    print(f"   ❌ Error al configurar: {e}")

# Probar modelo específico
print(f"\n4. Probando modelo gemini-1.5-flash...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Responde solo con: OK")
    print(f"   ✅ Modelo responde: {response.text[:50]}")
    print(f"   Tokens usados: {response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 'N/A'}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)