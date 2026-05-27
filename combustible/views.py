from django.shortcuts import render
from django.views.generic import TemplateView

from equipo.models import Equipo
from operador.models import Operador
from registros.models import Registro

class CombustibleView(TemplateView):
    template_name = "combustible/inicio.html"


def estadistica(request):
    equipos = Equipo.objects.all().count()
    operadores = Operador.objects.all().count()
    registros = Registro.objects.all()
    context= {
        'equipos': equipos,
        'operadores': operadores,
        'registros': registros
    }
    return render(request, 'combustible/inicio.html', context=context)
