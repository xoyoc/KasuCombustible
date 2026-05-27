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

from registros import views


urlpatterns = [
    path('', views.RegisterListView.as_view(), name='registro_list'),
    path('nuevo/', views.RegisterFormView.as_view(), name='registro_create'),
    path('<int:pk>/', views.RegisterDetailView.as_view(), name='registro_detail'),
    path('<int:pk>/editar/', views.RegisterFormView.as_view(), name='registro_update'),
    path('<int:pk>/eliminar/', views.RegisterDeleteView.as_view(), name='registro_delete'),
    path('webhook/whatsapp/', views.WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
]