from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.conf import settings

from .models import Mantenimiento, Notificacion, Supervisor, Equipo


@shared_task
def verificar_mantenimientos_pendientes():
    """
    Tarea que se ejecuta diariamente para verificar mantenimientos que necesitan recordatorios
    """
    hoy = timezone.now().date()
    
    # Buscar mantenimientos que necesitan recordatorio (5 días antes)
    fecha_recordatorio = hoy + timedelta(days=5)
    mantenimientos_recordatorio = Mantenimiento.objects.filter(
        estado='pendiente',
        fecha_programada=fecha_recordatorio
    )
    
    for mantenimiento in mantenimientos_recordatorio:
        crear_notificacion_recordatorio.delay(mantenimiento.id)
    
    # Buscar mantenimientos vencidos que necesitan reporte al supervisor
    mantenimientos_vencidos = Mantenimiento.objects.filter(
        estado='vencido',
        fecha_programada=hoy - timedelta(days=1)  # Vencidos ayer
    )
    
    for mantenimiento in mantenimientos_vencidos:
        enviar_reporte_supervisor.delay(mantenimiento.id)
    
    # Verificar por kilometraje (equipos que están cerca del límite)
    verificar_mantenimientos_por_kilometraje.delay()
    
    return f"Verificados {mantenimientos_recordatorio.count()} recordatorios y {mantenimientos_vencidos.count()} vencidos"


@shared_task
def verificar_mantenimientos_por_kilometraje():
    """
    Verificar equipos que están cerca del límite de kilometraje
    """
    equipos = Equipo.objects.filter(activo=True)
    notificaciones_creadas = 0
    
    for equipo in equipos:
        proximo = equipo.proximo_mantenimiento()
        
        # Si está a 100 km o menos del próximo mantenimiento
        if proximo['km_restantes'] <= 100 and proximo['km_restantes'] > 0:
            # Verificar si ya existe una notificación reciente
            notificacion_existente = Notificacion.objects.filter(
                mantenimiento__equipo=equipo,
                tipo='recordatorio',
                fecha_creacion__gte=timezone.now() - timedelta(days=1)
            ).exists()
            
            if not notificacion_existente:
                # Buscar o crear mantenimiento pendiente
                mantenimiento, created = Mantenimiento.objects.get_or_create(
                    equipo=equipo,
                    estado='pendiente',
                    defaults={
                        'fecha_programada': proximo['fecha'],
                        'kilometraje_programado': proximo['kilometraje'],
                        'operador': equipo.mantenimientos.first().operador if equipo.mantenimientos.exists() else None,
                        'tipo_mantenimiento_id': 1  # Asumiendo que existe un tipo por defecto
                    }
                )
                
                if mantenimiento.operador:
                    crear_notificacion_recordatorio.delay(mantenimiento.id, por_kilometraje=True)
                    notificaciones_creadas += 1
    
    return f"Creadas {notificaciones_creadas} notificaciones por kilometraje"


@shared_task
def crear_notificacion_recordatorio(mantenimiento_id, por_kilometraje=False):
    """
    Crear notificación de recordatorio para un mantenimiento
    """
    try:
        mantenimiento = Mantenimiento.objects.get(id=mantenimiento_id)
        
        if por_kilometraje:
            asunto = f"Recordatorio de Mantenimiento por Kilometraje - {mantenimiento.equipo.placa}"
            mensaje = render_to_string('mantenimiento/emails/recordatorio_kilometraje.txt', {
                'mantenimiento': mantenimiento,
                'equipo': mantenimiento.equipo,
                'operador': mantenimiento.operador,
            })
        else:
            asunto = f"Recordatorio de Mantenimiento - {mantenimiento.equipo.placa}"
            mensaje = render_to_string('mantenimiento/emails/recordatorio_fecha.txt', {
                'mantenimiento': mantenimiento,
                'equipo': mantenimiento.equipo,
                'operador': mantenimiento.operador,
            })
        
        notificacion = Notificacion.objects.create(
            mantenimiento=mantenimiento,
            tipo='recordatorio',
            destinatario_email=mantenimiento.operador.email,
            asunto=asunto,
            mensaje=mensaje,
            fecha_programada=timezone.now()
        )
        
        # Enviar inmediatamente
        enviar_notificacion.delay(notificacion.id)
        
        return f"Notificación de recordatorio creada para {mantenimiento.equipo.placa}"
        
    except Mantenimiento.DoesNotExist:
        return f"Mantenimiento con ID {mantenimiento_id} no encontrado"


