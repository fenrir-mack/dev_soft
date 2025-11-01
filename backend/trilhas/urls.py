from django.urls import path
from . import views

app_name = 'trilhas'  # ⬅️ required for reverse_lazy to work

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('explorar/', views.predefined_paths_view, name='todas_trilhas'),
    path('detalhes-da-trilha/', views.study_guide_view, name='ver_etapas'),
    path('minhas-trilhas/', views.all_paths_view, name='minhas_trilhas'),
    path("toggle-topico/", views.toggle_topico, name="toggle_topico"),

]
