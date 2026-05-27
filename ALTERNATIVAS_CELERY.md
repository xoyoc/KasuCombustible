# 📅 Alternativas a Celery para Programar Reportes Automáticos

## 🎯 Opciones Disponibles

### 1. **Cron Jobs (Linux/Unix)**
### 2. **GitHub Actions**
### 3. **DigitalOcean Functions**
### 4. **Webhooks Externos**
### 5. **Django Management Commands + Cron**

---

## 🐧 Opción 1: Cron Jobs (Más Simple)

### Configuración Local/Servidor

#### 1.1 Crear Script de Ejecución
```bash
# scripts/send_monthly_report.sh
#!/bin/bash

# Configurar variables de entorno
export DJANGO_SETTINGS_MODULE=combustible.settings
export PYTHONPATH=/ruta/a/tu/proyecto

# Cambiar al directorio del proyecto
cd /ruta/a/tu/proyecto

# Activar entorno virtual (si existe)
source venv/bin/activate

# Ejecutar comando de reporte
python manage.py enviar_reporte_mensual --send-email --send-whatsapp

# Log del resultado
echo "$(date): Reporte mensual ejecutado" >> /var/log/combustible_reports.log
```

#### 1.2 Configurar Cron
```bash
# Editar crontab
crontab -e

# Agregar estas líneas:
# Enviar reporte mensual el día 1 de cada mes a las 9:00 AM
0 9 1 * * /ruta/a/tu/proyecto/scripts/send_monthly_report.sh

# Verificar mantenimientos diariamente a las 8:00 AM
0 8 * * * /ruta/a/tu/proyecto/scripts/check_maintenance.sh

# Limpiar archivos temporales diariamente a las 2:00 AM
0 2 * * * /ruta/a/tu/proyecto/scripts/cleanup_files.sh
```

#### 1.3 Scripts Adicionales
```bash
# scripts/check_maintenance.sh
#!/bin/bash
export DJANGO_SETTINGS_MODULE=combustible.settings
cd /ruta/a/tu/proyecto
source venv/bin/activate
python manage.py verificar_mantenimientos
echo "$(date): Verificación de mantenimientos ejecutada" >> /var/log/combustible_maintenance.log

# scripts/cleanup_files.sh
#!/bin/bash
export DJANGO_SETTINGS_MODULE=combustible.settings
cd /ruta/a/tu/proyecto
source venv/bin/activate
python manage.py cleanup_old_files --days=180
echo "$(date): Limpieza de archivos ejecutada" >> /var/log/combustible_cleanup.log
```

---

## 🐙 Opción 2: GitHub Actions (Recomendado para CI/CD)

### Configuración

#### 2.1 Crear Workflow
```yaml
# .github/workflows/monthly-report.yml
name: Monthly Fuel Report

on:
  schedule:
    # Ejecutar el primer día de cada mes a las 9:00 AM UTC
    - cron: '0 9 1 * *'
  workflow_dispatch: # Permitir ejecución manual

jobs:
  send-report:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Set up environment
      env:
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
        DJANGO_DB_URL: ${{ secrets.DJANGO_DB_URL }}
        DO_SPACES_ACCESS_KEY: ${{ secrets.DO_SPACES_ACCESS_KEY }}
        DO_SPACES_SECRET_KEY: ${{ secrets.DO_SPACES_SECRET_KEY }}
        DO_SPACES_BUCKET_NAME: ${{ secrets.DO_SPACES_BUCKET_NAME }}
        DO_SPACES_ENDPOINT_URL: ${{ secrets.DO_SPACES_ENDPOINT_URL }}
        WHATSAPP_PHONE_NUMBER_ID: ${{ secrets.WHATSAPP_PHONE_NUMBER_ID }}
        WHATSAPP_ACCESS_TOKEN: ${{ secrets.WHATSAPP_ACCESS_TOKEN }}
        WHATSAPP_VERIFY_TOKEN: ${{ secrets.WHATSAPP_VERIFY_TOKEN }}
        EMAIL_HOST_PASSWORD: ${{ secrets.EMAIL_HOST_PASSWORD }}
        DEBUG: "False"
        USE_SPACES: "True"
      run: |
        echo "Environment configured"
        
    - name: Run migrations
      run: python manage.py migrate --noinput
      
    - name: Send monthly report
      run: python manage.py enviar_reporte_mensual --send-email --send-whatsapp
      
    - name: Notify on success
      if: success()
      run: echo "✅ Reporte mensual enviado exitosamente"
      
    - name: Notify on failure
      if: failure()
      run: echo "❌ Error enviando reporte mensual"
```

