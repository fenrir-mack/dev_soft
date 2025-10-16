from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

User = get_user_model()


def index_view(request):
    active_tab = 'login'  # default

    if request.method == 'POST':
        type_access = request.POST.get('action')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if type_access == "login":
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('trilhas:dashboard')
            else:
                messages.error(request, 'Email ou senha incorretos.')
                active_tab = 'login'
        elif type_access == 'signup':
            name = request.POST.get('name')
            nickname = request.POST.get('nickname')
            confirm_password = request.POST.get('confirm_password')
            active_tab = 'signup'  # make signup tab active

            if password != confirm_password:
                messages.error(request, 'As senhas não coincidem.')
                print("erro do senha")
            elif User.objects.filter(username=email).exists():
                messages.error(request, 'Email já registrado.')
                print("erro do email")
            elif User.objects.filter(nickname=nickname).exists():
                messages.error(request, 'Nickname já registrado.')
                print("erro do nickname")
            else:
                user = User.objects.create_user(username=email, email=email, password=password,full_name=name, nickname=nickname)
                login(request, user)
                return redirect('trilhas:dashboard')

        # If there’s an error, render the page with the correct tab and pre-fill email/name
        context = {
            'active_tab': active_tab,
            'prefill_email': email,
            'prefill_name': request.POST.get('name', ''),
            'prefill_nickname': request.POST.get('nickname', ''),
        }
        return render(request, 'users/index.html', context)

    return render(request, 'users/index.html', {'active_tab': active_tab})
