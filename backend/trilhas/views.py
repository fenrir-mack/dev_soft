from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from trilhas.models import Trilha, ProgressoTrilha
from django.shortcuts import render
from django.http import JsonResponse



def dashboard_view(request):
    return render(request, 'trilhas/dashboard.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Trilha, Categoria, ProgressoTrilha

@csrf_exempt
@login_required
def predefined_paths_view(request):
    """
    Página Explorar Trilhas:
    - GET → mostra todas as trilhas públicas disponíveis
      - Se for GET + ?format=json → retorna JSON com trilhas
    - POST → permite ação de inscrição (começar trilha)
    """
    user = request.user

    # Trilhas públicas
    trilhas_publicas = Trilha.objects.filter(visibilidade=True).select_related('categoria')

    # Serializador de trilhas
    def serialize_trilha(trilha):
        # Verifica se o usuário já está inscrito
        inscrito = ProgressoTrilha.objects.filter(user=user, trilha=trilha).exists()
        alunos = ProgressoTrilha.objects.filter(trilha=trilha).count()
        return {
            'id': trilha.id,
            'title': trilha.titulo,
            'description': trilha.descricao,
            'category': trilha.categoria.nome if trilha.categoria else 'Geral',
            'duration': trilha.duracao or '—',
            'level': trilha.get_dificuldade_display(),
            'modules': trilha.projetos.count(),
            'students': alunos,
            'enrolled': inscrito,
        }

    categorias = Categoria.objects.all()

    # GET JSON
    if request.method == 'GET' and request.GET.get('format') == 'json':
        trilhas_serializadas = [serialize_trilha(t) for t in trilhas_publicas]
        return JsonResponse({'paths': trilhas_serializadas}, safe=False)

    # POST → iniciar trilha
    if request.method == 'POST':
        trilha_id = request.POST.get('trilha_id')
        if not trilha_id:
            return HttpResponseBadRequest("ID da trilha não informado.")
        trilha = get_object_or_404(Trilha, id=trilha_id)

        progresso, created = ProgressoTrilha.objects.get_or_create(
            user=user,
            trilha=trilha,
            defaults={'status': 'em_progresso', 'progresso_percentual': 0.0}
        )

        if created:
            return JsonResponse({'success': True, 'message': f'Você começou a trilha "{trilha.titulo}"!'})
        else:
            return JsonResponse({'success': False, 'message': f'Você já está fazendo a trilha "{trilha.titulo}".'})

    # Renderização normal (HTML)
    return render(request, 'trilhas/predefined-paths.html', {
        "paths": [serialize_trilha(t) for t in trilhas_publicas],
        "categorias": categorias
    })


def study_guide_view(request):
    return render(request, 'trilhas/study-guide.html')

def path_details_view(request):
    return render(request, 'trilhas/path-details.html')


@csrf_exempt
@login_required
def all_paths_view(request):
    """
    Página Minhas Trilhas:
    - GET → mostra as trilhas do usuário atual, divididas por status
      - Se for GET + ?format=json → retorna JSON com trilhas
    - POST → permite ações (pausar, retomar, reiniciar, excluir progresso)
    """

    user = request.user

    # Lista de progresso do usuário (com trilhas associadas)
    progresso_list = ProgressoTrilha.objects.filter(user=user).select_related('trilha').order_by('data_inicio')

    # Se for requisição GET com ?format=json, retorna os dados como JSON (para JS)
    if request.method == 'GET' and request.GET.get('format') == 'json':
        def serialize_trilha(p):
            trilha = p.trilha
            return {
                'id': trilha.id,
                'title': trilha.titulo,
                'description': trilha.descricao,
                'duration': '—',  # Se quiser, substitua por trilha.duracao se existir
                'level': trilha.get_dificuldade_display(),
                'progress': float(p.progresso_percentual),
            }

        return JsonResponse({
            "inProgress": [serialize_trilha(p) for p in progresso_list if p.status == 'em_progresso'],
            "paused": [serialize_trilha(p) for p in progresso_list if p.status == 'pausada'],
            "completed": [serialize_trilha(p) for p in progresso_list if p.status == 'concluida'],
        })

    # Se for requisição POST, trata as ações
    if request.method == 'POST':
        action = request.POST.get('action')
        trilha_id = request.POST.get('trilha_id')

        if not trilha_id:
            return HttpResponseBadRequest("ID da trilha não informado.")

        trilha = get_object_or_404(Trilha, id=trilha_id)

        progresso, created = ProgressoTrilha.objects.get_or_create(
            user=user,
            trilha=trilha,
            defaults={'status': 'em_progresso', 'progresso_percentual': 0.0}
        )

        if action == 'pause':
            progresso.status = 'pausada'
            progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha "{trilha.titulo}" pausada com sucesso!'})

        elif action == 'resume':
            progresso.status = 'em_progresso'
            progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha "{trilha.titulo}" retomada!'})

        elif action == 'restart':
            progresso.progresso_percentual = 0.0
            progresso.status = 'em_progresso'
            progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha "{trilha.titulo}" reiniciada!'})

        elif action == 'delete':
            progresso.delete()
            return JsonResponse({'success': True, 'message': f'Progresso da trilha "{trilha.titulo}" excluído com sucesso!'})

        else:
            return HttpResponseBadRequest("Ação inválida.")

    # Renderização normal da página HTML
    return render(request, 'trilhas/all-paths.html', {
        "pathsData": {
            "inProgress": [p.trilha for p in progresso_list if p.status == 'em_progresso'],
            "paused": [p.trilha for p in progresso_list if p.status == 'pausada'],
            "completed": [p.trilha for p in progresso_list if p.status == 'concluida'],
        }
    })
