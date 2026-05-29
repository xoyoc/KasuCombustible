# Sistema de Gestión de Combustible - KasuCombustible

[![Django](https://img.shields.io/badge/Django-5.1.2-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org/)
[![DigitalOcean](https://img.shields.io/badge/DigitalOcean-Spaces-blue.svg)](https://digitalocean.com/)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Business%20API-green.svg)](https://business.whatsapp.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue.svg)](https://github.com/features/actions)

Sistema integral de gestión de combustible para la flota de Transportes Kasu. Registra consumos, genera reportes Excel automáticos, envía alertas por WhatsApp y email, y gestiona el mantenimiento preventivo de los vehículos.

## Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Variables de Entorno](#variables-de-entorno)
- [Comandos de Gestión](#comandos-de-gestión)
- [Automatización](#automatización)
- [Despliegue](#despliegue)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## Características

- **Registro de combustible** con foto del ticket, kilometraje, litros y costo
- **Diesel vs. Gasolina**: flujo diferenciado — diesel no requiere ticket manual ni foto; gasolina sí
- **Actualización automática** del kilometraje del equipo al guardar un registro
- **Reportes mensuales** en Excel generados automáticamente el día 1 de cada mes vía GitHub Actions
- **Envío por email** (SendGrid) y **WhatsApp Business API**
- **Mantenimiento preventivo**: alertas a 5 días / 100 km antes del próximo servicio
- **Almacenamiento en la nube** con DigitalOcean Spaces (fotos de tickets y reportes Excel)
- **Tareas programadas** con APScheduler (sin Redis ni Celery)

---

## Arquitectura

### Apps Django

| App | Responsabilidad |
|---|---|
| `combustible/` | Configuración del proyecto: `settings.py`, `urls.py`, `storage_backends.py`, `sendmail.py`, `scheduler.py` |
| `equipo/` | Modelo `Equipo` (vehículos): placa, modelo, marca, tipo de combustible, kilometraje |
| `operador/` | Modelos `Operador` y `Supervisor` |
| `registros/` | Modelo `Registro` (tickets de combustible); también gestiona `ReporteGenerado`, `WhatsAppContact`, `WhatsAppMessage`; todos los management commands viven aquí |
| `mantenimientos/` | `TipoMantenimiento`, `Mantenimiento`, `Notificacion`, `ReporteMantenimiento` |

### Scheduler (APScheduler)

Las tareas programadas corren con `django-apscheduler` mediante el comando `python manage.py runscheduler`. No requieren Redis ni un broker externo.

| Tarea | Frecuencia |
|---|---|
| Verificar mantenimientos pendientes y vencidos | Diario 8:00 AM |
| Verificar kilometraje próximo a mantenimiento | Cada 2 horas en horario laboral |
| Procesar notificaciones pendientes | Cada 30 minutos |
| Reporte mensual de combustible | Día 1 del mes 9:00 AM |
| Verificar operadores inactivos | Lunes 10:00 AM |
| Reporte semanal de mantenimientos | Lunes 9:00 AM |

### Almacenamiento

Controlado por la variable `USE_SPACES`:
- **`USE_SPACES=True` (producción)**: fotos y reportes en DigitalOcean Spaces via `django-storages`
- **`USE_SPACES=False` (desarrollo)**: sistema de archivos local en `media/`

Tres clases de storage en `combustible/storage_backends.py`:
- `StaticStorage` — archivos estáticos (`public-read`)
- `MediaStorage` — fotos de tickets (`public-read`, agrega timestamp al nombre)
- `ReportesStorage` — reportes Excel (`private`)

---

## Instalación

### Prerrequisitos

- Python 3.12+
- PostgreSQL
- Cuenta de DigitalOcean Spaces
- WhatsApp Business API (Meta for Developers)
- SendGrid API

### Pasos

```bash
# 1. Clonar
git clone <repository-url>
cd KasuCombustible

# 2. Entorno virtual
python -m venv .venv
source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Migraciones
python manage.py migrate

# 6. Importar flota (opcional)
python manage.py importar_unidades unidades.csv

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Correr servidor
python manage.py runserver
```

---

## Variables de Entorno

```env
# Django
SECRET_KEY=tu-secret-key
DEBUG=True
DJANGO_DB_URL=postgresql://usuario:password@localhost:5432/kasu_combustible

# DigitalOcean Spaces
USE_SPACES=False
DO_SPACES_ACCESS_KEY=
DO_SPACES_SECRET_KEY=
DO_SPACES_BUCKET_NAME=
DO_SPACES_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
DO_SPACES_REGION=nyc3

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=

# SendGrid
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxx
```

> En desarrollo usa `USE_SPACES=False`. Las variables `DO_SPACES_*` igual deben existir en el `.env` aunque no se usen para storage local.

---

## Comandos de Gestión

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Importar flota desde CSV
python manage.py importar_unidades unidades.csv
python manage.py importar_unidades unidades.csv --dry-run  # vista previa sin guardar

# Reporte mensual manual (completo, con WhatsApp)
python manage.py enviar_reporte_mensual
python manage.py enviar_reporte_mensual --mes 6 --año 2025
python manage.py enviar_reporte_mensual --test

# Reporte mensual simplificado (usado por GitHub Actions)
python manage.py enviar_reporte_mensual_r
python manage.py enviar_reporte_mensual_r --email usuario@ejemplo.com

# Iniciar el scheduler de tareas programadas
python manage.py runscheduler

# Archivos estáticos (producción)
python manage.py collectstatic
```

---

## Automatización

### GitHub Actions (reporte mensual)

El workflow `.github/workflows/EnvioReporteMensual.yml` se ejecuta automáticamente el **día 1 de cada mes a las 9:00 AM UTC**. Ejecuta `enviar_reporte_mensual_r`, que:

1. Consulta los registros del mes anterior
2. Genera un archivo Excel con `openpyxl` y lo guarda en Spaces
3. Lo envía por email via SendGrid
4. Lo envía a los contactos de WhatsApp activos con `receive_monthly_reports=True`

#### Secrets requeridos en GitHub

```
SECRET_KEY
DJANGO_DB_URL
USE_SPACES
DO_SPACES_ACCESS_KEY
DO_SPACES_SECRET_KEY
DO_SPACES_BUCKET_NAME
DO_SPACES_ENDPOINT_URL
DO_SPACES_REGION
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN
WHATSAPP_VERIFY_TOKEN
EMAIL_HOST_PASSWORD
```

### APScheduler (tareas diarias)

Para correr las tareas programadas en el servidor:

```bash
python manage.py runscheduler
```

En DigitalOcean App Platform se puede configurar como un worker process separado.

---

## Despliegue

### DigitalOcean App Platform

1. Conectar repositorio Git
2. Configurar variables de entorno en el panel de DigitalOcean
3. Agregar base de datos PostgreSQL administrada
4. Configurar `USE_SPACES=True` y las credenciales de Spaces
5. Agregar un worker process con el comando `python manage.py runscheduler`
6. Configurar los secrets en GitHub para el workflow de reportes

### Configuración de producción

```python
DEBUG = False
ALLOWED_HOSTS = ['tu-app.ondigitalocean.app']
USE_SPACES = True
```

---

## Estructura del Proyecto

```
KasuCombustible/
├── .github/
│   └── workflows/
│       └── EnvioReporteMensual.yml     # Reporte mensual automático
├── combustible/                        # Config principal del proyecto
│   ├── settings.py
│   ├── urls.py
│   ├── scheduler.py                    # APScheduler — jobs registrados
│   ├── storage_backends.py             # StaticStorage, MediaStorage, ReportesStorage
│   ├── sendmail.py                     # Envío de email via SendGrid
│   └── openwa_service.py               # Integración OpenWA
├── equipo/                             # Gestión de vehículos
│   ├── models.py                       # Equipo: placa, tipo_combustible, kilometraje
│   ├── views.py
│   ├── management/commands/
│   │   └── importar_unidades.py        # Importación desde CSV
│   └── templates/
├── operador/                           # Gestión de operadores y supervisores
│   ├── models.py
│   ├── views.py
│   └── templates/
├── registros/                          # Tickets de combustible
│   ├── models.py                       # Registro, ReporteGenerado, WhatsAppContact
│   ├── views.py                        # Vistas + webhook de WhatsApp
│   ├── forms.py                        # RegisterForm con lógica diesel/gasolina
│   ├── tasks.py                        # Funciones para APScheduler
│   ├── management/commands/
│   │   ├── enviar_reporte_mensual.py
│   │   ├── enviar_reporte_mensual_r.py
│   │   └── runscheduler.py             # Comando para iniciar APScheduler
│   └── templates/
├── mantenimientos/                     # Mantenimiento preventivo
│   ├── models.py                       # Mantenimiento, Notificacion
│   ├── views.py
│   ├── tasks.py                        # Funciones para APScheduler
│   └── templates/
├── templates/
│   └── base.html
├── static/
├── unidades.csv                        # Flota de Transportes Kasu
├── requirements.txt
├── manage.py
└── context.md                          # Contexto técnico del proyecto
```

---

*KasuCombustible — Transportes Kasu — 2026*
