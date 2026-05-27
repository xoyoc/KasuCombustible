# signals.py - Para tu modelo Registro y Equipo
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Registro, Equipo

@receiver(post_save, sender=Registro)
def actualizar_kilometraje_equipo(sender, instance, created, **kwargs):
    """
    Actualiza el kilometraje_actual del equipo cuando se crea un nuevo registro
    """
    if created and instance.kilometraje:  # Solo cuando se crea un nuevo registro
        equipo = instance.idEquipo  # Tu FK al modelo Equipo
        
        # Actualizar el kilometraje_actual del equipo
        if instance.kilometraje > 0:
            equipo.kilometraje_actual = instance.kilometraje
            equipo.save(update_fields=['kilometraje_actual'])

# Versión más avanzada con validaciones y logging
@receiver(post_save, sender=Registro)
def actualizar_kilometraje_equipo_avanzado(sender, instance, created, **kwargs):
    """
    Actualiza el kilometraje del equipo con validaciones adicionales
    """
    if created and instance.kilometraje:
        equipo = instance.idEquipo
        
        # Obtener el último registro para este equipo para asegurar consistencia
        ultimo_registro = Registro.objects.filter(
            idEquipo=equipo
        ).exclude(id=instance.id).order_by('-id').first()
        
        # Si este es el registro más reciente, actualizar el kilometraje
        if not ultimo_registro or instance.kilometraje >= ultimo_registro.kilometraje:
            if instance.kilometraje > equipo.kilometraje_actual:
                equipo.kilometraje_actual = instance.kilometraje
                equipo.save(update_fields=['kilometraje_actual'])
                
                # Opcional: Logging para auditoria
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Kilometraje actualizado para equipo {equipo.placa}: "
                    f"{equipo.kilometraje_actual} km"
                )