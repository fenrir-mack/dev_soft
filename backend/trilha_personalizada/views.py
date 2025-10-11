from django.shortcuts import render

def custom_path_view(request):
    """Criação de trilhas personalizadas com IA."""
    return render(request, 'trilha_personalizada/custom-path.html')
