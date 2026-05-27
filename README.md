# 🚛 Sistema de Gestión de Combustible - LogincoCobustible

[![Django](https://img.shields.io/badge/Django-5.1.2-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org/)
[![DigitalOcean](https://img.shields.io/badge/DigitalOcean-Spaces-blue.svg)](https://digitalocean.com/)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Business%20API-green.svg)](https://business.whatsapp.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue.svg)](https://github.com/features/actions)
[![Automated Reports](https://img.shields.io/badge/Reports-Automated-success.svg)](https://github.com/features/actions)

Sistema integral de gestión de combustible para flotas de vehículos con integración completa de WhatsApp, reportes automáticos via GitHub Actions, sistema de mantenimiento preventivo y almacenamiento en la nube.

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [GitHub Actions - Automatización](#-github-actions---automatización)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API y Integraciones](#-api-y-integraciones)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Comandos de Gestión](#-comandos-de-gestión)
- [Despliegue](#-despliegue)
- [Contribución](#-contribución)

## 🚀 Características Principales

### 📊 Gestión de Combustible
- **Registro de combustible** con fotos de tickets
- **Cálculo automático** de costos y estadísticas
- **Actualización automática** del kilometraje de vehículos
- **Reportes mensuales** automáticos con Excel

### 🚛 Gestión de Flota
- **Catálogo de equipos** (vehículos) con especificaciones
- **Gestión de operadores** y supervisores
- **Sistema de mantenimiento** preventivo automático
- **Alertas inteligentes** por tiempo y kilometraje

### 📱 Integración WhatsApp
- **Envío automático** de reportes mensuales
- **Mensajes interactivos** con botones
- **Alertas de operadores** inactivos
- **Webhook** para respuestas automáticas

### ☁️ Almacenamiento en la Nube
- **DigitalOcean Spaces** para archivos
- **Optimización automática** de imágenes
- **URLs públicas** para reportes
- **Backup automático** de archivos

### ⚙️ Automatización
- **GitHub Actions** para reportes automáticos
- **Tareas programadas** con Celery y cron
- **Notificaciones por email** con SendGrid
- **Reportes automáticos** mensuales el día 1
- **Verificación diaria** de mantenimientos
- **Scripts de mantenimiento** automatizados

## 🏗️ Arquitectura del Sistema

```mermaid
graph TB
    A[Usuario Web] --> B[Django App]
    B --> C[Base de Datos PostgreSQL]
    B --> D[DigitalOcean Spaces]
    B --> E[Celery Workers]
    
    E --> F[WhatsApp Business API]
    E --> G[SendGrid Email]
    E --> H[Reportes Excel]
    
    I[Webhook WhatsApp] --> B
    J[Cron Jobs] --> E
    K[GitHub Actions] --> L[Reporte Mensual]
    L --> B
    
    subgraph "GitHub Actions Workflows"
        M[Monthly Report]
        N[EnvioReporteMensual]
        O[Scripts Automáticos]
    end
    
    K --> M
    K --> N
    K --> O
    
    subgraph "Aplicaciones Django"
        P[equipo - Vehículos]
        Q[operador - Conductores]
        R[registros - Combustible]
        S[mantenimientos - Mantenimiento]
    end
    
    B --> P
    B --> Q
    B --> R
    B --> S
```

## 🤖 GitHub Actions - Automatización

### Configuración de Workflows

El sistema incluye **dos workflows principales** para automatización completa:

#### 1. 📊 Monthly Report (`monthly-report.yml`)
- **Programación**: Día 1 de cada mes a las 9:00 AM UTC
- **Funcionalidad**: Reporte completo con validaciones
- **Características**:
  - ✅ Ejecución automática mensual
  - ✅ Modo test para pruebas
  - ✅ Parámetros personalizables (mes/año)
  - ✅ Verificación de contactos WhatsApp
  - ✅ Check de mantenimientos
  - ✅ Upload de logs automático

#### 2. 🚀 Envío Reporte Mensual (`EnvioReporteMensual.yml`)
- **Programación**: Día 1 de cada mes a las 9:00 AM UTC  
- **Funcionalidad**: Envío directo del reporte
- **Comandos ejecutados**:
  ```bash
  python manage.py enviar_reporte_mensual_r --email xoyocl2@gmail.com
  python manage.py enviar_reporte_mensual_r
  ```

### 🔐 Configuración de Secrets

Para funcionar correctamente, los workflows requieren estos **GitHub Secrets**:

```bash
# Django Core
SECRET_KEY=django-insecure-abc123...
DJANGO_DB_URL=postgresql://user:pass@host:port/db

# DigitalOcean Spaces
DO_SPACES_ACCESS_KEY=DO00ABC123...
DO_SPACES_SECRET_KEY=abc123def456...
DO_SPACES_BUCKET_NAME=combustible-files
DO_SPACES_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
DO_SPACES_REGION=nyc3
USE_SPACES=True

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_VERIFY_TOKEN=mi_token_123

# Email
EMAIL_HOST_PASSWORD=SG.abc123def456...
```

> 📖 **Guía completa**: Ver [GITHUB_SECRETS_GUIDE.md](GITHUB_SECRETS_GUIDE.md)

### ⚡ Ejecución Manual

```bash
# Ejecutar workflow manualmente
# GitHub → Actions → Monthly Fuel Report → Run workflow

# Con parámetros personalizados:
# - test_mode: true (modo prueba)
# - month: 6 (junio)
# - year: 2024
```

### 📈 Monitoreo y Logs

- **Logs automáticos** en GitHub Actions
- **Artefactos** con logs detallados (30 días)
- **Notificaciones** de éxito/fallo
- **Verificación** de contactos y mantenimientos

---

## 📦 Instalación

### Prerrequisitos
- **Python 3.12+**
- **PostgreSQL** (base de datos principal)
- **Redis** (para Celery, opcional si usas solo GitHub Actions)
- **Cuenta de DigitalOcean Spaces** (almacenamiento)
- **WhatsApp Business API** (Meta for Developers)
- **SendGrid API** (envío de emails)
- **Repositorio en GitHub** (para GitHub Actions)
- **GitHub Secrets** configurados (ver guía)
### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd LogincoCobustible
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 5. Configurar base de datos
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Recopilar archivos estáticos
```bash
python manage.py collectstatic
```

### 7. Configurar GitHub Actions (Opcional)
```bash
# Configurar secrets en GitHub:
# Settings → Secrets and variables → Actions
# Ver GITHUB_SECRETS_GUIDE.md para detalles completos
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Django
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
DJANGO_DB_URL=postgresql://usuario:password@localhost:5432/combustible

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

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# GitHub Actions (Opcional - solo para automatización)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx  # Solo si usas API de GitHub
```

### Configuración de Celery

```bash
# Iniciar worker de Celery
celery -A combustible worker --loglevel=info

# Iniciar beat scheduler
celery -A combustible beat --loglevel=info
```

### Configuración de GitHub Actions

1. **Configurar Secrets** (ver [GITHUB_SECRETS_GUIDE.md](GITHUB_SECRETS_GUIDE.md))
2. **Los workflows se ejecutan automáticamente**
3. **Para pruebas manuales**:
   ```bash
   # Ir a GitHub → Actions → Seleccionar workflow → Run workflow
   ```

## 🎯 Uso

### Acceso Web
```bash
python manage.py runserver
# Acceder a http://localhost:8000
```

### Funcionalidades Principales

#### 1. **Registro de Combustible**
- Ir a `/registros/`
- Agregar nuevo registro con foto del ticket
- El sistema actualiza automáticamente el kilometraje del vehículo

#### 2. **Gestión de Equipos**
- Ir a `/equipos/`
- Agregar nuevos vehículos
- Ver estado de mantenimiento

#### 3. **Sistema de Mantenimiento**
- Ir a `/mantenimientos/`
- Ver dashboard con alertas
- Programar y completar mantenimientos

#### 4. **Reportes Automáticos**
- **GitHub Actions**: Reportes automáticos el día 1 de cada mes
- **Celery**: Tareas programadas diarias
- **Incluyen**: Estadísticas completas, archivo Excel y envío WhatsApp
- **Monitoreo**: Logs detallados en GitHub Actions

#### 5. **GitHub Actions Dashboard**
- Ir a `Actions` en GitHub para ver ejecuciones
- Monitorear logs y descargar artefactos
- Ejecutar reportes manualmente cuando sea necesario

## 🔌 API y Integraciones

### WhatsApp Business API

#### Envío de Mensajes
```python
from whatsaap_service import WhatsAppBusinessService

service = WhatsAppBusinessService()
result = service.send_text_message("+525512345678", "Mensaje de prueba")
```

#### Webhook Configuration
```python
# URL del webhook: /webhook/whatsapp/
# Método: POST
# Verificación: GET con parámetros hub.mode, hub.verify_token, hub.challenge
```

### DigitalOcean Spaces

#### Subida de Archivos
```python
from combustible.storage_backends import MediaStorage

storage = MediaStorage()
file_url = storage.save('archivo.jpg', file_content)
```

### SendGrid Email

#### Envío de Emails
```python
from combustible.sendmail import sendMail

sendMail("destino@email.com", "Asunto", "Contenido HTML")
```

## 📁 Estructura del Proyecto

```
LogincoCobustible/
├── .github/                    # 🤖 GitHub Actions
│   └── workflows/
│       ├── monthly-report.yml  # Reporte mensual completo
│       └── EnvioReporteMensual.yml # Envío directo de reporte
├── combustible/                # Configuración principal de Django
│   ├── settings.py             # Configuraciones del proyecto
│   ├── celery.py               # Configuración de Celery
│   ├── urls.py                 # URLs principales
│   ├── storage_backends.py     # Configuración de almacenamiento
│   └── sendmail.py             # Servicio de email
├── equipo/                     # Aplicación de gestión de vehículos
│   ├── models.py               # Modelo Equipo
│   ├── views.py                # Vistas CRUD
│   └── templates/              # Plantillas HTML
├── operador/                   # Aplicación de gestión de operadores
│   ├── models.py               # Modelos Operador y Supervisor
│   └── views.py                # Vistas CRUD
├── registros/                  # Aplicación principal de combustible
│   ├── models.py               # Modelos Registro, ReporteGenerado, WhatsApp
│   ├── views.py                # Vistas y webhook de WhatsApp
│   ├── management/commands/    # 🔧 Comandos personalizados
│   │   ├── enviar_reporte_mensual.py      # Reporte completo con WhatsApp
│   │   ├── enviar_reporte_mensual_r.py    # Reporte básico
│   │   ├── sync_whatsapp_contacts.py      # Gestión WhatsApp
│   │   └── check_and_send_reports.py      # Verificaciones
│   └── templates/              # Plantillas de reportes
├── mantenimientos/             # Sistema de mantenimiento
│   ├── models.py               # Modelos Mantenimiento, Notificacion
│   ├── views.py                # Dashboard y gestión
│   ├── tasks.py                # Tareas de Celery
│   └── templates/              # Plantillas de mantenimiento
├── scripts/                    # 📜 Scripts de automatización
│   ├── send_monthly_report.sh  # Script principal de reportes
│   └── generate_secrets.sh     # Generación de secrets
├── static/                     # Archivos estáticos
├── templates/                  # Plantillas base
├── requirements.txt            # Dependencias Python
├── whatsaap_service.py         # Servicio de WhatsApp
├── GITHUB_SECRETS_GUIDE.md     # 📖 Guía de configuración
└── manage.py                   # Script de gestión de Django
```

## 🛠️ Comandos de Gestión

### Reportes Mensuales

#### 📊 Comando Principal (Completo)
```bash
# Generar reporte del mes anterior
python manage.py enviar_reporte_mensual

# Generar reporte de mes específico
python manage.py enviar_reporte_mensual --mes 6 --año 2024

# Con todas las opciones
python manage.py enviar_reporte_mensual --send-email --send-whatsapp

# Solo enviar por WhatsApp
python manage.py enviar_reporte_mensual --whatsapp-only

# Modo test (sin enviar)
python manage.py enviar_reporte_mensual --test
```

#### 🚀 Comando GitHub Actions
```bash
# Reporte básico (usado en GitHub Actions)
python manage.py enviar_reporte_mensual_r

# Con email específico
python manage.py enviar_reporte_mensual_r --email usuario@ejemplo.com

# Modo test
python manage.py enviar_reporte_mensual_r --test
```

### Gestión de WhatsApp
```bash
# Listar contactos
python manage.py manage_whatsapp_contacts --list

# Agregar contacto
python manage.py manage_whatsapp_contacts --add "Juan Pérez,+525512345678,supervisor"

# Enviar mensaje de prueba
python manage.py manage_whatsapp_contacts --test "+525512345678"

# Sincronizar con operadores
python manage.py manage_whatsapp_contacts --sync

# Habilitar/deshabilitar reportes
python manage.py manage_whatsapp_contacts --enable-reports "+525512345678"
python manage.py manage_whatsapp_contacts --disable-reports "+525512345678"
```

### Mantenimientos
```bash
# Verificar mantenimientos pendientes
python manage.py verificar_mantenimientos

# Generar reporte semanal
python manage.py generar_reporte_semanal
```

### Scripts de Automatización
```bash
# Script principal de reportes
./scripts/send_monthly_report.sh

# Modo test
./scripts/send_monthly_report.sh --test

# Forzar envío
./scripts/send_monthly_report.sh --force

# Modo verbose
./scripts/send_monthly_report.sh --verbose
```

## 🚀 Despliegue

### DigitalOcean App Platform

1. **Crear App en DigitalOcean**
2. **Configurar variables de entorno**
3. **Conectar repositorio Git**
4. **Configurar base de datos PostgreSQL**
5. **Configurar Redis para Celery**
6. **Configurar GitHub Secrets** (ver guía completa)

### GitHub Actions

1. **Configurar Secrets**:
   ```bash
   # En GitHub: Settings → Secrets and variables → Actions
   # Agregar todos los secrets listados en GITHUB_SECRETS_GUIDE.md
   ```

2. **Los workflows están configurados** para ejecutarse automáticamente

3. **Verificar funcionamiento**:
   ```bash
   # Ejecutar manualmente primero:
   # GitHub → Actions → Monthly Fuel Report → Run workflow
   # Seleccionar "test_mode: true"
   ```

### Configuración de Producción

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['squid-app-5j4xm.ondigitalocean.app']
USE_SPACES = True
```

### Tareas Programadas

#### GitHub Actions (Recomendado)
```yaml
# Ya configurado en .github/workflows/
# Ejecución automática el día 1 de cada mes a las 9:00 AM UTC
```

#### Cron Local (Alternativo)
```bash
# Si prefieres usar cron local en lugar de GitHub Actions
0 9 1 * * cd /path/to/project && ./scripts/send_monthly_report.sh

# Para Celery Beat (tareas diarias)
* * * * * cd /path/to/project && celery -A combustible beat --loglevel=info
```

## 📊 Monitoreo y Logs

### GitHub Actions
- **Logs automáticos** en cada ejecución
- **Artefactos** con logs detallados (30 días)
- **Notificaciones** por email en caso de fallo
- **Dashboard** completo en GitHub Actions

### Logs del Sistema
- **Django**: Logs de aplicación en `logs/django.log`
- **Celery**: Logs de tareas asíncronas
- **WhatsApp**: Logs de webhooks y mensajes
- **Storage**: Logs de subida de archivos
- **Scripts**: Logs en `/var/log/combustible_reports.log`

### Métricas Importantes
- **GitHub Actions**: Éxito/fallo de ejecuciones automáticas
- **Reportes**: Envíos exitosos por email y WhatsApp
- **Registros**: Combustible por día/mes
- **Operadores**: Activos vs inactivos
- **Mantenimientos**: Pendientes/vencidos
- **Storage**: Uso de almacenamiento en Spaces
- **Contactos WhatsApp**: Estado y configuración

## 🔧 Mantenimiento

### Automatización con GitHub Actions
- **Día 1 de cada mes**: Reporte automático completo
- **Logs**: Almacenados automáticamente (30 días)
- **Monitoreo**: Dashboard en GitHub Actions
- **Alertas**: Notificaciones automáticas de errores

### Tareas Regulares
- **Diario**: Verificación automática de mantenimientos
- **Semanal**: Reportes de supervisores
- **Mensual**: Reportes completos automáticos (GitHub Actions)
- **Trimestral**: Revisión de configuración de WhatsApp
- **Anual**: Rotación de secrets y tokens

### Backup
- **Base de datos**: Backup automático diario
- **Archivos**: Replicación en DigitalOcean Spaces
- **Configuración**: Secrets seguros en GitHub
- **Logs**: Artefactos automáticos (30 días)
- **Código**: Versionado en Git con GitHub Actions

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📞 Soporte

Para soporte técnico o consultas:
- **Email**: zuly.becerra@loginco.com.mx
- **WhatsApp**: +52 753 119 0392
- **Issues**: Usar el sistema de issues de GitHub

## 📄 Licencia

Este proyecto es propiedad de Loginco y está destinado para uso interno de la empresa.

---

## 🎯 Guías Adicionales

- 📖 [**GITHUB_SECRETS_GUIDE.md**](GITHUB_SECRETS_GUIDE.md) - Configuración completa de secrets
- 🔧 [**DIGITALOCEAN_SETUP.md**](DIGITALOCEAN_SETUP.md) - Setup de DigitalOcean
- ⚡ [**ALTERNATIVAS_CELERY.md**](ALTERNATIVAS_CELERY.md) - Alternativas a Celery

## 🚀 Características Avanzadas

### ✅ **Lo que está funcionando:**
- 🤖 **Reportes automáticos** con GitHub Actions
- 📱 **WhatsApp Business API** completamente integrado
- ☁️ **DigitalOcean Spaces** para archivos
- 📧 **SendGrid** para emails
- 🔍 **Logging completo** y monitoreo
- 📊 **Dashboard** de mantenimientos
- 🔐 **Gestión segura** de secrets

### 🔄 **Flujo Completo Automatizado:**
1. **Día 1 del mes**: GitHub Actions ejecuta automáticamente
2. **Sistema**: Genera reporte Excel con estadísticas
3. **Storage**: Guarda archivo en DigitalOcean Spaces
4. **Email**: Envía reporte a destinatarios configurados
5. **WhatsApp**: Envía resumen y archivo a contactos
6. **Verificación**: Revisa mantenimientos y contactos
7. **Logs**: Almacena logs detallados para auditoría

---

**Desarrollado con ❤️ por el equipo de Loginco**

*Sistema de Gestión de Combustible v3.0 - 2025*  
*Con GitHub Actions y Automatización Completa* 🤖
