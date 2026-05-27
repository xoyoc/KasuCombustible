#!/bin/bash
# deploy.sh - Script de deployment para DigitalOcean App Platform

set -e

echo "🚀 Iniciando deployment del Sistema de Combustible..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar prerrequisitos
check_prerequisites() {
    log_info "Verificando prerrequisitos..."
    
    # Verificar si doctl está instalado
    if ! command -v doctl &> /dev/null; then
        log_error "doctl no está instalado. Instálalo desde: https://github.com/digitalocean/doctl"
        exit 1
    fi
    
    # Verificar autenticación
    if ! doctl account get &> /dev/null; then
        log_error "No estás autenticado con doctl. Ejecuta: doctl auth init"
        exit 1
    fi
    
    log_success "Prerrequisitos verificados"
}

# Configurar variables de entorno
setup_environment() {
    log_info "Configurando variables de entorno..."
    
    # Crear archivo .env si no existe
    if [ ! -f .env ]; then
        log_warning "Archivo .env no encontrado. Creando template..."
        cat > .env << EOF
# Django
SECRET_KEY=tu-secret-key-aqui
DEBUG=False
ALLOWED_HOSTS=squid-app-5j4xm.ondigitalocean.app

# Base de Datos (se configurará automáticamente)
DJANGO_DB_URL=postgresql://usuario:password@host:port/database

# Redis/Celery (se configurará automáticamente)
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
EOF
        log_warning "Archivo .env creado. Por favor, configura las variables necesarias."
    fi
    
    log_success "Variables de entorno configuradas"
}

# Crear base de datos PostgreSQL
create_database() {
    log_info "Creando base de datos PostgreSQL..."
    
    # Verificar si ya existe
    if doctl databases list | grep -q "combustible-db"; then
        log_warning "Base de datos ya existe"
    else
        doctl databases create combustible-db \
            --engine pg \
            --version 15 \
            --size db-s-dev-database \
            --region nyc3
        log_success "Base de datos PostgreSQL creada"
    fi
}

# Crear Redis
create_redis() {
    log_info "Creando Redis para Celery..."
    
    # Verificar si ya existe
    if doctl databases list | grep -q "combustible-redis"; then
        log_warning "Redis ya existe"
    else
        doctl databases create combustible-redis \
            --engine redis \
            --version 7 \
            --size db-s-dev-database \
            --region nyc3
        log_success "Redis creado"
    fi
}

# Crear Spaces bucket
create_spaces() {
    log_info "Creando bucket de Spaces..."
    
    BUCKET_NAME="combustible-files-$(date +%s)"
    
    # Crear bucket
    doctl spaces create $BUCKET_NAME --region nyc3
    
    log_success "Bucket de Spaces creado: $BUCKET_NAME"
    log_warning "Actualiza DO_SPACES_BUCKET_NAME en tu configuración con: $BUCKET_NAME"
}

# Desplegar aplicación
deploy_app() {
    log_info "Desplegando aplicación..."
    
    # Verificar si la app ya existe
    if doctl apps list | grep -q "combustible-app"; then
        log_warning "Aplicación ya existe. Actualizando..."
        doctl apps update $(doctl apps list --format ID --no-header | head -1) --spec .do/app.yaml
    else
        log_info "Creando nueva aplicación..."
        doctl apps create --spec .do/app.yaml
    fi
    
    log_success "Aplicación desplegada"
}

# Configurar dominio
setup_domain() {
    log_info "Configurando dominio..."
    
    read -p "¿Tienes un dominio personalizado? (y/n): " has_domain
    
    if [ "$has_domain" = "y" ]; then
        read -p "Ingresa tu dominio (ej: midominio.com): " domain
        
        # Agregar dominio a la app
        APP_ID=$(doctl apps list --format ID --no-header | head -1)
        doctl apps create-domain $APP_ID --domain $domain
        
        log_success "Dominio $domain configurado"
        log_warning "Configura los siguientes registros DNS:"
        echo "CNAME www tu-app.ondigitalocean.app"
        echo "CNAME @ tu-app.ondigitalocean.app"
    else
        log_info "Usando dominio por defecto de DigitalOcean"
    fi
}

# Verificar deployment
verify_deployment() {
    log_info "Verificando deployment..."
    
    # Obtener URL de la app
    APP_URL=$(doctl apps list --format "DefaultIngress" --no-header | head -1)
    
    if [ -n "$APP_URL" ]; then
        log_success "Aplicación disponible en: $APP_URL"
        
        # Verificar que responde
        if curl -s -o /dev/null -w "%{http_code}" "$APP_URL" | grep -q "200"; then
            log_success "Aplicación respondiendo correctamente"
        else
            log_warning "La aplicación puede estar iniciando. Espera unos minutos."
        fi
    else
        log_error "No se pudo obtener la URL de la aplicación"
    fi
}

# Mostrar información de configuración
show_config_info() {
    log_info "Información de configuración:"
    
    echo ""
    echo "📊 SERVICIOS CREADOS:"
    echo "• Web App: Django con Gunicorn"
    echo "• Worker: Celery para tareas asíncronas"
    echo "• Scheduler: Celery Beat para tareas programadas"
    echo "• Database: PostgreSQL"
    echo "• Cache: Redis"
    echo "• Storage: DigitalOcean Spaces"
    echo ""
    
    echo "🔧 PRÓXIMOS PASOS:"
    echo "1. Configura las variables de entorno en DigitalOcean App Platform"
    echo "2. Actualiza DO_SPACES_BUCKET_NAME con el bucket creado"
    echo "3. Configura WhatsApp Business API"
    echo "4. Configura SendGrid para emails"
    echo "5. Ejecuta migraciones: python manage.py migrate"
    echo "6. Crea superusuario: python manage.py createsuperuser"
    echo ""
    
    echo "📱 REPORTES AUTOMÁTICOS:"
    echo "• Reporte mensual: Día 1 de cada mes a las 9:00 AM"
    echo "• Verificación de mantenimientos: Diario a las 8:00 AM"
    echo "• Alertas de operadores inactivos: Semanal"
    echo "• Limpieza de archivos: Diario a las 2:00 AM"
    echo ""
    
    echo "🔍 MONITOREO:"
    echo "• Logs: DigitalOcean App Platform → Logs"
    echo "• Métricas: DigitalOcean App Platform → Metrics"
    echo "• Base de datos: DigitalOcean Databases"
    echo ""
}

# Función principal
main() {
    echo "🚛 Sistema de Gestión de Combustible - Deployment"
    echo "=================================================="
    echo ""
    
    check_prerequisites
    setup_environment
    
    echo ""
    read -p "¿Crear base de datos PostgreSQL? (y/n): " create_db
    if [ "$create_db" = "y" ]; then
        create_database
    fi
    
    echo ""
    read -p "¿Crear Redis para Celery? (y/n): " create_redis_choice
    if [ "$create_redis_choice" = "y" ]; then
        create_redis
    fi
    
    echo ""
    read -p "¿Crear bucket de Spaces? (y/n): " create_spaces_choice
    if [ "$create_spaces_choice" = "y" ]; then
        create_spaces
    fi
    
    echo ""
    read -p "¿Desplegar aplicación? (y/n): " deploy_choice
    if [ "$deploy_choice" = "y" ]; then
        deploy_app
        setup_domain
        verify_deployment
    fi
    
    show_config_info
    
    log_success "Deployment completado!"
    echo ""
    echo "Para más información, consulta: DIGITALOCEAN_SETUP.md"
}

# Ejecutar función principal
main "$@"
