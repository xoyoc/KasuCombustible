from django import forms

from operador.models import Operador


class OperationForm(forms.Form):
    nombre = forms.CharField(max_length=150, label="Nombre completo")
    email = forms.EmailField(label="Correo Electronico")
    movil = forms.CharField(max_length=10, label="Numero Celular")

    def save(self):
        Operador.objects.create(
            nombre=self.cleaned_data["nombre"],
            email=self.cleaned_data["email"],
            movil=self.cleaned_data["movil"],
        )
