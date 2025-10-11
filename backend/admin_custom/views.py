from django.shortcuts import render

def admin_view(request):
    """Página de administração customizada (CRUD)."""
    return render(request, 'admin_custom/admin.html')
