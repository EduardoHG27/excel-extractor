# extractor/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views 
from . import views

app_name = 'extractor'  

urlpatterns = [
    # ===== AUTENTICACIÓN (PÚBLICAS) =====
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ===== SOLICITUDES (PÚBLICAS) =====
    path('solicitudes/', views.solicitud_list, name='solicitud_list'),
    path('solicitudes/crear/', views.crear_solicitud, name='crear_solicitud'),
    path('solicitudes/<int:id>/', views.solicitud_detail, name='solicitud_detail'),
    path('solicitudes/<int:id>/imprimir/', views.imprimir_solicitud_excel, name='imprimir_solicitud'),
    
    # ===== TICKETS (PRIVADAS) =====
    path('catalogos/tickets/', views.ticket_list, name='ticket_list'),
    path('catalogos/tickets/<int:id>/', views.ticket_detail, name='ticket_detail'),
    path('catalogos/tickets/nuevo/', views.ticket_create, name='ticket_create'),
    path('catalogos/tickets/eliminar/<int:id>/', views.ticket_delete, name='ticket_delete'),
    path('catalogos/tickets/nuevo/simple/', views.ticket_create_simple, name='ticket_create_simple'),
    path('tickets/crear-manual/', views.crear_ticket_manual, name='crear_ticket_manual'),
    path('ticket/<int:id>/cambiar-asignado/', views.ticket_cambiar_asignado, name='ticket_cambiar_asignado'),
    path('solicitudes/<int:id>/generar-ticket/', views.solicitud_generar_ticket, name='solicitud_generar_ticket'),
    
    # ===== EXCEL UPLOAD (PRIVADAS) =====
    path('upload/', views.upload_excel, name='upload_excel'),
    path('list/', views.data_list, name='data_list'),
    
    # ===== CLIENTES (PRIVADAS) =====
    path('catalogos/clientes/', views.clientes_list, name='clientes_list'),
    path('catalogos/clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('catalogos/clientes/editar/<int:id>/', views.cliente_edit, name='cliente_edit'),
    path('catalogos/clientes/eliminar/<int:id>/', views.cliente_delete, name='cliente_delete'),
    
    # ===== PROYECTOS (PRIVADAS) =====
    path('catalogos/proyectos/', views.proyectos_list, name='proyectos_list'),
    path('catalogos/proyectos/nuevo/', views.proyecto_create, name='proyecto_create'),
    path('catalogos/proyectos/editar/<int:id>/', views.proyecto_edit, name='proyecto_edit'),
    path('catalogos/proyectos/eliminar/<int:id>/', views.proyecto_delete, name='proyecto_delete'),
    path('catalogos/proyectos/por-cliente/<int:cliente_id>/', views.proyectos_por_cliente, name='proyectos_por_cliente'),
    
    # ===== TIPOS DE SERVICIO (PRIVADAS) =====
    path('catalogos/tipo-servicio/', views.tipos_servicio_list, name='tipo_servicio_list'),
    path('catalogos/tipo-servicio/nuevo/', views.tipo_servicio_create, name='tipo_servicio_create'),
    path('catalogos/tipo-servicio/editar/<int:id>/', views.tipo_servicio_edit, name='tipo_servicio_edit'),
    path('catalogos/tipo-servicio/eliminar/<int:id>/', views.tipo_servicio_delete, name='tipo_servicio_delete'),
    
    # ===== GENERACIÓN DE EXCEL (PRIVADAS) =====
    path('tickets/<int:ticket_id>/dictamen/', views.generar_excel_dictamen, name='generar_dictamen'),
    path('tickets/<int:ticket_id>/resultados/', views.generar_excel_resultados, name='generar_resultados'),
    
    # ===== EXPORTACIONES (PRIVADAS) =====
    path('export/tickets/', views.export_tickets_excel, name='export_tickets_excel'),
    path('export/clientes/', views.export_clientes_csv, name='export_clientes_csv'),
    path('export/proyectos/', views.export_proyectos_csv, name='export_proyectos_csv'),
    path('export/tipos-servicio/', views.export_tipos_servicio_csv, name='export_tipos_servicio_csv'),
    path('export/table/<str:table_name>/', views.export_table_csv, name='export_table_csv'),
    path('export/backup/', views.export_all_tables_backup, name='export_all_backup'),
    
    # ===== UTILIDADES (PÚBLICA PARA PRUEBAS) =====
    path('verificar-plantilla/', views.verificar_plantilla, name='verificar_plantilla'),
    path('registro/', views.registro_view, name='registro'),

    # ===== SEGUIMIENTO DE TICKETS =====
    path('ticket/<int:id>/cambiar-estado/', views.ticket_cambiar_estado, name='ticket_cambiar_estado'),
    path('ticket/<int:id>/agregar-comentario/', views.ticket_agregar_comentario, name='ticket_agregar_comentario'),

    # ===== GESTIÓN DE USUARIOS =====
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuario/<int:id>/', views.usuario_detail, name='usuario_detail'),
    path('usuario/<int:id>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuario/crear/', views.usuario_create, name='usuario_create'),
    path('usuario/<int:id>/eliminar/', views.usuario_delete, name='usuario_delete'),
    path('usuario/<int:id>/activar/', views.usuario_activar, name='usuario_activar'),
    path('usuario/<int:id>/cambiar-rol/', views.usuario_cambiar_rol, name='usuario_cambiar_rol'),
    path('usuarios/exportar-csv/', views.export_usuarios_csv, name='export_usuarios_csv'),

    path('ticket/<int:id>/subir-dictamen/', views.subir_dictamen, name='subir_dictamen'),
    path('ticket/<int:id>/subir-evidencia/', views.subir_evidencia, name='subir_evidencia'),
    path('ticket/<int:id>/eliminar-archivo/<str:tipo>/', views.eliminar_archivo_cloudinary, name='eliminar_archivo'),
]