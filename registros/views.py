from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import logging
from datetime import timezone
from whatsaap_service import WhatsAppBusinessService
from .models import WhatsAppWebhookLog, WhatsAppMessage, WhatsAppContact

from registros.models import Registro, Equipo

# Create your views here.

class RegisterListView(generic.ListView):
    model = Registro
    template_name = "registros/list_register.html"
    ordering = '-fecha_hora'
    context_object_name = 'registros'

class RegisterDetailView(generic.DetailView):
    model = Registro
    template_name = 'registros/detail_register.html'

class RegisterFormView(generic.CreateView):
    model = Registro
    fields = [
            'numero_tiket',
            'idEquipo', 
            'idOperador',
            'Litros',
            'Litros',
            'costolitro',
            'kilometraje',
            'photo_tiket'
            ]
    template_name="registros/add_register.html"
    success_url = reverse_lazy('registro_list')
    
    def form_valid(self, form):
        # Guardar el registro primero
        response = super().form_valid(form)
        
        # Actualizar el kilometraje del equipo
        registro = self.object  # El objeto Registro recién creado
        equipo = registro.idEquipo  # Tu FK al modelo Equipo
        
        # Actualizar el kilometraje_actual del equipo
        if registro.kilometraje and registro.kilometraje > 0:
            equipo.kilometraje_actual = registro.kilometraje
            equipo.save(update_fields=['kilometraje_actual'])
            
            messages.success(
                self.request, 
                f'Registro guardado. Kilometraje del equipo {equipo.placa} actualizado a {registro.kilometraje} km'
            )
        else:
            messages.success(self.request, 'Registro guardado exitosamente')
        
        return response

class RegisterDeleteView(generic.DeleteView):
    model = Registro
    success_url = reverse_lazy('registro_list')


logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Vista para manejar webhooks de WhatsApp"""
    
    def __init__(self):
        super().__init__()
        self.whatsapp_service = WhatsAppBusinessService()
    
    def get(self, request):
        """Verificación del webhook"""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        verification_result = self.whatsapp_service.verify_webhook(mode, token, challenge)
        
        if verification_result:
            return HttpResponse(verification_result)
        else:
            return HttpResponse('Forbidden', status=403)
    
    def post(self, request):
        """Procesar webhooks entrantes"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Guardar webhook log
            webhook_log = WhatsAppWebhookLog.objects.create(
                webhook_data=data
            )
            
            # Procesar el webhook
            self._process_webhook(data, webhook_log)
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            logger.error("❌ Error decodificando JSON del webhook WhatsApp")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"❌ Error procesando webhook WhatsApp: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _process_webhook(self, data, webhook_log):
        """Procesa los datos del webhook"""
        try:
            # Extraer información del webhook
            entries = data.get('entry', [])
            
            for entry in entries:
                changes = entry.get('changes', [])
                
                for change in changes:
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        
                        # Procesar estados de mensajes
                        statuses = value.get('statuses', [])
                        for status in statuses:
                            self._update_message_status(status)
                        
                        # Procesar mensajes entrantes
                        messages = value.get('messages', [])
                        for message in messages:
                            self._process_incoming_message(message)
            
            # Marcar como procesado
            webhook_log.processed = True
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            
        except Exception as e:
            logger.error(f"❌ Error procesando webhook: {e}")
    
    def _update_message_status(self, status_data):
        """Actualiza el estado de un mensaje enviado"""
        try:
            message_id = status_data.get('id')
            status = status_data.get('status')
            timestamp = status_data.get('timestamp')
            
            # Buscar el mensaje en la base de datos
            try:
                message = WhatsAppMessage.objects.get(whatsapp_message_id=message_id)
                message.status = status
                
                if status == 'delivered' and not message.delivered_at:
                    message.delivered_at = timezone.now()
                elif status == 'read' and not message.read_at:
                    message.read_at = timezone.now()
                
                message.save()
                logger.info(f"📱 Estado de mensaje actualizado: {message_id} -> {status}")
                
            except WhatsAppMessage.DoesNotExist:
                logger.warning(f"⚠️ Mensaje no encontrado para actualizar estado: {message_id}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado de mensaje: {e}")
    
    def _process_incoming_message(self, message_data):
        """Procesa mensajes entrantes (respuestas de usuarios)"""
        try:
            from_number = message_data.get('from')
            message_id = message_data.get('id')
            message_type = message_data.get('type')
            
            # Buscar contacto
            try:
                contact = WhatsAppContact.objects.get(phone_number__contains=from_number[-10:])
                
                # Procesar según el tipo de mensaje
                if message_type == 'interactive':
                    self._handle_interactive_response(message_data, contact)
                elif message_type == 'text':
                    self._handle_text_response(message_data, contact)
                
                logger.info(f"📱 Mensaje entrante procesado de {contact.name}")
                
            except WhatsAppContact.DoesNotExist:
                logger.warning(f"⚠️ Contacto no encontrado para número: {from_number}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje entrante: {e}")
    
    def _handle_interactive_response(self, message_data, contact):
        """Maneja respuestas a mensajes interactivos"""
        try:
            interactive = message_data.get('interactive', {})
            button_reply = interactive.get('button_reply', {})
            button_id = button_reply.get('id', '')
            
            # Procesar según el botón presionado
            if 'top_equipos' in button_id:
                self._send_top_equipment_details(contact)
            elif 'operadores_inactivos' in button_id:
                self._send_inactive_operators_details(contact)
            elif 'analisis_costos' in button_id:
                self._send_cost_analysis_details(contact)
            
        except Exception as e:
            logger.error(f"❌ Error manejando respuesta interactiva: {e}")
    
    def _handle_text_response(self, message_data, contact):
        """Maneja respuestas de texto"""
        try:
            text = message_data.get('text', {}).get('body', '').lower()
            
            # Respuestas automáticas simples
            if 'reporte' in text or 'informe' in text:
                response = "📊 Para obtener el último reporte, usa el comando /reporte o contacta al administrador."
                self._send_auto_response(contact, response)
            elif 'ayuda' in text or 'help' in text:
                response = "🤖 *Comandos disponibles:*\n\n• /reporte - Último reporte mensual\n• /equipos - Estado de equipos\n• /operadores - Lista de operadores\n• /ayuda - Esta ayuda"
                self._send_auto_response(contact, response)
            
        except Exception as e:
            logger.error(f"❌ Error manejando respuesta de texto: {e}")
    
    def _send_auto_response(self, contact, message):
        """Envía una respuesta automática"""
        try:
            from whatsaap_service import WhatsAppBusinessService
            service = WhatsAppBusinessService()
            service.send_text_message(contact.phone_number, message)
        except Exception as e:
            logger.error(f"❌ Error enviando respuesta automática: {e}")