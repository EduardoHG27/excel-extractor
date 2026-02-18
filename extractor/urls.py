from django.urls import path
from django.contrib.auth import views as auth_views 
from . import views

urlpatterns = [
    path('upload/', views.upload_excel, name='upload_excel'),
    path('list/', views.data_list, name='data_list'),
    
    path('login/', auth_views.LoginView.as_view(template_name='extractor/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    # Rutas para catálogo de clientes
    path('catalogos/clientes/', views.clientes_list, name='clientes_list'),
    path('catalogos/clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('catalogos/clientes/editar/<int:id>/', views.cliente_edit, name='cliente_edit'),
    path('catalogos/clientes/eliminar/<int:id>/', views.cliente_delete, name='cliente_delete'),

    path('catalogos/proyectos/', views.proyectos_list, name='proyectos_list'),
    path('catalogos/proyectos/nuevo/', views.proyecto_create, name='proyecto_create'),
    path('catalogos/proyectos/editar/<int:id>/', views.proyecto_edit, name='proyecto_edit'),
    path('catalogos/proyectos/eliminar/<int:id>/', views.proyecto_delete, name='proyecto_delete'),
    path('catalogos/proyectos/por-cliente/<int:cliente_id>/', views.proyectos_por_cliente, name='proyectos_por_cliente'),

    path('catalogos/tipo-servicio/', views.tipos_servicio_list, name='tipo_servicio_list'),
    path('catalogos/tipo-servicio/nuevo/', views.tipo_servicio_create, name='tipo_servicio_create'),
    path('catalogos/tipo-servicio/editar/<int:id>/', views.tipo_servicio_edit, name='tipo_servicio_edit'),
    path('catalogos/tipo-servicio/eliminar/<int:id>/', views.tipo_servicio_delete, name='tipo_servicio_delete'),

    path('catalogos/tickets/', views.ticket_list, name='ticket_list'),
    path('catalogos/tickets/<int:id>/', views.ticket_detail, name='ticket_detail'),
    path('catalogos/tickets/nuevo/', views.ticket_create, name='ticket_create'),

    path('catalogos/tickets/nuevo/simple/', views.ticket_create_simple, name='ticket_create_simple'),

    path('tickets/<int:ticket_id>/dictamen/', views.generar_excel_dictamen, name='generar_dictamen'),
    path('tickets/<int:ticket_id>/resultados/', views.generar_excel_resultados, name='generar_resultados'),


    path('export/tickets/', views.export_tickets_excel, name='export_tickets_excel'),
    path('export/table/<str:table_name>/', views.export_table_csv, name='export_table_csv'),
    path('export/backup/', views.export_all_tables_backup, name='export_all_backup'),
  ]