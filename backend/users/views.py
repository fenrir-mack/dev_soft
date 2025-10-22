from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def _titlecase_name(value: str) -> str:
    parts = value.split()
    return " ".join(p.capitalize() for p in parts)

def index_view(request):
    active_tab = 'login'  # default

    if request.method == 'POST':
        type_access = request.POST.get('action')  # login ou signup
        raw_email = request.POST.get('email')
        password = request.POST.get('password')
        email = raw_email.strip().lower() if raw_email else ''

        if type_access == "login":
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('trilhas:dashboard')
            else:
                messages.error(request, 'Email ou senha incorretos.')
                active_tab = 'login'

        elif type_access == 'signup':
            raw_name = request.POST.get('name')
            nickname = request.POST.get('nickname')
            confirm_password = request.POST.get('confirm_password')
            active_tab = 'signup'

            name = _titlecase_name(raw_name or '')

            if password != confirm_password:
                messages.error(request, 'As senhas não coincidem.')
            elif User.objects.filter(username=email).exists():
                messages.error(request, 'Email já registrado.')
            elif User.objects.filter(nickname=nickname).exists():
                messages.error(request, 'Nickname já registrado.')
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    full_name=name,
                    nickname=nickname,
                )
                login(request, user)
                return redirect('trilhas:dashboard')

        # Renderiza com os campos pré-preenchidos (mantendo o que o usuário digitou)
        context = {
            'active_tab': active_tab,
            'prefill_email': email,
            'prefill_name': _titlecase_name(request.POST.get('name', '')),
            'prefill_nickname': request.POST.get('nickname', ''),
        }
        return render(request, 'users/index.html', context)

    # ✅ Agora inclui as variáveis prefill padrão no GET
    return render(request, 'users/index.html', {
        'active_tab': active_tab,
        'prefill_email': '',
        'prefill_name': '',
        'prefill_nickname': '',
    })
