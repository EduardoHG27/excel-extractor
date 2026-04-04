# ia_agent/services/ia_service.py
import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

class IAService:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.use_fallback = False
        self.model = None
        
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY no configurada")
            self.use_fallback = True
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Lista de modelos a probar en orden de preferencia
            modelos_a_probar = [
                'models/gemini-2.5-flash',     # ✅ Este funciona (según tu prueba)
                'models/gemini-1.5-flash',     # Alternativa estable
                'models/gemini-1.5-pro', 
            ]
            
            for model_name in modelos_a_probar:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    test_response = self.model.generate_content("Test connection")
                    if test_response and test_response.text:
                        logger.info(f"✅ Gemini conectado con modelo: {model_name}")
                        self.use_fallback = False
                        break
                except Exception as e:
                    logger.warning(f"Error con modelo {model_name}: {e}")
                    continue
            
            if not self.model:
                logger.error("No se pudo conectar con ningún modelo")
                self.use_fallback = True
                
        except Exception as e:
            logger.error(f"Error configurando Gemini: {e}")
            self.use_fallback = True
    
    def _limpiar_respuesta(self, texto: str) -> str:
        """Limpia la respuesta de Gemini para extraer JSON válido"""
        texto = texto.strip()
        if texto.startswith('```json'):
            texto = texto[7:]
        if texto.startswith('```'):
            texto = texto[3:]
        if texto.endswith('```'):
            texto = texto[:-3]
        return texto.strip()
    
    def generar_casos_prueba(self, 
                            requerimiento_texto: str, 
                            contexto: Optional[Dict] = None,
                            config: Optional[Dict] = None) -> List[Dict]:
        """
        Genera casos de prueba funcionales enfocados en riesgo
        
        Args:
            requerimiento_texto: Texto del requerimiento
            contexto: Diccionario con información contextual (proyecto, cliente, etc)
            config: Configuración de generación
        """
        
        if self.use_fallback or not self.model:
            logger.warning("Usando modo fallback")
            return self._generar_fallback(requerimiento_texto, config)
        
        try:
            # Configuración por defecto - ENFOQUE EN ALTO RIESGO
            if config is None:
                config = {
                    'num_casos': 8,
                    'enfoque_riesgo': True,
                    'incluir_negativos': True,
                    # NUEVOS PARÁMETROS PARA CONTROLAR DISTRIBUCIÓN
                    'alto_riesgo_pct': 70,   # 70% alto riesgo
                    'medio_riesgo_pct': 20,  # 20% medio riesgo
                    'bajo_riesgo_pct': 10,   # 10% bajo riesgo
                }
            
            # Validar que los porcentajes sumen 100
            total_pct = config.get('alto_riesgo_pct', 70) + config.get('medio_riesgo_pct', 20) + config.get('bajo_riesgo_pct', 10)
            if total_pct != 100:
                logger.warning(f"Los porcentajes suman {total_pct}, ajustando a 70/20/10")
                config['alto_riesgo_pct'] = 70
                config['medio_riesgo_pct'] = 20
                config['bajo_riesgo_pct'] = 10
            
            # Construir el prompt con enfoque en riesgo
            prompt = self._construir_prompt_riesgo(requerimiento_texto, contexto, config)
            
            # Temperatura baja para respuestas más consistentes
            temperature = 0.2
            
            # Generar respuesta
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                }
            )
            
            # Extraer y parsear JSON
            if response and response.text:
                texto_limpio = self._limpiar_respuesta(response.text)
                casos = json.loads(texto_limpio)
                logger.info(f"✅ Generados {len(casos)} casos de prueba funcionales con enfoque en riesgo")
                logger.info(f"📊 Distribución configurada: Alto: {config.get('alto_riesgo_pct')}%, Medio: {config.get('medio_riesgo_pct')}%, Bajo: {config.get('bajo_riesgo_pct')}%")
                return casos
            else:
                logger.error("Respuesta vacía de Gemini")
                return self._generar_fallback(requerimiento_texto, config)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            logger.debug(f"Respuesta: {response.text if response else 'None'}")
            return self._generar_fallback(requerimiento_texto, config)
        except Exception as e:
            logger.error(f"Error generando casos: {e}")
            return self._generar_fallback(requerimiento_texto, config)
    
    def _construir_prompt_riesgo(self, 
                             requerimiento_texto: str, 
                             contexto: Optional[Dict] = None,
                             config: Optional[Dict] = None) -> str:
        """Construye el prompt enfocado en pruebas funcionales basadas en riesgo con énfasis en alto riesgo"""
        
        if config is None:
            config = {}
        
        num_casos = config.get('num_casos', 8)
        
        # Extraer información del contexto
        proyecto = contexto.get('proyecto', 'No especificado') if contexto else 'No especificado'
        cliente = contexto.get('cliente', 'No especificado') if contexto else 'No especificado'
        version = contexto.get('version', 'No especificado') if contexto else 'No especificado'
        
        # Datos CRÍTICOS del Excel
        funcionalidad = contexto.get('funcionalidad', '') if contexto else ''
        detalle_cambios = contexto.get('detalle_cambios', '') if contexto else ''
        justificacion = contexto.get('justificacion', '') if contexto else ''
        
        # Extraer palabras clave del requerimiento para identificar el CORE
        requerimiento_lower = requerimiento_texto.lower()
        
        # Detectar el tipo de funcionalidad principal
        tipo_funcionalidad = self._detectar_tipo_funcionalidad(requerimiento_texto, contexto)
        
        # PROMPT OPTIMIZADO - Más directo y específico
        prompt = f"""Eres un experto en QA. Genera {num_casos} casos de prueba FUNCIONALES basados ESTRICTAMENTE en la información proporcionada.

    ⚠️ **CRÍTICO**: Cada caso debe usar los datos REALES de la solicitud, NO datos genéricos.

    == DATOS REALES DE LA SOLICITUD ==
    Proyecto: {proyecto}
    Cliente: {cliente}
    Versión: {version}
    Tipo de funcionalidad detectada: {tipo_funcionalidad}

    == FUNCIONALIDAD ESPECÍFICA A PROBAR ==
    {funcionalidad if funcionalidad else 'No especificada en Excel, extraer del requerimiento'}

    == CAMBIOS REALIZADOS ==
    {detalle_cambios if detalle_cambios else 'No especificados'}

    == JUSTIFICACIÓN DEL CAMBIO ==
    {justificacion if justificacion else 'No especificada'}

    == TEXTO COMPLETO DEL REQUERIMIENTO ==
    {requerimiento_texto[:3000]}

    == INSTRUCCIONES OBLIGATORIAS ==
    1. **USA LOS DATOS REALES**: Si la funcionalidad menciona "orden de compra", crea casos con órdenes de compra. Si menciona "facturación electrónica", usa facturación.
    2. **NO USES DATOS GENÉRICOS**: Evita "ejemplo", "test", "prueba" como datos. Usa nombres, valores y escenarios realistas.
    3. **PRIORIDAD POR RIESGO**: El 70% de los casos ({int(num_casos*0.7)}) deben ser ALTO RIESGO - cubrir el flujo principal y puntos críticos.
    4. **PASOS ESPECÍFICOS**: Cada paso debe ser ejecutable, con valores concretos.

    == DISTRIBUCIÓN OBLIGATORIA ==
    - ALTO RIESGO ({int(num_casos*0.7)} casos): Flujo principal, transacciones críticas, integraciones
    - MEDIO RIESGO ({int(num_casos*0.2)} casos): Validaciones importantes, flujos alternativos
    - BAJO RIESGO ({int(num_casos*0.1)} casos): Casos borde de baja prioridad

    == FORMATO JSON ==
    [
    {{
        "identificador": "TC-001",
        "titulo": "[Usar nombre específico de la funcionalidad real]",
        "descripcion": "Explicar QUÉ se prueba y POR QUÉ es importante para este proyecto/cliente",
        "nivel_riesgo": "alto|medio|bajo",
        "precondiciones": ["Condición1 específica con datos reales", "Condición2", "Condición3"],
        "pasos": [
        "1. Acción específica con valores reales (ej: Seleccionar proveedor 'Distribuidora ABC')",
        "2. Ingresar dato real: monto 15,750.00",
        "3. Continuar con acción específica"
        ],
        "resultados_esperados": [
        "Resultado verificable 1 con valores exactos",
        "Resultado verificable 2",
        "Resultado verificable 3"
        ],
        "datos_prueba": {{
        "campo1": "valor_real_específico",
        "campo2": 12345.67,
        "referencia": "usar datos reales del requerimiento"
        }}
    }}
    ]

    == EJEMPLO CON DATOS REALES (NO COPIAR, USAR DATOS DE ESTA SOLICITUD) ==
    Si la solicitud habla de "órdenes de compra para proveedor ABC":
    - Título: "Creación de orden de compra para proveedor ABC con monto > 5,000,000"
    - Datos: proveedor "ABC S.A.", monto 5,250,000, productos específicos del catálogo
    - Pasos: incluir los campos reales del formulario de órdenes

    Si la solicitud habla de "facturación electrónica DTE":
    - Título: "Generación de DTE tipo factura con monto > 1,000,000"
    - Datos: RUT 76.123.456-7, monto 1,250,000, producto "Servicio Consultoría"

    ⚠️ **NO INCLUIR ESTE EJEMPLO EN LA RESPUESTA. GENERAR SOLO EL JSON CON LOS CASOS.**

    RESPONDE ÚNICAMENTE CON EL JSON. NO INCLUIR TEXTO ADICIONAL.
    """
        return prompt
    
    def _generar_fallback(self, requerimiento_texto: str, config: Optional[Dict] = None) -> List[Dict]:
        """Genera casos de prueba funcionales de fallback enfocados en riesgo"""
        
        logger.info("Generando casos de prueba funcionales de fallback")
        
        if config is None:
            config = {}
        
        num_casos = config.get('num_casos', 8)
        
        # Obtener distribución de riesgos
        alto_riesgo_pct = config.get('alto_riesgo_pct', 70)
        medio_riesgo_pct = config.get('medio_riesgo_pct', 20)
        bajo_riesgo_pct = config.get('bajo_riesgo_pct', 10)
        
        # Calcular cantidad de casos por nivel
        alto_count = max(1, int(num_casos * alto_riesgo_pct / 100))
        medio_count = max(1, int(num_casos * medio_riesgo_pct / 100))
        bajo_count = num_casos - alto_count - medio_count
        
        if bajo_count < 1 and num_casos > 2:
            bajo_count = 1
            alto_count -= 1
        
        logger.info(f"Distribución fallback: Alto: {alto_count}, Medio: {medio_count}, Bajo: {bajo_count}")
        
        # Extraer palabras clave del requerimiento
        palabras_clave = requerimiento_texto.lower()
        
        # Detectar tipo de funcionalidad
        es_financiero = any(p in palabras_clave for p in ['pago', 'factura', 'orden', 'compra', 'monto', 'precio', 'costo', 'total'])
        es_critico = any(p in palabras_clave for p in ['crítico', 'urgente', 'prioritario', 'importante'])
        
        casos = []
        
        # Generar casos de alto riesgo
        for i in range(alto_count):
            if es_financiero:
                caso = self._crear_caso_financiero_alto_riesgo(i, requerimiento_texto)
            else:
                caso = self._crear_caso_generico_alto_riesgo(i, requerimiento_texto)
            casos.append(caso)
        
        # Generar casos de medio riesgo
        for i in range(medio_count):
            if es_financiero:
                caso = self._crear_caso_financiero_medio_riesgo(i, requerimiento_texto)
            else:
                caso = self._crear_caso_generico_medio_riesgo(i, requerimiento_texto)
            casos.append(caso)
        
        # Generar casos de bajo riesgo
        for i in range(bajo_count):
            caso = self._crear_caso_generico_bajo_riesgo(i, requerimiento_texto)
            casos.append(caso)
        
        # Asignar identificadores correlativos
        for idx, caso in enumerate(casos, 1):
            caso['identificador'] = f"TC-{idx:03d}"
        
        return casos[:num_casos]

    def _crear_caso_financiero_alto_riesgo(self, index: int, requerimiento: str) -> Dict:
        """Crea un caso de alto riesgo para funcionalidades financieras"""
        return {
            "titulo": f"Procesamiento exitoso de transacción financiera principal - Escenario {index + 1}",
            "descripcion": f"Prueba funcional del flujo principal de {requerimiento[:100]}. Este caso es de ALTO RIESGO porque involucra transacciones financieras que impactan directamente en la contabilidad del cliente. Una falla podría causar discrepancias contables o pérdidas económicas.",
            "nivel_riesgo": "alto",
            "precondiciones": [
                "Usuario autorizado con permisos de transacciones financieras",
                "Saldo o presupuesto suficiente disponible",
                "Sistema conectado al módulo de contabilidad",
                "Datos de prueba con valores reales preparados"
            ],
            "pasos": [
                "1. Acceder a la funcionalidad desde el menú principal",
                "2. Completar todos los campos obligatorios con datos válidos",
                "3. Verificar cálculos automáticos de totales",
                "4. Confirmar la transacción",
                "5. Validar el comprobante generado",
                "6. Verificar actualización en el módulo contable"
            ],
            "resultados_esperados": [
                "La transacción se completa exitosamente",
                "Se genera comprobante con número correlativo correcto",
                "Los saldos se actualizan correctamente",
                "Se registra auditoría con fecha y usuario",
                "El módulo contable refleja la transacción"
            ],
            "datos_prueba": {
                "usuario": "usuario_prueba",
                "monto": "15000.00",
                "concepto": "Prueba funcional - transacción crítica"
            }
        }

    def _crear_caso_generico_alto_riesgo(self, index: int, requerimiento: str) -> Dict:
        """Crea un caso de alto riesgo genérico"""
        return {
            "titulo": f"Ejecución exitosa del flujo principal crítico",
            "descripcion": f"Prueba funcional del flujo principal descrito en la solicitud. Caso de ALTO RIESGO porque representa la funcionalidad core que el usuario necesita para operar. Si falla, el usuario no puede completar su tarea principal.",
            "nivel_riesgo": "alto",
            "precondiciones": [
                "Usuario autenticado con permisos adecuados",
                "Sistema en estado normal operativo",
                "Datos de prueba preparados según requerimiento"
            ],
            "pasos": [
                "1. Acceder a la funcionalidad desde el menú principal",
                "2. Completar los campos obligatorios con datos válidos",
                "3. Ejecutar la acción principal",
                "4. Verificar respuesta del sistema",
                "5. Confirmar que los datos se procesan correctamente",
                "6. Validar que se puede continuar con el siguiente paso del proceso"
            ],
            "resultados_esperados": [
                "La acción se ejecuta sin errores",
                "Se muestra mensaje de éxito o confirmación",
                "Los datos se almacenan correctamente en el sistema",
                "El estado del proceso avanza según lo esperado",
                "Se registra auditoría de la acción"
            ],
            "datos_prueba": {
                "usuario": "usuario_prueba",
                "datos_entrada": "según especificación del requerimiento"
            }
        }

    def _crear_caso_financiero_medio_riesgo(self, index: int, requerimiento: str) -> Dict:
        """Crea un caso de medio riesgo para funcionalidades financieras"""
        return {
            "titulo": "Validación de límites máximos en transacciones financieras",
            "descripcion": f"Prueba de validación de límites de montos en {requerimiento[:100]}. Caso de MEDIO RIESGO porque superar los límites establecidos podría indicar un error en las validaciones o permitir transacciones no autorizadas.",
            "nivel_riesgo": "medio",
            "precondiciones": [
                "Usuario autorizado",
                "Configuración de límites activa (monto máximo: 10,000)",
                "Saldo suficiente"
            ],
            "pasos": [
                "1. Acceder a la funcionalidad",
                "2. Ingresar monto superior al límite configurado (ej: 15,000)",
                "3. Completar demás campos",
                "4. Intentar confirmar la transacción"
            ],
            "resultados_esperados": [
                "El sistema bloquea la transacción",
                "Se muestra mensaje claro: 'El monto excede el límite permitido de 10,000'",
                "La transacción no se registra en el sistema",
                "Se puede corregir el monto y reintentar"
            ],
            "datos_prueba": {
                "limite_configurado": 10000,
                "monto_prueba": 15000,
                "mensaje_esperado": "El monto excede el límite permitido de 10,000"
            }
        }

    def _crear_caso_generico_medio_riesgo(self, index: int, requerimiento: str) -> Dict:
        """Crea un caso de medio riesgo genérico"""
        return {
            "titulo": "Validación de campos obligatorios",
            "descripcion": f"Prueba de validación de campos requeridos en {requerimiento[:80]}. Caso de MEDIO RIESGO porque si las validaciones fallan, podrían ingresarse datos incompletos que afecten procesos posteriores.",
            "nivel_riesgo": "medio",
            "precondiciones": [
                "Formulario o interfaz de la funcionalidad accesible"
            ],
            "pasos": [
                "1. Acceder a la funcionalidad",
                "2. Dejar campos obligatorios vacíos",
                "3. Intentar ejecutar la acción",
                "4. Verificar mensajes de error"
            ],
            "resultados_esperados": [
                "Se muestran mensajes específicos por cada campo obligatorio",
                "La acción no se ejecuta",
                "Los campos se marcan visualmente",
                "Se puede completar la información y reintentar"
            ],
            "datos_prueba": {
                "campos_obligatorios": "identificar del requerimiento",
                "mensajes_esperados": "listar mensajes de validación"
            }
        }

    def _crear_caso_generico_bajo_riesgo(self, index: int, requerimiento: str) -> Dict:
        """Crea un caso de bajo riesgo genérico"""
        return {
            "titulo": "Cancelación de operación antes de confirmar",
            "descripcion": "Verificar que se puede cancelar una operación antes de confirmarla sin afectar datos. Caso de BAJO RIESGO pero necesario para experiencia de usuario.",
            "nivel_riesgo": "bajo",
            "precondiciones": [
                "En proceso de creación de operación",
                "Datos parcialmente ingresados"
            ],
            "pasos": [
                "1. Ingresar datos parciales de la operación",
                "2. Hacer clic en 'Cancelar' o cerrar la ventana",
                "3. Volver a ingresar a la funcionalidad"
            ],
            "resultados_esperados": [
                "La operación no se guarda",
                "Los datos ingresados no persisten",
                "No hay registros parciales en el sistema"
            ],
            "datos_prueba": {}
        }

    def _detectar_tipo_funcionalidad(self, texto: str, contexto: Dict) -> str:
        """Detecta el tipo de funcionalidad principal basado en el texto y contexto"""
        texto_lower = texto.lower()
        
        # Matrices de palabras clave
        tipos = {
            'financiero/contable': ['pago', 'factura', 'facturación', 'orden', 'compra', 'venta', 'monto', 'precio', 'costo', 'total', 'presupuesto', 'contabilidad'],
            'gestión de usuarios': ['usuario', 'login', 'registro', 'permiso', 'rol', 'acceso', 'autenticación'],
            'reportes': ['reporte', 'informe', 'dashboard', 'estadística', 'gráfico', 'exportar'],
            'workflow/aprobaciones': ['aprobación', 'flujo', 'workflow', 'estado', 'transición', 'revisión'],
            'integración': ['api', 'integración', 'web service', 'conexión', 'sincronización'],
            'catálogo/productos': ['producto', 'catálogo', 'inventario', 'stock', 'bodega'],
            'documentos': ['documento', 'pdf', 'adjunto', 'archivo', 'carga']
        }
        
        # Verificar también en el contexto (funcionalidad del Excel)
        funcionalidad = contexto.get('funcionalidad', '').lower() if contexto else ''
        
        for tipo, keywords in tipos.items():
            for keyword in keywords:
                if keyword in texto_lower or keyword in funcionalidad:
                    return tipo
        
        return 'funcionalidad general'