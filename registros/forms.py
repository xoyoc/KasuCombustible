from django import forms
from django.utils import timezone

from registros.models import Registro


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Registro
        fields = [
            'idEquipo',
            'idOperador',
            'numero_tiket',
            'Litros',
            'costolitro',
            'kilometraje',
            'photo_tiket',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero_tiket'].required = False
        self.fields['kilometraje'].required = False
        self.fields['photo_tiket'].required = False

    def clean(self):
        cleaned_data = super().clean()
        equipo = cleaned_data.get('idEquipo')
        numero_tiket = (cleaned_data.get('numero_tiket') or '').strip()

        if equipo and equipo.tipo_combustible == 'diesel':
            ts = timezone.now().strftime('%Y%m%d%H%M')
            cleaned_data['numero_tiket'] = f"DIESEL-{equipo.numero_economico}-{ts}"
            cleaned_data['kilometraje'] = equipo.kilometraje_actual
            cleaned_data['photo_tiket'] = None
        elif not numero_tiket:
            self.add_error('numero_tiket', 'Este campo es obligatorio para unidades de gasolina.')

        return cleaned_data
