from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect

from operador.forms import OperationForm
from operador.models import Operador


class OperationListView(generic.ListView):
    model = Operador
    template_name = "operador/list_operador.html"
    context_object_name = 'operadores'


class OperationFormView(generic.CreateView):
    model = Operador
    form_class = OperationForm
    template_name = "operador/add_operador.html"
    success_url = reverse_lazy("operador_list")


class OperadorUpdateView(generic.UpdateView):
    model = Operador
    form_class = OperationForm
    template_name = "operador/add_operador.html"
    success_url = reverse_lazy("operador_list")


class OperadorDeleteView(generic.DeleteView):
    model = Operador
    success_url = reverse_lazy('operador_list')

    def get(self, request, *args, **kwargs):
        return redirect('operador_list')
