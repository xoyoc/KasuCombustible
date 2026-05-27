# context.md — Contexto del Proyecto LogincoCobustible

## Contexto de Negocio

**¿Qué hace el sistema?**
Sistema de gestión de combustible para la flota de vehículos de Loginco. Cada vez que un operador carga combustible, registra el ticket (con foto), el kilometraje, los litros y el costo por litro. El sistema calcula costos totales, actualiza el kilometraje del vehículo automáticamente y genera reportes mensuales en Excel.

**¿Para quién?**
- **Operadores**: registran consumos de combustible
- **Supervisores**: reciben reportes semanales y alertas de mantenimientos vencidos
- **Gerencia/Admin**: reciben reportes mensuales completos vía email y WhatsApp

**Destinatarios fijos de reportes mensuales** (hardcoded en `settings.py`):
- `zuly.becerra@loginco.com.mx`
- `f.suarez@loginco.com.mx`
- `xoyoc_l2@hotmail.com`

**Reglas de negocio clave:**
- Mantenimiento preventivo: cada **90 días** o cada **10,000 km** desde el último mantenimiento completado
- Aviso previo de mantenimiento: **5 días** antes por fecha, **100 km** antes por kilometraje
- Al guardar un `Registro`, la señal `post_save` actualiza automáticamente `Equipo.kilometraje_actual` si el nuevo km es mayor al actual
- Al completar un `Mantenimiento`, la señal `post_save` crea automáticamente el siguiente mantenimiento programado
- Al crear un `Equipo` nuevo, se crea su primer mantenimiento automáticamente

---

## Estado Actual del Proyecto

**Lo que funciona en producción:**
- Registro de combustible con foto de ticket subida a DigitalOcean Spaces
- CRUD completo de equipos, operadores, registros y mantenimientos
- Reporte mensual automático via GitHub Actions (día 1 de cada mes, 9:00 AM UTC)
- Envío de reporte por email (SendGrid) y WhatsApp Business API
- Dashboard de mantenimientos con alertas
- Sistema de notificaciones por email a supervisores

**Pendiente / Deuda técnica conocida:**
- El `monthly-report.yml` fue **eliminado** (commit `4479062`); solo queda `EnvioReporteMensual.yml` como workflow activo
- La optimización de imágenes de tickets está **comentada** en `Registro.save()` — se dejó sin efecto porque causaba problemas; está lista para reactivar
- Celery está configurado completamente (`celery.py` con beat_schedule), pero en producción se usa GitHub Actions para el reporte mensual en lugar de Celery, evitando la necesidad de Redis
- `registros/signals.py` tiene **dos receptores duplicados** para `actualizar_kilometraje_equipo` (versión simple y versión avanzada); ambos se ejecutan en cada `post_save`, lo que puede causar doble ejecución
- `whatsaap_service.py` — el nombre tiene un typo intencional/heredado; no renombrar sin actualizar todos los imports
- `manage_whatsapp_contacts` aparece en la documentación pero el archivo del comando no está en `registros/management/commands/` con ese nombre exacto; verificar antes de usar

**Entorno local:**
- Virtualenv en `.venvCombustibleloginco/`
- `USE_SPACES=False` para desarrollo local (usa filesystem)
- PostgreSQL requerido localmente; Redis solo si se usa Celery

---

## Decisiones de Arquitectura

**¿Por qué GitHub Actions en lugar de Celery para el reporte mensual?**
El servidor en DigitalOcean App Platform no tiene Redis configurado de forma persistente. GitHub Actions resuelve el problema de programación mensual sin costo adicional de infraestructura y sin gestionar un broker.

**¿Por qué DigitalOcean Spaces?**
El proyecto ya vive en DigitalOcean App Platform. Spaces (compatible con S3) es la opción natural para almacenamiento de objetos en el mismo proveedor, simplificando la facturación y la latencia.

**¿Por qué tres clases de storage separadas?**
`StaticStorage`, `MediaStorage` y `ReportesStorage` en `storage_backends.py` permiten ACL diferentes: estáticos y fotos son `public-read`; reportes Excel son `private`. Además `MediaStorage._save()` agrega un timestamp al nombre para evitar colisiones.

**¿Por qué `django-environ` Y `python-decouple` juntos?**
`settings.py` importa ambos (`environ` y `decouple`). Es una deuda técnica menor; `env.db()` de `django-environ` es conveniente para parsear `DJANGO_DB_URL` directamente. Decouple se usa para el resto. No mezclar más, elegir uno al agregar nuevas vars.

**¿Por qué `crispy-tailwind`?**
El frontend usa Tailwind CSS. `crispy_tailwind` permite renderizar formularios Django con clases Tailwind sin escribir HTML manual por cada campo.

**Señales vs. lógica en `save()`:**
Se prefirió usar señales (`post_save`, `pre_save`) para la lógica cross-model (actualizar kilometraje del equipo al guardar un registro, crear el siguiente mantenimiento al completar uno). Esto mantiene los modelos más limpios pero requiere tener presente el orden de ejecución cuando hay múltiples receptores.

---

## Historial de Cambios Relevantes

| Commit | Cambio | Impacto |
|---|---|---|
| `4479062` | Eliminado `monthly-report.yml` | Solo queda `EnvioReporteMensual.yml` activo. El workflow eliminado tenía modo test y parámetros de mes/año; el actual es más simple |
| `abcd420` | Corrección de migración | Hubo un problema con migraciones que requirió corrección manual |
| `9238ba3` / `1c4bf24` | Actualizaciones de README y WARP | Documentación sincronizada después de cambios de arquitectura |
| `095b018` → `eefe0fe` | Múltiples iteraciones en `EnvioReporteMensual.yml` | El workflow pasó por ~8 correcciones seguidas — indica que la configuración de secrets/vars de GitHub fue el punto más problemático |
| `aa13868` / `c0edd37` | Correcciones de settings | Problemas con configuración de `settings.py` durante el ajuste del workflow |
| `c853ac7` / `3ea6808` | Correcciones de librerías | Problemas de dependencias al ejecutar en el runner de GitHub Actions |

**Patrón observado:** La mayor parte de los commits recientes son iteraciones sobre el workflow de GitHub Actions y su conexión con las variables de entorno. El código Django en sí está estable.

---

## Integraciones Externas

| Servicio | Variable clave | Uso |
|---|---|---|
| PostgreSQL (DigitalOcean) | `DJANGO_DB_URL` | Base de datos principal |
| DigitalOcean Spaces | `DO_SPACES_*` | Fotos de tickets, reportes Excel, archivos estáticos en producción |
| SendGrid | `EMAIL_HOST_PASSWORD` | Envío de reportes y notificaciones por email |
| WhatsApp Business API | `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` | Envío de reportes mensuales y alertas |
| GitHub Actions | GitHub Secrets (environment: `secrets`) | Automatización del reporte mensual |
| Redis | `CELERY_BROKER_URL` | Solo necesario si se activa Celery localmente |

**Nota:** El workflow de GitHub Actions usa `vars.*` (Variables de entorno del repositorio), NO `secrets.*`. Esto es una decisión consciente — las vars son visibles en los logs de Actions, lo que facilita el debugging pero implica que `SECRET_KEY` y credenciales de BD no son completamente ocultos en ese contexto.
