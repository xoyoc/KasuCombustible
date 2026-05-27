import os
from celery import Celery
from django.conf import settings

# Establecer el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tu_proyecto.settings')

app = Celery('mantenimiento')

# Usar Django settings para configurar Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las apps instaladas
app.autodiscover_tasks()

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    # Verificar mantenimientos cada día a las 8:00 AM
    'verificar-mantenimientos-diario': {
        'task': 'mantenimiento.tasks.verificar_mantenimientos_pendientes',
        'schedule': 60.0 * 60.0 * 24.0,  # 24 horas
        'options': {'expires': 60.0 * 60.0 * 6.0}  # Expira en 6 horas
    },
    
    # Verificar kilometrajes cada 2 horas durante horario laboral
    'verificar-kilometrajes': {
        'task': 'mantenimiento.tasks.verificar_mantenimientos_por_kilometraje',
        'schedule': 60.0 * 60.0 * 2.0,  # 2 horas
        'options': {'expires': 60.0 * 60.0}  # Expira en 1 hora
    },
    
    # Procesar notificaciones pendientes cada 30 minutos
    'procesar-notificaciones': {
        'task': 'mantenimiento.tasks.procesar_notificaciones_pendientes',
        'schedule': 60.0 * 30.0,  # 30 minutos
        'options': {'expires': 60.0 * 15.0}  # Expira en 15 minutos
    },
    
    # Generar reporte semanal los lunes a las 9:00 AM
    'reporte-semanal': {
        'task': 'mantenimiento.tasks.generar_reporte_semanal',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # 7 días
        'options': {'expires': 60.0 * 60.0 * 12.0}  # Expira en 12 horas
    },
}

# Configuración de timezone
app.conf.timezone = 'America/Bogota'  # Ajustar según tu zona horaria

# Configuración de broker y backend
app.conf.update(
    # Configuración de Redis (recomendado para producción)
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # Configuración alternativa con RabbitMQ
    # broker_url='amqp://guest@localhost//',
    # result_backend='rpc://',
    
    # Serialización
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Configuración de tareas
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_disable_rate_limits=True,
    
    # Configuración de resultados
    result_expires=60 * 60 * 24,  # 24 horas
    
    # Configuración de worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def debug_task(self):
    """Tarea de debug para probar Celery"""
    print(f'Request: {self.request!r}')