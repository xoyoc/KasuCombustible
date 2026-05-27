# 📊 Guía Completa: Proceso de Envío de Reportes y Configuración en DigitalOcean

## 🔍 Análisis del Proceso de Envío de Reportes

### 📋 Flujo del Proceso

```mermaid
graph TD
    A[Celery Beat Scheduler] --> B{¿Es día 1 del mes?}
    B -->|Sí| C[enviar_reporte_mensual_automatico]
    B -->|No| D[Saltar ejecución]
    
    C --> E[Generar datos del reporte]
    E --> F[Crear archivo Excel]
    F --> G[Subir a DigitalOcean Spaces]
    G --> H[Enviar por Email]
    G --> I[Enviar por WhatsApp]
    H --> J[Marcar como enviado]
    I --> J
    J --> K[Log de resultado]
```

### 🛠️ Componentes del Sistema

#### 1. **Comando Django** (`enviar_reporte_mensual.py`)
- **Ubicación**: `registros/management/commands/enviar_reporte_mensual.py`
- **Funcionalidad**: Genera reportes mensuales con estadísticas completas
- **Parámetros**:
  - `--mes`: Mes específico (1-12)
  - `--año`: Año específico
  - `--test`: Modo prueba sin envío
  - `--whatsapp-only`: Solo WhatsApp
  - `--email`: Email específico

#### 2. **Tareas de Celery** (`registros/tasks.py`)
- **`enviar_reporte_mensual_automatico`**: Tarea principal programada
- **`verificar_operadores_inactivos`**: Detección de operadores inactivos
- **`limpiar_archivos_temporales`**: Limpieza de archivos antiguos
- **`backup_database_daily`**: Backup diario de BD

#### 3. **Configuración de Celery** (`combustible/celery.py`)
- **Beat Schedule**: Tareas programadas
- **Colas**: Organización por tipo de tarea
- **Reintentos**: Configuración de fallos

## 🚀 Configuración Paso a Paso en DigitalOcean App Platform

### Paso 1: Preparar el Proyecto

#### 1.1 Actualizar `requirements.txt`
```txt
# Agregar estas dependencias si no están
celery==5.5.3
django-celery-beat==2.8.1
redis==5.0.1
```

#### 1.2 Actualizar `settings.py`
```python
# combustible/settings.py

# Agregar a INSTALLED_APPS
INSTALLED_APPS = [
    # ... apps existentes ...
    'django_celery_beat',
]

# Configuración de Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Mexico_City'

# Configuración de colas
CELERY_TASK_ROUTES = {
    'registros.tasks.enviar_reporte_mensual_automatico': {'queue': 'reports'},
    'registros.tasks.verificar_operadores_inactivos': {'queue': 'alerts'},
    'mantenimientos.tasks.*': {'queue': 'maintenance'},
}
```

#### 1.3 Crear archivo `__init__.py` en combustible
```python
# combustible/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Paso 2: Configurar DigitalOcean App Platform

#### 2.1 Crear la App
1. **Ir a DigitalOcean Control Panel**
2. **Apps → Create App**
3. **Conectar repositorio Git**
4. **Seleccionar rama**: `main`

#### 2.2 Configurar Servicios

##### **Servicio Web (Django)**
```yaml
# .do/app.yaml
name: combustible-web
source_dir: /
github:
  repo: tu-usuario/LogincoCobustible
  branch: main
  deploy_on_push: true

services:
- name: web
  source_dir: /
  github:
    repo: tu-usuario/LogincoCobustible
    branch: main
  run_command: gunicorn --bind 0.0.0.0:$PORT combustible.wsgi:application
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  routes:
  - path: /
  envs:
  - key: DJANGO_SETTINGS_MODULE
    value: combustible.settings
  - key: PORT
    value: "8080"
```

##### **Servicio Worker (Celery)**
```yaml
services:
- name: worker
  source_dir: /
  github:
    repo: tu-usuario/LogincoCobustible
    branch: main
  run_command: celery -A combustible worker --loglevel=info --concurrency=2
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DJANGO_SETTINGS_MODULE
    value: combustible.settings
```

##### **Servicio Scheduler (Celery Beat)**
```yaml
services:
- name: scheduler
  source_dir: /
  github:
    repo: tu-usuario/LogincoCobustible
    branch: main
  run_command: celery -A combustible beat --loglevel=info
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DJANGO_SETTINGS_MODULE
    value: combustible.settings
```

### Paso 3: Configurar Base de Datos y Redis

#### 3.1 Base de Datos PostgreSQL
1. **Crear Database Cluster**
2. **Configurar conexión**:
```env
DJANGO_DB_URL=postgresql://usuario:password@host:port/database
```

#### 3.2 Redis para Celery
1. **Crear Redis Cluster**
2. **Configurar variables**:
```env
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0
```

### Paso 4: Variables de Entorno

#### 4.1 Variables Requeridas
```env
# Django
SECRET_KEY=tu-secret-key-super-seguro
DEBUG=False
ALLOWED_HOSTS=squid-app-5j4xm.ondigitalocean.app,tu-dominio.com

# Base de Datos
DJANGO_DB_URL=postgresql://usuario:password@host:port/database

# Redis/Celery
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0

# DigitalOcean Spaces
DO_SPACES_ACCESS_KEY=tu-access-key
DO_SPACES_SECRET_KEY=tu-secret-key
DO_SPACES_BUCKET_NAME=tu-bucket-name
DO_SPACES_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
DO_SPACES_REGION=nyc3
USE_SPACES=True

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=tu-phone-number-id
WHATSAPP_ACCESS_TOKEN=tu-access-token
WHATSAPP_VERIFY_TOKEN=tu-verify-token

