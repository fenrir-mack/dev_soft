from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from trilhas.models import Trilha, ProgressoTrilha

def dashboard_view(request):
    user = request.user

    trilhas_em_progresso = ProgressoTrilha.objects.filter(user=user, status='em_progresso').count()
    trilhas_concluidas = ProgressoTrilha.objects.filter(user=user, status='concluida').count()
    trilhas_salvas = ProgressoTrilha.objects.filter(user=user, status='pausada').count()

    ultimas_trilhas = ProgressoTrilha.objects.filter(user=user).select_related('trilha').order_by('-ultima_atualizacao')[:3]

    context = {
        'trilhas_em_progresso': trilhas_em_progresso,
        'trilhas_concluidas': trilhas_concluidas,
        'trilhas_salvas': trilhas_salvas,
        'ultimas_trilhas': ultimas_trilhas,
    }
    return render(request, 'trilhas/dashboard.html', context)

def predefined_paths_view(request):
    return render(request, 'trilhas/predefined-paths.html')

def study_guide_view(request):
    return render(request, 'trilhas/study-guide.html')

@csrf_exempt
@login_required
def all_paths_view(request):
    user = request.user

    # 🔹 Lista de progresso do usuário (com trilhas associadas)
    progresso_list = ProgressoTrilha.objects.filter(user=user).select_related('trilha').order_by('data_inicio')

    # 🔹 Se for requisição GET com ?format=json, retorna os dados como JSON (para JS)
    if request.method == 'GET' and request.GET.get('format') == 'json':
        def serialize_trilha(p):
            trilha = p.trilha
            return {
                'id': trilha.id,
                'title': trilha.titulo,
                'description': trilha.descricao,
                'level': trilha.get_dificuldade_display(),
                'progress': float(p.progresso_percentual),
            }

        return JsonResponse({
            "inProgress": [serialize_trilha(p) for p in progresso_list if p.status == 'em_progresso'],
            "paused": [serialize_trilha(p) for p in progresso_list if p.status == 'pausada'],
            "completed": [serialize_trilha(p) for p in progresso_list if p.status == 'concluida'],
        })

    # 🔹 Se for requisição POST, trata as ações
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

    # 🔹 Renderização normal da página HTML
    return render(request, 'trilhas/all-paths.html', {
        "pathsData": {
            "inProgress": [p.trilha for p in progresso_list if p.status == 'em_progresso'],
            "paused": [p.trilha for p in progresso_list if p.status == 'pausada'],
            "completed": [p.trilha for p in progresso_list if p.status == 'concluida'],
        }
    })
