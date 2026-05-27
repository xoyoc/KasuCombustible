from django.urls import path

from operador.views import OperationFormView, OperationListView

def my_view(request):
    return "Prueba vista de operadores"

urlpatterns = [
    path('', OperationListView.as_view(), name='operador_list'),
    path('nuevo/', OperationFormView.as_view(), name='operador_create'),
    path('<int:pk>/',  my_view, name='operador_detail'),
    path('<int:pk>/editar/',  my_view, name='operador_update'),
    path('<int:pk>/eliminar/',  my_view, name='operador_delete'),
]