# management/commands/migrate_to_spaces.py
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from pathlib import Path

class Command(BaseCommand):
    help = 'Migra archivos locales existentes a DigitalOcean Spaces'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la migración sin transferir archivos'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Número de archivos a procesar por lote'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 MODO SIMULACIÓN - No se transferirán archivos')
            )
        
        self.stdout.write("🚀 Iniciando migración a DigitalOcean Spaces...")
        
        # Migrar archivos media
        self.migrate_media_files(dry_run, batch_size)
        
        # Migrar archivos estáticos (opcional)
        self.migrate_static_files(dry_run, batch_size)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Migración completada!')
        )

    def migrate_media_files(self, dry_run, batch_size):
        """Migra archivos de la carpeta media local a Spaces"""
        from registros.models import Registro, Equipo, Operador  # Ajusta la importación
        from combustible.storage_backends import MediaStorage
        
        storage = MediaStorage()
        migrated_count = 0
        error_count = 0
        
        # Migrar fotos de tickets
        self.stdout.write("\n📸 Migrando fotos de tickets...")
        registros_con_foto = Registro.objects.exclude(photo_tiket__isnull=True).exclude(photo_tiket='')
        
        for registro in registros_con_foto[:batch_size]:
            try:
                old_path = registro.photo_tiket.path
                if os.path.exists(old_path):
                    if not dry_run:
                        # Leer archivo local
                        with open(old_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Guardar en Spaces
                        new_path = storage.save(registro.photo_tiket.name, file_content)
                        
                        # Actualizar el modelo con la nueva ruta
                        registro.photo_tiket.name = new_path
                        registro.save(update_fields=['photo_tiket'])
                        
                        # Opcional: eliminar archivo local después de confirmar subida
                        # os.remove(old_path)
                    
                    migrated_count += 1
                    self.stdout.write(f"   ✅ {registro.numero_tiket}: {registro.photo_tiket.name}")
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error con {registro.numero_tiket}: {str(e)}")
                )
        
        # Migrar fotos de equipos
        self.stdout.write("\n🚛 Migrando fotos de equipos...")
        equipos_con_foto = Equipo.objects.exclude(foto_equipo__isnull=True).exclude(foto_equipo='')
        
        for equipo in equipos_con_foto:
            try:
                if hasattr(equipo.foto_equipo, 'path'):
                    old_path = equipo.foto_equipo.path
                    if os.path.exists(old_path):
                        if not dry_run:
                            with open(old_path, 'rb') as f:
                                file_content = f.read()
                            
                            new_path = storage.save(equipo.foto_equipo.name, file_content)
                            equipo.foto_equipo.name = new_path
                            equipo.save(update_fields=['foto_equipo'])
                        
                        migrated_count += 1
                        self.stdout.write(f"   ✅ {equipo.placa}: {equipo.foto_equipo.name}")
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error con equipo {equipo.placa}: {str(e)}")
                )
        
        self.stdout.write(f"\n📊 Archivos media: {migrated_count} migrados, {error_count} errores")

    def migrate_static_files(self, dry_run, batch_size):
        """Migra archivos estáticos a Spaces"""
        if not hasattr(settings, 'STATIC_ROOT') or not settings.STATIC_ROOT:
            self.stdout.write(
                self.style.WARNING("⚠️ STATIC_ROOT no configurado, saltando archivos estáticos")
            )
            return
        
        self.stdout.write("\n🎨 Migrando archivos estáticos...")
        
        static_root = Path(settings.STATIC_ROOT)
        if not static_root.exists():
            self.stdout.write(
                self.style.WARNING("⚠️ Directorio STATIC_ROOT no existe")
            )
            return
        
        from tu_app.storage_backends import StaticStorage
        storage = StaticStorage()
        
        migrated_count = 0
        error_count = 0
        
        # Migrar archivos CSS, JS, imágenes
        extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']
        
        for ext in extensions:
            files = list(static_root.rglob(f'*{ext}'))[:batch_size]
            
            for file_path in files:
                try:
                    relative_path = file_path.relative_to(static_root)
                    
                    if not dry_run:
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        
                        storage.save(str(relative_path), file_content)
                    
                    migrated_count += 1
                    self.stdout.write(f"   ✅ {relative_path}")
                
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error con {file_path}: {str(e)}")
                    )
        
        self.stdout.write(f"\n📊 Archivos estáticos: {migrated_count} migrados, {error_count} errores")

