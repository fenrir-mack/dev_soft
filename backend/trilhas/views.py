from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import Trilha, ProgressoTrilha, Topico, ProgressoTopico, Categoria


@login_required
def dashboard_view(request):
    user = request.user

    trilhas_em_progresso = ProgressoTrilha.objects.filter(user=user, status='em_progresso').count()
    trilhas_concluidas = ProgressoTrilha.objects.filter(user=user, status='concluida').count()
    trilhas_salvas = ProgressoTrilha.objects.filter(user=user, status='pausada').count()

    ultimas_trilhas = ProgressoTrilha.objects.filter(user=user).select_related('trilha').order_by('-data_ultima_modificacao')[:3]

    context = {
        'trilhas_em_progresso': trilhas_em_progresso,
        'trilhas_concluidas': trilhas_concluidas,
        'trilhas_salvas': trilhas_salvas,
        'ultimas_trilhas': ultimas_trilhas,
    }
    return render(request, 'trilhas/dashboard.html', context)


@login_required
def explorar_view(request):
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
                trilha.usuarios_salvos.add(request.user)

            return JsonResponse({'success': True, 'message': 'Trilha adicionada com sucesso.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    all_public_trilhas = Trilha.objects.filter(visibilidade=True).select_related('categoria')

    categorias = Categoria.objects.filter(trilha__visibilidade=True).distinct()

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
            'etapas': trilha.etapas.count() or trilha.projetos.count(),
            'students': trilha.total_salvos,
            'enrolled': trilha.id in enrolled_trilha_ids
        })

    context = {
        'paths': path_data,
        'categorias': categorias
    }
    return render(request, 'trilhas/explorar.html', context)


@login_required
def detalhes_da_trilha_view(request):
    trilha_id = request.GET.get('id')
    trilha = get_object_or_404(Trilha, id=trilha_id)

    # Etapas e tópicos
    etapas = trilha.etapas.prefetch_related('topicos').all()
    etapas_data = []
    for etapa in etapas:
        topicos_data = []
        for topico in etapa.topicos.all():
            concluido = ProgressoTopico.objects.filter(user=request.user, topico=topico, concluido=True).exists()
            topicos_data.append({
                "id": topico.id,
                "text": topico.texto,
                "completed": concluido
            })
        etapas_data.append({
            "id": etapa.id,
            "number": f"ETAPA {etapa.ordem}",
            "title": etapa.titulo,
            "topics": topicos_data
        })

    projeto = trilha.projetos.first()

    progresso, _ = ProgressoTrilha.objects.get_or_create(user=request.user, trilha=trilha)
    stroke_offset = 326.73 - (float(progresso.progresso_percentual) / 100) * 326.73

    context = {
        "trilha": trilha,
        "etapas_data": etapas_data,
        "projeto": projeto,
        "progresso_percentual": int(progresso.progresso_percentual),
        "topicos_concluidos": ProgressoTopico.objects.filter(user=request.user, topico__etapa__trilha=trilha,
                                                             concluido=True).count(),
        "total_topicos": sum(len(et['topics']) for et in etapas_data),
        "stroke_offset": stroke_offset,
    }

    return render(request, 'trilhas/detalhes-da-trilha.html', context)


@csrf_exempt  # OK para APIs internas, mas @csrf_protect é melhor
@login_required
def toggle_topico(request):
    if request.method == "POST":
        user = request.user
        topico_id = request.POST.get("topico_id")
        completed = request.POST.get("completed") == "true"

        try:
            topico = Topico.objects.get(id=topico_id)
        except Topico.DoesNotExist:
            return JsonResponse({"success": False, "error": "Tópico não encontrado"})

        # Marca o progresso do tópico
        progresso, created = ProgressoTopico.objects.get_or_create(user=user, topico=topico)

        # Chama seu método de modelo, que é mais robusto
        progresso.salvar_conclusao(concluido=completed)

        # O método salvar_conclusao já chama progresso_trilha.atualizar_progresso()
        # Então, o código manual de cálculo percentual aqui não é mais necessário
        # Apenas pegamos o valor atualizado para retornar no JSON
        progresso_trilha = ProgressoTrilha.objects.get(user=user, trilha=topico.etapa.trilha)

        print(
            f"[OK] {user.username}: Tópico {topico_id} atualizado — progresso da trilha agora {progresso_trilha.progresso_percentual:.2f}%")

        return JsonResponse({"success": True, "progress": progresso_trilha.progresso_percentual})

    return JsonResponse({"success": False, "error": "Método inválido"})


@login_required
def minhas_trilhas_view(request):
    user = request.user

    progresso_list = (
        ProgressoTrilha.objects
        .filter(user=user)
        .select_related('trilha')
        .order_by('data_inicio')
    )

    if request.method == 'GET' and request.GET.get('format') == 'json':
        def serialize_trilha(p):
            trilha = p.trilha
            return {
                'id': trilha.id,
                'title': trilha.titulo,
                'description': trilha.descricao,
                'level': trilha.get_dificuldade_display(),
                'progress': round(float(p.progresso_percentual), 2),
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

        if action != 'resume':
            progresso = get_object_or_404(ProgressoTrilha, user=user, trilha=trilha)

        if action == 'pause':
            progresso.status = 'pausada'
            progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha \"{trilha.titulo}\" pausada com sucesso!'})

        elif action == 'resume':
            progresso, created = ProgressoTrilha.objects.get_or_create(
                user=user,
                trilha=trilha,
                defaults={'status': 'em_progresso', 'progresso_percentual': 0.0}
            )
            if not created:
                progresso.status = 'em_progresso'
                progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha \"{trilha.titulo}\" retomada!'})

        elif action == 'restart':
            progresso.progresso_percentual = 0.0
            progresso.status = 'em_progresso'
            progresso.save()
            ProgressoTopico.objects.filter(user=user, topico__etapa__trilha=trilha).update(concluido=False,data_conclusao=None)
            return JsonResponse({'success': True, 'message': f'Trilha \"{trilha.titulo}\" reiniciada!'})

        elif action == 'delete':
            progresso = get_object_or_404(ProgressoTrilha, user=user, trilha=trilha)

            progresso.delete()

            ProgressoTopico.objects.filter(user=user, topico__etapa__trilha=trilha).delete()

            trilha.usuarios_salvos.remove(user)

            return JsonResponse(
                {'success': True, 'message': f'Progresso da trilha \"{trilha.titulo}\" excluído com sucesso!'})

        elif action == 'complete':
            progresso = get_object_or_404(ProgressoTrilha, user=user, trilha=trilha)
            progresso.status = 'concluida'
            progresso.progresso_percentual = 100.0
            progresso.save()
            return JsonResponse({'success': True, 'message': f'Trilha "{trilha.titulo}" marcada como concluída!'})

        else:
            return HttpResponseBadRequest("Ação inválida.")

    return render(request, 'trilhas/minhas-trilhas.html', {
        "pathsData": {
            "inProgress": [p for p in progresso_list if p.status == 'em_progresso'],
            "paused": [p for p in progresso_list if p.status == 'pausada'],
            "completed": [p for p in progresso_list if p.status == 'concluida'],
        }
    })