import logging
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

logger = logging.getLogger(__name__)


def _openwa_broadcast(message: str) -> None:
    """Envía un texto a todos los números OpenWA permitidos."""
    try:
        from combustible.openwa_service import OpenWAService
        OpenWAService().broadcast_text(message)
    except Exception as e:
        logger.error(f"Error OpenWA broadcast: {e}")


# ---------------------------------------------------------------------------
# Tareas programadas (llamadas por APScheduler)
# ---------------------------------------------------------------------------

def enviar_reporte_mensual_automatico() -> None:
    """
    Se ejecuta el día 1 de cada mes a las 9:00 AM.
    Llama al management command existente y luego notifica por OpenWA.
    """
    import datetime
    hoy = datetime.date.today()
    if hoy.day != 1:
        logger.info(f"No es día 1 del mes (día {hoy.day}), saltando reporte mensual")
        return

    logger.info("Iniciando envío automático de reporte mensual")
    try:
        call_command('enviar_reporte_mensual_r', verbosity=1)
        logger.info("Reporte mensual enviado exitosamente")

        mes_anterior = (hoy.replace(day=1) - timedelta(days=1))
        nombre_mes = mes_anterior.strftime('%B %Y')
        _openwa_broadcast(
            f"📊 *REPORTE MENSUAL DE COMBUSTIBLE*\n"
            f"📅 {nombre_mes}\n\n"
            f"✅ El reporte del mes ha sido generado y enviado por email.\n"
            f"📎 Revise su correo para el archivo Excel completo."
        )
    except Exception as e:
        logger.error(f"Error enviando reporte mensual: {e}")
        _openwa_broadcast(
            f"❌ *ERROR EN REPORTE MENSUAL*\n\n"
            f"No se pudo generar el reporte automático.\n"
            f"Error: {e}\n\n"
            f"Por favor genérelo manualmente desde el sistema."
        )


def verificar_operadores_inactivos() -> None:
    """
    Se ejecuta los lunes a las 10:00 AM.
    Detecta operadores sin registros en los últimos 7 días y notifica por OpenWA.
    """
    from registros.models import Registro
    from operador.models import Operador

    fecha_limite = timezone.now() - timedelta(days=7)

    operadores_activos_ids = set(
        Registro.objects.filter(
            fecha_hora__gte=fecha_limite
        ).values_list('idOperador_id', flat=True)
    )

    inactivos = Operador.objects.filter(activo=True).exclude(id__in=operadores_activos_ids)
    count = inactivos.count()

    logger.info(f"Operadores inactivos detectados: {count}")

    if not inactivos.exists():
        return

    lineas = "\n".join(
        f"{i}. {op.nombre} — {op.movil}" for i, op in enumerate(inactivos, 1)
    )
    _openwa_broadcast(
        f"⚠️ *OPERADORES SIN ACTIVIDAD — ÚLTIMA SEMANA*\n\n"
        f"Los siguientes {count} operador{'es' if count > 1 else ''} "
        f"no han registrado combustible en 7 días:\n\n"
        f"{lineas}\n\n"
        f"💡 Verifique su estado en el sistema."
    )


def limpiar_archivos_temporales() -> None:
    """Elimina reportes generados con más de 6 meses de antigüedad."""
    from registros.models import ReporteGenerado

    fecha_limite = timezone.now() - timedelta(days=180)
    antiguos = ReporteGenerado.objects.filter(fecha_generacion__lt=fecha_limite)

    eliminados = 0
    for reporte in antiguos:
        try:
            if reporte.archivo_excel:
                reporte.archivo_excel.delete(save=False)
            reporte.delete()
            eliminados += 1
        except Exception as e:
            logger.error(f"Error eliminando reporte {reporte.id}: {e}")

    logger.info(f"Archivos temporales: {eliminados} reportes eliminados")
