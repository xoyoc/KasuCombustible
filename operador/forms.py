from django import forms
from operador.models import Operador


class OperationForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['nombre', 'email', 'movil']
