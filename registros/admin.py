# admin.py - Administración de WhatsApp
from django.contrib import admin
from .models import Registro, WhatsAppContact, WhatsAppMessage, WhatsAppWebhookLog

@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'role', 'active', 'last_message_sent']
    list_filter = ['role', 'active', 'receive_monthly_reports', 'receive_alerts']
    search_fields = ['name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at', 'last_message_sent']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'phone_number', 'role', 'active')
        }),
        ('Preferencias', {
            'fields': ('receive_monthly_reports', 'receive_alerts', 'receive_summaries')
        }),
        ('Relaciones', {
            'fields': ('user', 'operador')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at', 'last_message_sent'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_test_message', 'activate_contacts', 'deactivate_contacts']
    
    def send_test_message(self, request, queryset):
        """Envía mensaje de prueba a contactos seleccionados"""
        from whatsaap_service import WhatsAppBusinessService
        service = WhatsAppBusinessService()
        
        sent_count = 0
        for contact in queryset:
            if contact.active:
                result = service.send_text_message(
                    contact.phone_number,
                    f"🤖 Mensaje de prueba para {contact.name}\n\nSistema de Combustible funcionando correctamente ✅"
                )
                if result['success']:
                    sent_count += 1
        
        self.message_user(request, f"Mensajes de prueba enviados: {sent_count}")
    
    send_test_message.short_description = "Enviar mensaje de prueba"
    
    def activate_contacts(self, request, queryset):
        queryset.update(active=True)
        self.message_user(request, f"Contactos activados: {queryset.count()}")
    
    activate_contacts.short_description = "Activar contactos seleccionados"
    
    def deactivate_contacts(self, request, queryset):
        queryset.update(active=False)
        self.message_user(request, f"Contactos desactivados: {queryset.count()}")
    
    deactivate_contacts.short_description = "Desactivar contactos seleccionados"

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['contact', 'message_type', 'status', 'sent_at', 'delivered_at']
    list_filter = ['message_type', 'status', 'sent_at']
    search_fields = ['contact__name', 'contact__phone_number', 'content']
    readonly_fields = ['whatsapp_message_id', 'sent_at', 'delivered_at', 'read_at']
    
    fieldsets = (
        ('Mensaje', {
            'fields': ('contact', 'message_type', 'content', 'file_url')
        }),
        ('Estado', {
            'fields': ('status', 'whatsapp_message_id', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        }),
        ('Relaciones', {
            'fields': ('reporte', 'template_name'),
            'classes': ('collapse',)
        })
    )

@admin.register(WhatsAppWebhookLog)
class WhatsAppWebhookLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'processed', 'from_number', 'message_status']
    list_filter = ['processed', 'created_at', 'message_status']
    search_fields = ['from_number', 'message_id']
    readonly_fields = ['webhook_data', 'created_at', 'processed_at']
    
    def has_add_permission(self, request):
        return False  # No permitir crear logs manualmente

class RecordAdmin(admin.ModelAdmin):
    model=Registro

admin.site.register(Registro, RecordAdmin)