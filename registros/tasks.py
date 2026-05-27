# registros/tasks.py - Tareas de Celery para reportes automáticos
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def enviar_reporte_mensual_automatico(self):
    """
    Tarea programada para enviar reporte mensual automáticamente
    Se ejecuta el primer día de cada mes a las 9:00 AM
    """
    try:
        logger.info("🚀 Iniciando envío automático de reporte mensual")
        
        # Ejecutar el comando de reporte mensual
        result = call_command(
            'enviar_reporte_mensual',
            verbosity=2,  # Mostrar output detallado
            save_to_spaces=True,
            send_email=True,
            send_whatsapp=True
        )
        
        logger.info("✅ Reporte mensual enviado exitosamente")
        return {
            'status': 'success',
            'message': 'Reporte mensual enviado correctamente',
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error enviando reporte mensual: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True)
def enviar_reporte_mensual_test(self, numero_whatsapp=None, email_test=None):
    """
    Tarea para enviar reporte de prueba
    """
    try:
        logger.info("🧪 Enviando reporte de prueba")
        
        # Ejecutar comando en modo test
        result = call_command(
            'enviar_reporte_mensual',
            test=True,
            verbosity=2,
            whatsapp=numero_whatsapp,
            email=email_test
        )
        
        logger.info("✅ Reporte de prueba enviado")
        return {
            'status': 'success',
            'message': 'Reporte de prueba enviado correctamente',
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error enviando reporte de prueba: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True)
def verificar_operadores_inactivos(self):
    """
    Tarea para verificar operadores inactivos y enviar alertas
    Se ejecuta semanalmente
    """
    try:
        from registros.models import Registro, Operador
        from datetime import datetime, timedelta
        
        # Obtener fecha de hace 7 días
        fecha_limite = timezone.now() - timedelta(days=7)
        
        # Operadores que han registrado combustible en los últimos 7 días
        operadores_activos = set(
            Registro.objects.filter(
                fecha_hora__gte=fecha_limite
            ).values_list('idOperador_id', flat=True)
        )
        
        # Operadores inactivos
        operadores_inactivos = Operador.objects.filter(
            activo=True
        ).exclude(id__in=operadores_activos)
        
        logger.info(f"📊 Operadores inactivos detectados: {operadores_inactivos.count()}")
        
        # Enviar alerta si hay operadores inactivos
        if operadores_inactivos.exists():
            from whatsaap_service import WhatsAppReportService
            whatsapp_service = WhatsAppReportService()
            
            # Obtener contactos de supervisores
            from registros.models import WhatsAppContact
            supervisores = WhatsAppContact.objects.filter(
                active=True,
                role='supervisor',
                receive_alerts=True
            )
            
            for supervisor in supervisores:
                try:
                    whatsapp_service.send_alert_inactive_operators(
                        supervisor.phone_number,
                        list(operadores_inactivos),
                        "Última semana"
                    )
                    logger.info(f"📱 Alerta enviada a supervisor: {supervisor.name}")
                except Exception as e:
                    logger.error(f"❌ Error enviando alerta a {supervisor.name}: {e}")
        
        return {
            'status': 'success',
            'operadores_inactivos': operadores_inactivos.count(),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error verificando operadores inactivos: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True)
def limpiar_archivos_temporales(self):
    """
    Tarea para limpiar archivos temporales y reportes antiguos
    Se ejecuta diariamente
    """
    try:
        from registros.models import ReporteGenerado
        from datetime import datetime, timedelta
        
        # Eliminar reportes más antiguos de 6 meses
        fecha_limite = timezone.now() - timedelta(days=180)
        reportes_antiguos = ReporteGenerado.objects.filter(
            fecha_generacion__lt=fecha_limite
        )
        
        count_deleted = 0
        for reporte in reportes_antiguos:
            try:
                # Eliminar archivo de Spaces
                if reporte.archivo_excel:
                    from combustible.storage_backends import delete_file_from_storage
                    delete_file_from_storage(reporte.archivo_excel.name)
                
                reporte.delete()
                count_deleted += 1
                
            except Exception as e:
                logger.error(f"❌ Error eliminando reporte {reporte.id}: {e}")
        
        logger.info(f"🗑️ Archivos temporales limpiados: {count_deleted} reportes eliminados")
        
        return {
            'status': 'success',
            'archivos_eliminados': count_deleted,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error limpiando archivos temporales: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(bind=True)
def backup_database_daily(self):
    """
    Tarea para crear backup diario de la base de datos
    """
    try:
        from django.core.management import call_command
        from datetime import datetime
        
        # Crear backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_combustible_{timestamp}.json"
        
        # Ejecutar dumpdata
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            '--exclude=contenttypes',
            '--exclude=auth.permission',
            '--exclude=admin.logentry',
            '--exclude=sessions.session',
            output=backup_filename,
            verbosity=1
        )
        
        logger.info(f"💾 Backup creado: {backup_filename}")
        
        return {
            'status': 'success',
            'backup_file': backup_filename,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando backup: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }
