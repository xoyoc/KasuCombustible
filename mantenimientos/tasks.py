import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Equipo, Mantenimiento, Notificacion, Supervisor

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

def verificar_mantenimientos_pendientes():
    """Verifica recordatorios (5 días antes) y mantenimientos vencidos."""
    hoy = timezone.now().date()
    fecha_recordatorio = hoy + timedelta(days=5)

    recordatorios = Mantenimiento.objects.filter(
        estado='pendiente',
        fecha_programada=fecha_recordatorio,
    )
    for m in recordatorios:
        crear_notificacion_recordatorio(m.id)

    vencidos = Mantenimiento.objects.filter(
        estado='vencido',
        fecha_programada=hoy - timedelta(days=1),
    )
    for m in vencidos:
        enviar_reporte_supervisor(m.id)

    verificar_mantenimientos_por_kilometraje()

    logger.info(
        f"Mantenimientos: {recordatorios.count()} recordatorios, "
        f"{vencidos.count()} vencidos procesados"
    )


def verificar_mantenimientos_por_kilometraje():
    """Notifica equipos que están a 100 km o menos del próximo mantenimiento."""
    notificaciones_creadas = 0

    for equipo in Equipo.objects.filter(activo=True):
        proximo = equipo.proximo_mantenimiento()
        km_restantes = proximo.get('km_restantes', 0)

        if 0 < km_restantes <= 100:
            ya_notificado = Notificacion.objects.filter(
                mantenimiento__equipo=equipo,
                tipo='recordatorio',
                fecha_creacion__gte=timezone.now() - timedelta(days=1),
            ).exists()

            if ya_notificado:
                continue

            mantenimiento, _ = Mantenimiento.objects.get_or_create(
                equipo=equipo,
                estado='pendiente',
                defaults={
                    'fecha_programada': proximo['fecha'],
                    'kilometraje_programado': proximo['kilometraje'],
                    'operador': (
                        equipo.mantenimientos.first().operador
                        if equipo.mantenimientos.exists() else None
                    ),
                    'tipo_mantenimiento_id': 1,
                },
            )

            if mantenimiento.operador:
                crear_notificacion_recordatorio(mantenimiento.id, por_kilometraje=True)
                notificaciones_creadas += 1

    logger.info(f"Kilómetraje: {notificaciones_creadas} notificaciones creadas")


def crear_notificacion_recordatorio(mantenimiento_id: int, por_kilometraje: bool = False) -> None:
    """Crea notificación de recordatorio por email y envía alerta por OpenWA."""
    try:
        m = Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        logger.warning(f"Mantenimiento {mantenimiento_id} no encontrado")
        return

    if por_kilometraje:
        asunto = f"Recordatorio de Mantenimiento por Kilometraje - {m.equipo.placa}"
        mensaje = render_to_string('mantenimiento/emails/recordatorio_kilometraje.txt', {
            'mantenimiento': m, 'equipo': m.equipo, 'operador': m.operador,
        })
        wa_msg = (
            f"⚙️ *RECORDATORIO DE MANTENIMIENTO POR KILOMETRAJE*\n\n"
            f"🚛 Equipo: {m.equipo.placa} ({m.equipo.marca} {m.equipo.modelo})\n"
            f"📏 Km actuales: {m.equipo.kilometraje_actual:,}\n"
            f"🔧 Próximo mantenimiento en: {m.equipo.proximo_mantenimiento().get('km_restantes', 0):,} km\n"
            f"👷 Operador: {m.operador.nombre if m.operador else 'N/A'}"
        )
    else:
        asunto = f"Recordatorio de Mantenimiento - {m.equipo.placa}"
        mensaje = render_to_string('mantenimiento/emails/recordatorio_fecha.txt', {
            'mantenimiento': m, 'equipo': m.equipo, 'operador': m.operador,
        })
        wa_msg = (
            f"📅 *RECORDATORIO DE MANTENIMIENTO*\n\n"
            f"🚛 Equipo: {m.equipo.placa} ({m.equipo.marca} {m.equipo.modelo})\n"
            f"📆 Fecha programada: {m.fecha_programada}\n"
            f"⚠️ Faltan 5 días para el mantenimiento\n"
            f"👷 Operador: {m.operador.nombre if m.operador else 'N/A'}"
        )

    notificacion = Notificacion.objects.create(
        mantenimiento=m,
        tipo='recordatorio',
        destinatario_email=m.operador.email,
        asunto=asunto,
        mensaje=mensaje,
        fecha_programada=timezone.now(),
    )
    enviar_notificacion(notificacion.id)
    _openwa_broadcast(wa_msg)


