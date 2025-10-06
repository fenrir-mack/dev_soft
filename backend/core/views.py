from django.shortcuts import render

from django.shortcuts import render

def admin_view(request):
    return render(request, 'admin.html')

def chat_view(request):
    return render(request, 'chat.html')

def custom_path_view(request):
    return render(request, 'custom-path.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')

def index_view(request):
    return render(request, 'index.html')

def path_details_view(request):
    return render(request, 'path-details.html')

def predefined_paths_view(request):
    return render(request, 'predefined-paths.html')
