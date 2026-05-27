# Configuraciones adicionales para Django settings.py
# Agregar estas configuraciones a tu archivo settings.py principal

# ===== APLICACIONES =====
# Agregar a INSTALLED_APPS:
INSTALLED_APPS = [
    # ... tus apps existentes ...
    'mantenimiento.apps.MantenimientoConfig',
    'django_celery_beat',  # Para tareas programadas
    'django_extensions',   # Útil para comandos adicionales (opcional)
]

# ===== CONFIGURACIÓN DE EMAIL =====
# Configuración para Gmail (ajustar según tu proveedor)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'  # Cambiar por tu email
EMAIL_HOST_PASSWORD = 'tu_app_password'  # Usar app password, no password normal
DEFAULT_FROM_EMAIL = 'Sistema de Mantenimiento <tu_email@gmail.com>'

# Configuración alternativa para desarrollo (console backend)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===== CONFIGURACIÓN DE CELERY =====
# Broker y backend para Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Configuración de Celery
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Bogota'  # Ajustar según tu zona horaria

# ===== CONFIGURACIÓN DE LOGGING =====
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'mantenimiento.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'mantenimiento': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ===== CONFIGURACIÓN DE ARCHIVOS MEDIA =====
# Para manejo de archivos adjuntos (si se necesitan en el futuro)
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ===== CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS =====
# Asegurar que Tailwind CSS funcione correctamente
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ===== CONFIGURACIÓN DE ZONA HORARIA =====
TIME_ZONE = 'America/Bogota'  # Ajustar según tu ubicación
USE_TZ = True

# ===== CONFIGURACIÓN DE INTERNACIONALIZACIÓN =====
LANGUAGE_CODE = 'es-es'
USE_I18N = True
USE_L10N = True

# ===== CONFIGURACIÓN DE CACHE =====
# Opcional: configurar cache para mejorar rendimiento
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache para sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ===== CONFIGURACIÓN DE SEGURIDAD =====
# Configuraciones de seguridad para producción
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ===== CONFIGURACIÓN ESPECÍFICA DE MANTENIMIENTO =====
# Configuraciones personalizadas para la app de mantenimiento

# Intervalos de mantenimiento por defecto
MANTENIMIENTO_INTERVALO_DIAS = 90  # 3 meses
MANTENIMIENTO_INTERVALO_KM = 10000  # 10,000 km

# Configuración de notificaciones
MANTENIMIENTO_DIAS_AVISO = 5  # Días antes para enviar recordatorio
MANTENIMIENTO_KM_AVISO = 100  # Kilómetros antes para enviar recordatorio

# Configuración de reportes
MANTENIMIENTO_EMAIL_SUPERVISORES = [
    'supervisor1@empresa.com',
    'supervisor2@empresa.com',
]

# Configuración de backup automático (opcional)
MANTENIMIENTO_BACKUP_ENABLED = True
MANTENIMIENTO_BACKUP_DAYS = 30  # Días para mantener backups

# ===== URLS PRINCIPALES =====
# Agregar a urlpatterns en tu urls.py principal:
"""
from django.urls import path, include

urlpatterns = [
    # ... tus URLs existentes ...
    path('mantenimiento/', include('mantenimiento.urls')),
    path('admin/', admin.site.urls),
]
"""

# ===== COMANDOS ÚTILES =====
"""
# Comandos para ejecutar después de la instalación:

# 1. Crear migraciones
python manage.py makemigrations mantenimiento

# 2. Aplicar migraciones
python manage.py migrate

# 3. Crear superusuario
python manage.py createsuperuser

# 4. Cargar datos iniciales (opcional)
python manage.py loaddata mantenimiento/fixtures/initial_data.json

# 5. Ejecutar servidor de desarrollo
python manage.py runserver

# 6. Ejecutar Celery worker (en otra terminal)
celery -A tu_proyecto worker --loglevel=info

# 7. Ejecutar Celery beat (en otra terminal)
celery -A tu_proyecto beat --loglevel=info

# 8. Verificar mantenimientos manualmente
python manage.py verificar_mantenimientos --dry-run

# 9. Ejecutar verificación real
python manage.py verificar_mantenimientos
"""

# ===== DEPENDENCIAS REQUERIDAS =====
"""
# Agregar a requirements.txt:
celery>=5.3.0
redis>=4.6.0
django-celery-beat>=2.5.0
django-extensions>=3.2.0  # Opcional
Pillow>=10.0.0  # Si necesitas manejo de imágenes
reportlab>=4.0.0  # Para generar PDFs (opcional)
"""