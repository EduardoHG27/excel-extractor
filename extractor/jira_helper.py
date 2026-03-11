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
            options = {
                'server': settings.JIRA_CONFIG['URL'],
                'verify': True
            }
            self.jira = JIRA(
                options,
                basic_auth=(
                    settings.JIRA_CONFIG['EMAIL'],
                    settings.JIRA_CONFIG['API_TOKEN']
                )
            )
            logger.info("✅ Conectado a Jira exitosamente")
            print("✅ Conectado a Jira exitosamente")
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
            return None
        
        try:
            # 🔥 NUEVO FORMATO DE TÍTULO:
            # PRUEBAS//BID-PRU-NAF-4-BRA-EPWE-005//Bradesco - Entrolamiento Presencial Webapp
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
                'project': {'key': settings.JIRA_CONFIG['PROJECT_KEY']},
                'issuetype': {'name': settings.JIRA_CONFIG['ISSUE_TYPE']},
                'summary': summary[:255],  # Jira limita a 255 caracteres
                'description': description.strip(),
                'priority': {'name': 'Medium'},
                'labels': ['qa-automation', 'excel-upload', ticket_data['tipo_servicio']],
            }
            
            # Crear la incidencia
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            logger.info(f"✅ Incidencia Jira creada: {new_issue.key}")
            print(f"✅ Incidencia Jira creada: {new_issue.key}")
            print(f"📌 Título: {summary}")
            return new_issue
            
        except Exception as e:
            logger.error(f"❌ Error creando incidencia en Jira: {e}")
            print(f"❌ Error creando incidencia en Jira: {e}")
            return None