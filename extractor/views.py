# extractor/views.py - VERSIÓN CORREGIDA (sin excel_extractor.)

# ===== AUTENTICACIÓN =====
from apps.auth_views.login import login_view, logout_view
from apps.auth_views.registro import registro_view
from apps.auth_views.public import consultar_ticket, descargar_archivo_publico

# ===== CATÁLOGOS =====
from apps.catalogos.views.clientes import (
    clientes_list, cliente_create, cliente_edit, cliente_delete, export_clientes_csv
)
from apps.catalogos.views.proyectos import (
    proyectos_list, proyecto_create, proyecto_edit, proyecto_delete,
    export_proyectos_csv, proyectos_por_cliente
)
from apps.catalogos.views.tipos_servicio import (
    tipos_servicio_list, tipo_servicio_create, tipo_servicio_edit,
    tipo_servicio_delete, export_tipos_servicio_csv
)
from apps.catalogos.views.usuarios import (
    usuarios_list, usuario_detail, usuario_create, usuario_edit,
    usuario_delete, usuario_activar, usuario_cambiar_rol, usuario_cambiar_lider, export_usuarios_csv  # 👈 Agrega usuario_cambiar_lider
)
from apps.catalogos.views.solicitudes import (
    solicitud_list, solicitud_detail, solicitud_generar_ticket,
    solicitud_delete, imprimir_solicitud_excel, crear_solicitud
)

# ===== TICKETS =====
from apps.tickets.views.ticket_crud import ticket_list, ticket_detail, ticket_delete
from apps.tickets.views.ticket_actions import (
    ticket_cambiar_estado, ticket_cambiar_asignado,
    ticket_agregar_comentario, ticket_cambiar_nombre
)
from apps.tickets.views.ticket_create import ticket_create, ticket_create_simple, crear_ticket_manual
from apps.tickets.views.ticket_export import export_tickets_csv_view, export_tickets_excel
from apps.tickets.views.ticket_files import (
    subir_dictamen, subir_evidencia, eliminar_archivo_cloudinary,
    ver_archivo_cloudinary, descargar_archivo_cloudinary, verificar_archivo_cloudinary
)

# ===== EXCEL PROCESSOR =====
from apps.excel_processor.views.upload import upload_excel
from apps.excel_processor.views.data import data_list, export_data_csv, data_detail
from apps.excel_processor.views.generate import (
    generar_excel_dictamen, generar_excel_resultados, verificar_plantilla
)
from apps.excel_processor.views.export import export_table_csv, export_all_tables_backup

# ===== SERVICIOS Y UTILIDADES =====
from apps.excel_processor.services.extractor_service import find_object_by_name_or_id
from apps.excel_processor.services.ticket_generator import generate_and_save_ticket
from apps.excel_processor.utils.helpers import generate_ticket_parts, calcular_dias_habiles, sanitizar_public_id, extraer_public_id_cloudinary

# ===== DASHBOARD =====
from apps.dashboard.views.lider_dashboard import dashboard_lider

