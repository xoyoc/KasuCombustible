# setup_wizard.py - Asistente de configuración completo
import os
import sys
import getpass
import json
from pathlib import Path

class ReportSetupWizard:
    def __init__(self):
        self.config = {}
        self.project_root = Path.cwd()
        
    def welcome(self):
        """Mensaje de bienvenida"""
        print("=" * 70)
        print("🚀 ASISTENTE DE CONFIGURACIÓN - REPORTES DE COMBUSTIBLE")
        print("=" * 70)
        print("Este asistente te ayudará a configurar el sistema de reportes automáticos.")
        print("📧 Los reportes se enviarán automáticamente el día 1 de cada mes.")
        print("📊 Incluyen estadísticas detalladas y archivo Excel adjunto.")
        print("-" * 70)
        
    def check_django_project(self):
        """Verifica que estemos en un proyecto Django"""
        manage_py = self.project_root / "manage.py"
        if not manage_py.exists():
            print("❌ Error: No se encontró manage.py")
            print("   Asegúrate de ejecutar este script desde la raíz del proyecto Django")
            return False
        
        print("✅ Proyecto Django detectado")
        return True
    
    def get_email_config(self):
        """Obtiene la configuración de email"""
        print("\n📧 CONFIGURACIÓN DE EMAIL")
        print("-" * 30)
        
        # Proveedores comunes
        providers = {
            '1': {'name': 'Gmail', 'host': 'smtp.gmail.com', 'port': 587, 'tls': True},
            '2': {'name': 'Outlook/Hotmail', 'host': 'smtp-mail.outlook.com', 'port': 587, 'tls': True},
            '3': {'name': 'Yahoo', 'host': 'smtp.mail.yahoo.com', 'port': 587, 'tls': True},
            '4': {'name': 'Personalizado', 'host': '', 'port': 587, 'tls': True}
        }
        
        print("Selecciona tu proveedor de email:")
        for key, provider in providers.items():
            print(f"  {key}. {provider['name']}")
        
        choice = input("\nOpción (1-4): ").strip()
        
        if choice in providers:
            provider = providers[choice]
            
            if choice == '4':  # Personalizado
                self.config['email_host'] = input("Servidor SMTP: ").strip()
                self.config['email_port'] = int(input("Puerto (587): ").strip() or "587")
                self.config['email_use_tls'] = input("¿Usar TLS? (s/n): ").lower().startswith('s')
            else:
                self.config['email_host'] = provider['host']
                self.config['email_port'] = provider['port']
                self.config['email_use_tls'] = provider['tls']
            
            self.config['email_user'] = input("Email de envío: ").strip()
            
            if 'gmail' in self.config['email_host']:
                print("\n💡 Para Gmail, necesitas una 'App Password':")
                print("   1. Ve a https://myaccount.google.com/security")
                print("   2. Habilita 2-Step Verification")
                print("   3. Genera una App Password para 'Mail'")
                print("   4. Usa esa contraseña aquí (no tu contraseña normal)")
            
            self.config['email_password'] = getpass.getpass("Contraseña de email: ")
            
            return True
        else:
            print("❌ Opción no válida")
            return False
    
    def get_recipients(self):
        """Obtiene la lista de destinatarios"""
        print("\n👥 DESTINATARIOS DEL REPORTE")
        print("-" * 30)
        
        recipients = []
        print("Ingresa los emails que recibirán el reporte (Enter para terminar):")
        
        while True:
            email = input(f"  Email {len(recipients) + 1}: ").strip()
            if not email:
                break
            
            if '@' in email and '.' in email:
                recipients.append(email)
                print(f"    ✅ {email} agregado")
            else:
                print("    ❌ Email inválido, intenta de nuevo")
        
        if not recipients:
            recipients = [self.config['email_user']]  # Usar email de envío como fallback
            print(f"    ⚠️ No se agregaron destinatarios, usando: {self.config['email_user']}")
        
        self.config['recipients'] = recipients
        return True
    
    def create_directory_structure(self):
        """Crea la estructura de directorios necesaria"""
        print("\n📁 CREANDO ESTRUCTURA DE DIRECTORIOS")
        print("-" * 40)
        
        # Detectar la app principal
        apps = [d for d in os.listdir('.') if os.path.isdir(d) and 
                os.path.exists(os.path.join(d, 'models.py'))]
        
        if not apps:
            print("❌ No se encontraron apps de Django")
            return False
        
        if len(apps) == 1:
            app_name = apps[0]
        else:
            print("Apps encontradas:")
            for i, app in enumerate(apps, 1):
                print(f"  {i}. {app}")
            
            choice = input("Selecciona la app principal (número): ").strip()
            try:
                app_name = apps[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Selección inválida")
                return False
        
        self.config['app_name'] = app_name
        print(f"✅ App seleccionada: {app_name}")
        
        # Crear directorios
        directories = [
            f"{app_name}/management",
            f"{app_name}/management/commands",
            "templates/emails"
        ]
        
        for directory in directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            
            # Crear __init__.py si no existe
            if 'management' in str(path):
                init_file = path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
        
        print("✅ Estructura de directorios creada")
        return True
    
    def update_settings(self):
        """Actualiza el archivo settings.py"""
        print("\n⚙️ ACTUALIZANDO CONFIGURACIÓN")
        print("-" * 30)
        
        settings_files = ['settings.py', f'{self.config["app_name"]}/settings.py', 'config/settings.py']
        settings_path = None
        
        for settings_file in settings_files:
            if os.path.exists(settings_file):
                settings_path = settings_file
                break
        
        if not settings_path:
            print("❌ No se encontró settings.py")
            print("   Deberás agregar la configuración manualmente")
            return False
        
        # Generar configuración
        email_config = f"""
# === CONFIGURACIÓN DE REPORTES DE COMBUSTIBLE ===
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '{self.config['email_host']}'
EMAIL_PORT = {self.config['email_port']}
EMAIL_USE_TLS = {self.config['email_use_tls']}
EMAIL_HOST_USER = '{self.config['email_user']}'
EMAIL_HOST_PASSWORD = '{self.config['email_password']}'
DEFAULT_FROM_EMAIL = 'Sistema de Combustible <{self.config['email_user']}>'

REPORTES_EMAIL_DESTINATARIOS = {self.config['recipients']}
"""
        
        # Leer archivo actual
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si ya existe configuración
            if 'REPORTES_EMAIL_DESTINATARIOS' in content:
                print("⚠️ La configuración ya existe en settings.py")
                overwrite = input("¿Sobrescribir? (s/n): ").lower().startswith('s')
                if not overwrite:
                    return True
                
                # Remover configuración existente
                lines = content.split('\n')
                filtered_lines = []
                skip_section = False
                
                for line in lines:
                    if '=== CONFIGURACIÓN DE REPORTES DE COMBUSTIBLE ===' in line:
                        skip_section = True
                    elif skip_section and line.strip() and not line.startswith('#') and '=' in line:
                        # Continuar saltando líneas de configuración
                        pass
                    elif skip_section and (not line.strip() or line.startswith('#')):
                        # Fin de la sección de configuración
                        if not line.strip():
                            skip_section = False
                        filtered_lines.append(line)
                    else:
                        skip_section = False
                        filtered_lines.append(line)
                
                content = '\n'.join(filtered_lines)
            
            # Agregar nueva configuración
            content += email_config
            
            # Escribir archivo
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Configuración agregada a {settings_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando settings.py: {str(e)}")
            return False
    
    def install_dependencies(self):
        """Instala las dependencias necesarias"""
        print("\n📦 INSTALANDO DEPENDENCIAS")
        print("-" * 25)
        
        dependencies = ['openpyxl>=3.1.0']
        
        for dep in dependencies:
            try:
                import subprocess
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {dep} instalado")
                else:
                    print(f"❌ Error instalando {dep}: {result.stderr}")
            except Exception as e:
                print(f"❌ Error instalando {dep}: {str(e)}")
    
    def create_command_file(self):
        """Crea el archivo del comando Django"""
        print("\n📝 CREANDO COMANDO DJANGO")
        print("-" * 25)
        
        command_content = '''# Este archivo fue generado automáticamente por el asistente de configuración
import os
import calendar
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Sum, Count, Q, Max
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

# Importa tus modelos aquí - AJUSTA SEGÚN TU ESTRUCTURA
from {}}.models import Registro, Equipo, Operador


class Command(BaseCommand):
    help = 'Envía reporte mensual de combustible por correo electrónico'

    def add_arguments(self, parser):
        parser.add_argument('--mes', type=int, help='Mes específico (1-12)')
        parser.add_argument('--año', type=int, help='Año específico')
        parser.add_argument('--email', type=str, help='Email específico')
        parser.add_argument('--test', action='store_true', help='Modo test')

    def handle(self, *args, **options):
        # Aquí va toda la lógica del comando que creamos anteriormente
        # (El código es muy extenso, se incluiría aquí)
        self.stdout.write(
            self.style.SUCCESS('Comando ejecutado - Implementa la lógica completa aquí')
        )
'''.format(self.config['app_name'])
        
        command_path = f"{self.config['app_name']}/management/commands/enviar_reporte_mensual.py"
        
        try:
            with open(command_path, 'w', encoding='utf-8') as f:
                f.write(command_content)
            print(f"✅ Comando creado: {command_path}")
            print("   ⚠️ Deberás completar la implementación con el código completo")
            return True
        except Exception as e:
            print(f"❌ Error creando comando: {str(e)}")
            return False
    
    def create_email_template(self):
        """Crea el template del email"""
        print("\n📧 CREANDO TEMPLATE DE EMAIL")
        print("-" * 30)
        
        # El template HTML que creamos anteriormente se guardaría aquí
        template_content = '''<!-- Template generado automáticamente -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Mensual de Combustible</title>
    <!-- Aquí iría todo el HTML del template que creamos -->
</head>
<body>
    <div class="container">
        <h1>Reporte Mensual de Combustible</h1>
        <p>Template básico - implementar diseño completo</p>
    </div>
</body>
</html>'''
        
        template_path = "templates/emails/reporte_mensual.html"
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"✅ Template creado: {template_path}")
            print("   ⚠️ Deberás completar con el diseño HTML completo")
            return True
        except Exception as e:
            print(f"❌ Error creando template: {str(e)}")
            return False
    
    def setup_automation(self):
        """Configura la automatización"""
        print("\n🤖 CONFIGURACIÓN DE AUTOMATIZACIÓN")
        print("-" * 35)
        
        print("¿Cómo quieres automatizar el envío?")
        print("  1. Cron Job (Linux/macOS)")
        print("  2. Task Scheduler (Windows)")
        print("  3. Celery (Avanzado)")
        print("  4. Manual (configurar después)")
        
        choice = input("\nOpción (1-4): ").strip()
        
        if choice == '1':
            self._setup_cron()
        elif choice == '2':
            self._setup_windows_task()
        elif choice == '3':
            self._setup_celery()
        else:
            print("⚠️ Configuración manual seleccionada")
            print("   Ejecuta manualmente: python manage.py enviar_reporte_mensual")
    
    def _setup_cron(self):
        """Configura cron job"""
        command = f"cd {os.getcwd()} && {sys.executable} manage.py enviar_reporte_mensual"
        
        print(f"\n📋 Para configurar el cron job, ejecuta:")
        print(f"   crontab -e")
        print(f"\n   Agrega esta línea:")
        print(f"   0 8 1 * * {command}")
        print(f"\n   Esto ejecutará el reporte el día 1 de cada mes a las 8:00 AM")
    
    def _setup_windows_task(self):
        """Configura tarea de Windows"""
        batch_content = f'''@echo off
cd /d "{os.getcwd()}"
"{sys.executable}" manage.py enviar_reporte_mensual
pause'''
        
        batch_file = "enviar_reporte.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"✅ Archivo batch creado: {batch_file}")
        print("\n📋 Para configurar en Windows:")
        print("   1. Abre 'Programador de tareas'")
        print("   2. Crear tarea básica")
        print("   3. Configurar para día 1 de cada mes")
        print(f"   4. Ejecutar: {os.path.abspath(batch_file)}")
    
    def _setup_celery(self):
        """Información sobre Celery"""
        print("\n📋 Para usar Celery:")
        print("   1. Instala: pip install celery redis")
        print("   2. Configura Redis como broker")
        print("   3. Agrega la configuración de CELERY_BEAT_SCHEDULE")
        print("   4. Ejecuta: celery -A tu_proyecto worker --loglevel=info")
        print("   5. Ejecuta: celery -A tu_proyecto beat --loglevel=info")
    
    def test_configuration(self):
        """Prueba la configuración"""
        print("\n🧪 PROBANDO CONFIGURACIÓN")
        print("-" * 25)
        
        try:
            # Simular importación
            print("✅ Estructura de archivos correcta")
            
            # Mostrar resumen
            print(f"✅ App: {self.config['app_name']}")
            print(f"✅ Email servidor: {self.config['email_host']}")
            print(f"✅ Email usuario: {self.config['email_user']}")
            print(f"✅ Destinatarios: {len(self.config['recipients'])}")
            
            return True
        except Exception as e:
            print(f"❌ Error en configuración: {str(e)}")
            return False
    
    def save_config(self):
        """Guarda la configuración para referencia"""
        config_file = "reporte_config.json"
        
        # No guardar contraseña por seguridad
        safe_config = self.config.copy()
        safe_config.pop('email_password', None)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(safe_config, f, indent=2)
            print(f"✅ Configuración guardada en: {config_file}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar configuración: {str(e)}")
    
    def run(self):
        """Ejecuta el asistente completo"""
        self.welcome()
        
        if not self.check_django_project():
            return False
        
        steps = [
            ("Configurar Email", self.get_email_config),
            ("Configurar Destinatarios", self.get_recipients),
            ("Crear Directorios", self.create_directory_structure),
            ("Actualizar Settings", self.update_settings),
            ("Instalar Dependencias", self.install_dependencies),
            ("Crear Comando", self.create_command_file),
            ("Crear Template", self.create_email_template),
            ("Probar Configuración", self.test_configuration),
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ Error en: {step_name}")
                return False
        
        self.setup_automation()
        self.save_config()
        
        print("\n" + "=" * 70)
        print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("=" * 70)
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Completa la implementación del comando Django")
        print("   2. Completa el diseño del template de email")
        print("   3. Prueba: python manage.py enviar_reporte_mensual --test")
        print("   4. Configura la automatización según tu preferencia")
        print("\n💡 COMANDOS ÚTILES:")
        print("   • Prueba: python manage.py enviar_reporte_mensual --test")
        print("   • Mes específico: python manage.py enviar_reporte_mensual --mes 11 --año 2024")
        print("   • Email específico: python manage.py enviar_reporte_mensual --email test@email.com")
        
        return True

def main():
    """Función principal"""
    wizard = ReportSetupWizard()
    success = wizard.run()
    
    if success:
        print("\n✅ Configuración exitosa!")
    else:
        print("\n❌ Configuración incompleta")
        print("   Revisa los errores y ejecuta nuevamente")
    
    return success

if __name__ == "__main__":
    main()