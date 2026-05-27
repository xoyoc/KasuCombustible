# setup_whatsapp.py - Asistente completo de configuración WhatsApp Business
import os
import sys
import json
import requests
from pathlib import Path

class WhatsAppSetupWizard:
    def __init__(self):
        self.config = {}
        self.project_root = Path.cwd()
        
    def welcome(self):
        """Mensaje de bienvenida"""
        print("=" * 70)
        print("📱 CONFIGURADOR DE WHATSAPP BUSINESS API")
        print("=" * 70)
        print("Este asistente configurará WhatsApp Business para enviar:")
        print("📊 Reportes mensuales automáticos")
        print("⚠️ Alertas de operadores inactivos") 
        print("🏆 Estadísticas de equipos top")
        print("💰 Análisis de costos")
        print("📋 Archivos Excel por WhatsApp")
        print("-" * 70)
        print("\n📋 REQUISITOS PREVIOS:")
        print("1. Cuenta de Meta Business (Facebook)")
        print("2. Número de teléfono verificado")
        print("3. WhatsApp Business API configurada")
        print("4. Access token permanente")
        print("-" * 70)

    def check_prerequisites(self):
        """Verifica los requisitos previos"""
        print("\n✅ VERIFICACIÓN DE REQUISITOS")
        print("-" * 30)
        
        requirements = [
            "¿Tienes una cuenta de Meta Business? (s/n): ",
            "¿Tu número de WhatsApp está verificado en Meta? (s/n): ",
            "¿Has configurado WhatsApp Business API? (s/n): ",
            "¿Tienes un Access Token permanente? (s/n): "
        ]
        
        for req in requirements:
            response = input(req).lower()
            if not response.startswith('s'):
                print("❌ Requisito no cumplido")
                print("\n📖 GUÍA DE CONFIGURACIÓN:")
                print("1. Ve a: https://business.facebook.com/")
                print("2. Configura WhatsApp Business API")
                print("3. Verifica tu número de teléfono")
                print("4. Genera un Access Token permanente")
                print("5. Ejecuta este script nuevamente")
                return False
        
        print("✅ Todos los requisitos cumplidos")
        return True

    def get_whatsapp_credentials(self):
        """Obtiene las credenciales de WhatsApp Business API"""
        print("\n🔑 CREDENCIALES DE WHATSAPP BUSINESS API")
        print("-" * 45)
        print("Necesitas esta información de tu cuenta de Meta Business:")
        print("1. Phone Number ID (de WhatsApp Business API)")
        print("2. Access Token (permanente, no temporal)")
        print("3. Webhook Verify Token (lo defines tú)")
        
        self.config['phone_number_id'] = input("\nPhone Number ID: ").strip()
        self.config['access_token'] = input("Access Token: ").strip()
        self.config['verify_token'] = input("Webhook Verify Token (ej: mi_token_secreto): ").strip()
        
        if not all([
            self.config['phone_number_id'], 
            self.config['access_token'], 
            self.config['verify_token']
        ]):
            print("❌ Todas las credenciales son obligatorias")
            return False
        
        return True

    def test_whatsapp_api(self):
        """Prueba las credenciales de WhatsApp API"""
        print("\n🔍 PROBANDO CREDENCIALES...")
        print("-" * 30)
        
        try:
            # Probar con una consulta básica a la API
            url = f"https://graph.facebook.com/v18.0/{self.config['phone_number_id']}"
            headers = {
                'Authorization': f"Bearer {self.config['access_token']}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Credenciales válidas")
                print(f"📱 Número verificado: {data.get('display_phone_number', 'N/A')}")
                print(f"🏢 Nombre de negocio: {data.get('name', 'N/A')}")
                return True
            else:
                print(f"❌ Error de API: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

    def configure_webhook(self):
        """Configura información del webhook"""
        print("\n🔗 CONFIGURACIÓN DE WEBHOOK")
        print("-" * 30)
        print("El webhook permite que WhatsApp envíe notificaciones a tu aplicación.")
        
        # Obtener dominio base
        domain = input("Dominio de tu aplicación (ej: https://mi-app.com): ").strip()
        if not domain.startswith('http'):
            domain = 'https://' + domain
        
        self.config['webhook_url'] = f"{domain}/webhook/whatsapp/"
        self.config['domain'] = domain
        
        print(f"📍 URL del webhook: {self.config['webhook_url']}")
        print("\n⚠️ IMPORTANTE:")
        print(f"   1. Configura esta URL en Meta Business:")
        print(f"      {self.config['webhook_url']}")
        print(f"   2. Usa este Verify Token: {self.config['verify_token']}")
        print(f"   3. Suscríbete a: messages, message_deliveries")
        
        return True

    def get_contact_configuration(self):
        """Configura los contactos que recibirán reportes"""
        print("\n👥 CONFIGURACIÓN DE CONTACTOS")
        print("-" * 35)
        
        contacts = []
        print("Agrega contactos que recibirán reportes por WhatsApp:")
        print("(Formato: +52XXXXXXXXXX para México)")
        
        while True:
            print(f"\nContacto {len(contacts) + 1}:")
            name = input("  Nombre (Enter para terminar): ").strip()
            if not name:
                break
            
            number = input("  Número WhatsApp (+52XXXXXXXXXX): ").strip()
            if not number:
                continue
            
            # Limpiar número
            clean_number = ''.join(filter(str.isdigit, number))
            if len(clean_number) == 10:
                clean_number = '52' + clean_number
            elif not clean_number.startswith('52'):
                clean_number = '52' + clean_number[-10:]
            
            role_options = {
                '1': 'manager',
                '2': 'supervisor', 
                '3': 'admin',
                '4': 'operator'
            }
            
            print("  Rol:")
            for key, role in role_options.items():
                print(f"    {key}. {role.title()}")
            
            role_choice = input("  Selecciona rol (1-4): ").strip()
            role = role_options.get(role_choice, 'operator')
            
            receive_reports = input("  ¿Recibir reportes mensuales? (s/n): ").lower().startswith('s')
            receive_alerts = input("  ¿Recibir alertas? (s/n): ").lower().startswith('s')
            
            contacts.append({
                'name': name,
                'number': f"+{clean_number}",
                'role': role,
                'receive_reports': receive_reports,
                'receive_alerts': receive_alerts
            })
            
            print(f"  ✅ {name} agregado")
        
        self.config['contacts'] = contacts
        
        if not contacts:
            print("⚠️ No se agregaron contactos")
            print("   Podrás agregar contactos después usando el admin de Django")
        
        return True

    def send_test_message(self):
        """Envía mensaje de prueba a los contactos"""
        if not self.config.get('contacts'):
            print("⚠️ No hay contactos para probar")
            return True
        
        test = input("\n¿Enviar mensaje de prueba a los contactos? (s/n): ").lower().startswith('s')
        if not test:
            return True
        
        print("\n📤 ENVIANDO MENSAJES DE PRUEBA...")
        print("-" * 40)
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.config['phone_number_id']}/messages"
            headers = {
                'Authorization': f"Bearer {self.config['access_token']}",
                'Content-Type': 'application/json'
            }
            
            sent_count = 0
            for contact in self.config['contacts']:
                # Mensaje de prueba personalizado
                message = f"🤖 *Mensaje de Prueba*\n\nHola {contact['name']}, el Sistema de Combustible está configurado correctamente ✅\n\nRecibirás:\n"
                
                if contact['receive_reports']:
                    message += "📊 Reportes mensuales\n"
                if contact['receive_alerts']:
                    message += "⚠️ Alertas importantes\n"
                
                message += "\n¡Sistema listo para funcionar!"
                
                payload = {
                    "messaging_product": "whatsapp",
                    "to": contact['number'].replace('+', ''),
                    "type": "text",
                    "text": {"body": message}
                }
                
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    sent_count += 1
                    print(f"   ✅ Enviado a {contact['name']} ({contact['number']})")
                else:
                    print(f"   ❌ Error enviando a {contact['name']}: {response.text}")
            
            print(f"\n📱 Mensajes enviados: {sent_count}/{len(self.config['contacts'])}")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensajes de prueba: {e}")
            return False

    def update_env_file(self):
        """Actualiza el archivo .env"""
        print("\n📝 ACTUALIZANDO ARCHIVO .ENV")
        print("-" * 30)
        
        env_file = self.project_root / '.env'
        env_content = []
        
        # Leer archivo existente
        if env_file.exists():
            with open(env_file, 'r') as f:
                existing_lines = f.readlines()
            
            # Filtrar líneas de WhatsApp existentes
            whatsapp_keys = [
                'WHATSAPP_PHONE_NUMBER_ID', 'WHATSAPP_ACCESS_TOKEN', 
                'WHATSAPP_VERIFY_TOKEN', 'WHATSAPP_WEBHOOK_URL'
            ]
            
            for line in existing_lines:
                if not any(key in line for key in whatsapp_keys):
                    env_content.append(line.strip())
        
        # Agregar configuración de WhatsApp
        env_content.extend([
            "",
            "# === WHATSAPP BUSINESS API CONFIGURATION ===",
            f"WHATSAPP_PHONE_NUMBER_ID={self.config['phone_number_id']}",
            f"WHATSAPP_ACCESS_TOKEN={self.config['access_token']}",
            f"WHATSAPP_VERIFY_TOKEN={self.config['verify_token']}",
            f"WHATSAPP_WEBHOOK_URL={self.config['webhook_url']}",
        ])
        
        # Escribir archivo
        with open(env_file, 'w') as f:
            f.write('\n'.join(env_content))
        
        print(f"✅ Archivo .env actualizado")
        return True

    def create_contacts_in_db(self):
        """Crea los contactos en la base de datos"""
        print("\n👥 CREANDO CONTACTOS EN BASE DE DATOS")
        print("-" * 40)
        
        if not self.config.get('contacts'):
            print("⚠️ No hay contactos para crear")
            return True
        
        # Generar script de migración
        migration_script = f"""
# Script para crear contactos de WhatsApp
# Ejecutar con: python manage.py shell < create_whatsapp_contacts.py

from tu_app.models import WhatsAppContact

print("📱 Creando contactos de WhatsApp...")

contacts_data = {json.dumps(self.config['contacts'], indent=2)}

created_count = 0
for contact_data in contacts_data:
    contact, created = WhatsAppContact.objects.get_or_create(
        phone_number=contact_data['number'],
        defaults={{
            'name': contact_data['name'],
            'role': contact_data['role'],
            'receive_monthly_reports': contact_data['receive_reports'],
            'receive_alerts': contact_data['receive_alerts'],
            'active': True
        }}
    )
    
    if created:
        created_count += 1
        print(f"✅ Creado: {{contact.name}} ({{contact.phone_number}})")
    else:
        print(f"⚠️ Ya existe: {{contact.name}} ({{contact.phone_number}})")

print(f"\\n📊 Total contactos creados: {{created_count}}")
"""
        
        script_file = self.project_root / 'create_whatsapp_contacts.py'
        with open(script_file, 'w') as f:
            f.write(migration_script)
        
        print(f"✅ Script creado: {script_file}")
        print("📋 Para crear los contactos, ejecuta:")
        print(f"   python manage.py shell < {script_file}")
        
        return True

    def update_settings(self):
        """Actualiza settings.py con configuración de WhatsApp"""
        print("\n⚙️ ACTUALIZANDO SETTINGS.PY")
        print("-" * 30)
        
        # Buscar archivo settings.py
        settings_files = ['settings.py', 'config/settings.py']
        settings_path = None
        
        for settings_file in settings_files:
            if os.path.exists(settings_file):
                settings_path = settings_file
                break
        
        if not settings_path:
            print("❌ No se encontró settings.py")
            return False
        
        # Configuración a agregar
        whatsapp_config = '''
# === WHATSAPP BUSINESS API CONFIGURATION ===
from decouple import config

# Credenciales de WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID = config('WHATSAPP_PHONE_NUMBER_ID', default='')
WHATSAPP_ACCESS_TOKEN = config('WHATSAPP_ACCESS_TOKEN', default='')
WHATSAPP_VERIFY_TOKEN = config('WHATSAPP_VERIFY_TOKEN', default='whatsapp_webhook_verify')

# Configuración de webhook
WHATSAPP_WEBHOOK_URL = config('WHATSAPP_WEBHOOK_URL', default='/webhook/whatsapp/')

# Configuración de plantillas
WHATSAPP_TEMPLATES = {
    'monthly_report': 'monthly_report_notification',
    'inactive_alert': 'inactive_operators_alert',
}

# Límites de envío
WHATSAPP_DAILY_LIMIT = 1000  # Mensajes por día
WHATSAPP_RATE_LIMIT = 20     # Mensajes por minuto

# Logging para WhatsApp
if 'LOGGING' in locals():
    LOGGING['loggers']['whatsapp'] = {
        'handlers': ['file', 'console'],
        'level': 'INFO',
        'propagate': True,
    }
'''
        
        try:
            # Leer archivo actual
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si ya existe configuración
            if 'WHATSAPP BUSINESS API CONFIGURATION' in content:
                print("⚠️ La configuración de WhatsApp ya existe")
                overwrite = input("¿Sobrescribir? (s/n): ").lower().startswith('s')
                if not overwrite:
                    return True
                
                # Eliminar configuración anterior
                lines = content.split('\n')
                filtered_lines = []
                skip_section = False
                
                for line in lines:
                    if '=== WHATSAPP BUSINESS API CONFIGURATION ===' in line:
                        skip_section = True
                        continue
                    elif skip_section and (not line.strip() or line.startswith('#') or '=' in line):
                        continue
                    else:
                        skip_section = False
                        filtered_lines.append(line)
                
                content = '\n'.join(filtered_lines)
            
            # Agregar nueva configuración
            content += whatsapp_config
            
            # Escribir archivo
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Settings.py actualizado")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando settings.py: {e}")
            return False

    def create_deployment_guide(self):
        """Crea guía de despliegue y uso"""
        print("\n📖 CREANDO GUÍA DE DESPLIEGUE")
        print("-" * 30)
        
        guide_content = f'''# GUÍA DE WHATSAPP BUSINESS API - SISTEMA DE COMBUSTIBLE

## 🎉 Configuración Completada

### Credenciales Configuradas:
- Phone Number ID: {self.config['phone_number_id']}
- Access Token: {self.config['access_token'][:10]}...
- Webhook URL: {self.config['webhook_url']}
- Verify Token: {self.config['verify_token']}

### Contactos Configurados:
{len(self.config.get('contacts', []))} contactos agregados para recibir reportes

## 📋 Próximos Pasos

### 1. Configurar Webhook en Meta Business
```
1. Ve a: https://developers.facebook.com/apps/
2. Selecciona tu app de WhatsApp Business
3. Ve a: WhatsApp > Configuration
4. Webhook URL: {self.config['webhook_url']}
5. Verify Token: {self.config['verify_token']}
6. Suscripciones: messages, message_deliveries, message_statuses
```

### 2. Crear Contactos en Django
```bash
python manage.py shell < create_whatsapp_contacts.py
```

### 3. Probar Configuración
```bash
# Probar conexión básica
python manage.py send_whatsapp_test --number +5215512345678

# Probar con todos los contactos
python manage.py send_whatsapp_test --all

# Sincronizar con operadores existentes
python manage.py sync_whatsapp_contacts
```

### 4. Enviar Reporte de Prueba
```bash
# Solo por WhatsApp
python manage.py enviar_reporte_mensual --test --whatsapp-only

# Por email y WhatsApp
python manage.py enviar_reporte_mensual --test --send-whatsapp
```

## 🚀 Funcionalidades Implementadas

### 📊 Reportes Automáticos
✅ **Resumen Ejecutivo**: Estadísticas principales del mes
✅ **Archivo Excel**: Documento completo por WhatsApp  
✅ **Top Equipos**: Ranking de vehículos más activos
✅ **Análisis de Costos**: Desglose detallado de gastos
✅ **Mensajes Interactivos**: Botones para más información

### ⚠️ Alertas Inteligentes
✅ **Operadores Inactivos**: Notificación automática
✅ **Equipos sin Uso**: Alertas de vehículos sin actividad
✅ **Gastos Elevados**: Notificaciones de consumo alto
✅ **Respuestas Automáticas**: Bot básico para consultas

### 📱 Gestión de Contactos
✅ **Contactos por Rol**: Manager, Supervisor, Operador, Admin
✅ **Preferencias Personalizadas**: Reportes, alertas, resúmenes
✅ **Sincronización**: Integración con operadores del sistema
✅ **Estado de Mensajes**: Tracking de entrega y lectura

## 🔧 Comandos Útiles

### Gestión de Contactos
```bash
# Listar contactos
python manage.py manage_whatsapp_contacts --list

# Agregar contacto
python manage.py manage_whatsapp_contacts --add "Juan Pérez,+5215512345678,manager"

# Habilitar reportes
python manage.py manage_whatsapp_contacts --enable-reports +5215512345678

# Enviar mensaje de prueba
python manage.py manage_whatsapp_contacts --test +5215512345678
```

### Reportes y Alertas
```bash
# Reporte mensual completo
python manage.py enviar_reporte_mensual --send-whatsapp

# Solo alertas de operadores inactivos
python manage.py enviar_reporte_mensual --whatsapp-only --mes 11

# Reporte a número específico
python manage.py enviar_reporte_mensual --whatsapp +5215512345678
```

### Mantenimiento
```bash
# Ver estadísticas de mensajes
python manage.py whatsapp_stats

# Limpiar logs antiguos
python manage.py cleanup_whatsapp_logs --days 30

# Verificar configuración
python manage.py check_whatsapp_config
```

## 🎯 Tipos de Mensajes Automáticos

### 1. Reporte Mensual (Día 1 de cada mes)
- 📊 Resumen ejecutivo con estadísticas principales
- 📄 Archivo Excel con datos completos
- 🏆 Top 5 equipos más activos
- 👥 Lista de operadores inactivos
- 💰 Análisis de costos y eficiencia

### 2. Alertas Inmediatas
- ⚠️ Operadores sin actividad por más de 7 días
- 🚨 Equipos con gastos anómalos
- 📈 Consumo por encima del promedio
- 🔧 Recordatorios de mantenimiento

### 3. Respuestas Automáticas
- 🤖 Comandos básicos (/reporte, /equipos, /ayuda)
- 📋 Consultas de estado
- 🔍 Búsqueda de información
- 📞 Escalación a administradores

## ⚙️ Configuración Avanzada

### Personalizar Mensajes
Edita los templates en `whatsapp_service.py`:
- `_generate_summary_message()`: Resumen del reporte
- `send_alert_inactive_operators()`: Alerta de operadores
- `send_cost_analysis()`: Análisis de costos

### Agregar Nuevos Tipos de Alerta
1. Crea función en `WhatsAppReportService`
2. Agrega lógica en el comando de reportes
3. Configura triggers en los modelos

### Webhooks Personalizados
Modifica `WhatsAppWebhookView` para:
- Procesar respuestas específicas
- Manejar botones interactivos
- Implementar conversaciones

## 🔒 Seguridad y Límites

### Límites de WhatsApp Business API
- **Mensajes por día**: 1,000 (configurable)
- **Mensajes por minuto**: 20 (configurable)
- **Tamaño de archivos**: 100MB máximo
- **Tipos de archivo**: PDF, Excel, imágenes

### Buenas Prácticas
- ✅ No enviar spam o mensajes no solicitados
- ✅ Respetar horarios comerciales
- ✅ Ofrecer opción de darse de baja
- ✅ Mantener mensajes relevantes y útiles

## 🆘 Solución de Problemas

### Error "Invalid Access Token"
- Verifica que el token sea permanente, no temporal
- Renueva el token en Meta Business
- Confirma permisos de WhatsApp Business API

### Mensajes No Se Entregan
- Verifica que los números estén en formato internacional
- Confirma que WhatsApp Business esté activo
- Revisa límites de envío diarios/por minuto

### Webhook No Funciona
- Verifica que la URL sea pública y accesible
- Confirma certificado SSL válido
- Revisa que el verify token coincida

### Contactos No Reciben Mensajes
- Confirma que `active=True` y `receive_monthly_reports=True`
- Verifica formato de número de teléfono
- Revisa logs de mensajes en Django Admin

## 📞 Soporte

- **Documentación WhatsApp**: https://developers.facebook.com/docs/whatsapp
- **Meta Business**: https://business.facebook.com/
- **Logs del Sistema**: Django Admin > WhatsApp Messages
- **Contacto Técnico**: admin@tuempresa.com

## 🔄 Automatización Completa

Con esta configuración, el sistema enviará automáticamente:

📅 **Día 1 de cada mes a las 8:00 AM**:
- Reporte mensual completo por WhatsApp
- Archivo Excel con todos los datos
- Alertas de operadores inactivos
- Análisis de equipos top

🔔 **Alertas en tiempo real**:
- Notificaciones de actividad anómala
- Recordatorios de mantenimiento
- Escalaciones automáticas

¡Tu sistema de combustible ahora incluye comunicación inteligente por WhatsApp! 🎉
'''
        
        with open('WHATSAPP_DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print("✅ Guía creada: WHATSAPP_DEPLOYMENT_GUIDE.md")
        return True

    def run(self):
        """Ejecuta el asistente completo"""
        self.welcome()
        
        if not self.check_prerequisites():
            return False
        
        steps = [
            ("Obtener Credenciales", self.get_whatsapp_credentials),
            ("Probar API", self.test_whatsapp_api),
            ("Configurar Webhook", self.configure_webhook),
            ("Configurar Contactos", self.get_contact_configuration),
            ("Enviar Pruebas", self.send_test_message),
            ("Actualizar .env", self.update_env_file),
            ("Actualizar Settings", self.update_settings),
            ("Crear Script de Contactos", self.create_contacts_in_db),
            ("Crear Guía", self.create_deployment_guide),
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ Error en: {step_name}")
                return False
        
        print("\n" + "=" * 70)
        print("🎉 ¡WHATSAPP BUSINESS API CONFIGURADO EXITOSAMENTE!")
        print("=" * 70)
        
        print(f"\n📋 RESUMEN DE CONFIGURACIÓN:")
        print(f"   • Phone Number ID: {self.config['phone_number_id']}")
        print(f"   • Webhook URL: {self.config['webhook_url']}")
        print(f"   • Contactos configurados: {len(self.config.get('contacts', []))}")
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("   1. Configura el webhook en Meta Business Manager")
        print("   2. python manage.py shell < create_whatsapp_contacts.py")
        print("   3. python manage.py send_whatsapp_test --all")
        print("   4. python manage.py enviar_reporte_mensual --test --whatsapp-only")
        print("   5. Lee: WHATSAPP_DEPLOYMENT_GUIDE.md")
        
        print(f"\n💡 COMANDOS ÚTILES:")
        print("   • python manage.py manage_whatsapp_contacts --list")
        print("   • python manage.py send_whatsapp_test --number +5215512345678")
        print("   • python manage.py enviar_reporte_mensual --whatsapp-only")
        
        print(f"\n🔗 ENLACES IMPORTANTES:")
        print("   • Meta Business: https://business.facebook.com/")
        print("   • WhatsApp API Docs: https://developers.facebook.com/docs/whatsapp")
        print("   • Webhook Config: https://developers.facebook.com/apps/")
        
        return True

def main():
    """Función principal"""
    wizard = WhatsAppSetupWizard()
    success = wizard.run()
    
    if success:
        print("\n✅ ¡Configuración exitosa!")
        print("📱 Tu sistema ahora enviará reportes por WhatsApp automáticamente")
    else:
        print("\n❌ Configuración incompleta")
        print("   Revisa los errores y ejecuta nuevamente")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Configuración cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

# === INSTRUCCIONES DE USO ===
"""
🚀 GUÍA RÁPIDA DE CONFIGURACIÓN:

1. **Ejecutar el asistente:**
   python setup_whatsapp.py

2. **Seguir los pasos del asistente:**
   - Verificar requisitos previos
   - Ingresar credenciales de Meta Business
   - Probar conexión a la API
   - Configurar webhook
   - Agregar contactos
   - Enviar mensajes de prueba

3. **Configurar webhook en Meta:**
   - Ve a developers.facebook.com
   - Configura la URL del webhook
   - Agrega el verify token
   - Suscríbete a eventos

4. **Crear contactos en Django:**
   python manage.py shell < create_whatsapp_contacts.py

5. **Probar funcionalidad:**
   python manage.py send_whatsapp_test --all

6. **Enviar primer reporte:**
   python manage.py enviar_reporte_mensual --test --whatsapp-only

🎯 BENEFICIOS DESPUÉS DE LA CONFIGURACIÓN:

✅ **Reportes Automáticos por WhatsApp**
   - Resúmenes ejecutivos cada mes
   - Archivos Excel enviados directamente
   - Alertas de operadores inactivos
   - Análisis de costos y eficiencia

✅ **Comunicación Inteligente**
   - Mensajes personalizados por rol
   - Botones interactivos para más info
   - Respuestas automáticas a consultas
   - Tracking de entrega y lectura

✅ **Gestión Centralizada**
   - Admin de Django para contactos
   - Logs de todos los mensajes
   - Estadísticas de uso
   - Configuración por rol y preferencias

✅ **Integración Perfecta**
   - Funciona con DigitalOcean Spaces
   - Se integra con sistema de reportes
   - Compatible con email simultáneo
   - Automatización completa

📱 EL SISTEMA AHORA ENVIARÁ AUTOMÁTICAMENTE:

• **Día 1 de cada mes**: Reporte completo con Excel
• **Alertas inmediatas**: Operadores inactivos, gastos altos
• **Respuestas automáticas**: Comandos básicos y ayuda
• **Notificaciones**: Estados de equipos y mantenimiento

¡Tu sistema de combustible ahora incluye WhatsApp Business! 🎉
"""