#### 2.2 Configurar Secrets en GitHub
```bash
# En GitHub: Settings → Secrets and variables → Actions
# Agregar estos secrets:
SECRET_KEY=tu-secret-key
DJANGO_DB_URL=postgresql://usuario:password@host:port/database
DO_SPACES_ACCESS_KEY=tu-access-key
DO_SPACES_SECRET_KEY=tu-secret-key
DO_SPACES_BUCKET_NAME=tu-bucket-name
DO_SPACES_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
WHATSAPP_PHONE_NUMBER_ID=tu-phone-number-id
WHATSAPP_ACCESS_TOKEN=tu-access-token
WHATSAPP_VERIFY_TOKEN=tu-verify-token
EMAIL_HOST_PASSWORD=tu-sendgrid-api-key
```

---

## ☁️ Opción 3: DigitalOcean Functions (Serverless)

### Configuración

#### 3.1 Crear Function
```python
# functions/send_monthly_report.py
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'combustible.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings

def main(args):
    """Función principal para enviar reporte mensual"""
    try:
        # Ejecutar comando de reporte
        call_command('enviar_reporte_mensual', 
                    send_email=True, 
                    send_whatsapp=True,
                    verbosity=2)
        
        return {
            'status': 'success',
            'message': 'Reporte mensual enviado exitosamente',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Para testing local
if __name__ == '__main__':
    result = main({})
    print(result)
```

#### 3.2 Configurar Trigger
```yaml
# .do/functions.yml
packages:
- name: combustible-functions
  functions:
  - name: send-monthly-report
    runtime: python:3.9
    source_dir: functions
    main: send_monthly_report.main
    environment:
      SECRET_KEY: ${SECRET_KEY}
      DJANGO_DB_URL: ${DJANGO_DB_URL}
      # ... otras variables
    triggers:
    - name: monthly-report-trigger
      type: cron
      schedule: "0 9 1 * *"  # Primer día del mes a las 9:00 AM
```

---

## 🔗 Opción 4: Webhooks Externos

### Usando Servicios de Terceros

#### 4.1 Zapier
```javascript
// Zapier Webhook
// Trigger: Schedule (Monthly)
// Action: Webhook POST a tu aplicación

// En tu Django app:
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command

@csrf_exempt
def webhook_monthly_report(request):
    if request.method == 'POST':
        try:
            call_command('enviar_reporte_mensual', 
                        send_email=True, 
                        send_whatsapp=True)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'}, status=405)
```

#### 4.2 IFTTT (If This Then That)
```javascript
// IFTTT Applet
// Trigger: Date & Time (Monthly)
// Action: Webhook POST

// URL del webhook: https://tu-app.com/webhook/monthly-report/
// Método: POST
// Headers: Content-Type: application/json
```

---

## 🛠️ Opción 5: Django Management Commands + Cron (Híbrido)

### Configuración Completa

#### 5.1 Crear Comando de Verificación
```python
# registros/management/commands/check_and_send_reports.py
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Verifica si debe enviar reporte mensual y lo envía'
    
    def handle(self, *args, **options):
        hoy = datetime.now()
        
        # Solo ejecutar el día 1 del mes
        if hoy.day == 1:
            self.stdout.write(
                self.style.SUCCESS(f'📅 Es día de reporte mensual: {hoy.strftime("%Y-%m-%d")}')
            )
            
            # Ejecutar reporte mensual
            from django.core.management import call_command
            call_command('enviar_reporte_mensual', 
                        send_email=True, 
                        send_whatsapp=True)
        else:
            self.stdout.write(
                self.style.WARNING(f'⏰ No es día de reporte. Hoy es día {hoy.day}')
            )
```

