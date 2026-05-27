from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
import json
from django.core.paginator import Paginator

from .models import (Mantenimiento, TipoMantenimiento, 
                     Notificacion, ReporteMantenimiento)
from operador.models import Operador, Supervisor
from equipo.models import Equipo
from .forms import MantenimientoForm, EquipoForm

def dashboard(request):
    # Estadísticas generales
    total_equipos = Equipo.objects.filter(activo=True).count()
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        estado='pendiente',
        fecha_programada__lte=timezone.now().date()
    ).count()
    mantenimientos_vencidos = Mantenimiento.objects.filter(estado='vencido').count()
    
    # Equipos que necesitan mantenimiento
    equipos_mantenimiento = []
    for equipo in Equipo.objects.filter(activo=True):
        if equipo.necesita_mantenimiento():
            equipos_mantenimiento.append(equipo)
    
    # Próximos mantenimientos (próximos 30 días)
    proximos_mantenimientos = Mantenimiento.objects.filter(
        estado='pendiente',
        fecha_programada__lte=timezone.now().date() + timedelta(days=30)
    ).order_by('fecha_programada')[:10]
    
    # Notificaciones recientes
    notificaciones_recientes = Notificacion.objects.all()[:10]
    
    context = {
        'total_equipos': total_equipos,
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'mantenimientos_vencidos': mantenimientos_vencidos,
        'equipos_mantenimiento': equipos_mantenimiento,
        'proximos_mantenimientos': proximos_mantenimientos,
        'notificaciones_recientes': notificaciones_recientes,
    }
    
    return render(request, 'mantenimientos/dashboard.html', context)

class MantenimientoListView(ListView):
    model = Mantenimiento
    template_name = 'mantenimientos/mantenimiento_list.html'
    context_object_name = 'mantenimientos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Mantenimiento.objects.select_related('equipo', 'operador', 'tipo_mantenimiento')
        
        # Filtros
        estado = self.request.GET.get('estado')
        equipo_id = self.request.GET.get('equipo')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        if fecha_desde:
            queryset = queryset.filter(fecha_programada__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_programada__lte=fecha_hasta)
            
        return queryset.order_by('-fecha_programada')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipos'] = Equipo.objects.filter(activo=True)
        context['estados'] = Mantenimiento.ESTADO_CHOICES
        return context

class MantenimientoCreateView(CreateView):
    model = Mantenimiento
    form_class = MantenimientoForm
    template_name = 'mantenimientos/mantenimiento_form.html'
    success_url = reverse_lazy('mantenimiento:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Mantenimiento creado exitosamente.')
        return super().form_valid(form)

class MantenimientoUpdateView(UpdateView):
    model = Mantenimiento
    form_class = MantenimientoForm
    template_name = 'mantenimientos/mantenimiento_form.html'
    success_url = reverse_lazy('mantenimiento:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Mantenimiento actualizado exitosamente.')
        return super().form_valid(form)

def completar_mantenimiento(request, pk):
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    
    if request.method == 'POST':
        kilometraje = request.POST.get('kilometraje_actual')
        observaciones = request.POST.get('observaciones', '')
        costo = request.POST.get('costo')
        
        try:
            if kilometraje:
                mantenimiento.equipo.kilometraje_actual = int(kilometraje)
                mantenimiento.equipo.save()
                mantenimiento.kilometraje_en_mantenimiento = int(kilometraje)
            
            if costo:
                mantenimiento.costo = float(costo)
            
            mantenimiento.observaciones = observaciones
            mantenimiento.completado = True
            mantenimiento.save()
            
            # Crear próximo mantenimiento automáticamente
            crear_proximo_mantenimiento(mantenimiento)
            
            messages.success(request, 'Mantenimiento completado exitosamente.')
            return redirect('mantenimiento:list')
            
        except Exception as e:
            messages.error(request, f'Error al completar mantenimiento: {str(e)}')
    
    return render(request, 'mantenimientos/completar_mantenimiento.html', {
        'mantenimiento': mantenimiento
    })

def crear_proximo_mantenimiento(mantenimiento_completado):
    """Crear automáticamente el próximo mantenimiento"""
    equipo = mantenimiento_completado.equipo
    proximo = equipo.proximo_mantenimiento()
    
    nuevo_mantenimiento = Mantenimiento.objects.create(
        equipo=equipo,
        operador=mantenimiento_completado.operador,
        tipo_mantenimiento=mantenimiento_completado.tipo_mantenimiento,
        fecha_programada=proximo['fecha'],
        kilometraje_programado=proximo['kilometraje'],
        estado='pendiente'
    )
    
    # Programar notificaciones
    programar_notificaciones(nuevo_mantenimiento)
    
    return nuevo_mantenimiento

def programar_notificaciones(mantenimiento):
    """Programar notificaciones automáticas para un mantenimiento"""
    from .tasks import crear_notificaciones_mantenimiento
    
    # Crear notificaciones en la base de datos
    crear_notificaciones_mantenimiento(mantenimiento.id)

