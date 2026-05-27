from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Mantenimiento, Equipo, Notificacion


@receiver(post_save, sender=Mantenimiento)
def mantenimiento_post_save(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar un mantenimiento.
    - Si es nuevo, programa las notificaciones automáticas
    - Si se completa, crea el próximo mantenimiento automáticamente
    """
    if created:
        # Programar notificaciones para nuevo mantenimiento
        programar_notificaciones_mantenimiento(instance)
    
    elif instance.completado and not kwargs.get('raw', False):
        # Si el mantenimiento se completó, crear el próximo automáticamente
        crear_proximo_mantenimiento_automatico(instance)


@receiver(pre_save, sender=Mantenimiento)
def mantenimiento_pre_save(sender, instance, **kwargs):
    """
    Señal que se ejecuta antes de guardar un mantenimiento.
    Actualiza el estado automáticamente basado en las fechas.
    """
    if not instance.completado:
        hoy = timezone.now().date()
        
        if instance.fecha_programada < hoy:
            instance.estado = 'vencido'
        elif instance.estado == 'vencido' and instance.fecha_programada >= hoy:
            instance.estado = 'pendiente'


@receiver(post_save, sender=Equipo)
def equipo_post_save(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar un equipo.
    Si es nuevo, crea el primer mantenimiento automáticamente.
    """
    if created and instance.activo:
        crear_primer_mantenimiento(instance)


def programar_notificaciones_mantenimiento(mantenimiento):
    """
    Programa todas las notificaciones necesarias para un mantenimiento.
    """
    try:
        # Importar aquí para evitar circular imports
        from .tasks import crear_notificaciones_mantenimiento
        
        # Usar Celery si está disponible, sino crear directamente
        if hasattr(crear_notificaciones_mantenimiento, 'delay'):
            crear_notificaciones_mantenimiento.delay(mantenimiento.id)
        else:
            crear_notificaciones_mantenimiento(mantenimiento.id)
            
    except ImportError:
        # Si Celery no está disponible, crear notificaciones directamente
        crear_notificaciones_directas(mantenimiento)


def crear_notificaciones_directas(mantenimiento):
    """
    Crear notificaciones directamente sin usar Celery.
    """
    # Notificación 5 días antes
    fecha_recordatorio = mantenimiento.fecha_programada - timedelta(days=5)
    
    if fecha_recordatorio >= timezone.now().date():
        Notificacion.objects.create(
            mantenimiento=mantenimiento,
            tipo='recordatorio',
            destinatario_email=mantenimiento.operador.email,
            asunto=f"Recordatorio: Mantenimiento programado - {mantenimiento.equipo.placa}",
            mensaje=f"""
Estimado {mantenimiento.operador.nombre},

Le recordamos que el equipo {mantenimiento.equipo.placa} tiene mantenimiento programado.

Detalles:
- Equipo: {mantenimiento.equipo.placa} ({mantenimiento.equipo.marca} {mantenimiento.equipo.modelo})
- Fecha programada: {mantenimiento.fecha_programada.strftime('%d/%m/%Y')}
- Kilometraje programado: {mantenimiento.kilometraje_programado:,} km
- Tipo: {mantenimiento.tipo_mantenimiento.nombre}

Por favor, programe el mantenimiento lo antes posible.

Saludos,
Sistema de Mantenimiento
            """.strip(),
            fecha_programada=timezone.make_aware(
                timezone.datetime.combine(fecha_recordatorio, timezone.datetime.min.time())
            )
        )


def crear_proximo_mantenimiento_automatico(mantenimiento_completado):
    """
    Crear automáticamente el próximo mantenimiento cuando uno se completa.
    """
    equipo = mantenimiento_completado.equipo
    proximo = equipo.proximo_mantenimiento()
    
    # Verificar que no existe ya un mantenimiento programado próximo
    mantenimiento_existente = Mantenimiento.objects.filter(
        equipo=equipo,
        estado='pendiente',
        fecha_programada__gte=timezone.now().date()
    ).exists()
    
    if not mantenimiento_existente:
        nuevo_mantenimiento = Mantenimiento.objects.create(
            equipo=equipo,
            operador=mantenimiento_completado.operador,
            tipo_mantenimiento=mantenimiento_completado.tipo_mantenimiento,
            fecha_programada=proximo['fecha'],
            kilometraje_programado=proximo['kilometraje'],
            estado='pendiente'
        )
        
        # Las notificaciones se crearán automáticamente por la señal post_save
        return nuevo_mantenimiento


def crear_primer_mantenimiento(equipo):
    """
    Crear el primer mantenimiento para un equipo nuevo.
    """
    from .models import TipoMantenimiento, Operador
    
    # Intentar obtener un tipo de mantenimiento por defecto
    tipo_mantenimiento = TipoMantenimiento.objects.first()
    if not tipo_mantenimiento:
        # Crear tipo de mantenimiento por defecto si no existe
        tipo_mantenimiento = TipoMantenimiento.objects.create(
            nombre="Mantenimiento Preventivo",
            descripcion="Mantenimiento preventivo estándar"
        )
    
    # Intentar obtener un operador por defecto
    operador = Operador.objects.filter(activo=True).first()
    if not operador:
        # No crear mantenimiento si no hay operadores
        return
    
    proximo = equipo.proximo_mantenimiento()
    
    Mantenimiento.objects.create(
        equipo=equipo,
        operador=operador,
        tipo_mantenimiento=tipo_mantenimiento,
        fecha_programada=proximo['fecha'],
        kilometraje_programado=proximo['kilometraje'],
        estado='pendiente'
    )


# Señales para auditoría (opcional)
@receiver(post_save, sender=Mantenimiento)
def auditoria_mantenimiento(sender, instance, created, **kwargs):
    """
    Registrar cambios en mantenimientos para auditoría.
    """
    # Aquí podrías registrar en un log o tabla de auditoría
    import logging
    
    logger = logging.getLogger('mantenimiento')
    
    if created:
        logger.info(f"Nuevo mantenimiento creado: {instance.id} para equipo {instance.equipo.placa}")
    elif instance.completado:
        logger.info(f"Mantenimiento completado: {instance.id} para equipo {instance.equipo.placa}")


@receiver(post_save, sender=Equipo)
def auditoria_equipo(sender, instance, created, **kwargs):
    """
    Registrar cambios en equipos para auditoría.
    """
    import logging
    
    logger = logging.getLogger('mantenimiento')
    
    if created:
        logger.info(f"Nuevo equipo registrado: {instance.placa}")
    
    # Detectar cambio de kilometraje
    if not created and hasattr(instance, '_old_kilometraje'):
        if instance._old_kilometraje != instance.kilometraje_actual:
            logger.info(f"Kilometraje actualizado para {instance.placa}: {instance._old_kilometraje} -> {instance.kilometraje_actual}")


@receiver(pre_save, sender=Equipo)
def guardar_kilometraje_anterior(sender, instance, **kwargs):
    """
    Guardar el kilometraje anterior para detectar cambios.
    """
    if instance.pk:
        try:
            old_instance = Equipo.objects.get(pk=instance.pk)
            instance._old_kilometraje = old_instance.kilometraje_actual
        except Equipo.DoesNotExist:
            instance._old_kilometraje = None