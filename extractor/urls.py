from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_excel, name='upload_excel'),
    path('list/', views.data_list, name='data_list'),
    
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

    path('tickets/', views.tickets_list, name='tickets_list'),
    path('tickets/ver/<int:id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/cambiar-estado/<int:id>/', views.ticket_cambiar_estado, name='ticket_cambiar_estado'),
]