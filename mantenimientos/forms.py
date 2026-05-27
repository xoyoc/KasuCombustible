from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Mantenimiento, Equipo, Operador, TipoMantenimiento, Supervisor

class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = [
            'equipo', 'operador', 'tipo_mantenimiento', 
            'fecha_programada', 'kilometraje_programado', 
            'observaciones', 'costo'
        ]
        widgets = {
            'equipo': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'operador': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'tipo_mantenimiento': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'fecha_programada': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'kilometraje_programado': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 3
            }),
            'costo': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo equipos y operadores activos
        self.fields['equipo'].queryset = Equipo.objects.filter(activo=True)
        self.fields['operador'].queryset = Operador.objects.filter(activo=True)
        
        # Si se está editando, calcular valores sugeridos
        if not self.instance.pk:
            equipo_id = self.data.get('equipo') or self.initial.get('equipo')
            if equipo_id:
                try:
                    equipo = Equipo.objects.get(pk=equipo_id)
                    proximo = equipo.proximo_mantenimiento()
                    self.initial['fecha_programada'] = proximo['fecha']
                    self.initial['kilometraje_programado'] = proximo['kilometraje']
                except Equipo.DoesNotExist:
                    pass
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_programada = cleaned_data.get('fecha_programada')
        equipo = cleaned_data.get('equipo')
        kilometraje_programado = cleaned_data.get('kilometraje_programado')
        
        # Validar que la fecha no sea en el pasado (excepto para edición)
        if fecha_programada and not self.instance.pk:
            if fecha_programada < timezone.now().date():
                raise forms.ValidationError('La fecha programada no puede ser en el pasado.')
        
        # Validar que el kilometraje sea mayor al actual del equipo
        if equipo and kilometraje_programado:
            if kilometraje_programado <= equipo.kilometraje_actual:
                raise forms.ValidationError(
                    f'El kilometraje programado debe ser mayor al actual del equipo ({equipo.kilometraje_actual} km).'
                )
        
        return cleaned_data

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['placa', 'modelo', 'marca', 'year', 'capacidad_tanque', 'kilometraje_actual', 'activo']
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'capacidad_tanque': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'kilometraje_actual': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }

class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['nombre', 'email', 'movil', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'movil': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }

class SupervisorForm(forms.ModelForm):
    class Meta:
        model = Supervisor
        fields = ['nombre', 'email', 'telefono', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }

class FiltroMantenimientoForm(forms.Form):
    equipo = forms.ModelChoiceField(
        queryset=Equipo.objects.filter(activo=True),
        required=False,
        empty_label="Todos los equipos",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Mantenimiento.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )

class ActualizarKilometrajeForm(forms.Form):
    kilometraje = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Nuevo kilometraje'
        })
    )
    
    def __init__(self, equipo=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if equipo:
            self.fields['kilometraje'].initial = equipo.kilometraje_actual
            self.fields['kilometraje'].widget.attrs['min'] = equipo.kilometraje_actual

class CompletarMantenimientoForm(forms.Form):
    kilometraje_actual = forms.IntegerField(
        label="Kilometraje actual del equipo",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    observaciones = forms.CharField(
        label="Observaciones del mantenimiento",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'rows': 4,
            'placeholder': 'Detalles del mantenimiento realizado...'
        })
    )
    costo = forms.DecimalField(
        label="Costo del mantenimiento",
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '0.00'
        })
    )
    
    def __init__(self, mantenimiento=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if mantenimiento:
            self.fields['kilometraje_actual'].initial = mantenimiento.equipo.kilometraje_actual
            self.fields['observaciones'].initial = mantenimiento.observaciones
            self.fields['costo'].initial = mantenimiento.costo