from django import forms

from equipo.models import Equipo


class TeamForm(forms.Form):
    placa = forms.CharField(max_length=50, label="Placa")
    modelo = forms.CharField(max_length=100, label="Modelo")
    marca = forms.CharField(max_length=100, label="Marca")
    year = forms.IntegerField(label="Año")
    capacidad_tanque = forms.IntegerField(label="Capacidad del tanque")

    def save(self):
        Equipo.objects.create(
            placa=self.cleaned_data["placa"],
            modelo=self.cleaned_data["modelo"],
            marca=self.cleaned_data["marca"],
            year=self.cleaned_data["year"],
            capacidad_tanque=self.cleaned_data["capacidad_tanque"],
        )