# SendGrid Email
EMAIL_HOST_PASSWORD=tu-sendgrid-api-key
```

### Paso 5: Configurar Dominio y SSL

#### 5.1 Dominio Personalizado
1. **Agregar dominio** en App Platform
2. **Configurar DNS**:
```
CNAME www tu-app.ondigitalocean.app
CNAME @ tu-app.ondigitalocean.app
```

#### 5.2 SSL Automático
- **Se configura automáticamente** con Let's Encrypt

### Paso 6: Monitoreo y Logs

#### 6.1 Configurar Logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'registros.tasks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

#### 6.2 Monitoreo en DigitalOcean
- **Logs**: Disponibles en App Platform → Logs
- **Métricas**: CPU, memoria, requests
- **Alertas**: Configurar notificaciones

## 🔧 Comandos de Gestión y Testing

### Comandos Locales para Testing

#### 1. **Probar Reporte Manualmente**
```bash
# Modo test (sin envío)
python manage.py enviar_reporte_mensual --test

# Enviar a número específico
python manage.py enviar_reporte_mensual --whatsapp "+525512345678" --test

# Generar reporte de mes específico
python manage.py enviar_reporte_mensual --mes 12 --año 2024 --test
```

#### 2. **Probar Celery Localmente**
```bash
# Iniciar Redis
redis-server

# Iniciar Worker
celery -A combustible worker --loglevel=info

# Iniciar Beat Scheduler
celery -A combustible beat --loglevel=info

# Probar tarea manualmente
python manage.py shell
>>> from registros.tasks import enviar_reporte_mensual_automatico
>>> enviar_reporte_mensual_automatico.delay()
```

#### 3. **Verificar Configuración**
```bash
# Verificar configuración de Celery
celery -A combustible inspect active

# Ver tareas programadas
celery -A combustible beat --loglevel=info --dry-run

# Verificar conexión a Redis
redis-cli ping
```

### Comandos en Producción

#### 1. **Ejecutar Migraciones**
```bash
python manage.py migrate
```

#### 2. **Recopilar Archivos Estáticos**
```bash
python manage.py collectstatic --noinput
```

#### 3. **Crear Superusuario**
```bash
python manage.py createsuperuser
```

## 📊 Monitoreo del Sistema

### Métricas Importantes

#### 1. **Reportes Mensuales**
- ✅ **Éxito**: Reporte enviado correctamente
- ❌ **Error**: Fallo en generación o envío
- 📊 **Estadísticas**: Número de destinatarios, tamaño de archivo

#### 2. **Operadores Inactivos**
- 👥 **Detectados**: Operadores sin actividad
- 📱 **Alertas**: Notificaciones enviadas a supervisores

#### 3. **Mantenimientos**
- 🔧 **Pendientes**: Mantenimientos programados
- ⚠️ **Vencidos**: Mantenimientos atrasados
- 📧 **Notificaciones**: Emails enviados

### Logs a Monitorear

#### 1. **Logs de Celery**
```bash
# En DigitalOcean App Platform
tail -f /var/log/celery/worker.log
tail -f /var/log/celery/beat.log
```

#### 2. **Logs de Django**
```bash
# Logs de aplicación
tail -f /var/log/django/app.log
```

#### 3. **Logs de WhatsApp**
- **Webhooks**: Respuestas recibidas
- **Mensajes**: Estado de envío
- **Errores**: Fallos de API

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. **Reporte no se envía**
```bash
# Verificar Celery Beat
celery -A combustible inspect scheduled

# Verificar logs
grep "reporte-mensual" /var/log/celery/beat.log

# Ejecutar manualmente
python manage.py enviar_reporte_mensual --test
```

#### 2. **Error de conexión Redis**
```bash
# Verificar conexión
redis-cli -h host -p port ping

# Verificar variables de entorno
echo $CELERY_BROKER_URL
```

#### 3. **Error de WhatsApp API**
```bash
# Verificar configuración
python manage.py shell
>>> from whatsaap_service import WhatsAppBusinessService
>>> service = WhatsAppBusinessService()
>>> print(service.access_token)
```

#### 4. **Error de DigitalOcean Spaces**
```bash
# Verificar credenciales
python manage.py shell
>>> from django.conf import settings
>>> print(settings.AWS_ACCESS_KEY_ID)
```

## 📈 Optimizaciones

### 1. **Performance**
- **Colas separadas** para diferentes tipos de tareas
- **Concurrencia limitada** para evitar sobrecarga
- **Timeouts apropiados** para tareas largas

### 2. **Escalabilidad**
- **Múltiples workers** para alta carga
- **Load balancer** para múltiples instancias
- **Database connection pooling**

### 3. **Confiabilidad**
- **Reintentos automáticos** para tareas fallidas
- **Dead letter queue** para mensajes problemáticos
- **Health checks** para servicios

## 🔐 Seguridad

### 1. **Variables de Entorno**
- **Nunca commitear** archivos `.env`
- **Rotar credenciales** regularmente
- **Usar secretos** de DigitalOcean

### 2. **API Keys**
- **WhatsApp**: Rotar tokens periódicamente
- **SendGrid**: Usar API keys específicas
- **Spaces**: Limitar permisos por bucket

### 3. **Base de Datos**
- **Conexiones SSL** obligatorias
- **Backup automático** diario
- **Acceso restringido** por IP

---

## 📞 Soporte

Para problemas específicos:
1. **Revisar logs** en DigitalOcean App Platform
2. **Verificar variables** de entorno
3. **Probar comandos** localmente
4. **Contactar soporte** técnico

**¡Sistema de reportes automáticos configurado exitosamente! 🎉**