# management/commands/cleanup_spaces.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Limpia archivos antiguos y huérfanos en DigitalOcean Spaces'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Eliminar archivos de reportes temporales más antiguos que X días'
        )
        parser.add_argument(
            '--remove-orphaned',
            action='store_true',
            help='Eliminar archivos que no tienen referencia en la base de datos'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la limpieza sin eliminar archivos'
        )

    def handle(self, *args, **options):
        days = options['days']
        remove_orphaned = options['remove_orphaned']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 MODO SIMULACIÓN - No se eliminarán archivos')
            )
        
        self.stdout.write("🧹 Iniciando limpieza de DigitalOcean Spaces...")
        
        # Limpiar reportes temporales antiguos
        self.cleanup_old_reports(days, dry_run)
        
        # Limpiar archivos huérfanos si se solicita
        if remove_orphaned:
            self.cleanup_orphaned_files(dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Limpieza completada!')
        )

    def cleanup_old_reports(self, days, dry_run):
        """Elimina reportes temporales antiguos"""
        from registros.models import ReporteGenerado
        from combustible.storage_backends import delete_file_from_storage, ReportesStorage
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_reports = ReporteGenerado.objects.filter(
            fecha_generacion__lt=cutoff_date,
            tipo='personalizado'  # Solo reportes temporales
        )
        
        deleted_count = 0
        error_count = 0
        
        self.stdout.write(f"\n📊 Limpiando reportes más antiguos que {days} días...")
        
        for report in old_reports:
            try:
                if report.archivo_excel:
                    if not dry_run:
                        success = delete_file_from_storage(
                            report.archivo_excel.name, 
                            ReportesStorage
                        )
                        if success:
                            report.delete()
                    
                    deleted_count += 1
                    self.stdout.write(f"   🗑️ {report.nombre}")
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error eliminando {report.nombre}: {str(e)}")
                )
        
        self.stdout.write(f"\n📊 Reportes: {deleted_count} eliminados, {error_count} errores")

    def cleanup_orphaned_files(self, dry_run):
        """Elimina archivos que no tienen referencia en la base de datos"""
        # Esta función requeriría listar todos los archivos en Spaces
        # y compararlos con las referencias en la base de datos
        # Es más compleja y requiere acceso directo a la API de Spaces
        
        self.stdout.write("\n🔍 Búsqueda de archivos huérfanos...")
        self.stdout.write(
            self.style.WARNING("⚠️ Función en desarrollo - requiere implementación completa")
        )

# management/commands/spaces_stats.py
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count

class Command(BaseCommand):
    help = 'Muestra estadísticas de uso de DigitalOcean Spaces'

    def handle(self, *args, **options):
        self.stdout.write("📊 ESTADÍSTICAS DE DIGITALOCEAN SPACES")
        self.stdout.write("=" * 50)
        
        # Estadísticas de archivos de tickets
        self.show_ticket_stats()
        
        # Estadísticas de archivos de equipos
        self.show_equipment_stats()
        
        # Estadísticas de reportes
        self.show_reports_stats()
        
        # Estadísticas generales de storage
        self.show_storage_stats()

    def show_ticket_stats(self):
        """Muestra estadísticas de fotos de tickets"""
        from registros.models import Registro
        
        total_registros = Registro.objects.count()
        registros_con_foto = Registro.objects.exclude(
            photo_tiket__isnull=True
        ).exclude(photo_tiket='').count()
        
        porcentaje_con_foto = (registros_con_foto / total_registros * 100) if total_registros > 0 else 0
        
        self.stdout.write(f"\n🎫 TICKETS:")
        self.stdout.write(f"   • Total de registros: {total_registros}")
        self.stdout.write(f"   • Registros con foto: {registros_con_foto}")
        self.stdout.write(f"   • Porcentaje con foto: {porcentaje_con_foto:.1f}%")

    def show_equipment_stats(self):
        """Muestra estadísticas de fotos de equipos"""
        from registros.models import Equipo
        
        total_equipos = Equipo.objects.count()
        equipos_con_foto = Equipo.objects.exclude(
            foto_equipo__isnull=True
        ).exclude(foto_equipo='').count()
        
        porcentaje_con_foto = (equipos_con_foto / total_equipos * 100) if total_equipos > 0 else 0
        
        self.stdout.write(f"\n🚛 EQUIPOS:")
        self.stdout.write(f"   • Total de equipos: {total_equipos}")
        self.stdout.write(f"   • Equipos con foto: {equipos_con_foto}")
        self.stdout.write(f"   • Porcentaje con foto: {porcentaje_con_foto:.1f}%")

    def show_reports_stats(self):
        """Muestra estadísticas de reportes generados"""
        from registros.models import ReporteGenerado
        
        total_reportes = ReporteGenerado.objects.count()
        reportes_con_archivo = ReporteGenerado.objects.exclude(
            archivo_excel__isnull=True
        ).exclude(archivo_excel='').count()
        
        reportes_enviados = ReporteGenerado.objects.filter(
            enviado_por_email=True
        ).count()
        
        self.stdout.write(f"\n📋 REPORTES:")
        self.stdout.write(f"   • Total de reportes: {total_reportes}")
        self.stdout.write(f"   • Reportes con archivo: {reportes_con_archivo}")
        self.stdout.write(f"   • Reportes enviados: {reportes_enviados}")

    def show_storage_stats(self):
        """Muestra estadísticas generales de almacenamiento"""
        from registros.models import ConfiguracionSpaces
        
        try:
            config = ConfiguracionSpaces.objects.filter(activa=True).first()
            if config:
                self.stdout.write(f"\n💾 ALMACENAMIENTO:")
                self.stdout.write(f"   • Bucket: {config.bucket_name}")
                self.stdout.write(f"   • Región: {config.region}")
                self.stdout.write(f"   • Espacio usado: {config.espacio_usado_gb:.2f} GB")
                self.stdout.write(f"   • Límite: {config.limite_espacio_total_gb} GB")
                self.stdout.write(f"   • Uso: {config.porcentaje_uso:.1f}%")
                self.stdout.write(f"   • CDN: {'✅' if config.cdn_enabled else '❌'}")
            else:
                self.stdout.write(f"\n💾 ALMACENAMIENTO:")
                self.stdout.write(f"   ⚠️ No hay configuración de Spaces activa")
                
        except Exception as e:
            self.stdout.write(f"\n❌ Error obteniendo estadísticas: {str(e)}")

