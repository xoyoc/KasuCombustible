"""
Importa unidades desde un archivo CSV con las columnas:
N.E., MODELO, MARCA, año, Tipo de combustible, Tanque, Rendimiento, ASIGNACIÓN, PLACA, NIV
"""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from equipo.models import Equipo


TIPO_MAP = {
    'gasolina': 'gasolina',
    'diesel':   'diesel',
    'diésel':   'diesel',
    'gas':      'gasolina',
}


def _str(val: str) -> str:
    return val.strip()


def _int_or_none(val: str):
    val = val.strip()
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _decimal_or_none(val: str):
    val = val.strip()
    if not val:
        return None
    try:
        return float(val.replace(',', '.'))
    except ValueError:
        return None


def _combustible(val: str) -> str:
    return TIPO_MAP.get(val.strip().lower(), 'gasolina')


class Command(BaseCommand):
    help = 'Importa unidades desde un CSV. Usa --actualizar para sobreescribir existentes.'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path',
            nargs='?',
            default='unidades.csv',
            help='Ruta al archivo CSV (default: unidades.csv en la raíz del proyecto)',
        )
        parser.add_argument(
            '--actualizar',
            action='store_true',
            help='Actualiza los registros existentes (por numero_economico)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la importación sin guardar nada en la base de datos',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        if not csv_path.is_absolute():
            # Buscar relativo a BASE_DIR del proyecto
            from django.conf import settings
            csv_path = settings.BASE_DIR / csv_path

        if not csv_path.exists():
            raise CommandError(f"Archivo no encontrado: {csv_path}")

        actualizar = options['actualizar']
        dry_run    = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING("--- MODO DRY-RUN: no se guardará nada ---\n"))

        creados    = 0
        actualizados = 0
        omitidos   = 0
        errores    = 0

        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for fila in reader:
                ne = _str(fila.get('N.E.', ''))
                if not ne:
                    continue  # fila vacía

                modelo = _str(fila.get('MODELO', ''))
                if not modelo:
                    self.stdout.write(self.style.WARNING(f"  [{ne}] Sin modelo — omitida"))
                    omitidos += 1
                    continue

                datos = dict(
                    modelo          = modelo,
                    marca           = _str(fila.get('MARCA', '')),
                    year            = _int_or_none(fila.get('año', '')),
                    tipo_combustible= _combustible(fila.get('Tipo de combustible', 'gasolina')),
                    capacidad_tanque= _int_or_none(fila.get('Tanque', '')),
                    rendimiento     = _decimal_or_none(fila.get('Rendimiento', '')),
                    asignacion      = _str(fila.get('ASIGNACIÓN', '')),
                    placa           = _str(fila.get('PLACA', '')),
                    niv             = _str(fila.get('NIV', '')),
                )

                try:
                    existente = Equipo.objects.filter(numero_economico=ne).first()

                    if existente:
                        if actualizar:
                            if not dry_run:
                                for campo, valor in datos.items():
                                    setattr(existente, campo, valor)
                                existente.save()
                            self.stdout.write(
                                f"  [{ne}] Actualizado: {datos['marca']} {datos['modelo']}"
                            )
                            actualizados += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"  [{ne}] Ya existe — omitido (usa --actualizar para sobreescribir)")
                            )
                            omitidos += 1
                    else:
                        if not dry_run:
                            Equipo.objects.create(numero_economico=ne, **datos)
                        self.stdout.write(
                            self.style.SUCCESS(f"  [{ne}] Creado: {datos['marca']} {datos['modelo']}")
                        )
                        creados += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  [{ne}] Error: {e}"))
                    errores += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Creados:     {creados}"))
        if actualizar:
            self.stdout.write(self.style.SUCCESS(f"Actualizados:{actualizados}"))
        self.stdout.write(self.style.WARNING(f"Omitidos:    {omitidos}"))
        if errores:
            self.stdout.write(self.style.ERROR(f"Errores:     {errores}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry-run completado. Ejecuta sin --dry-run para guardar."))
