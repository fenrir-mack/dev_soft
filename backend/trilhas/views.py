from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.urls import reverse

# Importamos os models que vamos usar
from .models import Trilha, ProgressoTrilha, Categoria


def dashboard_view(request):
    return render(request, 'trilhas/dashboard.html')


# ==========================================================
# 🔹 1. VIEW 'PREDEFINED_PATHS' (EXPLORAR) ATUALIZADA 🔹
# Agora ela lida com GET (mostrar página) e POST (adicionar trilha)
# ==========================================================
@login_required
@csrf_protect  # Garante proteção CSRF para ambas as requisições
def predefined_paths_view(request):
    # 🔹 Lógica de POST (quando o JS clica em "Começar") 🔹
    if request.method == 'POST':
        try:
            trilha_id = request.POST.get('trilha_id')
            if not trilha_id:
                return JsonResponse({'success': False, 'message': 'ID da trilha não enviado.'}, status=400)

            trilha = get_object_or_404(Trilha, id=trilha_id, visibilidade=True)

            progresso, created = ProgressoTrilha.objects.get_or_create(
                user=request.user,
                trilha=trilha,
                defaults={'status': 'em_progresso', 'progresso_percentual': 0.0}
            )

            if created:
                trilha.total_salvos += 1
                trilha.save()

            return JsonResponse({'success': True, 'message': 'Trilha adicionada com sucesso.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # 🔹 Lógica de GET (quando o usuário carrega a página) 🔹
    # (Todo o código que já tínhamos para exibir a página)
    all_public_trilhas = Trilha.objects.filter(visibilidade=True).select_related('categoria')
    categorias = Categoria.objects.all()

    enrolled_trilha_ids = ProgressoTrilha.objects.filter(
        user=request.user,
        trilha__in=all_public_trilhas
    ).values_list('trilha_id', flat=True)

    path_data = []
    for trilha in all_public_trilhas:
        path_data.append({
            'id': trilha.id,
            'title': trilha.titulo,
            'description': trilha.descricao,
            'category': trilha.categoria.nome if trilha.categoria else 'Sem Categoria',
            'category_slug': trilha.categoria.nome.lower() if trilha.categoria else '',
            'level': trilha.get_dificuldade_display(),
            'modules': trilha.etapa_set.count() or trilha.projetos.count(),
            'students': trilha.total_salvos,
            'enrolled': trilha.id in enrolled_trilha_ids
        })

    context = {
        'paths': path_data,
        'categorias': categorias
    }
    return render(request, 'trilhas/predefined-paths.html', context)


def study_guide_view(request):
    return render(request, 'trilhas/study-guide.html')


def path_details_view(request):
    return render(request, 'trilhas/path-details.html')



@csrf_exempt
@login_required
def all_paths_view(request):
    # (A sua view 'all_paths_view' de "Minhas Trilhas" continua aqui...
    # ...sem nenhuma alteração)

    user = request.user
    progresso_list = ProgressoTrilha.objects.filter(user=user).select_related('trilha').order_by('data_inicio')

    if request.method == 'GET' and request.GET.get('format') == 'json':
        def serialize_trilha(p):
            trilha = p.trilha
            return {
                'id': trilha.id,
                'title': trilha.titulo,
                'description': trilha.descricao,
                'duration': '—',
                'level': trilha.get_dificuldade_display(),
                'progress': float(p.progresso_percentual),
            }

        return JsonResponse({
            "inProgress": [serialize_trilha(p) for p in progresso_list if p.status == 'em_progresso'],
            "paused": [serialize_trilha(p) for p in progresso_list if p.status == 'pausada'],
            "completed": [serialize_trilha(p) for p in progresso_list if p.status == 'concluida'],
        })

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
            return JsonResponse({'success': True, 'message': f'Trilha "{trilha.titulo}" pausada!'})
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
            return JsonResponse({'success': True, 'message': 'Progresso excluído!'})
        elif action == 'complete':
            progresso.status = 'concluida'
            progresso.progresso_percentual = 100.0
            progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha "{trilha.titulo}" concluída!'})
        else:
            return HttpResponseBadRequest("Ação inválida.")

    return render(request, 'trilhas/all-paths.html', {
        "pathsData": {
            "inProgress": [p.trilha for p in progresso_list if p.status == 'em_progresso'],
            "paused": [p.trilha for p in progresso_list if p.status == 'pausada'],
            "completed": [p.trilha for p in progresso_list if p.status == 'concluida'],
        }
    })