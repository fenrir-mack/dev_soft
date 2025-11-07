from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import google.generativeai as genai
from .prompt import build_prompt
from django.views.decorators.csrf import csrf_exempt
from trilhas.models import Trilha, Etapa, Topico, Projeto, Categoria
import logging
from django.shortcuts import redirect, reverse
from django.http import JsonResponse
import json
logger = logging.getLogger(__name__)
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-2.5-flash")



@login_required
def custom_path_view(request):
    if request.method == "POST":
        tema = request.POST.get("tema_trilha", "").strip()
        dificuldade = request.POST.get("dificuldade", "intermediário").strip()

        if not tema:
            return JsonResponse({"error": "Tema não fornecido"}, status=400)

        try:
            prompt = build_prompt(tema, dificuldade)
            response = model.generate_content(prompt)
            trilha_data = json.loads(response.text)
            print("[IA RAW RESPONSE]", trilha_data)        # print simples

            etapas = trilha_data.get("etapas", [])
            projetos = trilha_data.get("projetos", [])

            if etapas and projetos:
                etapas_ordem = sorted([etapa["ordem"] for etapa in etapas])
                ultima_ordem = max(etapas_ordem) if etapas_ordem else 0

                for projeto in projetos:
                    titulo = projeto.get("titulo", "").lower()

                    # Projeto final → depois da última etapa
                    if "final" in titulo or "conclus" in titulo:
                        projeto["ordem"] = ultima_ordem + 1
                    # Projeto inicial → após a primeira etapa
                    elif "inicial" in titulo or "introdu" in titulo:
                        projeto["ordem"] = etapas_ordem[0] + 1
                    # Projeto intermediário → depois da metade
                    else:
                        meio = etapas_ordem[len(etapas_ordem) // 2]
                        projeto["ordem"] = meio + 1

                # Junta etapas e projetos e ordena
                conteudo = sorted(etapas + projetos, key=lambda x: x["ordem"])

                # 🔢 Reatribui ordens inteiras consecutivas (1, 2, 3, ...)
                for i, item in enumerate(conteudo, start=1):
                    item["ordem"] = i

                # Salva lista unificada e coerente
                trilha_data["conteudo_ordenado"] = conteudo

            # Salva no session
            request.session['trilha_ia'] = trilha_data
            return JsonResponse(trilha_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "A IA retornou JSON inválido"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, 'trilha_personalizada/trilhas-personalizadas.html')

@csrf_exempt
def salvar_trilha_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Body recebido: {request.body}")

            trilha_data = data.get('trilha', {})
            conteudo = data.get('conteudo_ordenado', [])

            etapas_data = [c for c in conteudo if 'topicos' in c]
            projetos_data = [c for c in conteudo if 'topicos' not in c]

            # 🔹 Cria a trilha com visibilidade desativada (0)
            trilha = Trilha.objects.create(
                titulo=trilha_data.get('titulo', 'Nova Trilha'),
                descricao=trilha_data.get('descricao', ''),
                dificuldade=trilha_data.get('dificuldade', 'iniciante'),
                visibilidade=False,
            )

            # 🔹 Cria as etapas e tópicos
            for etapa_data in etapas_data:
                etapa = Etapa.objects.create(
                    trilha=trilha,
                    titulo=etapa_data.get('titulo', 'Nova Etapa'),
                    ordem=int(etapa_data.get('ordem') or 0)
                )
                for topico_data in etapa_data.get('topicos', []):
                    Topico.objects.create(
                        etapa=etapa,
                        texto=topico_data.get('texto', ''),
                        ordem=int(topico_data.get('ordem') or 0)
                    )

            for projeto_data in projetos_data:
                Projeto.objects.create(
                    trilha=trilha,
                    titulo=projeto_data.get('titulo', 'Novo Projeto'),
                    descricao=projeto_data.get('descricao', ''),
                    ordem=int(projeto_data.get('ordem') or 0)
                )

            # 🟢 Cria progresso inicial (0%) pro usuário logado
            if request.user.is_authenticated:
                from trilhas.models import ProgressoTrilha
                ProgressoTrilha.objects.create(
                    user=request.user,
                    trilha=trilha,
                    progresso_percentual=0.0,
                    status='em_progresso'
                )

            # 🔹 Redireciona
            redirect_url = reverse('trilhas:ver_etapas') + f'?id={trilha.id}'
            return JsonResponse({'redirect_url': redirect_url})

        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=400)

    return JsonResponse({'erro': 'Método inválido'}, status=405)


