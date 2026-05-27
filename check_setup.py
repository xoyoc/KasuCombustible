import sys
import importlib
import smtplib
from email.mime.text import MIMEText

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    dependencies = ['openpyxl', 'django']
    missing = []
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep} - Instalado")
        except ImportError:
            print(f"❌ {dep} - NO instalado")
            missing.append(dep)
    
    return len(missing) == 0

def check_email_config():
    """Verifica la configuración de email"""
    try:
        from django.conf import settings
        
        required_settings = [
            'EMAIL_HOST',
            'EMAIL_PORT',
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD',
            'REPORTES_EMAIL_DESTINATARIOS'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"❌ Configuraciones faltantes: {', '.join(missing_settings)}")
            return False
        else:
            print("✅ Configuración de email completa")
            return True
            
    except ImportError:
        print("❌ No se puede importar Django settings")
        return False

def test_email_connection():
    """Prueba la conexión de email"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        send_mail(
            'Prueba de Configuración',
            'Si recibes este email, la configuración es correcta.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.REPORTES_EMAIL_DESTINATARIOS[0]],
            fail_silently=False,
        )
        print("✅ Email de prueba enviado")
        return True
    except Exception as e:
        print(f"❌ Error enviando email de prueba: {str(e)}")
        return False

def main():
    """Función principal de verificación"""
    print("🔍 Verificando configuración del sistema de reportes...\n")
    
    deps_ok = check_dependencies()
    email_config_ok = check_email_config()
    
    if deps_ok and email_config_ok:
        print("\n📧 Probando conexión de email...")
        email_test_ok = test_email_connection()
        
        if email_test_ok:
            print("\n🎉 ¡Configuración completa y funcionando!")
            print("\n📋 Próximos pasos:")
            print("1. Ejecutar: python manage.py enviar_reporte_mensual --test")
            print("2. Si funciona, configurar automatización (cron/task scheduler)")
            print("3. El reporte se enviará automáticamente el día 1 de cada mes")
        else:
            print("\n⚠️ Configuración incompleta - revisar configuración de email")
    else:
        print("\n❌ Configuración incompleta - revisar dependencias y settings")

if __name__ == "__main__":
    main()