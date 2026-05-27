# combustible/celery.py - Configuración principal de Celery
import os
from celery import Celery
from django.conf import settings

# Establecer el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'combustible.settings')

app = Celery('combustible')

# Usar Django settings para configurar Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las apps instaladas
app.autodiscover_tasks()

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    # === REPORTES MENSUALES ===
    # Enviar reporte mensual el primer día de cada mes a las 9:00 AM
    'reporte-mensual-automatico': {
        'task': 'registros.tasks.enviar_reporte_mensual_automatico',
        'schedule': 60.0 * 60.0 * 24.0 * 1.0,  # Cada día (se ejecutará solo el día 1)
        'options': {'expires': 60.0 * 60.0 * 6.0}  # Expira en 6 horas
    },
    
    # === MANTENIMIENTOS ===
    # Verificar mantenimientos cada día a las 8:00 AM
    'verificar-mantenimientos-diario': {
        'task': 'mantenimientos.tasks.verificar_mantenimientos_pendientes',
        'schedule': 60.0 * 60.0 * 24.0,  # 24 horas
        'options': {'expires': 60.0 * 60.0 * 6.0}  # Expira en 6 horas
    },
    
    # Verificar kilometrajes cada 2 horas durante horario laboral
    'verificar-kilometrajes': {
        'task': 'mantenimientos.tasks.verificar_mantenimientos_por_kilometraje',
        'schedule': 60.0 * 60.0 * 2.0,  # 2 horas
        'options': {'expires': 60.0 * 60.0}  # Expira en 1 hora
    },
    
    # Procesar notificaciones pendientes cada 30 minutos
    'procesar-notificaciones': {
        'task': 'mantenimientos.tasks.procesar_notificaciones_pendientes',
        'schedule': 60.0 * 30.0,  # 30 minutos
        'options': {'expires': 60.0 * 15.0}  # Expira en 15 minutos
    },
    
    # === REPORTES Y ALERTAS ===
    # Verificar operadores inactivos cada lunes a las 10:00 AM
    'verificar-operadores-inactivos': {
        'task': 'registros.tasks.verificar_operadores_inactivos',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # 7 días
        'options': {'expires': 60.0 * 60.0 * 12.0}  # Expira en 12 horas
    },
    
    # Generar reporte semanal los lunes a las 9:00 AM
    'reporte-semanal': {
        'task': 'mantenimientos.tasks.generar_reporte_semanal',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # 7 días
        'options': {'expires': 60.0 * 60.0 * 12.0}  # Expira en 12 horas
    },
    
    # === MANTENIMIENTO DEL SISTEMA ===
    # Limpiar archivos temporales diariamente a las 2:00 AM
    'limpiar-archivos-temporales': {
        'task': 'registros.tasks.limpiar_archivos_temporales',
        'schedule': 60.0 * 60.0 * 24.0,  # 24 horas
        'options': {'expires': 60.0 * 60.0 * 6.0}  # Expira en 6 horas
    },
    
    # Backup diario de base de datos a las 3:00 AM
    'backup-database-daily': {
        'task': 'registros.tasks.backup_database_daily',
        'schedule': 60.0 * 60.0 * 24.0,  # 24 horas
        'options': {'expires': 60.0 * 60.0 * 6.0}  # Expira en 6 horas
    },
}

# Configuración de timezone (México)
app.conf.timezone = 'America/Mexico_City'

# Configuración de broker y backend
app.conf.update(
    # Configuración de Redis (recomendado para producción)
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
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
    
    # Configuración de reintentos
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Configuración de colas
    task_routes={
        'registros.tasks.enviar_reporte_mensual_automatico': {'queue': 'reports'},
        'registros.tasks.verificar_operadores_inactivos': {'queue': 'alerts'},
        'mantenimientos.tasks.*': {'queue': 'maintenance'},
        'registros.tasks.limpiar_archivos_temporales': {'queue': 'cleanup'},
        'registros.tasks.backup_database_daily': {'queue': 'backup'},
    },
)

@app.task(bind=True)
def debug_task(self):
    """Tarea de debug para probar Celery"""
    print(f'Request: {self.request!r}')
    return f'Debug task executed at {self.request.id}'

# Tarea para verificar que el reporte mensual se ejecute solo el día 1
@app.task
def verificar_dia_reporte_mensual():
    """
    Verifica si es el primer día del mes para ejecutar el reporte mensual
    """
    from datetime import datetime
    
    hoy = datetime.now()
    if hoy.day == 1:  # Solo el día 1 del mes
        enviar_reporte_mensual_automatico.delay()
        return f"Reporte mensual programado para {hoy.strftime('%Y-%m-%d')}"
    else:
        return f"No es día de reporte mensual. Hoy es día {hoy.day}"
