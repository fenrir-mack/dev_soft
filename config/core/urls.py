from django.urls import path
from .views import ping, home

urlpatterns = [
    path("", home),      # 👈 empty path now points to home
    path("ping/", ping),
]



