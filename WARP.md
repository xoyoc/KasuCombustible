# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 🚀 Sistema de Gestión de Combustible - LogincoCobustible

Sistema integral Django para gestión de combustible con automatización completa via GitHub Actions, WhatsApp Business API, y almacenamiento en DigitalOcean Spaces.

## 🔧 Common Development Commands

### Essential Commands
```bash
# Development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### Monthly Report Commands
```bash
# Generate complete monthly report (with WhatsApp integration)
python manage.py enviar_reporte_mensual

# Basic report (used by GitHub Actions)
python manage.py enviar_reporte_mensual_r

# Test mode (no actual sending)
python manage.py enviar_reporte_mensual --test

# Specific month/year
python manage.py enviar_reporte_mensual --mes 6 --año 2024
```

### WhatsApp Management
```bash
# List WhatsApp contacts
python manage.py manage_whatsapp_contacts --list

# Add new contact
python manage.py manage_whatsapp_contacts --add "Name,+525512345678,supervisor"

# Test WhatsApp functionality
python manage.py manage_whatsapp_contacts --test "+525512345678"

# Sync with operators
python manage.py manage_whatsapp_contacts --sync
```

### Maintenance Commands
```bash
# Check pending maintenance
python manage.py verificar_mantenimientos

# Generate weekly report
python manage.py generar_reporte_semanal
```

### Celery (if used locally)
```bash
# Start Celery worker
celery -A combustible worker --loglevel=info

# Start Celery beat scheduler
celery -A combustible beat --loglevel=info
```

## 🏗️ High-Level Architecture

### Core Django Apps
- **`combustible/`** - Main Django configuration with Celery setup
- **`registros/`** - Core fuel records management with WhatsApp integration
- **`equipo/`** - Vehicle (equipment) management
- **`operador/`** - Driver/operator management  
- **`mantenimientos/`** - Preventive maintenance system

### Key Architectural Patterns

**Automated Reporting Pipeline:**
1. **GitHub Actions** execute monthly (day 1) at 9:00 AM UTC
2. **Django management commands** generate Excel reports
3. **DigitalOcean Spaces** stores files with public URLs
4. **WhatsApp Business API** sends interactive reports
5. **SendGrid** handles email delivery
6. **Logging system** tracks all operations

**Storage Strategy:**
- **Media files** (ticket photos) → DigitalOcean Spaces
- **Generated reports** → DigitalOcean Spaces with ReportesStorage
- **Static files** → DigitalOcean Spaces (production)
- **Database** → PostgreSQL

**WhatsApp Integration:**
- **Business API** with proper webhook handling
- **Contact management** system with roles and preferences
- **Message tracking** with delivery status
- **Interactive reporting** with Excel file attachments

### Critical Configuration Files
- **`combustible/settings.py`** - Main configuration with Spaces, WhatsApp, and email setup
- **`combustible/celery.py`** - Celery configuration with scheduled tasks
- **`combustible/storage_backends.py`** - Custom storage classes for DigitalOcean Spaces
- **`whatsaap_service.py`** - WhatsApp Business API service layer

## 🤖 GitHub Actions Workflows

### Primary Workflows
1. **`monthly-report.yml`** - Complete monthly report with validation and monitoring
2. **`EnvioReporteMensual.yml`** - Direct report sending (simplified)

Both execute automatically on day 1 of each month at 9:00 AM UTC.

### Required Secrets
All GitHub Secrets must be configured in repository settings:
- Django: `SECRET_KEY`, `DJANGO_DB_URL`
- DigitalOcean: `DO_SPACES_ACCESS_KEY`, `DO_SPACES_SECRET_KEY`, etc.
- WhatsApp: `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, etc.
- Email: `EMAIL_HOST_PASSWORD` (SendGrid)

See `GITHUB_SECRETS_GUIDE.md` for complete setup instructions.

## 🗃️ Database Models

### Key Models
- **`Registro`** - Fuel records with photo storage and cost calculations
- **`Equipo`** - Vehicles with maintenance tracking
- **`Operador`** - Drivers with contact information
- **`WhatsAppContact`** - WhatsApp contact management with preferences
- **`ReporteGenerado`** - Generated reports tracking with file URLs

### Important Relationships
- Registro → Equipo (vehicle used)
- Registro → Operador (driver)
- WhatsAppContact → Operador (optional link)
- ReporteGenerado → WhatsAppMessage (tracking)

## 🧪 Testing Strategy

### Test Commands
```bash
# Test monthly report generation
python manage.py enviar_reporte_mensual --test

# Test WhatsApp functionality
python manage.py manage_whatsapp_contacts --test "+525512345678"

# Test GitHub Actions workflow manually
# Go to GitHub → Actions → Select workflow → Run workflow
```

### Local Development Setup
1. Configure `.env` file with all required variables
2. Set `USE_SPACES=False` for local development
3. Use `DEBUG=True` for development
4. Ensure PostgreSQL and Redis are running if using Celery

## 📁 File Organization Patterns

### Management Commands Location
All custom Django commands are in `registros/management/commands/`:
- Report generation commands
- WhatsApp management utilities
- Maintenance verification tools

### Templates Structure
- Base templates in `templates/`
- App-specific templates in `{app}/templates/`
- Email templates for automated sending

### Static Files
- Development: Local static files
- Production: DigitalOcean Spaces with CDN

## 🔐 Security Considerations

### Production Settings
- `DEBUG=False` in production
- `USE_SPACES=True` for production storage
- All sensitive data in environment variables or GitHub Secrets
- CSRF and session cookies secured for HTTPS

### API Security
- WhatsApp webhook verification with tokens
- SendGrid API key protection
- DigitalOcean Spaces with proper ACL settings

## 🚨 Common Issues & Solutions

### WhatsApp API Issues
- Check phone number ID and access token validity
- Verify webhook URL is accessible
- Monitor rate limits (20 messages/minute)

### File Storage Issues
- Ensure DigitalOcean Spaces keys have proper permissions
- Check bucket name and region configuration
- Verify CDN endpoint if using custom domain

### GitHub Actions Failures
- Check all secrets are properly configured
- Verify database connectivity in Actions environment
- Monitor logs in Actions artifacts

## 📊 Monitoring & Maintenance

### GitHub Actions Monitoring
- Actions dashboard shows execution status
- Artifacts contain detailed logs (30-day retention)
- Email notifications on workflow failures

### Database Maintenance
- Regular PostgreSQL maintenance via DigitalOcean
- Backup strategy with scheduled snapshots
- Monitor database size and performance

### File Storage Monitoring
- Track DigitalOcean Spaces usage
- Monitor CDN performance if applicable
- Regular cleanup of old temporary files

## 🔄 Development Workflow

### Making Changes
1. Work on local development environment
2. Test thoroughly with `--test` flags
3. Push to GitHub to trigger workflows (if applicable)
4. Monitor GitHub Actions execution
5. Verify production functionality

### Adding New Features
- Follow Django app structure
- Add management commands in appropriate app
- Update workflows if automation needed
- Document in README.md
- Test WhatsApp integration if applicable

This system represents a mature, production-ready fuel management solution with comprehensive automation, monitoring, and integration capabilities.