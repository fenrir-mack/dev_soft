from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

User = get_user_model()

# ==========================================================
# 🧩 TESTES UNITÁRIOS
# ==========================================================
class DashboardUnitTest(TestCase):
    """Testes básicos da view da dashboard"""

    def setUp(self):
        # Cria um usuário de teste com username e nickname
        self.user = User.objects.create_user(
            username="testeuser",
            email="testeuser@example.com",
            password="12345",
            nickname="testeuser"
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
        self.assertIn("/", response.url)


# ==========================================================
# 🔗 TESTE DE INTEGRAÇÃO
# ==========================================================
class DashboardIntegrationTest(TestCase):
    """Verifica o fluxo de login e navegação para a dashboard"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="teste_integ",
            email="teste_integ@example.com",
            password="12345",
            nickname="teste_integ"
        )

    def test_fluxo_login_e_dashboard(self):
        """Fluxo completo de login e acesso"""
        login_ok = self.client.login(username="teste_integ", password="12345")
        self.assertTrue(login_ok, "Falha ao logar usuário de integração.")

        response = self.client.get(reverse("trilhas:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard - EstudaAI")


# ==========================================================
# 🌐 TESTE FUNCIONAL (SELENIUM)
# ==========================================================
class DashboardFunctionalTest(LiveServerTestCase):
    """Simula o login real no navegador e acesso à dashboard"""

    def setUp(self):
        # Inicia o navegador (usa Firefox por padrão)
        self.browser = webdriver.Firefox()

    def tearDown(self):
        # Fecha o navegador após o teste
        self.browser.quit()

    def test_usuario_pode_fazer_login_e_ver_dashboard(self):
        """
        Simula login real via username (o site mostra 'email',
        mas autentica com username internamente)
        """
        User.objects.all().delete()

        user = User.objects.create_user(
            username="teste_func",
            email="teste_func@example.com",
            password="12345",
            nickname="teste_func"
        )

        self.browser.get(f"{self.live_server_url}/")

        try:
            campo_email = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "loginEmail"))
            )
            campo_senha = self.browser.find_element(By.ID, "loginPassword")
            botao_login = self.browser.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")
        except TimeoutException:
            self.fail("Campos de login não encontrados na página.")

        # 🔹 Desativa a validação de formato de e-mail
        self.browser.execute_script(
            "document.getElementById('loginEmail').setAttribute('type','text');"
        )

        # Preenche com username (já que backend autentica por username)
        campo_email.send_keys("teste_func")
        campo_senha.send_keys("12345")

        botao_login.click()

        try:
            WebDriverWait(self.browser, 10).until(
                EC.title_contains("Dashboard - EstudaAI")
            )
        except TimeoutException:
            html_preview = self.browser.page_source[:500]
            self.fail(f"A dashboard não carregou corretamente.\nTrecho HTML:\n{html_preview}")

        self.assertIn("Dashboard - EstudaAI", self.browser.title)
