from django.shortcuts import render

def index_view(request):
    """Página inicial (login)."""
    return render(request, 'users/index.html')
