#!/bin/bash
# scripts/generate_secrets.sh - Generador de secrets para GitHub Actions

echo "🔐 Generador de Secrets para GitHub Actions"
echo "============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para generar secret
generate_secret() {
    local name=$1
    local description=$2
    local example=$3
    
    echo -e "${BLUE}📋 $name${NC}"
    echo -e "${YELLOW}Descripción:${NC} $description"
    echo -e "${YELLOW}Ejemplo:${NC} $example"
    echo ""
}

echo -e "${GREEN}🔑 SECRETS DE DJANGO${NC}"
echo "=================="
generate_secret "SECRET_KEY" "Clave secreta de Django" "django-insecure-$(openssl rand -hex 32)"
generate_secret "DEBUG" "Modo debug (producción)" "False"
generate_secret "ALLOWED_HOSTS" "Hosts permitidos" "squid-app-5j4xm.ondigitalocean.app,tu-dominio.com"

echo ""
echo -e "${GREEN}🗄️ SECRETS DE BASE DE DATOS${NC}"
echo "=========================="
generate_secret "DJANGO_DB_URL" "URL de conexión PostgreSQL" "postgresql://usuario:password@host:port/database"

echo ""
echo -e "${GREEN}☁️ SECRETS DE DIGITALOCEAN SPACES${NC}"
echo "=================================="
generate_secret "DO_SPACES_ACCESS_KEY" "Access Key de Spaces" "DO00ABC123DEF456GHI789"
generate_secret "DO_SPACES_SECRET_KEY" "Secret Key de Spaces" "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890"
generate_secret "DO_SPACES_BUCKET_NAME" "Nombre del bucket" "combustible-files-prod"
generate_secret "DO_SPACES_ENDPOINT_URL" "URL del endpoint" "https://nyc3.digitaloceanspaces.com"
generate_secret "DO_SPACES_REGION" "Región del bucket" "nyc3"

echo ""
echo -e "${GREEN}📱 SECRETS DE WHATSAPP${NC}"
echo "======================"
generate_secret "WHATSAPP_PHONE_NUMBER_ID" "ID del número de WhatsApp" "123456789012345"
generate_secret "WHATSAPP_ACCESS_TOKEN" "Token de acceso WhatsApp" "EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
generate_secret "WHATSAPP_VERIFY_TOKEN" "Token de verificación" "mi_token_verificacion_123"

echo ""
echo -e "${GREEN}📧 SECRETS DE EMAIL${NC}"
echo "=================="
generate_secret "EMAIL_HOST_PASSWORD" "API Key de SendGrid" "SG.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890.xyz123abc456def789ghi012jkl345mno678pqr901stu234vwx567yz890"

echo ""
echo -e "${YELLOW}📝 INSTRUCCIONES PARA CONFIGURAR:${NC}"
echo "=================================="
echo "1. Ve a tu repositorio en GitHub"
echo "2. Settings → Secrets and variables → Actions"
echo "3. Haz clic en 'New repository secret'"
echo "4. Agrega cada secret con su nombre y valor"
echo "5. Guarda cada secret"
echo ""
echo -e "${BLUE}💡 TIP:${NC} Puedes copiar y pegar los nombres exactos de arriba"
echo ""

# Generar SECRET_KEY automáticamente
echo -e "${GREEN}🎲 GENERANDO SECRET_KEY AUTOMÁTICAMENTE:${NC}"
echo "=========================================="
SECRET_KEY=$(python3 -c "import secrets; print('django-insecure-' + secrets.token_urlsafe(50))")
echo "SECRET_KEY: $SECRET_KEY"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC} Copia este SECRET_KEY y úsalo en GitHub Secrets"
echo ""

# Verificar si tienes doctl instalado para obtener info de DigitalOcean
if command -v doctl &> /dev/null; then
    echo -e "${GREEN}🔍 INFORMACIÓN DE DIGITALOCEAN:${NC}"
    echo "==============================="
    
    # Obtener información de bases de datos
    echo "📊 Bases de datos disponibles:"
    doctl databases list --format "Name,Engine,Status" 2>/dev/null || echo "No se pudo obtener información de bases de datos"
    
    echo ""
    echo "☁️ Spaces disponibles:"
    doctl spaces list 2>/dev/null || echo "No se pudo obtener información de Spaces"
    
else
    echo -e "${YELLOW}💡 TIP:${NC} Instala 'doctl' para obtener información automática de DigitalOcean"
    echo "curl -sL https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz | tar -xzv"
fi

echo ""
echo -e "${GREEN}✅ Script completado${NC}"
echo "Ahora puedes configurar los secrets en GitHub Actions"
