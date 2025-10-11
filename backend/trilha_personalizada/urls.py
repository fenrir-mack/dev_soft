from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_path_view, name='trilha_personalizada'),
]
