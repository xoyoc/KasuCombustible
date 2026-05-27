# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.1.2 fuel management system (Python 3.12+) for a vehicle fleet. Tracks fuel consumption, generates Excel reports, sends them via WhatsApp Business API and SendGrid email, and manages preventive maintenance schedules. Deployed on DigitalOcean App Platform.

## Common Commands

```bash
# Run development server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Static files (production)
python manage.py collectstatic

# Generate monthly fuel report (full, with WhatsApp)
python manage.py enviar_reporte_mensual
python manage.py enviar_reporte_mensual --mes 6 --año 2024
python manage.py enviar_reporte_mensual --test   # dry run

# Generate monthly report (simplified, used by GitHub Actions)
python manage.py enviar_reporte_mensual_r
python manage.py enviar_reporte_mensual_r --email user@example.com

# WhatsApp contact management
python manage.py manage_whatsapp_contacts --list
python manage.py manage_whatsapp_contacts --sync
python manage.py manage_whatsapp_contacts --test "+525512345678"

# Celery (requires Redis)
celery -A combustible worker --loglevel=info
celery -A combustible beat --loglevel=info
```

## Architecture

### Django Apps

- **`combustible/`** — Project config: `settings.py`, `celery.py`, `urls.py`, `storage_backends.py`, `sendmail.py`
- **`equipo/`** — Vehicle (`Equipo`) model: placa, modelo, marca, kilometraje_actual, active flag; includes `proximo_mantenimiento()` and `necesita_mantenimiento()` helpers
- **`operador/`** — `Operador` (drivers) and `Supervisor` models
- **`registros/`** — Core fuel records (`Registro`) with ticket photo storage; also owns `ReporteGenerado`, `WhatsAppContact`, `WhatsAppMessage`, `WhatsAppWebhookLog`; all management commands live here at `registros/management/commands/`
- **`mantenimientos/`** — `TipoMantenimiento`, `Mantenimiento` (estado: pendiente/en_proceso/completado/vencido), `Notificacion`, `ReporteMantenimiento`; Celery tasks in `tasks.py`

### Storage Strategy

Controlled by the `USE_SPACES` env var:
- **`USE_SPACES=True` (production)**: media and static files go to DigitalOcean Spaces (S3-compatible) via `django-storages`; `MediaStorage` and `ReportesStorage` are custom subclasses in `combustible/storage_backends.py`
- **`USE_SPACES=False` (development)**: local filesystem at `media/` and `staticfiles/`

### WhatsApp Integration

`whatsaap_service.py` (note the typo — intentional filename) is a standalone service class. The webhook endpoint lives in `registros/views.py`. `WhatsAppContact` model links contacts to `Operador` records and stores per-contact notification preferences.

### Automated Reporting Pipeline

GitHub Actions (`.github/workflows/EnvioReporteMensual.yml`) triggers on day 1 of each month at 9:00 AM UTC, runs `enviar_reporte_mensual_r`, which:
1. Queries `Registro` records for the prior month
2. Generates an Excel file (`openpyxl`) and saves it to Spaces via `ReportesStorage`
3. Emails it via SendGrid
4. Sends it to active `WhatsAppContact` records with `receive_monthly_reports=True`

### Key Environment Variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DJANGO_DB_URL` | PostgreSQL connection string |
| `USE_SPACES` | Enable DigitalOcean Spaces (bool) |
| `DO_SPACES_ACCESS_KEY/SECRET_KEY/BUCKET_NAME/ENDPOINT_URL/REGION` | Spaces credentials |
| `EMAIL_HOST_PASSWORD` | SendGrid API key |
| `WHATSAPP_PHONE_NUMBER_ID/ACCESS_TOKEN/VERIFY_TOKEN` | WhatsApp Business API |

Set `USE_SPACES=False` locally; all Spaces vars are still required to import but won't be used for storage.

### Maintenance Logic

`Equipo.proximo_mantenimiento()` calculates the next service at +90 days / +10,000 km from the last completed `Mantenimiento`. Signals and Celery tasks in `mantenimientos/` auto-update states and send email notifications through `Notificacion.enviar()`.

### Forms & Templates

Forms use `django-crispy-forms` with the Tailwind template pack (`crispy_tailwind`). Base template is at `templates/base.html`; app-level templates live inside each app's `templates/` directory.