#### 5.2 Cron Job Simplificado
```bash
# Crontab - ejecutar diariamente, el comando decide si enviar
0 9 * * * /ruta/a/tu/proyecto/scripts/daily_check.sh

# scripts/daily_check.sh
#!/bin/bash
export DJANGO_SETTINGS_MODULE=combustible.settings
cd /ruta/a/tu/proyecto
source venv/bin/activate
python manage.py check_and_send_reports
```

---

## 📊 Comparación de Opciones

| Opción | Complejidad | Costo | Confiabilidad | Escalabilidad |
|--------|-------------|-------|---------------|----------------|
| **Cron Jobs** | ⭐⭐ | Gratis | ⭐⭐⭐ | ⭐⭐ |
| **GitHub Actions** | ⭐⭐⭐ | Gratis* | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **DigitalOcean Functions** | ⭐⭐⭐⭐ | Bajo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Webhooks Externos** | ⭐⭐⭐ | Variable | ⭐⭐⭐ | ⭐⭐⭐ |
| **Django + Cron** | ⭐⭐ | Gratis | ⭐⭐⭐ | ⭐⭐ |

*GitHub Actions: 2000 minutos/mes gratis

---

## 🎯 Recomendación por Escenario

### Para Desarrollo/Testing
```bash
# Opción más simple: Cron Jobs
0 9 1 * * /path/to/send_report.sh
```

### Para Producción Pequeña
```bash
# GitHub Actions (gratis y confiable)
# Usar el workflow de GitHub Actions
```

### Para Producción Empresarial
```bash
# DigitalOcean Functions (escalable y confiable)
# Usar serverless functions
```

### Para Máximo Control
```bash
# Cron Jobs en servidor dedicado
# Control total sobre el entorno
```

---

## 🚀 Implementación Rápida: GitHub Actions

### Paso 1: Crear el Workflow
```bash
mkdir -p .github/workflows
# Crear el archivo monthly-report.yml (ver arriba)
```

### Paso 2: Configurar Secrets
```bash
# En GitHub: Settings → Secrets → Actions
# Agregar todas las variables de entorno necesarias
```

### Paso 3: Activar el Workflow
```bash
# El workflow se ejecutará automáticamente el día 1 de cada mes
# También puedes ejecutarlo manualmente desde GitHub Actions
```

### Paso 4: Monitorear
```bash
# Ver logs en GitHub Actions
# Configurar notificaciones por email/Slack
```

---

## 🔧 Ventajas de Cada Opción

### ✅ Cron Jobs
- **Simplicidad**: Fácil de configurar y entender
- **Control**: Control total sobre el entorno
- **Costo**: Gratis
- **Flexibilidad**: Puedes ejecutar cualquier script

### ✅ GitHub Actions
- **Confiabilidad**: Infraestructura de GitHub
- **Monitoreo**: Logs detallados y notificaciones
- **CI/CD**: Integración con el repositorio
- **Gratis**: 2000 minutos/mes

### ✅ DigitalOcean Functions
- **Escalabilidad**: Serverless, escala automáticamente
- **Integración**: Perfecta con DigitalOcean
- **Costo**: Solo pagas por ejecución
- **Mantenimiento**: Sin servidores que mantener

---

## 🎯 Mi Recomendación

Para tu caso específico, recomiendo **GitHub Actions** porque:

1. **Ya tienes el código en GitHub**
2. **Es gratis para tu uso**
3. **Logs detallados y notificaciones**
4. **Fácil de configurar y mantener**
5. **Se ejecuta en la nube, no depende de tu servidor**

¿Te gustaría que implemente alguna de estas opciones específicamente?
