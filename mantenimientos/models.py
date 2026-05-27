from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta

# Create your models here.
from equipo.models import Equipo
from operador.models import Operador, Supervisor

class TipoMantenimiento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Tipo de mantenimiento")
    descripcion = models.TextField(verbose_name="Descripción", blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Tipos de mantenimiento"

class Mantenimiento(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('vencido', 'Vencido'),
    ]
    
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='mantenimientos')
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE)
    tipo_mantenimiento = models.ForeignKey(TipoMantenimiento, on_delete=models.CASCADE)
    
    fecha_programada = models.DateField(verbose_name="Fecha programada")
    fecha_completado = models.DateTimeField(null=True, blank=True, verbose_name="Fecha completado")
    kilometraje_programado = models.IntegerField(verbose_name="Kilometraje programado")
    kilometraje_en_mantenimiento = models.IntegerField(null=True, blank=True, verbose_name="Kilometraje al momento del mantenimiento")
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    completado = models.BooleanField(default=False)
    
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Costo")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.completado and not self.fecha_completado:
            self.fecha_completado = timezone.now()
            self.estado = 'completado'
            if not self.kilometraje_en_mantenimiento:
                self.kilometraje_en_mantenimiento = self.equipo.kilometraje_actual
        elif not self.completado and self.fecha_completado:
            self.fecha_completado = None
            if timezone.now().date() > self.fecha_programada:
                self.estado = 'vencido'
            else:
                self.estado = 'pendiente'
        super().save(*args, **kwargs)
    
    def dias_vencido(self):
        if self.estado == 'vencido':
            return (timezone.now().date() - self.fecha_programada).days
        return 0
    
    def __str__(self):
        return f"Mantenimiento {self.equipo.placa} - {self.fecha_programada}"
    
    class Meta:
        ordering = ['-fecha_programada']

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('recordatorio', 'Recordatorio'),
        ('vencimiento', 'Vencimiento'),
        ('reporte_supervisor', 'Reporte a Supervisor'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('fallida', 'Fallida'),
    ]
    
    mantenimiento = models.ForeignKey(Mantenimiento, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    destinatario_email = models.EmailField()
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    
    fecha_programada = models.DateTimeField()
    fecha_enviada = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    error_mensaje = models.TextField(blank=True, verbose_name="Mensaje de error")
    
    def enviar(self):
        try:
            send_mail(
                subject=self.asunto,
                message=self.mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.destinatario_email],
                fail_silently=False,
            )
            self.estado = 'enviada'
            self.fecha_enviada = timezone.now()
            self.error_mensaje = ''
        except Exception as e:
            self.estado = 'fallida'
            self.error_mensaje = str(e)
        self.save()
    
    def __str__(self):
        return f"{self.tipo} - {self.mantenimiento.equipo.placa} - {self.estado}"
    
    class Meta:
        ordering = ['-fecha_creacion']

class ReporteMantenimiento(models.Model):
    titulo = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo_reporte = models.CharField(max_length=50)
    
    mantenimientos_incluidos = models.ManyToManyField(Mantenimiento, blank=True)
    notificaciones_incluidas = models.ManyToManyField(Notificacion, blank=True)
    
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generado_por = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha_generacion.strftime('%Y-%m-%d')}"
    
    class Meta:
        ordering = ['-fecha_generacion']