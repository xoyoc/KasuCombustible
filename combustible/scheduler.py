import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Devuelve la instancia del scheduler (singleton)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone='America/Mexico_City')
        _scheduler.add_jobstore(DjangoJobStore(), 'default')
    return _scheduler


def start():
    """
    Registra todos los jobs y arranca el scheduler.
    Se llama desde el management command `runscheduler` (producción)
    o desde RegistrosConfig.ready() (desarrollo).
    """
    from mantenimientos.tasks import (
        generar_reporte_semanal,
        procesar_notificaciones_pendientes,
        verificar_mantenimientos_pendientes,
        verificar_mantenimientos_por_kilometraje,
    )
    from registros.tasks import (
        enviar_reporte_mensual_automatico,
        limpiar_archivos_temporales,
        verificar_operadores_inactivos,
    )

    scheduler = get_scheduler()

    jobs = [
        # Día 1 de cada mes a las 9:00 AM
        (enviar_reporte_mensual_automatico, CronTrigger(day=1, hour=9, minute=0), 'reporte-mensual'),
        # Todos los días a las 8:00 AM
        (verificar_mantenimientos_pendientes, CronTrigger(hour=8, minute=0), 'verificar-mantenimientos'),
        # Cada 2 horas en horario laboral
        (verificar_mantenimientos_por_kilometraje, CronTrigger(hour='8,10,12,14,16,18', minute=0), 'verificar-km'),
        # Cada 30 minutos
        (procesar_notificaciones_pendientes, CronTrigger(minute='*/30'), 'procesar-notificaciones'),
        # Lunes a las 10:00 AM
        (verificar_operadores_inactivos, CronTrigger(day_of_week='mon', hour=10, minute=0), 'operadores-inactivos'),
        # Lunes a las 9:00 AM
        (generar_reporte_semanal, CronTrigger(day_of_week='mon', hour=9, minute=0), 'reporte-semanal'),
        # Todos los días a las 3:00 AM
        (limpiar_archivos_temporales, CronTrigger(hour=3, minute=0), 'limpiar-archivos'),
    ]

    for func, trigger, job_id in jobs:
        scheduler.add_job(
            func,
            trigger,
            id=job_id,
            replace_existing=True,
            misfire_grace_time=60 * 60,  # 1 hora de gracia si el servidor estuvo caído
        )
        logger.info(f"Job registrado: {job_id}")

    scheduler.start()
    logger.info("APScheduler iniciado")
    return scheduler
