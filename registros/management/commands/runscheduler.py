import logging
import time

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Inicia el APScheduler con todos los jobs programados'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando APScheduler...')

        from combustible.scheduler import start
        scheduler = start()

        self.stdout.write(self.style.SUCCESS('APScheduler corriendo. Ctrl+C para detener.'))

        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            self.stdout.write(self.style.WARNING('APScheduler detenido.'))
