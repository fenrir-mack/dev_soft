from django.shortcuts import render

def dashboard_view(request):
    """Página do dashboard principal."""
    return render(request, 'trilhas/dashboard.html')
def predefined_paths_view(request):
    """Lista de trilhas pré-definidas."""
    return render(request, 'trilhas/predefined-paths.html')
def study_guide_view(request):
    """Nova página de detalhes da trilha."""
    return render(request, 'trilhas/study-guide.html')
def path_details_view(request):
    """Versão antiga dos detalhes da trilha."""
    return render(request, 'trilhas/path-details.html')
def all_paths_view(request):
    """Trilhas salvas do usuário."""
    return render(request, 'trilhas/all-paths.html')
