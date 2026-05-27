from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse
from django.shortcuts import render

from equipo.forms import TeamForm
from equipo.models import Equipo


# Create your views here.
class TeamListView(generic.ListView):
    model = Equipo
    template_name="equipo/list_equipo.html"
    context_object_name = 'equipos'

class TeamFormView(generic.FormView):
    template_name = "equipo/add_equipo.html"
    form_class = TeamForm
    success_url = reverse_lazy('add_team')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    

def my_test_view(request):
    return HttpResponse("Prueba vista de equipo")

def my_view_detalle(request, *args, **kwargs):
    print(args)
    print(kwargs)
    return HttpResponse("Prueba vista de equipo detallado")
