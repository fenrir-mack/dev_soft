from django.urls import path
from . import views

app_name = 'trilhas'  # ⬅️ required for reverse_lazy to work

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('explorar/', views.explorar_view, name='todas_trilhas'),
    path('detalhes-da-trilha/', views.detalhes_da_trilha_view, name='ver_etapas'),
    path('minhas-trilhas/', views.minhas_trilhas_view, name='minhas_trilhas'),
    path("toggle-topico/", views.toggle_topico, name="toggle_topico"),

]
