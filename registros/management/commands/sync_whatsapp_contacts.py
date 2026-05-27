from django.core.management.base import BaseCommand
from registros.models import WhatsAppContact, Operador
from django.conf import settings

class Command(BaseCommand):
    help = 'Sincroniza contactos de WhatsApp con operadores del sistema'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Sincronizando contactos de WhatsApp...")
        
        # Sincronizar operadores que tienen número de móvil
        operadores_con_movil = Operador.objects.exclude(movil__isnull=True).exclude(movil='')
        
        created_count = 0
        updated_count = 0
        
        for operador in operadores_con_movil:
            contact, created = WhatsAppContact.objects.get_or_create(
                phone_number=operador.movil,
                defaults={
                    'name': operador.nombre,
                    'role': 'operator',
                    'operador': operador,
                    'receive_monthly_reports': False,  # Los operadores no reciben reportes por defecto
                    'receive_alerts': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✅ Creado: {contact.name}')
            else:
                # Actualizar información si cambió
                if contact.name != operador.nombre:
                    contact.name = operador.nombre
                    contact.save()
                    updated_count += 1
                    self.stdout.write(f'🔄 Actualizado: {contact.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'📱 Sincronización completada: {created_count} creados, {updated_count} actualizados')
        )