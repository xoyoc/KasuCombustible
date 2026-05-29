from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect

from equipo.forms import TeamForm
from equipo.models import Equipo


class TeamListView(generic.ListView):
    model = Equipo
    template_name = "equipo/list_equipo.html"
    context_object_name = 'equipos'


class TeamFormView(generic.CreateView):
    model = Equipo
    form_class = TeamForm
    template_name = "equipo/add_equipo.html"
    success_url = reverse_lazy('equipo_list')


class EquipoUpdateView(generic.UpdateView):
    model = Equipo
    form_class = TeamForm
    template_name = "equipo/add_equipo.html"
    success_url = reverse_lazy('equipo_list')


class EquipoDeleteView(generic.DeleteView):
    model = Equipo
    success_url = reverse_lazy('equipo_list')

    def get(self, request, *args, **kwargs):
        return redirect('equipo_list')
