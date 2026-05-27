# management/commands/send_whatsapp_test.py
from django.core.management.base import BaseCommand
from whatsaap_service import WhatsAppBusinessService
from registros.models import WhatsAppContact

class Command(BaseCommand):
    help = 'Envía mensaje de prueba por WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument('--number', type=str, help='Número específico')
        parser.add_argument('--all', action='store_true', help='Enviar a todos los contactos activos')

    def handle(self, *args, **options):
        service = WhatsAppBusinessService()
        
        if options['number']:
            # Enviar a número específico
            result = service.send_text_message(
                options['number'],
                "🤖 Mensaje de prueba del Sistema de Combustible\n\n✅ WhatsApp Business API funcionando correctamente"
            )
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f'✅ Mensaje enviado a {options["number"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {result["error"]}'))
        
        elif options['all']:
            # Enviar a todos los contactos activos
            contacts = WhatsAppContact.objects.filter(active=True)
            sent_count = 0
            
            for contact in contacts:
                result = service.send_text_message(
                    contact.phone_number,
                    f"🤖 Mensaje de prueba para {contact.name}\n\nSistema de Combustible funcionando ✅"
                )
                
                if result['success']:
                    sent_count += 1
                    self.stdout.write(f'✅ Enviado a {contact.name}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Error enviando a {contact.name}'))
            
            self.stdout.write(self.style.SUCCESS(f'📱 Total enviados: {sent_count}/{contacts.count()}'))
        
        else:
            self.stdout.write(self.style.ERROR('❌ Especifica --number o --all'))
