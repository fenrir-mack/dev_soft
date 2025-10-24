from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import ensure_csrf_cookie

User = get_user_model()

def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()

def _titlecase_name(value: str) -> str:
    parts = (value or "").split()
    return " ".join(p.capitalize() for p in parts)

@ensure_csrf_cookie
def index_view(request):
    active_tab = 'login'  # default

    if request.method == 'POST':
        type_access = request.POST.get('action')

        # captura bruta
        raw_email = request.POST.get('email')
        password = request.POST.get('password')
        email = _normalize_email(raw_email)

        if type_access == "login":
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)  # Django rotaciona a sessão
                return redirect('trilhas:dashboard')
            else:
                messages.error(request, 'Email ou senha incorretos.')
                active_tab = 'login'

        elif type_access == 'signup':
            raw_name = request.POST.get('name') or ""
            nickname = request.POST.get('nickname')
            confirm_password = request.POST.get('confirm_password')
            active_tab = 'signup'

            name = _titlecase_name(raw_name)

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
                    password=password,   # não alterar senha
                    full_name=name,      # Title Case
                    nickname=nickname,   # preservar
                )
                login(request, user)
                return redirect('trilhas:dashboard')

        elif type_access == 'reset_password':
            confirm_password = request.POST.get('confirm_password')
            active_tab = 'reset'  # mantém UI de reset aberta se der erro

            if not email:
                messages.error(request, 'Informe um e-mail válido.')
            elif password != confirm_password:
                messages.error(request, 'As senhas não coincidem.')
            else:
                try:
                    user = User.objects.get(username=email)
                except User.DoesNotExist:
                    # mensagem neutra (não revelar se a conta existe)
                    messages.error(request, 'Se o e-mail existir, enviaremos a confirmação.')
                else:
                    user.set_password(password)
                    user.save()
                    messages.success(request, 'Senha atualizada! Faça login com a nova senha.')
                    active_tab = 'login'

        context = {
            'active_tab': active_tab,
            'prefill_email': email,
            'prefill_name': _titlecase_name(request.POST.get('name', '')),
            'prefill_nickname': request.POST.get('nickname', ''),
        }
        return render(request, 'users/index.html', context)

    return render(request, 'users/index.html', {'active_tab': active_tab})