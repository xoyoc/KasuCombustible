from django import forms
from equipo.models import Equipo


class TeamForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = [
            'numero_economico', 'placa', 'niv',
            'marca', 'modelo', 'year',
            'tipo_combustible', 'capacidad_tanque', 'rendimiento',
            'asignacion',
        ]
