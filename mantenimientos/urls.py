from django.urls import path
from . import views

app_name = 'mantenimiento'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Mantenimientos
    path('mantenimientos/', views.MantenimientoListView.as_view(), name='list'),
    path('mantenimientos/crear/', views.MantenimientoCreateView.as_view(), name='create'),
    path('mantenimientos/<int:pk>/editar/', views.MantenimientoUpdateView.as_view(), name='update'),
    path('mantenimientos/<int:pk>/completar/', views.completar_mantenimiento, name='completar'),
    
    # Equipos
    path('equipos/estado/', views.equipos_estado, name='equipos_estado'),
    path('equipos/<int:equipo_id>/actualizar-kilometraje/', views.actualizar_kilometraje, name='actualizar_kilometraje'),
    
    # Notificaciones
    path('notificaciones/', views.notificaciones_list, name='notificaciones'),
    path('notificaciones/<int:pk>/enviar/', views.enviar_notificacion_manual, name='enviar_notificacion'),
    
    # Reportes
    path('reportes/mantenimientos/', views.reporte_mantenimientos, name='reporte_mantenimientos'),
    
    # API endpoints
    path('api/equipos-mantenimiento/', views.api_equipos_mantenimiento, name='api_equipos_mantenimiento'),
]