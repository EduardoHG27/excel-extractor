# extractor/jira_helper.py
from jira import JIRA
from django.conf import settings
import logging

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