# management/commands/test_spaces_connection.py
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Prueba la conexión a DigitalOcean Spaces'

    def handle(self, *args, **options):
        self.stdout.write("🔍 PROBANDO CONEXIÓN A DIGITALOCEAN SPACES")
        self.stdout.write("=" * 50)
        
        # Probar conexión básica
        if self.test_basic_connection():
            # Probar subida de archivo
            self.test_file_upload()
            
            # Probar listado de archivos
            self.test_file_listing()
            
            # Probar eliminación
            self.test_file_deletion()
        
        self.stdout.write("\n✅ Pruebas completadas!")

    def test_basic_connection(self):
        """Prueba la conexión básica a Spaces"""
        try:
            from combustible.storage_backends import MediaStorage
            storage = MediaStorage()
            
            # Intentar acceder al bucket
            exists = storage.bucket_name
            self.stdout.write(f"✅ Conexión exitosa al bucket: {exists}")
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error de conexión: {str(e)}")
            )
            return False

    def test_file_upload(self):
        """Prueba la subida de un archivo de prueba"""
        try:
            from combustible.storage_backends import MediaStorage
            storage = MediaStorage()
            
            # Crear archivo de prueba
            test_content = ContentFile(b"Archivo de prueba para DigitalOcean Spaces")
            test_filename = "test_upload.txt"
            
            # Subir archivo
            saved_path = storage.save(test_filename, test_content)
            self.stdout.write(f"✅ Archivo subido: {saved_path}")
            
            # Verificar que existe
            if storage.exists(saved_path):
                self.stdout.write("✅ Archivo verificado en Spaces")
                return saved_path
            else:
                self.stdout.write("❌ Archivo no encontrado después de subir")
                return None
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error subiendo archivo: {str(e)}")
            )
            return None

    def test_file_listing(self):
        """Prueba el listado de archivos"""
        try:
            from combustible.storage_backends import MediaStorage
            storage = MediaStorage()
            
            # Listar algunos archivos
            files = storage.listdir('')[1][:5]  # Primeros 5 archivos
            
            if files:
                self.stdout.write("✅ Listado de archivos exitoso:")
                for file in files:
                    self.stdout.write(f"   📄 {file}")
            else:
                self.stdout.write("ℹ️ No hay archivos en el bucket")
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error listando archivos: {str(e)}")
            )
            return False

    def test_file_deletion(self):
        """Prueba la eliminación del archivo de prueba"""
        try:
            from combustible.storage_backends import MediaStorage
            storage = MediaStorage()
            
            test_filename = "test_upload.txt"
            
            if storage.exists(test_filename):
                storage.delete(test_filename)
                self.stdout.write(f"✅ Archivo de prueba eliminado: {test_filename}")
            else:
                self.stdout.write(f"ℹ️ Archivo de prueba no encontrado para eliminar")
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error eliminando archivo: {str(e)}")
            )
            return False