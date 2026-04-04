#!/usr/bin/env python
"""
Script para probar la conexión con Gemini AI
Ejecutar: python test_gemini_connection.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')  # Ajusta según tu proyecto

django.setup()

from django.conf import settings
import google.generativeai as genai
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variable global para el modelo funcional
MODELO_FUNCIONAL = None

def test_gemini_connection():
    """Prueba básica de conexión con Gemini"""
    global MODELO_FUNCIONAL
    
    print("\n" + "="*60)
    print("🔌 PROBANDO CONEXIÓN CON GEMINI AI")
    print("="*60)
    
    # 1. Verificar API Key
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY no está configurada en settings")
        print("   Debes agregarla en settings.py: GEMINI_API_KEY = 'tu-api-key'")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else ''}")
    
    # 2. Configurar Gemini
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        return False
    
    # 3. Probar modelos disponibles (SOLO MODELOS VÁLIDOS)
    modelos_a_probar = [
        'models/gemini-2.5-flash',
        'models/gemini-1.5-flash',
        'models/gemini-1.5-pro',
        'models/gemini-2.0-flash-exp',  # Experimental
    ]
    
    modelo_funcional = None
    
    print("\n📡 Probando modelos disponibles:")
    for model_name in modelos_a_probar:
        try:
            print(f"   → Probando {model_name}...", end=" ")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Di 'OK' si recibes este mensaje")
            if response and response.text:
                print(f"✅ RESPONDE: {response.text[:50]}")
                modelo_funcional = model_name
                MODELO_FUNCIONAL = model_name
                break
            else:
                print("❌ Respuesta vacía")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not available" in error_msg:
                print("❌ Modelo no disponible")
            else:
                print(f"❌ Error: {error_msg[:50]}")
            continue
    
    if modelo_funcional:
        print(f"\n✅ Gemini conectado exitosamente con modelo: {modelo_funcional}")
        return True
    else:
        print("\n❌ No se pudo conectar con ningún modelo de Gemini")
        return False

def test_simple_prompt():
    """Prueba con un prompt simple usando el modelo funcional"""
    global MODELO_FUNCIONAL
    
    print("\n" + "="*60)
    print("💬 PROBANDO PROMPT SIMPLE")
    print("="*60)
    
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or not MODELO_FUNCIONAL:
        print("❌ API Key o modelo funcional no disponible")
        return False
    
    try:
        genai.configure(api_key=api_key)
        # Usar el modelo funcional detectado
        model = genai.GenerativeModel(MODELO_FUNCIONAL)
        
        prompt = "Responde con una breve descripción de qué es una prueba de software en QA."
        print(f"📝 Prompt: {prompt}")
        print(f"🤖 Usando modelo: {MODELO_FUNCIONAL}")
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            print(f"✅ Respuesta recibida ({len(response.text)} caracteres):")
            print("-"*40)
            print(response.text[:300])
            print("-"*40)
            return True
        else:
            print("❌ Respuesta vacía")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_json_response():
    """Prueba de generación de JSON usando el modelo funcional"""
    global MODELO_FUNCIONAL
    
    print("\n" + "="*60)
    print("📊 PROBANDO GENERACIÓN DE JSON")
    print("="*60)
    
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or not MODELO_FUNCIONAL:
        print("❌ API Key o modelo funcional no disponible")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODELO_FUNCIONAL)
        
        prompt = """
        Genera un caso de prueba simple en formato JSON para validar login.
        Responde ÚNICAMENTE con el JSON, sin texto adicional.
        
        Formato:
        {
            "titulo": "Login exitoso con credenciales válidas",
            "precondiciones": ["Usuario registrado", "Sistema disponible"],
            "pasos": ["1. Ingresar usuario", "2. Ingresar contraseña", "3. Click login"],
            "resultado_esperado": "Redirige al dashboard"
        }
        """
        
        print(f"📝 Enviando prompt para generar JSON...")
        print(f"🤖 Usando modelo: {MODELO_FUNCIONAL}")
        response = model.generate_content(prompt)
        
        if response and response.text:
            print(f"✅ Respuesta recibida ({len(response.text)} caracteres)")
            print("-"*40)
            print(response.text)
            print("-"*40)
            
            # Intentar parsear JSON
            import json
            try:
                # Limpiar respuesta
                texto_limpio = response.text.strip()
                if texto_limpio.startswith('```json'):
                    texto_limpio = texto_limpio[7:]
                if texto_limpio.startswith('```'):
                    texto_limpio = texto_limpio[3:]
                if texto_limpio.endswith('```'):
                    texto_limpio = texto_limpio[:-3]
                
                datos = json.loads(texto_limpio.strip())
                print("✅ JSON válido parseado correctamente")
                print(f"   Título: {datos.get('titulo', 'N/A')}")
                return True
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON inválido: {e}")
                return False
        else:
            print("❌ Respuesta vacía")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_con_texto_largo():
    """Prueba con texto más extenso usando el modelo funcional"""
    global MODELO_FUNCIONAL
    
    print("\n" + "="*60)
    print("📝 PROBANDO CON TEXTO EXTENSO")
    print("="*60)
    
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or not MODELO_FUNCIONAL:
        print("❌ API Key o modelo funcional no disponible")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODELO_FUNCIONAL)
        
        texto_prueba = """
        Se requiere implementar una funcionalidad de órdenes de compra donde:
        - El usuario comprador puede crear órdenes hasta 5,000,000 CLP
        - Órdenes sobre 5,000,000 requieren aprobación de jefatura
        - Las órdenes deben tener mínimo 1 producto
        - El sistema debe validar stock disponible
        """
        
        prompt = f"""
        Analiza el siguiente requerimiento y genera 3 casos de prueba en formato JSON:
        
        {texto_prueba}
        
        Cada caso debe tener: titulo, nivel_riesgo (alto/medio/bajo), pasos (lista)
        Responde ÚNICAMENTE con el JSON.
        """
        
        print(f"📝 Enviando prompt con texto extenso...")
        print(f"🤖 Usando modelo: {MODELO_FUNCIONAL}")
        response = model.generate_content(prompt)
        
        if response and response.text:
            print(f"✅ Respuesta recibida ({len(response.text)} caracteres)")
            print("-"*40)
            print(response.text[:500])
            print("-"*40)
            return True
        else:
            print("❌ Respuesta vacía")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    global MODELO_FUNCIONAL
    
    print("\n" + "🚀 INICIANDO PRUEBAS DE CONEXIÓN GEMINI")
    
    resultados = []
    
    # Ejecutar pruebas
    resultados.append(("Conexión básica", test_gemini_connection()))
    
    # Solo continuar si la conexión básica funciona Y tenemos modelo funcional
    if resultados[-1][1] and MODELO_FUNCIONAL:
        resultados.append(("Prompt simple", test_simple_prompt()))
        resultados.append(("Generación JSON", test_json_response()))
        resultados.append(("Texto extenso", test_con_texto_largo()))
    else:
        print("\n⚠️ No se pudo establecer conexión con Gemini. Omitiendo pruebas adicionales.")
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    for nombre, resultado in resultados:
        estado = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{estado} - {nombre}")
    
    total = len(resultados)
    exitosos = sum(1 for _, r in resultados if r)
    
    print(f"\n✅ Pruebas exitosas: {exitosos}/{total}")
    
    if exitosos == total:
        print("\n🎉 ¡Gemini está funcionando correctamente!")
        print(f"📌 Modelo recomendado: {MODELO_FUNCIONAL}")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los logs para más detalles.")
    
    return exitosos == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)