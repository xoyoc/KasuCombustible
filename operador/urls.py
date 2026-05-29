from django.urls import path

from operador.views import OperationListView, OperationFormView, OperadorUpdateView, OperadorDeleteView

urlpatterns = [
    path('', OperationListView.as_view(), name='operador_list'),
    path('nuevo/', OperationFormView.as_view(), name='operador_create'),
    path('<int:pk>/', OperadorUpdateView.as_view(), name='operador_detail'),
    path('<int:pk>/editar/', OperadorUpdateView.as_view(), name='operador_update'),
    path('<int:pk>/eliminar/', OperadorDeleteView.as_view(), name='operador_delete'),
]
