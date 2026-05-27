from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import (
    TipoMantenimiento, Mantenimiento, 
    Notificacion, ReporteMantenimiento
)
from equipo.models import Equipo
from operador.models import Operador, Supervisor

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'marca', 'modelo', 'year', 'kilometraje_actual', 'estado_mantenimiento', 'activo']
    list_filter = ['marca', 'year', 'activo']
    search_fields = ['placa', 'marca', 'modelo']
    list_editable = ['kilometraje_actual', 'activo']
    ordering = ['placa']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('placa', 'marca', 'modelo', 'year')
        }),
        ('Especificaciones', {
            'fields': ('capacidad_tanque', 'kilometraje_actual')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def estado_mantenimiento(self, obj):
        if obj.necesita_mantenimiento():
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Necesita Mantenimiento</span>'
            )
        elif obj.mantenimiento_proximo():
            return format_html(
                '<span style="color: orange; font-weight: bold;">🔔 Próximo Mantenimiento</span>'
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Al Día</span>'
            )
    estado_mantenimiento.short_description = 'Estado de Mantenimiento'
    
    actions = ['marcar_activo', 'marcar_inactivo', 'actualizar_kilometraje']
    
    def marcar_activo(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} equipos marcados como activos.')
    marcar_activo.short_description = "Marcar equipos seleccionados como activos"
    
    def marcar_inactivo(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} equipos marcados como inactivos.')
    marcar_inactivo.short_description = "Marcar equipos seleccionados como inactivos"

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'movil', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'email']
    list_editable = ['activo']
    ordering = ['nombre']
    
    def total_equipos_asignados(self, obj):
        return obj.mantenimientos.filter(
            estado__in=['pendiente', 'en_proceso']
        ).values('equipo').distinct().count()
    total_equipos_asignados.short_description = 'Equipos Asignados'

@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'telefono', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'email']
    list_editable = ['activo']
    ordering = ['nombre']


@admin.register(TipoMantenimiento)
class TipoMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'total_mantenimientos']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    
    def total_mantenimientos(self, obj):
        return obj.mantenimiento_set.count()
    total_mantenimientos.short_description = 'Total Mantenimientos'


