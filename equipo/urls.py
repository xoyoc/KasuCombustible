from django.urls import path

from equipo.views import TeamListView, TeamFormView, EquipoUpdateView, EquipoDeleteView

urlpatterns = [
    path('', TeamListView.as_view(), name='equipo_list'),
    path('nuevo/', TeamFormView.as_view(), name='equipo_create'),
    path('<int:pk>/', EquipoUpdateView.as_view(), name='equipo_detail'),
    path('<int:pk>/editar/', EquipoUpdateView.as_view(), name='equipo_update'),
    path('<int:pk>/eliminar/', EquipoDeleteView.as_view(), name='equipo_delete'),
]
