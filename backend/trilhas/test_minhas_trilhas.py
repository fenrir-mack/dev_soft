from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from trilhas.models import Trilha, Categoria, ProgressoTrilha

User = get_user_model()  # usa o CustomUser definido em users.models


class MinhasTrilhasViewTests(TestCase):
    def setUp(self):
        # Cria o cliente e o usuário
        self.client = Client()
        self.user = User.objects.create_user(
            username="usuario",
            password="12345",
            full_name="usuario",
            nickname="user"
        )
        self.client.login(username="usuario", password="12345")

        # Cria categoria e trilha
        self.categoria = Categoria.objects.create(nome="Programação")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Django",
            descricao="Aprenda Django com projetos reais",
            categoria=self.categoria,
            dificuldade="iniciante",
        )

    def test_01_iniciar_trilha(self):
        """Deve permitir iniciar uma trilha (action=resume)"""
        resp = self.client.post("/trilhas/minhas-trilhas/", {
            "action": "resume",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("retomada", resp.json()["message"])
        self.assertTrue(ProgressoTrilha.objects.filter(user=self.user, trilha=self.trilha).exists())

    def test_02_pausar_trilha(self):
        """Deve permitir pausar uma trilha em progresso"""
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso")
        resp = self.client.post("/trilhas/minhas-trilhas/", {
            "action": "pause",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(resp.status_code, 200)
        progresso = ProgressoTrilha.objects.get(user=self.user, trilha=self.trilha)
        self.assertEqual(progresso.status, "pausada")

    def test_03_retomar_trilha(self):
        """Deve permitir retomar uma trilha pausada"""
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="pausada")
        resp = self.client.post("/trilhas/minhas-trilhas/", {
            "action": "resume",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(resp.status_code, 200)
        progresso = ProgressoTrilha.objects.get(user=self.user, trilha=self.trilha)
        self.assertEqual(progresso.status, "em_progresso")

    def test_04_concluir_trilha(self):
        """Deve permitir marcar uma trilha como concluída"""
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso")
        resp = self.client.post("/trilhas/minhas-trilhas/", {
            "action": "complete",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(resp.status_code, 200)
        progresso = ProgressoTrilha.objects.get(user=self.user, trilha=self.trilha)
        self.assertEqual(progresso.status, "concluida")
        self.assertEqual(float(progresso.progresso_percentual), 100.0)

    def test_05_excluir_trilha(self):
        """Deve permitir deletar o progresso de uma trilha"""
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso")
        resp = self.client.post("/trilhas/minhas-trilhas/", {
            "action": "delete",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ProgressoTrilha.objects.filter(user=self.user, trilha=self.trilha).exists())

    def test_06_listagem_json(self):
        """Deve retornar JSON correto com as trilhas do usuário"""
        ProgressoTrilha.objects.create(
            user=self.user,
            trilha=self.trilha,
            status="em_progresso",
            progresso_percentual=42.5
        )
        resp = self.client.get("/trilhas/minhas-trilhas/?format=json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("inProgress", data)
        self.assertEqual(len(data["inProgress"]), 1)
        self.assertEqual(data["inProgress"][0]["progress"], 42.5)
