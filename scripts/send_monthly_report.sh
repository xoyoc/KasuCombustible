#!/bin/bash
# scripts/send_monthly_report.sh - Script para envío automático de reportes

# Configuración
PROJECT_DIR="/Users/xoyoc/Developer/LogincoCobustible"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="/var/log/combustible_reports.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para logging
log_message() {
    echo -e "$1"
    echo "[$DATE] $1" >> "$LOG_FILE"
}

# Verificar si es día de reporte mensual
check_report_day() {
    local day=$(date +%d)
    if [ "$day" = "01" ]; then
        return 0  # Es día de reporte
    else
        return 1  # No es día de reporte
    fi
}

# Función principal
main() {
    log_message "${BLUE}🚀 Iniciando verificación de reporte mensual...${NC}"
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_DIR" || {
        log_message "${RED}❌ Error: No se pudo acceder al directorio del proyecto${NC}"
        exit 1
    }
    
    # Activar entorno virtual si existe
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        log_message "${GREEN}✅ Entorno virtual activado${NC}"
    else
        log_message "${YELLOW}⚠️  Entorno virtual no encontrado, usando Python del sistema${NC}"
    fi
    
    # Configurar variables de entorno
    export DJANGO_SETTINGS_MODULE=combustible.settings
    export PYTHONPATH="$PROJECT_DIR"
    
    # Verificar si es día de reporte
    if check_report_day; then
        log_message "${GREEN}📅 Es día de reporte mensual!${NC}"
        
        # Ejecutar reporte mensual
        log_message "${BLUE}📊 Enviando reporte mensual...${NC}"
        
        if python manage.py enviar_reporte_mensual --send-email --send-whatsapp; then
            log_message "${GREEN}✅ Reporte mensual enviado exitosamente${NC}"
            
            # Verificar contactos de WhatsApp
            log_message "${BLUE}📱 Verificando contactos de WhatsApp...${NC}"
            python manage.py manage_whatsapp_contacts --list
            
            # Verificar mantenimientos
            log_message "${BLUE}🔧 Verificando mantenimientos...${NC}"
            python manage.py verificar_mantenimientos
            
        else
            log_message "${RED}❌ Error enviando reporte mensual${NC}"
            exit 1
        fi
        
    else
        day=$(date +%d)
        log_message "${YELLOW}⏰ No es día de reporte. Hoy es día $day${NC}"
        
        # Ejecutar verificaciones diarias
        log_message "${BLUE}🔧 Ejecutando verificaciones diarias...${NC}"
        
        # Verificar mantenimientos
        if python manage.py verificar_mantenimientos; then
            log_message "${GREEN}✅ Verificación de mantenimientos completada${NC}"
        else
            log_message "${RED}❌ Error en verificación de mantenimientos${NC}"
        fi
        
        # Limpiar archivos temporales (solo los domingos)
        if [ "$(date +%u)" = "7" ]; then
            log_message "${BLUE}🗑️  Limpiando archivos temporales...${NC}"
            python manage.py cleanup_old_files --days=180
        fi
    fi
    
    log_message "${GREEN}🎉 Proceso completado exitosamente${NC}"
}

# Función de ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help     Mostrar esta ayuda"
    echo "  -t, --test     Ejecutar en modo test"
    echo "  -f, --force    Forzar envío aunque no sea día 1"
    echo "  -v, --verbose  Mostrar output detallado"
    echo ""
    echo "Ejemplos:"
    echo "  $0              # Ejecución normal"
    echo "  $0 --test       # Modo test"
    echo "  $0 --force      # Forzar envío"
}

# Procesar argumentos
TEST_MODE=false
FORCE_MODE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test)
            TEST_MODE=true
            shift
            ;;
        -f|--force)
            FORCE_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Configurar verbose si se solicita
if [ "$VERBOSE" = true ]; then
    set -x
fi

# Modificar función principal para modo test
if [ "$TEST_MODE" = true ]; then
    log_message "${YELLOW}🧪 Ejecutando en modo TEST${NC}"
    # Sobrescribir función de verificación para siempre ejecutar
    check_report_day() {
        return 0
    }
    # Agregar flag --test al comando
    python manage.py enviar_reporte_mensual --test
    exit 0
fi

# Modificar función principal para modo force
if [ "$FORCE_MODE" = true ]; then
    log_message "${YELLOW}⚡ Ejecutando en modo FORCE${NC}"
    # Sobrescribir función de verificación para siempre ejecutar
    check_report_day() {
        return 0
    }
fi

# Ejecutar función principal
main

# Código de salida
if [ $? -eq 0 ]; then
    exit 0
else
    log_message "${RED}❌ El script terminó con errores${NC}"
    exit 1
fi
