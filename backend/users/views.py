from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()

def _titlecase_name(value: str) -> str:
    # cada palavra com inicial maiúscula; remove espaços duplicados
    parts = (value or "").split()
    return " ".join(p.capitalize() for p in parts)

def index_view(request):
    active_tab = 'login'  # default

    if request.method == 'POST':
        type_access = request.POST.get('action')

        # CAPTURA BRUTA (sem alterar nickname/senha)
        raw_email = request.POST.get('email')
        password = request.POST.get('password')

        # NORMALIZAÇÕES (somente email e nome)
        email = _normalize_email(raw_email)

        if type_access == "login":
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('trilhas:dashboard')
            else:
                messages.error(request, 'Email ou senha incorretos.')
                active_tab = 'login'

        elif type_access == 'signup':
            raw_name = request.POST.get('name') or ""
            nickname = request.POST.get('nickname')  # NÃO alterar nickname
            confirm_password = request.POST.get('confirm_password')
            active_tab = 'signup'

            # aplica Title Case no nome
            name = _titlecase_name(raw_name)

            if password != confirm_password:
                messages.error(request, 'As senhas não coincidem.')
            elif User.objects.filter(username=email).exists():
                messages.error(request, 'Email já registrado.')
            elif User.objects.filter(nickname=nickname).exists():
                messages.error(request, 'Nickname já registrado.')
            else:
                # cria com email/username normalizados e nome em Title Case
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,     # NÃO alterar a senha
                    full_name=name,
                    nickname=nickname,     # NÃO alterar nickname
                )
                login(request, user)
                return redirect('trilhas:dashboard')

        # Render com os campos pré-preenchidos (mantendo o que o usuário digitou)
        context = {
            'active_tab': active_tab,
            'prefill_email': email,                      # já em minúsculas
            'prefill_name': _titlecase_name(request.POST.get('name', '')),
            'prefill_nickname': request.POST.get('nickname', ''),
        }
        return render(request, 'users/index.html', context)

    return render(request, 'users/index.html', {'active_tab': active_tab})
