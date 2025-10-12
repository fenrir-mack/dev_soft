from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

User = get_user_model()


def index_view(request):
    if request.method == 'POST':
        type_access = request.POST.get('action')
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(email, password)
        if type_access == "login":
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('trilhas:dashboard')
            else:
                messages.error(request, 'Email ou senha incorretos.')
                return redirect('login')
        elif type_access == 'signup':
            name = request.POST.get('name')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                messages.error(request, 'As senhas não coincidem.')
            elif User.objects.filter(username=email).exists():
                messages.error(request, 'Email já registrado.')
            else:
                user = User.objects.create_user(username=email, email=email, password=password, full_name=name)
                login(request, user)
                return redirect('trilhas:dashboard')

    return render(request, 'users/index.html')
