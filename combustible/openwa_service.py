import requests
import logging
from django.conf import settings
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class OpenWAService:
    """Cliente para la API REST de OpenWA (open-wa/wa-automate)."""

    def __init__(self):
        self.base_url = getattr(settings, 'OPENWA_API_URL', '').rstrip('/')
        self.api_key = getattr(settings, 'OPENWA_API_KEY', '')
        self.allowed_numbers = getattr(settings, 'OPENWA_ALLOWED_NUMBERS', [])

        if not self.base_url or not self.api_key:
            logger.warning("OpenWA no configurado: WA_API_URL o WA_API_KEY ausentes")

    def _headers(self) -> Dict:
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
        }

    def _to_chat_id(self, number: str) -> str:
        """Convierte un número de teléfono al formato OpenWA (xxxxxxxxxxx@c.us)."""
        if '@' in number:
            return number
        clean = ''.join(filter(str.isdigit, number))
        return f"{clean}@c.us"

    def send_text(self, to: str, message: str) -> Dict:
        """Envía un mensaje de texto a un número."""
        chat_id = self._to_chat_id(to)
        try:
            response = requests.post(
                f"{self.base_url}/sendText",
                headers=self._headers(),
                json={"to": chat_id, "content": message},
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Mensaje OpenWA enviado a {chat_id}")
            return {'success': True, 'data': response.json()}
        except requests.RequestException as e:
            logger.error(f"Error OpenWA sendText a {chat_id}: {e}")
            return {'success': False, 'error': str(e)}

    def send_file(self, to: str, url: str, filename: str, caption: str = '') -> Dict:
        """Envía un archivo (por URL pública) a un número."""
        chat_id = self._to_chat_id(to)
        try:
            response = requests.post(
                f"{self.base_url}/sendFile",
                headers=self._headers(),
                json={"to": chat_id, "url": url, "filename": filename, "caption": caption},
                timeout=60,
            )
            response.raise_for_status()
            logger.info(f"Archivo OpenWA enviado a {chat_id}: {filename}")
            return {'success': True, 'data': response.json()}
        except requests.RequestException as e:
            logger.error(f"Error OpenWA sendFile a {chat_id}: {e}")
            return {'success': False, 'error': str(e)}

    def broadcast_text(self, message: str, numbers: Optional[List[str]] = None) -> List[Dict]:
        """Envía un texto a todos los números permitidos (o a los indicados)."""
        targets = numbers if numbers is not None else self.allowed_numbers
        return [{'number': n, **self.send_text(n, message)} for n in targets]

    def broadcast_file(self, url: str, filename: str, caption: str = '',
                       numbers: Optional[List[str]] = None) -> List[Dict]:
        """Envía un archivo a todos los números permitidos (o a los indicados)."""
        targets = numbers if numbers is not None else self.allowed_numbers
        return [{'number': n, **self.send_file(n, url, filename, caption)} for n in targets]