@shared_task
def enviar_reporte_supervisor(mantenimiento_id):
    """
    Enviar reporte al supervisor sobre mantenimiento vencido
    """
    try:
        mantenimiento = Mantenimiento.objects.get(id=mantenimiento_id)
        supervisores = Supervisor.objects.filter(activo=True)
        
        if not supervisores.exists():
            return "No hay supervisores activos configurados"
        
        asunto = f"ALERTA: Mantenimiento Vencido - {mantenimiento.equipo.placa}"
        mensaje = render_to_string('mantenimiento/emails/reporte_supervisor.txt', {
            'mantenimiento': mantenimiento,
            'equipo': mantenimiento.equipo,
            'operador': mantenimiento.operador,
            'dias_vencido': mantenimiento.dias_vencido(),
        })
        
        notificaciones_creadas = 0
        for supervisor in supervisores:
            notificacion = Notificacion.objects.create(
                mantenimiento=mantenimiento,
                tipo='reporte_supervisor',
                destinatario_email=supervisor.email,
                asunto=asunto,
                mensaje=mensaje,
                fecha_programada=timezone.now()
            )
            
            enviar_notificacion.delay(notificacion.id)
            notificaciones_creadas += 1
        
        # Marcar mantenimiento como vencido
        mantenimiento.estado = 'vencido'
        mantenimiento.save()
        
        return f"Enviado reporte a {notificaciones_creadas} supervisores"
        
    except Mantenimiento.DoesNotExist:
        return f"Mantenimiento con ID {mantenimiento_id} no encontrado"


@shared_task
def enviar_notificacion(notificacion_id):
    """
    Enviar una notificación específica
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id)
        notificacion.enviar()
        
        if notificacion.estado == 'enviada':
            return f"Notificación {notificacion_id} enviada exitosamente"
        else:
            return f"Error al enviar notificación {notificacion_id}: {notificacion.error_mensaje}"
            
    except Notificacion.DoesNotExist:
        return f"Notificación con ID {notificacion_id} no encontrada"


@shared_task
def crear_notificaciones_mantenimiento(mantenimiento_id):
    """
    Crear todas las notificaciones para un nuevo mantenimiento
    """
    try:
        mantenimiento = Mantenimiento.objects.get(id=mantenimiento_id)
        
        # Notificación 5 días antes por fecha
        fecha_recordatorio = mantenimiento.fecha_programada - timedelta(days=5)
        if fecha_recordatorio >= timezone.now().date():
            Notificacion.objects.create(
                mantenimiento=mantenimiento,
                tipo='recordatorio',
                destinatario_email=mantenimiento.operador.email,
                asunto=f"Recordatorio: Mantenimiento programado - {mantenimiento.equipo.placa}",
                mensaje=f"Su equipo {mantenimiento.equipo.placa} tiene mantenimiento programado para el {mantenimiento.fecha_programada}",
                fecha_programada=datetime.combine(fecha_recordatorio, datetime.min.time())
            )
        
        return f"Notificaciones programadas para mantenimiento {mantenimiento_id}"
        
    except Mantenimiento.DoesNotExist:
        return f"Mantenimiento con ID {mantenimiento_id} no encontrado"


@shared_task
def procesar_notificaciones_pendientes():
    """
    Procesar todas las notificaciones pendientes que deben enviarse
    """
    ahora = timezone.now()
    notificaciones_pendientes = Notificacion.objects.filter(
        estado='pendiente',
        fecha_programada__lte=ahora
    )
    
    enviadas = 0
    for notificacion in notificaciones_pendientes:
        enviar_notificacion.delay(notificacion.id)
        enviadas += 1
    
    return f"Procesadas {enviadas} notificaciones pendientes"


@shared_task
def generar_reporte_semanal():
    """
    Generar reporte semanal de mantenimientos para supervisores
    """
    fecha_inicio = timezone.now().date() - timedelta(days=7)
    fecha_fin = timezone.now().date()
    
    # Estadísticas de la semana
    mantenimientos_completados = Mantenimiento.objects.filter(
        fecha_completado__date__range=[fecha_inicio, fecha_fin],
        completado=True
    ).count()
    
    mantenimientos_vencidos = Mantenimiento.objects.filter(
        estado='vencido',
        fecha_programada__range=[fecha_inicio, fecha_fin]
    ).count()
    
    equipos_pendientes = Equipo.objects.filter(activo=True).count()
    
    supervisores = Supervisor.objects.filter(activo=True)
    
    for supervisor in supervisores:
        asunto = "Reporte Semanal de Mantenimientos"
        mensaje = f"""
        Reporte semanal del {fecha_inicio} al {fecha_fin}:
        
        - Mantenimientos completados: {mantenimientos_completados}
        - Mantenimientos vencidos: {mantenimientos_vencidos}
        - Equipos activos: {equipos_pendientes}
        
        Revise el sistema para más detalles.
        """
        
        # Crear notificación del reporte
        notificacion = Notificacion.objects.create(
            mantenimiento=None,  # Reporte general, no asociado a mantenimiento específico
            tipo='reporte_supervisor',
            destinatario_email=supervisor.email,
            asunto=asunto,
            mensaje=mensaje,
            fecha_programada=timezone.now()
        )
        
        enviar_notificacion.delay(notificacion.id)
    
    return f"Reporte semanal enviado a {supervisores.count()} supervisores"