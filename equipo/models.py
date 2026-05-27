from datetime import timedelta
from django.utils import timezone
from django.db import models

# Create your models here.
class Equipo(models.Model):
    placa = models.TextField(max_length=50, verbose_name="Placa")
    modelo = models.TextField(max_length=100, verbose_name="Modelo")
    marca = models.TextField(max_length=100, verbose_name="Marca")
    year = models.IntegerField(default=2023, verbose_name="Año")
    capacidad_tanque = models.IntegerField(default=10, verbose_name="Capacidad del taque")
    kilometraje_actual = models.IntegerField(default=0, verbose_name="Kilometraje actual", blank=True)
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self) -> str:
        return f"Placa:{self.placa} Modelo:{self.modelo} Marca:{self.marca} Año:{self.year} Tanque:{self.capacidad_tanque}"
    
    def proximo_mantenimiento(self):
        ultimo_mantenimiento = self.mantenimientos.filter(completado=True).order_by('-fecha_completado').first()
        if ultimo_mantenimiento:
            fecha_base = ultimo_mantenimiento.fecha_completado
            km_base = ultimo_mantenimiento.kilometraje_en_mantenimiento
        else:
            fecha_base = timezone.now().date()
            km_base = self.kilometraje_actual
        
        # Calcular próximas fechas
        proxima_fecha = fecha_base + timedelta(days=90)  # 3 meses
        proximo_km = km_base + 10000
        
        return {
            'fecha': proxima_fecha,
            'kilometraje': proximo_km,
            'dias_restantes': (proxima_fecha - timezone.now().date()).days,
            'km_restantes': proximo_km - self.kilometraje_actual
        }
    
    def necesita_mantenimiento(self):
        proximo = self.proximo_mantenimiento()
        return proximo['dias_restantes'] <= 0 or proximo['km_restantes'] <= 0
    
    def mantenimiento_proximo(self, dias_aviso=5, km_aviso=100):
        proximo = self.proximo_mantenimiento()
        return proximo['dias_restantes'] <= dias_aviso or proximo['km_restantes'] <= km_aviso