def enviar_reporte_supervisor(mantenimiento_id: int) -> None:
    """Envía alerta de mantenimiento vencido al supervisor por email y OpenWA."""
    try:
        m = Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        logger.warning(f"Mantenimiento {mantenimiento_id} no encontrado")
        return

    supervisores = Supervisor.objects.filter(activo=True)
    if not supervisores.exists():
        logger.warning("No hay supervisores activos configurados")
        return

    asunto = f"ALERTA: Mantenimiento Vencido - {m.equipo.placa}"
    mensaje = render_to_string('mantenimiento/emails/reporte_supervisor.txt', {
        'mantenimiento': m,
        'equipo': m.equipo,
        'operador': m.operador,
        'dias_vencido': m.dias_vencido(),
    })

    for supervisor in supervisores:
        notificacion = Notificacion.objects.create(
            mantenimiento=m,
            tipo='reporte_supervisor',
            destinatario_email=supervisor.email,
            asunto=asunto,
            mensaje=mensaje,
            fecha_programada=timezone.now(),
        )
        enviar_notificacion(notificacion.id)

    m.estado = 'vencido'
    m.save()

    wa_msg = (
        f"🚨 *ALERTA: MANTENIMIENTO VENCIDO*\n\n"
        f"🚛 Equipo: {m.equipo.placa} ({m.equipo.marca} {m.equipo.modelo})\n"
        f"📅 Fecha programada: {m.fecha_programada}\n"
        f"⏰ Días vencido: {m.dias_vencido()}\n"
        f"👷 Operador: {m.operador.nombre if m.operador else 'N/A'}\n\n"
        f"⚠️ Se requiere atención inmediata."
    )
    _openwa_broadcast(wa_msg)


def enviar_notificacion(notificacion_id: int) -> None:
    """Envía una notificación de email específica."""
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id)
        notificacion.enviar()
        if notificacion.estado != 'enviada':
            logger.error(f"Error al enviar notificación {notificacion_id}: {notificacion.error_mensaje}")
    except Notificacion.DoesNotExist:
        logger.warning(f"Notificación {notificacion_id} no encontrada")


def procesar_notificaciones_pendientes() -> None:
    """Envía todas las notificaciones pendientes cuya fecha ya pasó."""
    pendientes = Notificacion.objects.filter(
        estado='pendiente',
        fecha_programada__lte=timezone.now(),
    )
    for notificacion in pendientes:
        enviar_notificacion(notificacion.id)
    logger.info(f"Procesadas {pendientes.count()} notificaciones pendientes")


def generar_reporte_semanal() -> None:
    """Genera reporte semanal de mantenimientos para supervisores vía email y OpenWA."""
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=7)

    completados = Mantenimiento.objects.filter(
        fecha_completado__date__range=[fecha_inicio, fecha_fin],
        completado=True,
    ).count()

    vencidos = Mantenimiento.objects.filter(
        estado='vencido',
        fecha_programada__range=[fecha_inicio, fecha_fin],
    ).count()

    equipos_activos = Equipo.objects.filter(activo=True).count()
    supervisores = Supervisor.objects.filter(activo=True)

    for supervisor in supervisores:
        notificacion = Notificacion.objects.create(
            mantenimiento=None,
            tipo='reporte_supervisor',
            destinatario_email=supervisor.email,
            asunto="Reporte Semanal de Mantenimientos",
            mensaje=(
                f"Reporte semanal del {fecha_inicio} al {fecha_fin}:\n\n"
                f"- Mantenimientos completados: {completados}\n"
                f"- Mantenimientos vencidos: {vencidos}\n"
                f"- Equipos activos: {equipos_activos}\n\n"
                "Revise el sistema para más detalles."
            ),
            fecha_programada=timezone.now(),
        )
        enviar_notificacion(notificacion.id)

    _openwa_broadcast(
        f"📋 *REPORTE SEMANAL DE MANTENIMIENTOS*\n"
        f"📅 {fecha_inicio} al {fecha_fin}\n\n"
        f"✅ Completados: {completados}\n"
        f"🚨 Vencidos: {vencidos}\n"
        f"🚛 Equipos activos: {equipos_activos}\n\n"
        f"Ingrese al sistema para ver el detalle completo."
    )

    logger.info(f"Reporte semanal enviado a {supervisores.count()} supervisores")
