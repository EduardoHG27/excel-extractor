# extractor/jira_helper.py
from jira import JIRA
from django.conf import settings
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self):
        self.jira = None
        self.connect()
    
    def connect(self):
        """Conecta con Jira usando las credenciales"""
        try:
            # Verificar que JIRA_CONFIG existe
            if not hasattr(settings, 'JIRA_CONFIG'):
                logger.error("❌ JIRA_CONFIG no está definido en settings.py")
                print("❌ JIRA_CONFIG no está definido en settings.py")
                self.jira = None
                return
            
            config = settings.JIRA_CONFIG
            
            # Verificar que tenemos todas las configuraciones necesarias
            required = ['URL', 'EMAIL', 'API_TOKEN', 'PROJECT_KEY']
            missing = [key for key in required if not config.get(key)]
            
            if missing:
                error_msg = f"Faltan configuraciones en JIRA_CONFIG: {', '.join(missing)}"
                logger.error(error_msg)
                print(f"❌ {error_msg}")
                self.jira = None
                return
            
            options = {
                'server': config['URL'],
                'verify': True
            }
            
            print(f"🔄 Conectando a Jira: {config['URL']}")
            print(f"📋 Proyecto: {config['PROJECT_KEY']}")
            print(f"📧 Email: {config['EMAIL']}")
            
            self.jira = JIRA(
                options,
                basic_auth=(config['EMAIL'], config['API_TOKEN'])
            )
            
            # Probar la conexión
            projects = self.jira.projects()
            print(f"✅ Conectado a Jira exitosamente. Proyectos disponibles: {len(projects)}")
            logger.info("✅ Conectado a Jira exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Jira: {e}")
            print(f"❌ Error conectando a Jira: {e}")
            self.jira = None
    
    def create_issue(self, ticket_data):
        """
        Crea una incidencia en Jira con los datos del ticket
        """
        if not self.jira:
            logger.error("No hay conexión a Jira")
            print("❌ No hay conexión a Jira")
            return None
        
        try:
            config = settings.JIRA_CONFIG
            
            # Título formateado
            summary = f"PRUEBAS//{ticket_data['codigo']}//{ticket_data['cliente']} - {ticket_data['proyecto']}"
            
            print(f"📌 Título de incidencia: {summary}")
            
            # Construir la descripción formateada
            description = f"""
h3. Detalles del Ticket
* *Código:* {ticket_data['codigo']}
* *Cliente:* {ticket_data['cliente']}
* *Proyecto:* {ticket_data['proyecto']}
* *Tipo Servicio:* {ticket_data['tipo_servicio']}

h3. Responsables
* *Responsable Solicitud:* {ticket_data['responsable_solicitud']}
* *Líder Proyecto:* {ticket_data['lider_proyecto']}
* *Versión:* {ticket_data['numero_version']}

h3. Descripción de Cambios
* *Funcionalidad:* {ticket_data['funcionalidad_liberacion']}
* *Detalle:* {ticket_data['detalle_cambios']}
* *Justificación:* {ticket_data['justificacion_cambio']}

----
*Generado automáticamente desde el sistema de carga de Excel*
*Fecha:* {ticket_data.get('fecha', '')}
*Usuario:* {ticket_data.get('usuario', '')}
"""
            
            # Crear la incidencia
            issue_dict = {
                'project': {'key': config['PROJECT_KEY']},
                'issuetype': {'name': config.get('ISSUE_TYPE', 'Task')},
                'summary': summary[:255],  # Jira limita a 255 caracteres
                'description': description.strip(),
                'priority': {'name': 'Medium'},
                'labels': ['qa-automation', 'excel-upload', ticket_data['tipo_servicio']],
            }
            
            print(f"🔄 Creando incidencia en Jira...")
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            logger.info(f"✅ Incidencia Jira creada: {new_issue.key}")
            print(f"✅ Incidencia Jira creada: {new_issue.key}")
            print(f"📌 Título: {summary}")
            print(f"🔗 URL: {new_issue.permalink()}")
            
            return new_issue
            
        except KeyError as e:
            logger.error(f"❌ Falta dato requerido en ticket_data: {e}")
            print(f"❌ Falta dato requerido en ticket_data: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creando incidencia en Jira: {e}")
            print(f"❌ Error creando incidencia en Jira: {e}")
            return None
    
    # 👇 AGREGAR ESTE NUEVO MÉTODO 👇
    def close_issue(self, issue_key, resolution='Done'):
        """
        Cierra una incidencia en Jira - Versión para workflow con estado FINALIZADA
        """
        if not self.jira:
            logger.error("No hay conexión a Jira")
            return {
                'success': False,
                'warning': 'No hay conexión a Jira'
            }
        
        try:
            # Obtener la incidencia
            issue = self.jira.issue(issue_key)
            current_status = issue.fields.status.name
            logger.info(f"Cerrando incidencia {issue_key} - Estado actual: {current_status}")
            
            # Verificar si ya está finalizada
            if current_status == "FINALIZADA":
                logger.info(f"Incidencia {issue_key} ya está FINALIZADA")
                return {
                    'success': True,
                    'issue_key': issue_key,
                    'message': f'Incidencia {issue_key} ya estaba finalizada'
                }
            
            # Obtener transiciones disponibles
            transitions = self.jira.transitions(issue)
            
            # ============================================================
            # 🔍 DEPURACIÓN: Mostrar TODAS las transiciones con sus destinos
            # ============================================================
            print(f"\n{'='*60}")
            print(f"🔍 TRANSICIONES DISPONIBLES PARA {issue_key}")
            print(f"Estado actual: {current_status}")
            print(f"{'='*60}")
            for idx, t in enumerate(transitions):
                # Intentar obtener el estado destino de diferentes maneras
                to_name = "DESCONOCIDO"
                
                # Método 1: Si es un objeto con atributo 'to'
                if hasattr(t, 'to') and t.to:
                    to_name = t.to.name if hasattr(t.to, 'name') else str(t.to)
                # Método 2: Si es un diccionario
                elif isinstance(t, dict) and 'to' in t:
                    if isinstance(t['to'], dict):
                        to_name = t['to'].get('name', 'DESCONOCIDO')
                    else:
                        to_name = str(t['to'])
                
                print(f"{idx+1}. ID: {t['id']} | Nombre: '{t['name']}' → Destino: '{to_name}'")
            
            print(f"{'='*60}\n")

            if not transitions:
                logger.warning(f"No hay transiciones disponibles para {issue_key}")
                return {
                    'success': False,
                    'warning': f'No hay transiciones disponibles para {issue_key}'
                }
            
            # 🔍 Buscar específicamente la transición a FINALIZADA
            close_transition_id = None
            transition_name = None
            
            # Prioridad: buscar transición que lleve a FINALIZADA o nombres similares
            keywords = ['finalizada', 'finalizado', 'finish', 'complete', 'close', 'cerrar', 'done']
            
            for transition in transitions:
                name_lower = transition['name'].lower()
                # Verificar si la transición lleva a FINALIZADA
                if hasattr(transition, 'to') and transition.to and transition.to.name == "FINALIZADA":
                    close_transition_id = transition['id']
                    transition_name = transition['name']
                    logger.info(f"✅ Transición a FINALIZADA encontrada: {transition_name} (ID: {close_transition_id})")
                    break
                # Si no, buscar por keywords
                for keyword in keywords:
                    if keyword in name_lower:
                        close_transition_id = transition['id']
                        transition_name = transition['name']
                        logger.info(f"✅ Transición encontrada por keyword '{keyword}': {transition_name}")
                        break
                if close_transition_id:
                    break
            
            # Si no encontró, mostrar todas las transiciones disponibles para depuración
            if not close_transition_id:
                logger.warning(f"⚠️ No se encontró transición a FINALIZADA. Transiciones disponibles:")
                for t in transitions:
                    to_name = t.get('to', {}).get('name', 'Desconocido') if hasattr(t, 'to') else 'N/A'
                    logger.warning(f"  - {t['id']}: {t['name']} → {to_name}")
                
                # Último recurso: usar la primera transición que contenga palabras clave
                for transition in transitions:
                    name_lower = transition['name'].lower()
                    if any(k in name_lower for k in ['final', 'complet', 'close', 'cerr']):
                        close_transition_id = transition['id']
                        transition_name = transition['name']
                        logger.warning(f"⚠️ Usando transición por keyword: {transition_name}")
                        break
                
                # Si aún nada, usar la primera transición disponible
                if not close_transition_id and transitions:
                    close_transition_id = transitions[0]['id']
                    transition_name = transitions[0]['name']
                    logger.warning(f"⚠️ Usando primera transición disponible: {transition_name}")
            
            if not close_transition_id:
                return {
                    'success': False,
                    'warning': f'No se encontró transición para finalizar {issue_key}'
                }
            
            # Ejecutar la transición
            try:
                self.jira.transition_issue(issue_key, close_transition_id)
                
                # Agregar comentario de cierre
                try:
                    comment = f"Incidencia finalizada automáticamente desde el sistema QA.\nEstado del ticket: {'COMPLETADO' if resolution == 'Done' else 'NO EXITOSO'}"
                    self.jira.add_comment(issue_key, comment)
                except Exception as e:
                    logger.warning(f"No se pudo agregar comentario: {e}")
                
                logger.info(f"✅ Incidencia {issue_key} finalizada exitosamente")
                
                return {
                    'success': True,
                    'issue_key': issue_key,
                    'message': f'Incidencia {issue_key} finalizada exitosamente',
                    'transition_used': transition_name
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error al ejecutar transición: {error_msg}")
                
                # Intentar con resolución si es necesario
                if 'resolution' in error_msg.lower():
                    try:
                        self.jira.transition_issue(
                            issue_key, 
                            close_transition_id,
                            fields={'resolution': {'name': resolution}}
                        )
                        logger.info(f"✅ Incidencia {issue_key} finalizada con resolución")
                        return {
                            'success': True,
                            'issue_key': issue_key,
                            'message': f'Incidencia {issue_key} finalizada exitosamente'
                        }
                    except Exception as e2:
                        return {
                            'success': False,
                            'warning': f'Error al finalizar: {str(e2)}'
                        }
                else:
                    return {
                        'success': False,
                        'warning': f'Error al finalizar: {error_msg}'
                    }
                
        except Exception as e:
            error_msg = f"Error al finalizar incidencia {issue_key}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'warning': error_msg
            }

