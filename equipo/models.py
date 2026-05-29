from datetime import timedelta
from django.utils import timezone
from django.db import models


class Equipo(models.Model):
    TIPO_COMBUSTIBLE = [
        ('diesel', 'Diesel'),
        ('gasolina', 'Gasolina'),
    ]

    numero_economico = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="No. Económico",
        help_text="Número de unidad en la flota (ej. 01, 02...)",
    )
    placa = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="Placa",
    )
    niv = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="NIV / VIN",
        help_text="Número de Identificación Vehicular",
    )
    marca = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Marca",
    )
    modelo = models.CharField(
        max_length=100,
        verbose_name="Modelo",
    )
    year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Año",
    )
    tipo_combustible = models.CharField(
        max_length=10,
        choices=TIPO_COMBUSTIBLE,
        default='diesel',
        verbose_name="Tipo de combustible",
    )
    capacidad_tanque = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Capacidad del tanque (L)",
    )
    rendimiento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Rendimiento (km/L)",
    )
    asignacion = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Asignación",
        help_text="Operador o área a quien está asignada la unidad",
    )
    kilometraje_actual = models.IntegerField(
        default=0,
        blank=True,
        verbose_name="Kilometraje actual",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        ordering = ['numero_economico']
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"

    def __str__(self) -> str:
        partes = [f"#{self.numero_economico}", self.marca, self.modelo]
        if self.placa:
            partes.append(f"({self.placa})")
        return " ".join(filter(None, partes))

    def proximo_mantenimiento(self):
        ultimo = self.mantenimientos.filter(completado=True).order_by('-fecha_completado').first()
        if ultimo:
            fecha_base = ultimo.fecha_completado
            km_base = ultimo.kilometraje_en_mantenimiento
        else:
            fecha_base = timezone.now().date()
            km_base = self.kilometraje_actual

        proxima_fecha = fecha_base + timedelta(days=90)
        proximo_km = km_base + 10000

        return {
            'fecha': proxima_fecha,
            'kilometraje': proximo_km,
            'dias_restantes': (proxima_fecha - timezone.now().date()).days,
            'km_restantes': proximo_km - self.kilometraje_actual,
        }

    def necesita_mantenimiento(self):
        proximo = self.proximo_mantenimiento()
        return proximo['dias_restantes'] <= 0 or proximo['km_restantes'] <= 0

    def mantenimiento_proximo(self, dias_aviso=5, km_aviso=100):
        proximo = self.proximo_mantenimiento()
        return proximo['dias_restantes'] <= dias_aviso or proximo['km_restantes'] <= km_aviso
