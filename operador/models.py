from django.db import models

# Create your models here.
class Operador(models.Model):
    nombre = models.TextField(max_length=150, verbose_name="Nombre completo del operador")
    email = models.EmailField(verbose_name="Correo del operador")
    movil = models.TextField(max_length=10, verbose_name="Celular del operador")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self) -> str:
        return f"Nombre:{self.nombre} Email:{self.email} Celular:{self.movil}"

class Supervisor(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre completo del supervisor")
    email = models.EmailField(verbose_name="Correo del supervisor")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono del supervisor")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    def __str__(self):
        return self.nombre