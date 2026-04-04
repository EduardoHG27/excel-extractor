# test_gemini_v2.py
import os
import sys

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')

import django
django.setup()

from django.conf import settings
import google.generativeai as genai

print("=" * 60)
print("🔍 PROBANDO GEMINI CON NOMBRES CORRECTOS")
print("=" * 60)

api_key = settings.GEMINI_API_KEY
print(f"✅ API Key: {api_key[:10]}...")

genai.configure(api_key=api_key)

# Probar con los nombres correctos
modelos_correctos = [
    'models/gemini-1.5-flash',
    'models/gemini-1.5-pro', 
    'models/gemini-pro',
]

for modelo in modelos_correctos:
    print(f"\n📝 Probando modelo: {modelo}")
    try:
        model = genai.GenerativeModel(modelo)
        response = model.generate_content("Di 'Hola'")
        print(f"   ✅ ÉXITO! Respuesta: {response.text[:50]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)