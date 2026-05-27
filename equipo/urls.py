"""
URL configuration for combustible project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from equipo.views import TeamListView, my_view_detalle, TeamFormView


urlpatterns = [
    path('', TeamListView.as_view(), name='equipo_list'),
    path('nuevo/', TeamFormView.as_view(), name='equipo_create'),
    path('<int:pk>/', my_view_detalle, name='equipo_detail'),
    path('<int:pk>/editar/', my_view_detalle, name='equipo_update'),
    path('<int:pk>/eliminar/', my_view_detalle, name='equipo_delete'),
]
