from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.index_view, name='login'),
    path('logout/',csrf_exempt(auth_views.LogoutView.as_view(next_page='login')),name='logout'),
]