def create_jira_issue_from_ticket(ticket_obj, jira_data, request=None):
    """
    Helper function to create Jira issue from ticket data
    
    Args:
        ticket_obj: Objeto Ticket recién creado
        jira_data: Diccionario con datos necesarios para Jira:
            - cliente_obj o cliente_nombre
            - proyecto_obj o proyecto_nombre
            - tipo_servicio
            - responsable_solicitud
            - lider_proyecto
            - numero_version
            - funcionalidad_liberacion
            - detalle_cambios
            - justificacion_cambio
        request: Objeto request de Django (opcional)
    
    Returns:
        tuple: (success, message, jira_issue)
    """
    try:
        # Extraer nombres de cliente y proyecto
        if 'cliente_obj' in jira_data and jira_data['cliente_obj']:
            cliente_nombre = jira_data['cliente_obj'].nombre
        else:
            cliente_nombre = jira_data.get('cliente_nombre', '')
        
        if 'proyecto_obj' in jira_data and jira_data['proyecto_obj']:
            proyecto_nombre = jira_data['proyecto_obj'].nombre
        else:
            proyecto_nombre = jira_data.get('proyecto_nombre', '')
        
        tipo_servicio = jira_data.get('tipo_servicio', 'PRU')
        
        # Preparar datos para Jira (siguiendo el mismo formato que _create_jira_issue)
        jira_issue_data = {
            'codigo': ticket_obj.codigo[:50],
            'cliente': cliente_nombre[:100],
            'proyecto': proyecto_nombre[:100],
            'tipo_servicio': tipo_servicio[:50],
            'responsable_solicitud': jira_data.get('responsable_solicitud', '')[:100],
            'lider_proyecto': jira_data.get('lider_proyecto', '')[:100],
            'numero_version': jira_data.get('numero_version', '')[:50],
            'funcionalidad_liberacion': jira_data.get('funcionalidad_liberacion', '')[:500],
            'detalle_cambios': jira_data.get('detalle_cambios', '')[:1000],
            'justificacion_cambio': jira_data.get('justificacion_cambio', '')[:500],
            'fecha': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'usuario': request.user.username[:50] if request and request.user.is_authenticated else 'Sistema',
        }
        
        # Crear cliente de Jira y el issue
        jira_client = JiraClient()
        jira_issue = jira_client.create_issue(jira_issue_data)
        
        if jira_issue:
            # Actualizar el ticket con la información de Jira
            ticket_obj.jira_issue_key = jira_issue.key
            ticket_obj.jira_issue_url = jira_issue.permalink()
            ticket_obj.fecha_sincronizacion_jira = timezone.now()
            ticket_obj.save()
            
            logger.info(f"✅ Jira issue creado para ticket {ticket_obj.codigo}: {jira_issue.key}")
            return True, f'Incidencia creada en Jira: {jira_issue.key}', jira_issue
        else:
            logger.warning(f"⚠️ No se pudo crear Jira issue para ticket {ticket_obj.codigo}")
            return False, 'No se pudo crear la incidencia en Jira', None
            
    except Exception as e:
        logger.error(f"❌ Error creando Jira issue para ticket {ticket_obj.codigo}: {str(e)}")
        return False, f'Error al crear incidencia en Jira: {str(e)}', None