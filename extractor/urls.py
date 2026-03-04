from django.urls import path
from django.contrib.auth import views as auth_views 
from . import views

urlpatterns = [
    # ===== AUTENTICACIÓN (PÚBLICAS) =====
    path('login/', views.login_view, name='login'),  # Usar vista personalizada
    path('logout/', views.logout_view, name='logout'),  # Usar vista personalizada
    
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
    path('export/table/<str:table_name>/', views.export_table_csv, name='export_table_csv'),
    path('export/backup/', views.export_all_tables_backup, name='export_all_backup'),
    
    # ===== UTILIDADES (PÚBLICA PARA PRUEBAS) =====
    path('verificar-plantilla/', views.verificar_plantilla, name='verificar_plantilla'),
]