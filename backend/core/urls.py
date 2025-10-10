from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'), # Login
    path('admin-page/', views.admin_view, name='admin'), # pagina do admin
    path('custom-path/', views.custom_path_view, name='custom-path'), # criar trilha pers
    path('dashboard/', views.dashboard_view, name='dashboard'), # junta as informações
    path('path-details/', views.path_details_view, name='path-details'), # legacy, vai ser deletado
    path('predefined-paths/', views.predefined_paths_view, name='predefined-paths'), # Buscar trilhas predefinidas
    path('all-paths/', views.all_paths_view, name='all-paths'), # Trilhas Salvas
    path('study-guide/', views.study_guide_view, name='study-guide'), # Detalhes da trilha
]