class NotificacionInline(admin.TabularInline):
    model = Notificacion
    extra = 0
    readonly_fields = ['fecha_creacion', 'fecha_enviada', 'estado']
    fields = ['tipo', 'destinatario_email', 'estado', 'fecha_programada', 'fecha_enviada']


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = [
        'equipo', 'operador', 'tipo_mantenimiento', 'fecha_programada', 
        'estado_badge', 'dias_para_vencer', 'km_para_vencer', 'completado'
    ]
    list_filter = [
        'estado', 'completado', 'tipo_mantenimiento', 
        'fecha_programada', 'equipo__marca'
    ]
    search_fields = [
        'equipo__placa', 'operador__nombre', 'tipo_mantenimiento__nombre'
    ]
    date_hierarchy = 'fecha_programada'
    ordering = ['-fecha_programada']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('equipo', 'operador', 'tipo_mantenimiento')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'kilometraje_programado')
        }),
        ('Estado', {
            'fields': ('estado', 'completado')
        }),
        ('Realización', {
            'fields': ('fecha_completado', 'kilometraje_en_mantenimiento', 'costo'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    inlines = [NotificacionInline]
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': 'orange',
            'en_proceso': 'blue',
            'completado': 'green',
            'vencido': 'red'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def dias_para_vencer(self, obj):
        if obj.completado:
            return format_html('<span style="color: green;">✅ Completado</span>')
        
        dias = (obj.fecha_programada - timezone.now().date()).days
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} días vencido</span>',
                abs(dias)
            )
        elif dias <= 5:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🔔 {} días</span>',
                dias
            )
        else:
            return format_html('<span style="color: green;">{} días</span>', dias)
    dias_para_vencer.short_description = 'Días para Vencer'
    
    def km_para_vencer(self, obj):
        if obj.completado:
            return format_html('<span style="color: green;">✅ Completado</span>')
        
        km_restantes = obj.kilometraje_programado - obj.equipo.kilometraje_actual
        if km_restantes <= 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} km sobre límite</span>',
                abs(km_restantes)
            )
        elif km_restantes <= 100:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🔔 {} km</span>',
                km_restantes
            )
        else:
            return format_html('<span style="color: green;">{:,} km</span>', km_restantes)
    km_para_vencer.short_description = 'KM para Vencer'
    
    actions = ['marcar_completado', 'enviar_recordatorio', 'generar_reporte']
    
    def marcar_completado(self, request, queryset):
        updated = 0
        for mantenimiento in queryset.filter(completado=False):
            mantenimiento.completado = True
            mantenimiento.fecha_completado = timezone.now()
            mantenimiento.save()
            updated += 1
        self.message_user(request, f'{updated} mantenimientos marcados como completados.')
    marcar_completado.short_description = "Marcar como completado"
    
    def enviar_recordatorio(self, request, queryset):
        from .tasks import crear_notificacion_recordatorio
        enviados = 0
        for mantenimiento in queryset.filter(completado=False):
            crear_notificacion_recordatorio.delay(mantenimiento.id)
            enviados += 1
        self.message_user(request, f'Recordatorios enviados para {enviados} mantenimientos.')
    enviar_recordatorio.short_description = "Enviar recordatorio"


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = [
        'asunto_corto', 'tipo', 'destinatario_email', 'equipo_relacionado',
        'estado_badge', 'fecha_programada', 'fecha_enviada'
    ]
    list_filter = ['tipo', 'estado', 'fecha_creacion', 'fecha_programada']
    search_fields = ['asunto', 'destinatario_email', 'mantenimiento__equipo__placa']
    date_hierarchy = 'fecha_creacion'
    ordering = ['-fecha_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('mantenimiento', 'tipo', 'destinatario_email')
        }),
        ('Contenido', {
            'fields': ('asunto', 'mensaje')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'estado')
        }),
        ('Resultado', {
            'fields': ('fecha_enviada', 'error_mensaje'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_enviada']
    
    def asunto_corto(self, obj):
        return obj.asunto[:50] + '...' if len(obj.asunto) > 50 else obj.asunto
    asunto_corto.short_description = 'Asunto'
    
    def equipo_relacionado(self, obj):
        if obj.mantenimiento:
            return obj.mantenimiento.equipo.placa
        return '-'
    equipo_relacionado.short_description = 'Equipo'
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': 'orange',
            'enviada': 'green',
            'fallida': 'red'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    actions = ['enviar_ahora', 'marcar_pendiente']
    
    def enviar_ahora(self, request, queryset):
        from .tasks import enviar_notificacion
        enviadas = 0
        for notificacion in queryset.filter(estado__in=['pendiente', 'fallida']):
            enviar_notificacion.delay(notificacion.id)
            enviadas += 1
        self.message_user(request, f'{enviadas} notificaciones enviadas.')
    enviar_ahora.short_description = "Enviar ahora"
    
    def marcar_pendiente(self, request, queryset):
        updated = queryset.update(estado='pendiente')
        self.message_user(request, f'{updated} notificaciones marcadas como pendientes.')
    marcar_pendiente.short_description = "Marcar como pendiente"


@admin.register(ReporteMantenimiento)
class ReporteMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_reporte', 'fecha_inicio', 'fecha_fin', 'fecha_generacion', 'total_mantenimientos']
    list_filter = ['tipo_reporte', 'fecha_generacion']
    search_fields = ['titulo', 'generado_por']
    date_hierarchy = 'fecha_generacion'
    ordering = ['-fecha_generacion']
    
    readonly_fields = ['fecha_generacion']
    
    def total_mantenimientos(self, obj):
        return obj.mantenimientos_incluidos.count()
    total_mantenimientos.short_description = 'Total Mantenimientos'


# Configuración del admin site
admin.site.site_header = "Sistema de Mantenimiento de Equipos"
admin.site.site_title = "Mantenimiento Admin"
admin.site.index_title = "Administración del Sistema de Mantenimiento"

# Dashboard personalizado con widgets
class DashboardAdmin(admin.AdminSite):
    site_header = "Dashboard de Mantenimiento"
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Estadísticas para el dashboard
        hoy = timezone.now().date()
        
        extra_context.update({
            'total_equipos': Equipo.objects.filter(activo=True).count(),
            'mantenimientos_pendientes': Mantenimiento.objects.filter(
                estado='pendiente',
                fecha_programada__lte=hoy
            ).count(),
            'mantenimientos_vencidos': Mantenimiento.objects.filter(estado='vencido').count(),
            'notificaciones_pendientes': Notificacion.objects.filter(estado='pendiente').count(),
            'equipos_necesitan_mantenimiento': [
                equipo for equipo in Equipo.objects.filter(activo=True) 
                if equipo.necesita_mantenimiento()
            ][:5],  # Solo los primeros 5
        })
        
        return super().index(request, extra_context)

# Crear instancia del dashboard personalizado
dashboard_admin = DashboardAdmin(name='dashboard_admin')

# Registrar modelos en el dashboard personalizado
dashboard_admin.register(Equipo, EquipoAdmin)
dashboard_admin.register(Mantenimiento, MantenimientoAdmin)
dashboard_admin.register(Notificacion, NotificacionAdmin)