from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail

from mantenimientos.models import Mantenimiento, Equipo, Notificacion, Supervisor


class Command(BaseCommand):
    help = 'Verifica mantenimientos pendientes y envía notificaciones'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin enviar notificaciones reales',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar envío aunque ya se hayan enviado notificaciones hoy',
        )
        parser.add_argument(
            '--dias-aviso',
            type=int,
            default=5,
            help='Días de anticipación para recordatorios (default: 5)',
        )
        parser.add_argument(
            '--km-aviso',
            type=int,
            default=100,
            help='Kilómetros de anticipación para recordatorios (default: 100)',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.dias_aviso = options['dias_aviso']
        self.km_aviso = options['km_aviso']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Iniciando verificación de mantenimientos...'
            )
        )
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se enviarán notificaciones reales')
            )
        
        # Estadísticas
        recordatorios_enviados = 0
        reportes_supervisor = 0
        mantenimientos_vencidos = 0
        
        try:
            # 1. Verificar mantenimientos por fecha
            recordatorios_enviados += self.verificar_mantenimientos_fecha()
            
            # 2. Verificar mantenimientos por kilometraje
            recordatorios_enviados += self.verificar_mantenimientos_kilometraje()
            
            # 3. Verificar mantenimientos vencidos
            mantenimientos_vencidos, reportes_supervisor = self.verificar_mantenimientos_vencidos()
            
            # 4. Procesar notificaciones pendientes
            notificaciones_procesadas = self.procesar_notificaciones_pendientes()
            
            # Resumen
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n=== RESUMEN DE VERIFICACIÓN ==='
                )
            )
            self.stdout.write(f'Recordatorios enviados: {recordatorios_enviados}')
            self.stdout.write(f'Mantenimientos vencidos detectados: {mantenimientos_vencidos}')
            self.stdout.write(f'Reportes a supervisor enviados: {reportes_supervisor}')
            self.stdout.write(f'Notificaciones pendientes procesadas: {notificaciones_procesadas}')
            
        except Exception as e:
            raise CommandError(f'Error durante la verificación: {str(e)}')
    
    def verificar_mantenimientos_fecha(self):
        """Verificar mantenimientos que necesitan recordatorio por fecha"""
        self.stdout.write('Verificando mantenimientos por fecha...')
        
        fecha_limite = timezone.now().date() + timedelta(days=self.dias_aviso)
        
        mantenimientos = Mantenimiento.objects.filter(
            estado='pendiente',
            fecha_programada__lte=fecha_limite,
            fecha_programada__gte=timezone.now().date()
        )
        
        recordatorios_enviados = 0
        
        for mantenimiento in mantenimientos:
            # Verificar si ya se envió recordatorio hoy
            if not self.force:
                recordatorio_hoy = Notificacion.objects.filter(
                    mantenimiento=mantenimiento,
                    tipo='recordatorio',
                    fecha_creacion__date=timezone.now().date()
                ).exists()
                
                if recordatorio_hoy:
                    continue
            
            dias_restantes = (mantenimiento.fecha_programada - timezone.now().date()).days
            
            self.stdout.write(
                f'  - {mantenimiento.equipo.placa}: {dias_restantes} días para mantenimiento'
            )
            
            if self.crear_notificacion_recordatorio(mantenimiento, por_fecha=True):
                recordatorios_enviados += 1
        
        return recordatorios_enviados
    
    def verificar_mantenimientos_kilometraje(self):
        """Verificar mantenimientos que necesitan recordatorio por kilometraje"""
        self.stdout.write('Verificando mantenimientos por kilometraje...')
        
        recordatorios_enviados = 0
        
        for equipo in Equipo.objects.filter(activo=True):
            proximo = equipo.proximo_mantenimiento()
            
            if proximo['km_restantes'] <= self.km_aviso and proximo['km_restantes'] > 0:
                # Buscar mantenimiento pendiente para este equipo
                mantenimiento = Mantenimiento.objects.filter(
                    equipo=equipo,
                    estado='pendiente'
                ).first()
                
                if mantenimiento:
                    # Verificar si ya se envió recordatorio hoy
                    if not self.force:
                        recordatorio_hoy = Notificacion.objects.filter(
                            mantenimiento=mantenimiento,
                            tipo='recordatorio',
                            fecha_creacion__date=timezone.now().date()
                        ).exists()
                        
                        if recordatorio_hoy:
                            continue
                    
                    self.stdout.write(
                        f'  - {equipo.placa}: {proximo["km_restantes"]} km para mantenimiento'
                    )
                    
                    if self.crear_notificacion_recordatorio(mantenimiento, por_kilometraje=True):
                        recordatorios_enviados += 1
        
        return recordatorios_enviados
    
    def verificar_mantenimientos_vencidos(self):
        """Verificar mantenimientos vencidos y enviar reportes al supervisor"""
        self.stdout.write('Verificando mantenimientos vencidos...')
        
        # Mantenimientos vencidos ayer (para dar un día de gracia)
        fecha_vencimiento = timezone.now().date() - timedelta(days=1)
        
        mantenimientos_vencidos = Mantenimiento.objects.filter(
            estado='pendiente',
            fecha_programada=fecha_vencimiento
        )
        
        reportes_enviados = 0
        
        for mantenimiento in mantenimientos_vencidos:
            # Marcar como vencido
            mantenimiento.estado = 'vencido'
            if not self.dry_run:
                mantenimiento.save()
            
            self.stdout.write(
                f'  - VENCIDO: {mantenimiento.equipo.placa} - {mantenimiento.fecha_programada}'
            )
            
            # Enviar reporte a supervisores
            if self.enviar_reporte_supervisor(mantenimiento):
                reportes_enviados += 1
        
        return len(mantenimientos_vencidos), reportes_enviados
    
    def crear_notificacion_recordatorio(self, mantenimiento, por_fecha=False, por_kilometraje=False):
        """Crear y enviar notificación de recordatorio"""
        if por_kilometraje:
            asunto = f"Recordatorio por Kilometraje - {mantenimiento.equipo.placa}"
            mensaje = f"""
Estimado {mantenimiento.operador.nombre},

El equipo {mantenimiento.equipo.placa} está próximo al límite de kilometraje para mantenimiento.

Detalles:
- Equipo: {mantenimiento.equipo.placa}
- Kilometraje actual: {mantenimiento.equipo.kilometraje_actual:,} km
- Kilometraje programado: {mantenimiento.kilometraje_programado:,} km
- Kilómetros restantes: {mantenimiento.kilometraje_programado - mantenimiento.equipo.kilometraje_actual:,} km

Por favor, programe el mantenimiento lo antes posible.
            """.strip()
        else:
            dias_restantes = (mantenimiento.fecha_programada - timezone.now().date()).days
            asunto = f"Recordatorio de Mantenimiento - {mantenimiento.equipo.placa}"
            mensaje = f"""
Estimado {mantenimiento.operador.nombre},

Le recordamos que el equipo {mantenimiento.equipo.placa} tiene mantenimiento programado.

Detalles:
- Equipo: {mantenimiento.equipo.placa}
- Fecha programada: {mantenimiento.fecha_programada.strftime('%d/%m/%Y')}
- Días restantes: {dias_restantes}
- Tipo: {mantenimiento.tipo_mantenimiento.nombre}

Por favor, programe el mantenimiento lo antes posible.
            """.strip()
        
        # Crear notificación
        notificacion = Notificacion(
            mantenimiento=mantenimiento,
            tipo='recordatorio',
            destinatario_email=mantenimiento.operador.email,
            asunto=asunto,
            mensaje=mensaje,
            fecha_programada=timezone.now()
        )
        
        if not self.dry_run:
            notificacion.save()
            notificacion.enviar()
            return notificacion.estado == 'enviada'
        else:
            self.stdout.write(f'    [DRY-RUN] Notificación creada para {mantenimiento.operador.email}')
            return True
    
    def enviar_reporte_supervisor(self, mantenimiento):
        """Enviar reporte de mantenimiento vencido al supervisor"""
        supervisores = Supervisor.objects.filter(activo=True)
        
        if not supervisores.exists():
            self.stdout.write(
                self.style.WARNING('    No hay supervisores activos configurados')
            )
            return False
        
        asunto = f"ALERTA: Mantenimiento Vencido - {mantenimiento.equipo.placa}"
        mensaje = f"""
ALERTA DE MANTENIMIENTO VENCIDO

El siguiente mantenimiento está vencido y requiere atención inmediata:

Equipo: {mantenimiento.equipo.placa} ({mantenimiento.equipo.marca} {mantenimiento.equipo.modelo})
Operador Responsable: {mantenimiento.operador.nombre}
Email Operador: {mantenimiento.operador.email}
Fecha Programada: {mantenimiento.fecha_programada.strftime('%d/%m/%Y')}
Días Vencido: {mantenimiento.dias_vencido()}
Tipo de Mantenimiento: {mantenimiento.tipo_mantenimiento.nombre}

Es necesario tomar acción inmediata para programar este mantenimiento.

Sistema de Mantenimiento
        """.strip()
        
        reportes_enviados = 0
        
        for supervisor in supervisores:
            notificacion = Notificacion(
                mantenimiento=mantenimiento,
                tipo='reporte_supervisor',
                destinatario_email=supervisor.email,
                asunto=asunto,
                mensaje=mensaje,
                fecha_programada=timezone.now()
            )
            
            if not self.dry_run:
                notificacion.save()
                notificacion.enviar()
                if notificacion.estado == 'enviada':
                    reportes_enviados += 1
            else:
                self.stdout.write(f'    [DRY-RUN] Reporte enviado a {supervisor.email}')
                reportes_enviados += 1
        
        return reportes_enviados > 0
    
    def procesar_notificaciones_pendientes(self):
        """Procesar notificaciones pendientes que deben enviarse"""
        self.stdout.write('Procesando notificaciones pendientes...')
        
        notificaciones_pendientes = Notificacion.objects.filter(
            estado='pendiente',
            fecha_programada__lte=timezone.now()
        )
        
        procesadas = 0
        
        for notificacion in notificaciones_pendientes:
            if not self.dry_run:
                notificacion.enviar()
                if notificacion.estado == 'enviada':
                    procesadas += 1
            else:
                self.stdout.write(f'    [DRY-RUN] Procesando notificación {notificacion.id}')
                procesadas += 1
        
        return procesadas