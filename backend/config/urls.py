from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('trilhas/', include('trilhas.urls')),
    path('trilha-personalizada/', include('trilha_personalizada.urls')),
    path('admin-page/', include('admin_custom.urls')),

    path('dashboard/', RedirectView.as_view(url=reverse_lazy('trilhas:dashboard'), permanent=False)),
    path('explorar/', RedirectView.as_view(url=reverse_lazy('trilhas:todas_trilhas'), permanent=False)),
    path('detalhes-da-trilha/', RedirectView.as_view(url=reverse_lazy('trilhas:ver_etapas'), permanent=False)),
    path('velho-detalhes-da-trilha/', RedirectView.as_view(url=reverse_lazy('trilhas:velho_ver_etapas'), permanent=False)),
    path('minhas-trilhas/', RedirectView.as_view(url=reverse_lazy('trilhas:minhas_trilhas'), permanent=False)),
]