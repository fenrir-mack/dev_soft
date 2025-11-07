from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import LiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

User = get_user_model()


# ==========================================================
# 🧩 TESTES UNITÁRIOS - DASHBOARD
# ==========================================================
class DashboardUnitTest(TestCase):
    """Testes básicos da view da dashboard"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testeuser",
            email="testeuser@example.com",
            password="12345",
            nickname="testeuser",
        )

    def test_dashboard_view_autenticada(self):
        """Usuário autenticado deve acessar a dashboard"""
        login_ok = self.client.login(username="testeuser", password="12345")
        self.assertTrue(login_ok, "Falha ao logar usuário de teste.")

        response = self.client.get(reverse("trilhas:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_dashboard_view_nao_autenticada(self):
        """Usuário não autenticado deve ser redirecionado"""
        response = self.client.get(reverse("trilhas:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("?next=", response.url)


# ==========================================================
# 🔗 TESTE DE INTEGRAÇÃO - DASHBOARD
# ==========================================================
class DashboardIntegrationTest(TestCase):
    """Verifica o fluxo de login e navegação para a dashboard"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="teste_integ",
            email="teste_integ@example.com",
            password="12345",
            nickname="teste_integ",
        )

    def test_fluxo_login_e_dashboard(self):
        """Fluxo completo de login e acesso"""
        login_ok = self.client.login(username="teste_integ", password="12345")
        self.assertTrue(login_ok, "Falha ao logar usuário de integração.")

        response = self.client.get(reverse("trilhas:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard - EstudaAI")


# ==========================================================
# 🌐 TESTE FUNCIONAL (SELENIUM) - DASHBOARD
# ==========================================================
class DashboardFunctionalTest(LiveServerTestCase):
    """Simula o login real no navegador e acesso à dashboard"""

    def setUp(self):
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.browser = webdriver.Chrome(options=options)

    def tearDown(self):
        self.browser.quit()

    def test_usuario_pode_fazer_login_e_ver_dashboard(self):
        """Simula login real via Selenium"""
        User.objects.all().delete()

        User.objects.create_user(
            username="teste_func",
            email="teste_func@example.com",
            password="12345",
            nickname="teste_func",
        )

        self.browser.get(f"{self.live_server_url}/")

        try:
            campo_email = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "loginEmail"))
            )
            campo_senha = self.browser.find_element(By.ID, "loginPassword")
            botao_login = self.browser.find_element(
                By.CSS_SELECTOR, "button.btn.btn-primary"
            )
        except TimeoutException:
            self.fail("Campos de login não encontrados na página.")

        # Desativa validação de formato de e-mail
        self.browser.execute_script(
            "document.getElementById('loginEmail').setAttribute('type','text');"
        )

        campo_email.send_keys("teste_func")
        campo_senha.send_keys("12345")
        botao_login.click()

        try:
            WebDriverWait(self.browser, 10).until(
                EC.title_contains("Dashboard - EstudaAI")
            )
        except TimeoutException:
            html_preview = self.browser.page_source[:500]
            self.fail(
                f"A dashboard não carregou corretamente.\nTrecho HTML:\n{html_preview}"
            )

        self.assertIn("Dashboard - EstudaAI", self.browser.title)
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
