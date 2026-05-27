# whatsapp_service.py - Servicio de WhatsApp Business API
import requests
import json
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime
from typing import Optional, Dict, List
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class WhatsAppBusinessService:
    """Servicio para enviar mensajes y archivos por WhatsApp Business API"""
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v23.0"
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        self.verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', None)
        
        if not all([self.phone_number_id, self.access_token]):
            logger.warning("⚠️ WhatsApp Business API no está completamente configurado")
    
    def send_text_message(self, to_number: str, message: str) -> Dict:
        """Envía un mensaje de texto simple"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Limpiar número de teléfono (remover espacios, guiones, etc.)
        clean_number = self._clean_phone_number(to_number)
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"📱 Mensaje enviado a {clean_number}: {result.get('messages', [{}])[0].get('id', 'unknown')}")
            return {'success': True, 'data': result}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando mensaje WhatsApp: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_document(self, to_number: str, document_url: str, filename: str, caption: str = "") -> Dict:
        """Envía un documento (Excel, PDF, etc.)"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        clean_number = self._clean_phone_number(to_number)
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }
        
        if caption:
            payload["document"]["caption"] = caption
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"📄 Documento enviado a {clean_number}: {filename}")
            return {'success': True, 'data': result}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando documento WhatsApp: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_image(self, to_number: str, image_url: str, caption: str = "") -> Dict:
        """Envía una imagen"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        clean_number = self._clean_phone_number(to_number)
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        
        if caption:
            payload["image"]["caption"] = caption
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"🖼️ Imagen enviada a {clean_number}")
            return {'success': True, 'data': result}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando imagen WhatsApp: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_template_message(self, to_number: str, template_name: str, template_params: List = None) -> Dict:
        """Envía un mensaje de plantilla pre-aprobada"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        clean_number = self._clean_phone_number(to_number)
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "es_MX"  # Español México
                }
            }
        }
        
        if template_params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": param} for param in template_params
                    ]
                }
            ]
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"📋 Template enviado a {clean_number}: {template_name}")
            return {'success': True, 'data': result}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando template WhatsApp: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_interactive_message(self, to_number: str, header_text: str, body_text: str, buttons: List[Dict]) -> Dict:
        """Envía un mensaje interactivo con botones"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        clean_number = self._clean_phone_number(to_number)
        
        # Formatear botones para WhatsApp API
        interactive_buttons = []
        for i, button in enumerate(buttons[:3]):  # WhatsApp permite max 3 botones
            interactive_buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}_{button.get('id', 'action')}",
                    "title": button.get('title', 'Acción')[:20]  # Max 20 caracteres
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": header_text[:60]  # Max 60 caracteres
                },
                "body": {
                    "text": body_text[:1024]  # Max 1024 caracteres
                },
                "action": {
                    "buttons": interactive_buttons
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"🔘 Mensaje interactivo enviado a {clean_number}")
            return {'success': True, 'data': result}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando mensaje interactivo: {e}")
            return {'success': False, 'error': str(e)}
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Limpia y formatea el número de teléfono para WhatsApp"""
        # Remover todos los caracteres no numéricos
        clean = ''.join(filter(str.isdigit, phone_number))
        
        # Si no tiene código de país, asumir México (+52)
        if len(clean) == 10:
            clean = "52" + clean
        elif len(clean) == 11 and clean.startswith("1"):
            # Número mexicano con 1 inicial (formato antiguo)
            clean = "52" + clean[1:]
        elif not clean.startswith("52") and len(clean) >= 10:
            clean = "52" + clean[-10:]
        
        logger.debug(f"📞 Número limpiado: {phone_number} -> {clean}")
        return clean
    
    def get_media_url(self, media_id: str) -> Optional[str]:
        """Obtiene la URL de descarga de un archivo multimedia"""
        url = f"{self.base_url}/{media_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('url')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo URL de media: {e}")
            return None
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verifica el webhook de WhatsApp"""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("✅ Webhook de WhatsApp verificado")
            return challenge
        else:
            logger.warning("❌ Verificación de webhook fallida")
            return None

class WhatsAppReportService:
    """Servicio especializado para envío de reportes por WhatsApp"""
    
    def __init__(self):
        self.whatsapp = WhatsAppBusinessService()
    
    def send_monthly_report_summary(self, to_number: str, report_data: Dict) -> Dict:
        """Envía un resumen del reporte mensual"""
        
        # Generar mensaje de resumen
        summary_message = self._generate_summary_message(report_data)
        
        # Enviar mensaje de texto con resumen
        result = self.whatsapp.send_text_message(to_number, summary_message)
        
        if result['success']:
            logger.info(f"📊 Resumen de reporte enviado por WhatsApp a {to_number}")
        
        return result
    
    def send_report_with_excel(self, to_number: str, report_data: Dict, excel_url: str, filename: str) -> List[Dict]:
        """Envía reporte completo con archivo Excel"""
        results = []
        
        # 1. Enviar resumen
        summary_result = self.send_monthly_report_summary(to_number, report_data)
        results.append(summary_result)
        
        # 2. Enviar archivo Excel
        if excel_url:
            caption = f"📊 Reporte completo de {report_data.get('nombre_mes', '')} {report_data.get('año', '')}"
            excel_result = self.whatsapp.send_document(to_number, excel_url, filename, caption)
            results.append(excel_result)
        
        # 3. Enviar mensaje interactivo con opciones
        interactive_result = self._send_report_interactive_menu(to_number, report_data)
        results.append(interactive_result)
        
        return results
    
    def send_alert_inactive_operators(self, to_number: str, inactive_operators: List, month_name: str) -> Dict:
        """Envía alerta de operadores inactivos"""
        
        if not inactive_operators:
            return {'success': True, 'message': 'No hay operadores inactivos'}
        
        message = f"⚠️ *ALERTA - OPERADORES INACTIVOS*\n\n"
        message += f"📅 Mes: {month_name}\n"
        message += f"👥 {len(inactive_operators)} operador{'es' if len(inactive_operators) > 1 else ''} sin actividad:\n\n"
        
        for i, operator in enumerate(inactive_operators, 1):
            message += f"{i}. {operator.nombre}\n"
            message += f"   📧 {operator.email}\n"
            message += f"   📱 {operator.movil}\n\n"
        
        message += "💡 *Recomendación:* Contactar a estos operadores para verificar su estado."
        
        return self.whatsapp.send_text_message(to_number, message)
    
    def send_top_equipment_performance(self, to_number: str, top_equipment: List, month_name: str) -> Dict:
        """Envía información del top de equipos"""
        
        message = f"🏆 *TOP EQUIPOS - {month_name.upper()}*\n\n"
        
        for i, (placa, stats) in enumerate(top_equipment[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            message += f"{emoji} *{placa}*\n"
            message += f"   🚛 {stats['equipo'].marca} {stats['equipo'].modelo}\n"
            message += f"   ⛽ {stats['total_litros']:.1f}L\n"
            message += f"   💰 ${stats['total_gastado']:.2f}\n"
            message += f"   📊 {stats['num_registros']} registros\n\n"
        
        return self.whatsapp.send_text_message(to_number, message)
    
    def send_cost_analysis(self, to_number: str, report_data: Dict) -> Dict:
        """Envía análisis de costos"""
        
        message = f"💰 *ANÁLISIS DE COSTOS - {report_data.get('nombre_mes', '').upper()}*\n\n"
        message += f"📊 *Estadísticas Generales:*\n"
        message += f"• Total gastado: ${report_data.get('total_gastado', 0):.2f}\n"
        message += f"• Promedio diario: ${report_data.get('promedio_diario', 0):.2f}\n"
        message += f"• Total litros: {report_data.get('total_litros', 0):.1f}L\n"
        message += f"• Registros: {report_data.get('total_registros', 0)}\n\n"
        
        message += f"📈 *Eficiencia:*\n"
        message += f"• Promedio por registro: {report_data.get('promedio_litros_registro', 0):.1f}L\n"
        
        if report_data.get('registros_con_foto', 0) > 0:
            porcentaje_foto = report_data.get('porcentaje_con_foto', 0)
            message += f"• Registros con foto: {porcentaje_foto:.1f}%\n"
        
        return self.whatsapp.send_text_message(to_number, message)
    
    def _generate_summary_message(self, report_data: Dict) -> str:
        """Genera mensaje de resumen del reporte"""
        
        message = f"📊 *REPORTE MENSUAL DE COMBUSTIBLE*\n"
        message += f"📅 {report_data.get('nombre_mes', '')} {report_data.get('año', '')}\n\n"
        
        message += f"📈 *RESUMEN EJECUTIVO:*\n"
        message += f"• Registros totales: {report_data.get('total_registros', 0)}\n"
        message += f"• Litros consumidos: {report_data.get('total_litros', 0):.1f}L\n"
        message += f"• Total gastado: ${report_data.get('total_gastado', 0):.2f}\n"
        message += f"• Promedio diario: ${report_data.get('promedio_diario', 0):.2f}\n\n"
        
        # Top equipo
        top_equipos = report_data.get('top_equipos', [])
        if top_equipos:
            top_equipo = top_equipos[0]
            message += f"🏆 *EQUIPO MÁS ACTIVO:*\n"
            message += f"🚛 {top_equipo[0]} - {top_equipo[1]['total_litros']:.1f}L\n\n"
        
        # Operadores inactivos
        operadores_inactivos = report_data.get('operadores_inactivos', [])
        if operadores_inactivos:
            message += f"⚠️ *ATENCIÓN:*\n"
            message += f"👥 {len(operadores_inactivos)} operador{'es' if len(operadores_inactivos) > 1 else ''} sin actividad\n\n"
        
        message += f"📋 El archivo Excel con el detalle completo se envía a continuación."
        
        return message
    
    def _send_report_interactive_menu(self, to_number: str, report_data: Dict) -> Dict:
        """Envía menú interactivo con opciones del reporte"""
        
        header = "📊 Opciones del Reporte"
        body = "Selecciona una opción para obtener más información:"
        
        buttons = [
            {"id": "top_equipos", "title": "🏆 Top Equipos"},
            {"id": "operadores_inactivos", "title": "⚠️ Operadores Inactivos"},
            {"id": "analisis_costos", "title": "💰 Análisis Costos"}
        ]
        
        return self.whatsapp.send_interactive_message(to_number, header, body, buttons)