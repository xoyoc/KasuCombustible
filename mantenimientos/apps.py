from django.apps import AppConfig


class MantenimientoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mantenimientos'
    verbose_name = 'Sistema de Mantenimiento'
    
    def ready(self):
        """
        Configuración que se ejecuta cuando la app está lista.
        Aquí importamos las señales para que se registren.
        """
        import mantenimientos.signals