def equipos_estado(request):
    """Vista para mostrar el estado de mantenimiento de todos los equipos"""
    equipos = Equipo.objects.filter(activo=True)
    equipos_data = []
    
    for equipo in equipos:
        proximo = equipo.proximo_mantenimiento()
        ultimo_mantenimiento = equipo.mantenimientos.filter(completado=True).order_by('-fecha_completado').first()
        
        equipos_data.append({
            'equipo': equipo,
            'proximo_mantenimiento': proximo,
            'ultimo_mantenimiento': ultimo_mantenimiento,
            'necesita_mantenimiento': equipo.necesita_mantenimiento(),
            'mantenimiento_proximo': equipo.mantenimiento_proximo(),
        })
    
    return render(request, 'mantenimientos/equipos_estado.html', {
        'equipos_data': equipos_data
    })

def notificaciones_list(request):
    """Lista de todas las notificaciones"""
    notificaciones = Notificacion.objects.select_related('mantenimiento__equipo').order_by('-fecha_creacion')
    
    # Filtros
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    
    if tipo:
        notificaciones = notificaciones.filter(tipo=tipo)
    if estado:
        notificaciones = notificaciones.filter(estado=estado)
    
    paginator = Paginator(notificaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tipos': Notificacion.TIPO_CHOICES,
        'estados': Notificacion.ESTADO_CHOICES,
    }
    
    return render(request, 'mantenimientos/notificaciones_list.html', context)

def reporte_mantenimientos(request):
    """Generar reporte de mantenimientos"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    equipo_id = request.GET.get('equipo')
    
    # Filtros por defecto (último mes)
    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
    
    mantenimientos = Mantenimiento.objects.filter(
        fecha_programada__range=[fecha_inicio, fecha_fin]
    ).select_related('equipo', 'operador', 'tipo_mantenimiento')
    
    if estado:
        mantenimientos = mantenimientos.filter(estado=estado)
    if equipo_id:
        mantenimientos = mantenimientos.filter(equipo_id=equipo_id)
    
    # Estadísticas
    total_mantenimientos = mantenimientos.count()
    completados = mantenimientos.filter(completado=True).count()
    pendientes = mantenimientos.filter(estado='pendiente').count()
    vencidos = mantenimientos.filter(estado='vencido').count()
    costo_total = sum([m.costo for m in mantenimientos if m.costo])
    
    context = {
        'mantenimientos': mantenimientos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_mantenimientos': total_mantenimientos,
        'completados': completados,
        'pendientes': pendientes,
        'vencidos': vencidos,
        'costo_total': costo_total,
        'equipos': Equipo.objects.filter(activo=True),
        'estados': Mantenimiento.ESTADO_CHOICES,
    }
    
    return render(request, 'mantenimientos/reporte_mantenimientos.html', context)

def api_equipos_mantenimiento(request):
    """API para obtener estado de mantenimiento de equipos (para gráficos)"""
    equipos = Equipo.objects.filter(activo=True)
    data = {
        'labels': [],
        'necesitan_mantenimiento': [],
        'proximos': [],
        'al_dia': []
    }
    
    for equipo in equipos:
        data['labels'].append(equipo.placa)
        if equipo.necesita_mantenimiento():
            data['necesitan_mantenimiento'].append(1)
            data['proximos'].append(0)
            data['al_dia'].append(0)
        elif equipo.mantenimiento_proximo():
            data['necesitan_mantenimiento'].append(0)
            data['proximos'].append(1)
            data['al_dia'].append(0)
        else:
            data['necesitan_mantenimiento'].append(0)
            data['proximos'].append(0)
            data['al_dia'].append(1)
    
    return JsonResponse(data)

def enviar_notificacion_manual(request, pk):
    """Enviar notificación manualmente"""
    notificacion = get_object_or_404(Notificacion, pk=pk)
    
    if request.method == 'POST':
        notificacion.enviar()
        if notificacion.estado == 'enviada':
            messages.success(request, 'Notificación enviada exitosamente.')
        else:
            messages.error(request, f'Error al enviar notificación: {notificacion.error_mensaje}')
    
    return redirect('mantenimiento:notificaciones')

def actualizar_kilometraje(request, equipo_id):
    """Actualizar el kilometraje actual de un equipo"""
    equipo = get_object_or_404(Equipo, pk=equipo_id)
    
    if request.method == 'POST':
        nuevo_kilometraje = request.POST.get('kilometraje')
        try:
            equipo.kilometraje_actual = int(nuevo_kilometraje)
            equipo.save()
            messages.success(request, f'Kilometraje actualizado para {equipo.placa}')
        except ValueError:
            messages.error(request, 'El kilometraje debe ser un número válido')
    
    return redirect('mantenimiento:equipos_estado')