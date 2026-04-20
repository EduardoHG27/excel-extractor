# extractor/urls.py - VERSIÓN ACTUALIZADA
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views  # ← Esto ahora importa desde el nuevo views.py modular

app_name = 'extractor'

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    
    # Consulta pública
    path('consultar/', views.consultar_ticket, name='consultar_ticket'),
    path('descargar/<int:ticket_id>/<str:tipo>/', views.descargar_archivo_publico, name='descargar_archivo_publico'),
    
    # Upload Excel
    path('upload/', views.upload_excel, name='upload_excel'),
    path('data/', views.data_list, name='data_list'),
    
    # Tickets
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('ticket/<int:id>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/delete/<int:id>/', views.ticket_delete, name='ticket_delete'),
    path('ticket/create/', views.ticket_create, name='ticket_create'),
    path('ticket/create-simple/', views.ticket_create_simple, name='ticket_create_simple'),
    path('ticket/crear-manual/', views.crear_ticket_manual, name='crear_ticket_manual'),
    
    # Acciones API
    path('api/ticket/<int:id>/cambiar-estado/', views.ticket_cambiar_estado, name='ticket_cambiar_estado'),
    path('api/ticket/<int:id>/cambiar-asignado/', views.ticket_cambiar_asignado, name='ticket_cambiar_asignado'),
    path('api/ticket/<int:id>/agregar-comentario/', views.ticket_agregar_comentario, name='ticket_agregar_comentario'),
    path('api/ticket/<int:ticket_id>/cambiar-nombre/', views.ticket_cambiar_nombre, name='ticket_cambiar_nombre'),
    
    # Archivos
    path('ticket/<int:id>/subir-dictamen/', views.subir_dictamen, name='subir_dictamen'),
    path('ticket/<int:id>/subir-evidencia/', views.subir_evidencia, name='subir_evidencia'),
    path('ticket/<int:id>/ver/<str:tipo>/', views.ver_archivo_cloudinary, name='ver_archivo_cloudinary'),
    path('ticket/<int:id>/descargar/<str:tipo>/', views.descargar_archivo_cloudinary, name='descargar_archivo_cloudinary'),
    path('api/ticket/<int:ticket_id>/eliminar-archivo/<str:tipo_archivo>/', views.eliminar_archivo_cloudinary, name='eliminar_archivo_cloudinary'),
    
    # Exportaciones
    path('export/tickets/csv/', views.export_tickets_csv_view, name='export_tickets_csv'),
    path('export/tickets/excel/', views.export_tickets_excel, name='export_tickets_excel'),
    path('export/table/<str:table_name>/csv/', views.export_table_csv, name='export_table_csv'),
    path('export/backup/', views.export_all_tables_backup, name='export_all_tables_backup'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/editar/<int:id>/', views.cliente_edit, name='cliente_edit'),
    path('clientes/eliminar/<int:id>/', views.cliente_delete, name='cliente_delete'),
    path('clientes/exportar/csv/', views.export_clientes_csv, name='export_clientes_csv'),
    
    # Proyectos
    path('proyectos/', views.proyectos_list, name='proyectos_list'),
    path('proyectos/nuevo/', views.proyecto_create, name='proyecto_create'),
    path('proyectos/editar/<int:id>/', views.proyecto_edit, name='proyecto_edit'),
    path('proyectos/eliminar/<int:id>/', views.proyecto_delete, name='proyecto_delete'),
    path('proyectos/exportar/csv/', views.export_proyectos_csv, name='export_proyectos_csv'),
    path('api/proyectos-por-cliente/<int:cliente_id>/', views.proyectos_por_cliente, name='proyectos_por_cliente'),
    
    # Tipos de Servicio
    path('tipos-servicio/', views.tipos_servicio_list, name='tipos_servicio_list'),
    path('tipos-servicio/nuevo/', views.tipo_servicio_create, name='tipo_servicio_create'),
    path('tipos-servicio/editar/<int:id>/', views.tipo_servicio_edit, name='tipo_servicio_edit'),
    path('tipos-servicio/eliminar/<int:id>/', views.tipo_servicio_delete, name='tipo_servicio_delete'),
    path('tipos-servicio/exportar/csv/', views.export_tipos_servicio_csv, name='export_tipos_servicio_csv'),
    
    # Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:id>/', views.usuario_detail, name='usuario_detail'),
    path('usuarios/editar/<int:id>/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/eliminar/<int:id>/', views.usuario_delete, name='usuario_delete'),
    path('usuarios/activar/<int:id>/', views.usuario_activar, name='usuario_activar'),
    path('api/usuario/<int:id>/cambiar-rol/', views.usuario_cambiar_rol, name='usuario_cambiar_rol'),
    path('usuarios/exportar/csv/', views.export_usuarios_csv, name='export_usuarios_csv'),
    
    # Solicitudes
    path('solicitudes/', views.solicitud_list, name='solicitud_list'),
    path('solicitudes/nueva/', views.crear_solicitud, name='crear_solicitud'),
    path('solicitudes/<int:id>/', views.solicitud_detail, name='solicitud_detail'),
    path('solicitudes/<int:id>/generar-ticket/', views.solicitud_generar_ticket, name='solicitud_generar_ticket'),
    path('solicitudes/<int:id>/eliminar/', views.solicitud_delete, name='solicitud_delete'),
    path('solicitudes/<int:id>/imprimir/', views.imprimir_solicitud_excel, name='imprimir_solicitud_excel'),
    
    # Documentos
    path('ticket/<int:ticket_id>/dictamen/', views.generar_excel_dictamen, name='generar_excel_dictamen'),
    path('ticket/<int:ticket_id>/resultados/', views.generar_excel_resultados, name='generar_excel_resultados'),
    path('verificar-plantilla/', views.verificar_plantilla, name='verificar_plantilla'),
]