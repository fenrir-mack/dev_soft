from django.test import TestCase, LiveServerTestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from trilhas.models import Trilha, Etapa, Topico, ProgressoTrilha, ProgressoTopico, Categoria

User = get_user_model()

# TESTES UNITÁRIOS
class ProgressoTrilhaUnitarioTests(TestCase):
    """Testes unitários do método atualizar_progresso() da model ProgressoTrilha."""

    def setUp(self):
        self.user = User.objects.create_user(username="lucas", password="12345")
        self.categoria = Categoria.objects.create(nome="Programação")
        self.trilha = Trilha.objects.create(
            titulo="Trilha de Teste Unitário",
            descricao="Teste da função atualizar_progresso",
            categoria=self.categoria,
            dificuldade="iniciante"
        )
        self.etapa = Etapa.objects.create(trilha=self.trilha, titulo="Etapa 1", ordem=1)
        self.topico1 = Topico.objects.create(etapa=self.etapa, texto="Tópico 1", ordem=1)
        self.topico2 = Topico.objects.create(etapa=self.etapa, texto="Tópico 2", ordem=2)
        self.progresso = ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha)

    def test_progresso_inicial_zero(self):
        """Deve iniciar com 0% quando nenhum tópico está concluído."""
        self.progresso.atualizar_progresso()
        self.assertEqual(float(self.progresso.progresso_percentual), 0.0)

    def test_progresso_meio(self):
        """Deve calcular 50% quando metade dos tópicos está concluída."""
        ProgressoTopico.objects.create(user=self.user, topico=self.topico1, concluido=True)
        self.progresso.atualizar_progresso()
        self.assertEqual(float(self.progresso.progresso_percentual), 50.0)

    def test_progresso_completo(self):
        """Deve calcular 100% quando todos os tópicos estão concluídos."""
        ProgressoTopico.objects.create(user=self.user, topico=self.topico1, concluido=True)
        ProgressoTopico.objects.create(user=self.user, topico=self.topico2, concluido=True)
        self.progresso.atualizar_progresso()
        self.assertEqual(float(self.progresso.progresso_percentual), 100.0)

    def test_progresso_sem_topicos(self):
        """Deve manter 0% se a trilha não tiver nenhum tópico."""
        trilha_vazia = Trilha.objects.create(
            titulo="Trilha Vazia",
            descricao="Sem etapas",
            categoria=self.categoria,
            dificuldade="iniciante"
        )
        progresso_vazio = ProgressoTrilha.objects.create(user=self.user, trilha=trilha_vazia)
        progresso_vazio.atualizar_progresso()
        self.assertEqual(float(progresso_vazio.progresso_percentual), 0.0)

# TESTES DE INTEGRAÇÃO

class MinhasTrilhasViewTests(TestCase):
    """Testes de integração da view minhas_trilhas."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="usuario",
            password="12345",
            full_name="usuario",
            nickname="user"
        )
        self.client.login(username="usuario", password="12345")
        self.categoria = Categoria.objects.create(nome="Programação")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Django",
            descricao="Aprenda Django com projetos reais",
            categoria=self.categoria,
            dificuldade="iniciante",
        )

    def test_01_iniciar_trilha(self):
        resp = self.client.post("/trilhas/minhas-trilhas/", {"action": "resume", "trilha_id": self.trilha.id})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("retomada", resp.json()["message"])

    def test_02_pausar_trilha(self):
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso")
        resp = self.client.post("/trilhas/minhas-trilhas/", {"action": "pause", "trilha_id": self.trilha.id})
        self.assertEqual(resp.status_code, 200)

    def test_03_retomar_trilha(self):
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="pausada")
        resp = self.client.post("/trilhas/minhas-trilhas/", {"action": "resume", "trilha_id": self.trilha.id})
        self.assertEqual(resp.status_code, 200)

    def test_04_concluir_trilha(self):
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso")
        resp = self.client.post("/trilhas/minhas-trilhas/", {"action": "complete", "trilha_id": self.trilha.id})
        self.assertEqual(resp.status_code, 200)

    def test_05_excluir_trilha(self):
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso")
        resp = self.client.post("/trilhas/minhas-trilhas/", {"action": "delete", "trilha_id": self.trilha.id})
        self.assertEqual(resp.status_code, 200)

    def test_06_listagem_json(self):
        ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha, status="em_progresso", progresso_percentual=42.5)
        resp = self.client.get("/trilhas/minhas-trilhas/?format=json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("inProgress", data)
        self.assertEqual(len(data["inProgress"]), 1)
        self.assertEqual(data["inProgress"][0]["progress"], 42.5)


#  TESTE FUNCIONAL
class MinhasTrilhasFunctionalTests(LiveServerTestCase):
    """Testes funcionais: simula o comportamento real do usuário."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="funcional_user",
            password="12345",
            full_name="Usuário Funcional",
            nickname="func"
        )
        self.client.login(username="funcional_user", password="12345")
        self.categoria = Categoria.objects.create(nome="Programação")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Django Funcional",
            descricao="Aprenda Django com testes funcionais",
            categoria=self.categoria,
            dificuldade="iniciante",
            visibilidade=True
        )

    def test_fluxo_completo_usuario(self):
        response = self.client.get(reverse('trilhas:todas_trilhas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trilha Django Funcional")

        response = self.client.post(reverse('trilhas:minhas_trilhas'),
            {"action": "resume", "trilha_id": self.trilha.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("retomada", response.json()["message"])
