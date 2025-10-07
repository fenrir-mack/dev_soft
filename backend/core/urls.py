from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('admin-page/', views.admin_view, name='admin'),
    path('custom-path/', views.custom_path_view, name='custom-path'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('path-details/', views.path_details_view, name='path-details'),
    path('predefined-paths/', views.predefined_paths_view, name='predefined-paths'),
]
