from django import forms

from registros.models import Registro
from combustible.sendmail import sendMail


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Registro
        fields = [
                    'numero_tiket',
                    'idEquipo', 
                    'idOperador',
                    'Litros',
                    'Litros',
                    'costolitro',
                    'kilometraje',
                    'photo_tiket'
                  ]

    def save(self):
        Registro.objects.create(
            numero_tiket = self.cleaned_data["numero_tiket"],
            idEquipo = self.cleaned_data["idEquipo"],
            idOperador = self.cleaned_data["idOperador"],
            Litros = self.cleaned_data["Litros"],
            costolitro = self.cleaned_data["costolitro"],
            kilometraje = self.cleaned_data["kilometraje"],
            photo_tiket = self.cleaned_data["photo_tiket"],
        )
        email=self.cleaned_data["idOperador"].email
        titulo="Registro de ticket"
        contenido = f"Numero de ticket: {self.cleaned_data["numero_tiket"]} Cantidad:{self.cleaned_data["Litros"]}"
        sendMail(email, titulo, contenido)