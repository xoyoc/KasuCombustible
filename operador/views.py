from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import TemplateView
from django.shortcuts import render

from operador.forms import OperationForm
from operador.models import Operador

# Create your views here.


class OperationFormView(generic.FormView):
    template_name = "operador/add_operador.html"
    form_class = OperationForm
    success_url = reverse_lazy("add_operation")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class OperationListView(generic.ListView):
    model = Operador
    template_name="operador/list_operador.html"
    context_object_name = 'operadores'