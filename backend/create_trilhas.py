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
