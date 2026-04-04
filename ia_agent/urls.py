from django.urls import path
from . import views

app_name = 'ia_agent'

urlpatterns = [
    # Generación desde diferentes fuentes
    path('generar/ticket/<int:ticket_id>/', views.generar_desde_ticket, name='generar_ticket'),
    path('generar/solicitud/<int:solicitud_id>/', views.generar_desde_solicitud, name='generar_solicitud'),
    path('generar/url/', views.generar_desde_url, name='generar_url'),
    
    # Ver casos
    path('casos/', views.ver_casos, name='ver_casos_todos'),
    path('casos/ticket/<int:ticket_id>/', views.ver_casos, name='ver_casos_ticket'),
    path('casos/solicitud/<int:solicitud_id>/', views.ver_casos, name='ver_casos_solicitud'),
    path('casos/requerimiento/<int:requerimiento_id>/', views.ver_casos, name='ver_casos_requerimiento'),
    
    # Detalle y edición
    path('caso/<int:caso_id>/', views.detalle_caso, name='detalle_caso'),
    path('caso/<int:caso_id>/editar/', views.editar_caso, name='editar_caso'),
    path('caso/<int:caso_id>/eliminar/', views.eliminar_caso, name='eliminar_caso'),
    
    # API
    path('api/generar/', views.api_generar_casos, name='api_generar'),

    
]