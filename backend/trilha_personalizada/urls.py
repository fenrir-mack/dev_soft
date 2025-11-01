from django.urls import path
from . import views

app_name = 'trilha_personalizada'

urlpatterns = [
    path('', views.custom_path_view, name='trilha_personalizada'),
    path('salvar/', views.salvar_trilha_view, name='salvar_trilha'),
]
