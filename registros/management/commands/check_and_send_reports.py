# registros/management/commands/check_and_send_reports.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica si debe enviar reporte mensual y ejecuta las tareas correspondientes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar envío de reporte aunque no sea día 1',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Ejecutar en modo test',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar output detallado',
        )
    
    def handle(self, *args, **options):
        hoy = datetime.now()
        force = options['force']
        test_mode = options['test']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'📅 Fecha actual: {hoy.strftime("%Y-%m-%d %H:%M:%S")}')
            )
        
        # Verificar si es día de reporte mensual
        if hoy.day == 1 or force:
            if hoy.day == 1:
                self.stdout.write(
                    self.style.SUCCESS(f'📊 Es día de reporte mensual: {hoy.strftime("%Y-%m-%d")}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚡ Modo FORCE activado - enviando reporte')
                )
            
            # Ejecutar reporte mensual
            try:
                if test_mode:
                    self.stdout.write(
                        self.style.WARNING('🧪 Ejecutando en modo TEST')
                    )
                    call_command('enviar_reporte_mensual', test=True, verbosity=2)
                else:
                    call_command('enviar_reporte_mensual', 
                               send_email=True, 
                               send_whatsapp=True,
                               verbosity=2)
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Reporte mensual procesado exitosamente')
                )
                
                # Verificar contactos de WhatsApp
                if not test_mode:
                    self.stdout.write(
                        self.style.SUCCESS('📱 Verificando contactos de WhatsApp...')
                    )
                    call_command('manage_whatsapp_contacts', list=True, verbosity=1)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error procesando reporte mensual: {str(e)}')
                )
                logger.error(f"Error en reporte mensual: {str(e)}")
                return
        
        else:
            self.stdout.write(
                self.style.WARNING(f'⏰ No es día de reporte. Hoy es día {hoy.day}')
            )
        
        # Ejecutar verificaciones diarias
        self.stdout.write(
            self.style.SUCCESS('🔧 Ejecutando verificaciones diarias...')
        )
        
        try:
            # Verificar mantenimientos
            call_command('verificar_mantenimientos', verbosity=1)
            self.stdout.write(
                self.style.SUCCESS('✅ Verificación de mantenimientos completada')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en verificación de mantenimientos: {str(e)}')
            )
            logger.error(f"Error en verificación de mantenimientos: {str(e)}")
        
        # Limpiar archivos temporales (solo los domingos)
        if hoy.weekday() == 6:  # Domingo
            self.stdout.write(
                self.style.SUCCESS('🗑️  Ejecutando limpieza de archivos...')
            )
            try:
                # Crear comando de limpieza si no existe
                from registros.models import ReporteGenerado
                from datetime import timedelta
                
                # Eliminar reportes más antiguos de 6 meses
                fecha_limite = timezone.now() - timedelta(days=180)
                reportes_antiguos = ReporteGenerado.objects.filter(
                    fecha_generacion__lt=fecha_limite
                )
                
                count_deleted = reportes_antiguos.count()
                reportes_antiguos.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Limpieza completada: {count_deleted} reportes eliminados')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error en limpieza: {str(e)}')
                )
                logger.error(f"Error en limpieza: {str(e)}")
        
        # Verificar operadores inactivos (solo los lunes)
        if hoy.weekday() == 0:  # Lunes
            self.stdout.write(
                self.style.SUCCESS('👥 Verificando operadores inactivos...')
            )
            try:
                from registros.models import Registro, Operador
                from datetime import timedelta
                
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
                
                if operadores_inactivos.exists():
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {operadores_inactivos.count()} operadores inactivos detectados')
                    )
                    
                    # Enviar alerta por WhatsApp si está configurado
                    try:
                        from whatsaap_service import WhatsAppReportService
                        from registros.models import WhatsAppContact
                        
                        whatsapp_service = WhatsAppReportService()
                        supervisores = WhatsAppContact.objects.filter(
                            active=True,
                            role='supervisor',
                            receive_alerts=True
                        )
                        
                        for supervisor in supervisores:
                            whatsapp_service.send_alert_inactive_operators(
                                supervisor.phone_number,
                                list(operadores_inactivos),
                                "Última semana"
                            )
                            self.stdout.write(
                                self.style.SUCCESS(f'📱 Alerta enviada a supervisor: {supervisor.name}')
                            )
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Error enviando alertas WhatsApp: {str(e)}')
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Todos los operadores están activos')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error verificando operadores: {str(e)}')
                )
                logger.error(f"Error verificando operadores: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Verificaciones diarias completadas')
        )
