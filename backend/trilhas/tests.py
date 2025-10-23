from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from trilhas.models import (
    Categoria, Trilha, Etapa, Topico,
    ProgressoTrilha, ProgressoTopico
)

User = get_user_model()


class TrilhaViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user@ex.com",
            email="user@ex.com",
            password="senha123",
            full_name="Usuário Teste",
            nickname="teste"
        )
        self.client.login(username="user@ex.com", password="senha123")

        # Criação da estrutura de trilha
        self.cat = Categoria.objects.create(nome="Programação")
        self.trilha = Trilha.objects.create(
            titulo="Python Básico",
            descricao="Aprenda o básico de Python",
            categoria=self.cat,
            dificuldade="iniciante"
        )
        self.etapa = Etapa.objects.create(
            trilha=self.trilha,
            titulo="Introdução",
            descricao="Primeiros passos",
            ordem=1
        )
        self.topico1 = Topico.objects.create(
            etapa=self.etapa,
            texto="Variáveis e tipos",
            ordem=1
        )
        self.topico2 = Topico.objects.create(
            etapa=self.etapa,
            texto="Operadores e expressões",
            ordem=2
        )

        self.progresso = ProgressoTrilha.objects.create(
            user=self.user,
            trilha=self.trilha,
            status="em_progresso",
            progresso_percentual=0
        )

    # ==== DASHBOARD ====
    def test_dashboard_view_context_counts(self):
        url = reverse("trilhas:dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("trilhas_em_progresso", resp.context)
        self.assertEqual(resp.context["trilhas_em_progresso"], 1)
        self.assertEqual(resp.context["trilhas_concluidas"], 0)
        self.assertEqual(resp.context["trilhas_salvas"], 0)

    # ==== STUDY GUIDE ====
    def test_study_guide_view_generates_correct_context(self):
        url = reverse("trilhas:ver_etapas") + f"?id={self.trilha.id}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertEqual(ctx["trilha"], self.trilha)
        self.assertEqual(ctx["total_topicos"], 2)
        self.assertEqual(ctx["progresso_percentual"], 0)

    # ==== TOGGLE TÓPICO ====
    def test_toggle_topico_marks_topic_completed_and_updates_progress(self):
        url = reverse("trilhas:toggle_topico")
        resp = self.client.post(url, {"topico_id": self.topico1.id, "completed": "true"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

        prog_topico = ProgressoTopico.objects.get(user=self.user, topico=self.topico1)
        self.assertTrue(prog_topico.concluido)

        prog_trilha = ProgressoTrilha.objects.get(user=self.user, trilha=self.trilha)
        self.assertGreater(float(prog_trilha.progresso_percentual), 0)

    def test_toggle_topico_inexistente_retorna_erro(self):
        url = reverse("trilhas:toggle_topico")
        resp = self.client.post(url, {"topico_id": 999, "completed": "true"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["success"], False)
        self.assertIn("Tópico não encontrado", resp.json()["error"])

    # ==== MINHAS TRILHAS (GET JSON) ====
    def test_all_paths_view_returns_json_categorized(self):
        url = reverse("trilhas:minhas_trilhas") + "?format=json"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("inProgress", data)
        self.assertEqual(len(data["inProgress"]), 1)
        self.assertEqual(data["inProgress"][0]["title"], "Python Básico")

    # ==== MINHAS TRILHAS (POST ACTIONS) ====
    def test_all_paths_pause_resume_restart_delete(self):
        url = reverse("trilhas:minhas_trilhas")

        # Pausar trilha
        r1 = self.client.post(url, {"action": "pause", "trilha_id": self.trilha.id})
        self.assertEqual(r1.status_code, 200)
        self.assertIn("pausada", r1.json()["message"].lower())
        self.progresso.refresh_from_db()
        self.assertEqual(self.progresso.status, "pausada")

        # Retomar trilha
        r2 = self.client.post(url, {"action": "resume", "trilha_id": self.trilha.id})
        self.assertEqual(r2.status_code, 200)
        self.progresso.refresh_from_db()
        self.assertEqual(self.progresso.status, "em_progresso")

        # Reiniciar trilha (zera progresso)
        ProgressoTopico.objects.create(user=self.user, topico=self.topico1, concluido=True)
        self.progresso.progresso_percentual = 80
        self.progresso.save()

        r3 = self.client.post(url, {"action": "restart", "trilha_id": self.trilha.id})
        self.assertEqual(r3.status_code, 200)
        self.progresso.refresh_from_db()
        self.assertEqual(float(self.progresso.progresso_percentual), 0.0)
        self.assertEqual(self.progresso.status, "em_progresso")

        # Excluir progresso
        r4 = self.client.post(url, {"action": "delete", "trilha_id": self.trilha.id})
        self.assertEqual(r4.status_code, 200)
        self.assertFalse(ProgressoTrilha.objects.filter(user=self.user, trilha=self.trilha).exists())

    def test_all_paths_invalid_action_returns_bad_request(self):
        url = reverse("trilhas:minhas_trilhas")
        resp = self.client.post(url, {"action": "invalida", "trilha_id": self.trilha.id})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Ação inválida", resp.content.decode())

    def test_all_paths_missing_trilha_id_returns_bad_request(self):
        url = reverse("trilhas:minhas_trilhas")
        resp = self.client.post(url, {"action": "pause"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ID da trilha não informado", resp.content.decode())
