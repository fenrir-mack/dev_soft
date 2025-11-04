# create_trilhas_with_progress.py
from django.contrib.auth import get_user_model
from trilhas.models import (
    Categoria, Trilha, Etapa, Topico, Projeto,
    ProgressoTrilha, ProgressoTopico
)
from django.utils import timezone

User = get_user_model()

# CONFIG
TARGET_EMAIL = "fenrir@gmail.com"
MARK_FIRST_TOPIC_COMPLETED = False  # set True if you want the first topic marked as completed

# Get the existing user
user = User.objects.filter(email=TARGET_EMAIL).first()

if not user:
    print(f"User with email {TARGET_EMAIL} not found.")
else:
    print(f"Found user: {user.username}")

    # --- Create category ---
    categoria, _ = Categoria.objects.get_or_create(nome="Programação")

    # --- Trilhas data ---
    trilhas_data = [
        {
            "titulo": "Introdução à Programação",
            "descricao": "Aprenda os conceitos básicos de lógica e algoritmos.",
            "dificuldade": "iniciante",
        },
        {
            "titulo": "Desenvolvimento Web com Django",
            "descricao": "Crie aplicações web completas com Django.",
            "dificuldade": "intermediario",
        },
        {
            "titulo": "Machine Learning com Python",
            "descricao": "Construa modelos inteligentes com bibliotecas modernas.",
            "dificuldade": "avancado",
        },
    ]

    for t_index, trilha_data in enumerate(trilhas_data, start=1):
        trilha, created = Trilha.objects.get_or_create(
            titulo=trilha_data["titulo"],
            defaults={
                "descricao": trilha_data["descricao"],
                "categoria": categoria,
                "visibilidade": True,
                "dificuldade": trilha_data["dificuldade"],
            },
        )

        # Save to user's saved trilhas (ManyToMany)
        trilha.usuarios_salvos.add(user)

        # --- Add Etapas and Topicos ---
        for i in range(1, 4):
            etapa, _ = Etapa.objects.get_or_create(
                trilha=trilha,
                ordem=i,
                defaults={"titulo": f"Etapa {i} - Conceitos principais"},
            )

            for j in range(1, 4):
                Topico.objects.get_or_create(
                    etapa=etapa,
                    ordem=j,
                    defaults={"texto": f"Conteúdo do tópico {j} da {etapa.titulo}"},
                )

        # --- Add one Projeto ---
        Projeto.objects.get_or_create(
            trilha=trilha,
            ordem=1,
            defaults={
                "titulo": f"Projeto Final - {trilha.titulo}",
                "descricao": "Desenvolva um projeto prático aplicando todo o conhecimento aprendido.",
            },
        )

        # --- Create progress records ---
        progresso_trilha, _ = ProgressoTrilha.objects.get_or_create(
            user=user,
            trilha=trilha,
            defaults={
                "status": "em_progresso",
                "progresso_percentual": 0.00,
                "data_inicio": timezone.now(),
                "data_ultima_modificacao": timezone.now(),
            }
        )

        # Ensure a ProgressoTopico exists for every topico of this trilha
        all_topicos = Topico.objects.filter(etapa__trilha=trilha).order_by('etapa__ordem', 'ordem')
        for idx, topico in enumerate(all_topicos, start=1):
            pt, created_pt = ProgressoTopico.objects.get_or_create(
                user=user,
                topico=topico,
                defaults={
                    "concluido": False,
                    "data_conclusao": None
                }
            )

            # Optionally mark the very first topic of the first trilha as completed
            if MARK_FIRST_TOPIC_COMPLETED and t_index == 1 and idx == 1:
                # use the model's helper method if available
                try:
                    pt.salvar_conclusao(concluido=True)
                except Exception:
                    pt.concluido = True
                    pt.data_conclusao = timezone.now()
                    pt.save()

        # Recalculate trilha progress using the model method
        try:
            progresso_trilha.atualizar_progresso()
        except Exception:
            # fallback: compute simple percentage
            total_topicos = all_topicos.count()
            concluidos = ProgressoTopico.objects.filter(user=user, topico__etapa__trilha=trilha, concluido=True).count()
            progresso_trilha.progresso_percentual = (concluidos / total_topicos) * 100 if total_topicos else 0
            progresso_trilha.status = 'concluida' if progresso_trilha.progresso_percentual == 100 else 'em_progresso'
            progresso_trilha.data_ultima_modificacao = timezone.now()
            progresso_trilha.save()

        print(f"Created or updated trilha: {trilha.titulo} (progress: {progresso_trilha.progresso_percentual}%)")

    print("Trilhas and progress created and assigned to user successfully.")

# 1. IMPORTAÇÕES
from django.contrib.auth import get_user_model
from trilhas.models import Categoria, Trilha, Etapa, Topico, ProgressoTrilha, ProgressoTopico
from django.utils import timezone

# 2. CONFIGURAÇÃO
TARGET_EMAIL = "fenrir@gmail.com" # Este email é o seu USERNAME
print("--- Iniciando script [FORÇAR 100% EM PROGRESSO] ---")

User = get_user_model()

# 3. VERIFICA O USUÁRIO
user = User.objects.get(username=TARGET_EMAIL)
print(f"✅ Usuario encontrado: {user.username}")

# 4. CRIAR UMA TRILHA NOVA DO ZERO
print("Criando trilha de teste do zero...")
cat, _ = Categoria.objects.get_or_create(nome="Testes de Status")
trilha_teste, created = Trilha.objects.get_or_create(
    titulo="Trilha de Teste 100% (Em Progresso)",
    defaults={
        "categoria": cat,
        "descricao": "Trilha para testar o status 'em_progresso' com 100%.",
        "visibilidade": False
    }
)
if created:
     print(f"   -> Trilha '{trilha_teste.titulo}' criada.")
else:
     print(f"   -> Trilha '{trilha_teste.titulo}' já existia, será utilizada.")

etapa_teste, _ = Etapa.objects.get_or_create(trilha=trilha_teste, ordem=1, defaults={"titulo": "Etapa Única"})
topico1_teste, _ = Topico.objects.get_or_create(etapa=etapa_teste, ordem=1, defaults={"texto": "Tópico de Teste 1"})
topico2_teste, _ = Topico.objects.get_or_create(etapa=etapa_teste, ordem=2, defaults={"texto": "Tópico de Teste 2"})

# 5. CRIAR PROGRESSO MANUALMENTE
print("Marcando tópicos como concluídos (manualmente)...")
pt1, _ = ProgressoTopico.objects.get_or_create(user=user, topico=topico1_teste)
pt1.concluido = True
pt1.data_conclusao = timezone.now()
pt1.save()

pt2, _ = ProgressoTopico.objects.get_or_create(user=user, topico=topico2_teste)
pt2.concluido = True
pt2.data_conclusao = timezone.now()
pt2.save()

# 6. FORÇAR O ESTADO DA TRILHA PRINCIPAL
print("Forçando status da trilha principal...")
progresso_trilha, _ = ProgressoTrilha.objects.get_or_create(user=user, trilha=trilha_teste)
progresso_trilha.progresso_percentual = 100.00
progresso_trilha.status = 'em_progresso'
progresso_trilha.save()

print("\n✅✅✅ SCRIPT CONCLUÍDO COM SUCESSO! ✅✅✅")
print(f"Trilha: '{progresso_trilha.trilha.titulo}'")
print(f"Status Final: '{progresso_trilha.status}'")
print(f"Percentual Final: {progresso_trilha.progresso_percentual}%")
print("Atualize sua página 'Minhas Trilhas'.")