# test_ia_service.py
import os
import sys
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
sys.path.insert(0, os.path.dirname(__file__))

import django
django.setup()

from ia_agent.services.ia_service import IAService

def test_generacion_casos():
    print("=" * 60)
    print("🧪 PROBANDO SERVICIO DE IA")
    print("=" * 60)
    
    # Diagnóstico inicial
    print("\n📋 DIAGNÓSTICO INICIAL:")
    from django.conf import settings
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    print(f"   API Key: {'✅ Configurada' if api_key else '❌ No configurada'}")
    if api_key:
        print(f"   Longitud: {len(api_key)} caracteres")
        print(f"   Prefijo: {api_key[:10]}...")
    
    # Crear instancia del servicio
    print("\n1. Inicializando IAService...")
    try:
        ia_service = IAService()
        
        if ia_service.use_fallback:
            print("   ⚠️ Servicio en modo fallback (usando datos simulados)")
            print(f"   Razón: {ia_service.fallback_reason if hasattr(ia_service, 'fallback_reason') else 'desconocida'}")
        else:
            print(f"   ✅ Servicio conectado")
            if hasattr(ia_service, 'model'):
                print(f"   Modelo: {ia_service.model.model_name if hasattr(ia_service.model, 'model_name') else 'desconocido'}")
            
            # Probar conexión con un mensaje simple
            print("\n   Probando conexión con Gemini...")
            try:
                test_response = ia_service._call_gemini_api("Responde solo con: OK")
                if test_response:
                    print(f"   ✅ Conexión exitosa: {test_response[:50]}")
                else:
                    print("   ⚠️ Respuesta vacía de Gemini")
            except Exception as e:
                print(f"   ❌ Error en prueba de conexión: {e}")
                
    except Exception as e:
        print(f"   ❌ Error al inicializar servicio: {e}")
        return
    
    # Requerimiento de prueba
    requerimiento = """
    El sistema debe permitir a los usuarios registrarse con email y contraseña.
    Requisitos:
    - Email debe ser válido
    - Contraseña mínimo 8 caracteres
    - Confirmar contraseña
    - Enviar email de verificación
    - Usuario debe confirmar email para activar cuenta
    """
    
    print("\n2. Generando casos de prueba...")
    print(f"   Requerimiento: {requerimiento[:100]}...")
    
    try:
        casos = ia_service.generar_casos_prueba(requerimiento)
        
        if casos:
            print(f"\n3. ✅ ÉXITO: {len(casos)} casos generados")
            
            # Verificar estructura de los casos
            print("\n📊 ESTRUCTURA DE CASOS:")
            for i, caso in enumerate(casos[:3]):  # Mostrar primeros 3
                print(f"\n   Caso {i+1}:")
                print(f"   - Identificador: {caso.get('identificador', '❌')}")
                print(f"   - Título: {caso.get('titulo', '❌')[:50]}")
                print(f"   - Prioridad: {caso.get('prioridad', '❌')}")
                print(f"   - Pasos: {len(caso.get('pasos', []))} pasos")
                if caso.get('pasos'):
                    print(f"     * Primer paso: {caso['pasos'][0][:50]}")
            
            # Guardar resultado
            with open('casos_prueba_generados.json', 'w', encoding='utf-8') as f:
                json.dump(casos, f, ensure_ascii=False, indent=2)
            print("\n💾 Casos guardados en: casos_prueba_generados.json")
            
        else:
            print("\n❌ No se generaron casos de prueba")
            
    except Exception as e:
        print(f"\n❌ Error al generar casos: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

def test_gemini_directo():
    """Prueba directa de Gemini sin usar el servicio"""
    print("=" * 60)
    print("🧪 PRUEBA DIRECTA DE GEMINI")
    print("=" * 60)
    
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            print("❌ No hay API Key configurada")
            return
        
        print("1. Configurando Gemini...")
        genai.configure(api_key=api_key)
        
        print("2. Creando modelo...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        print("3. Enviando prompt...")
        prompt = """
        Genera 2 casos de prueba para un formulario de registro:
        1. Caso positivo: registro exitoso
        2. Caso negativo: email inválido
        
        Devuelve en formato JSON con esta estructura:
        {
            "casos": [
                {
                    "identificador": "TC001",
                    "titulo": "Título del caso",
                    "descripcion": "Descripción",
                    "prioridad": "Alta/Media/Baja",
                    "pasos": ["Paso 1", "Paso 2"]
                }
            ]
        }
        """
        
        response = model.generate_content(prompt)
        print(f"\n✅ Respuesta recibida:")
        print(f"   Longitud: {len(response.text)} caracteres")
        print(f"\n--- RESPUESTA ---")
        print(response.text[:500])
        print("...")
        
        # Intentar parsear JSON
        try:
            import json
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                print(f"\n✅ JSON parseado exitosamente")
                print(f"   Casos encontrados: {len(data.get('casos', []))}")
            else:
                print("\n⚠️ No se encontró JSON en la respuesta")
        except Exception as e:
            print(f"\n⚠️ Error al parsear JSON: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Primero probar Gemini directamente
    test_gemini_directo()
    
    print("\n" + "=" * 60)
    print("\n")
    
    # Luego probar el servicio
    test_generacion_casos()