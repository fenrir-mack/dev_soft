from django.test import TestCase, LiveServerTestCase, Client
from .models import (Categoria,Trilha,Etapa,Topico,Projeto,ProgressoTrilha,ProgressoTopico)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()


# ==========================================================
# 🧩 TESTES UNITÁRIOS - DASHBOARD
# ==========================================================
class DashboardUnitTest(TestCase):
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






# ==========================================================
# 🧩 TESTES UNITÁRIOS - MODELS (TRILHAS)
# ==========================================================
class TrilhaModelUnitTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="senha123",
            nickname="User 1",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="senha123",
            nickname="User 2",
        )

        self.categoria = Categoria.objects.create(nome="Backend")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Python",
            descricao="Aprenda Python do zero",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="iniciante",
        )

    def test_total_salvos_conta_usuarios_corretamente(self):
        """Deve retornar a quantidade de usuários que salvaram a trilha."""
        self.trilha.usuarios_salvos.add(self.user1, self.user2)
        self.assertEqual(self.trilha.total_salvos, 2)

    def test_itens_ordenados_retorna_etapas_e_projetos_em_ordem(self):
        """Deve juntar etapas e projetos e ordenar pelo campo 'ordem'."""
        Etapa.objects.create(trilha=self.trilha, titulo="Etapa 1", ordem=2)
        Etapa.objects.create(trilha=self.trilha, titulo="Etapa 2", ordem=1)
        Projeto.objects.create(
            trilha=self.trilha, titulo="Projeto Final", descricao="Desc", ordem=3
        )

        itens = self.trilha.itens_ordenados()
        ordens = [item.ordem for item in itens]
        self.assertEqual(ordens, [1, 2, 3])


class ProgressoTrilhaModelUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user_prog",
            email="user_prog@example.com",
            password="senha123",
            nickname="Prog User",
        )

        self.categoria = Categoria.objects.create(nome="Web")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Web",
            descricao="HTML, CSS, JS",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="intermediario",
        )

        self.etapa = Etapa.objects.create(
            trilha=self.trilha, titulo="Fundamentos", ordem=1
        )
        self.topico1 = Topico.objects.create(
            etapa=self.etapa, texto="HTML básico", ordem=1
        )
        self.topico2 = Topico.objects.create(
            etapa=self.etapa, texto="CSS básico", ordem=2
        )
        self.topico3 = Topico.objects.create(
            etapa=self.etapa, texto="JS básico", ordem=3
        )

        self.progresso_trilha = ProgressoTrilha.objects.create(
            user=self.user,
            trilha=self.trilha,
            status="em_progresso",
            progresso_percentual=Decimal("0.00"),
        )

    def test_atualizar_progresso_calcula_percentual_correto(self):
        """Deve calcular o percentual com base nos tópicos concluídos."""
        ProgressoTopico.objects.create(
            user=self.user, topico=self.topico1, concluido=True
        )
        ProgressoTopico.objects.create(
            user=self.user, topico=self.topico2, concluido=True
        )

        self.progresso_trilha.atualizar_progresso()
        self.assertAlmostEqual(
            float(self.progresso_trilha.progresso_percentual), 66.66, places=1
        )


class ProgressoTopicoModelUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user_topic",
            email="user_topic@example.com",
            password="senha123",
            nickname="Topic User",
        )

        self.categoria = Categoria.objects.create(nome="Data Science")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Dados",
            descricao="Introdução a Dados",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="iniciante",
        )

        self.etapa = Etapa.objects.create(
            trilha=self.trilha, titulo="Intro", ordem=1
        )
        self.topico = Topico.objects.create(
            etapa=self.etapa, texto="O que é dado?", ordem=1
        )

    def test_salvar_conclusao_true_registra_data_e_atualiza_trilha(self):
        """Quando marcar concluído=True, deve salvar data e atualizar progresso da trilha."""
        progresso_topico = ProgressoTopico.objects.create(
            user=self.user, topico=self.topico, concluido=False
        )

        progresso_topico.salvar_conclusao(concluido=True)
        progresso_topico.refresh_from_db()

        self.assertTrue(progresso_topico.concluido)
        self.assertIsNotNone(progresso_topico.data_conclusao)

        progresso_trilha = ProgressoTrilha.objects.get(
            user=self.user, trilha=self.trilha
        )
        self.assertEqual(float(progresso_trilha.progresso_percentual), 100.0)


# ==========================================================
# 🔗 TESTES DE INTEGRAÇÃO - TRILHAS
# ==========================================================
class ToggleTopicoIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user_toggle",
            email="user_toggle@example.com",
            password="senha123",
            nickname="Toggle User",
        )

        self.categoria = Categoria.objects.create(nome="DevOps")
        self.trilha = Trilha.objects.create(
            titulo="Trilha DevOps",
            descricao="CI/CD, Docker, etc.",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="avancado",
        )

        self.etapa = Etapa.objects.create(
            trilha=self.trilha, titulo="Docker", ordem=1
        )
        self.topico = Topico.objects.create(
            etapa=self.etapa, texto="Instalar Docker", ordem=1
        )

        self.url_toggle = reverse("trilhas:toggle_topico")

    def test_toggle_topico_cria_progresso_topico_e_trilha(self):
        """POST em toggle_topico deve criar ProgressoTopico + ProgressoTrilha e retornar progresso em JSON."""
        self.client.force_login(self.user)

        response = self.client.post(
            self.url_toggle,
            data={"topico_id": self.topico.id, "completed": "true"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        pt = ProgressoTopico.objects.get(user=self.user, topico=self.topico)
        self.assertTrue(pt.concluido)

        progresso_trilha = ProgressoTrilha.objects.get(
            user=self.user, trilha=self.trilha
        )
        self.assertEqual(float(progresso_trilha.progresso_percentual), 100.0)

    def test_toggle_topico_desmarca_topico_e_zera_progresso(self):
        """Se enviar completed=false, deve desmarcar o tópico e reduzir progresso."""
        self.client.force_login(self.user)

        self.client.post(
            self.url_toggle,
            data={"topico_id": self.topico.id, "completed": "true"},
        )

        response = self.client.post(
            self.url_toggle,
            data={"topico_id": self.topico.id, "completed": "false"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        pt = ProgressoTopico.objects.get(user=self.user, topico=self.topico)
        self.assertFalse(pt.concluido)

        progresso_trilha = ProgressoTrilha.objects.get(
            user=self.user, trilha=self.trilha
        )
        self.assertEqual(float(progresso_trilha.progresso_percentual), 0.0)


class ExplorarViewIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user_explorar",
            email="user_explorar@example.com",
            password="senha123",
            nickname="Explorar User",
        )

        # Trilhas de banco (domínio), mesmo que o template use paths fixos
        self.categoria = Categoria.objects.create(nome="Mobile")
        self.trilha1 = Trilha.objects.create(
            titulo="Trilha Android",
            descricao="Kotlin e Android Studio",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="intermediario",
        )
        self.trilha2 = Trilha.objects.create(
            titulo="Trilha iOS",
            descricao="Swift e Xcode",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="avancado",
        )

        self.url_explorar = reverse("trilhas:todas_trilhas")

    def test_explorar_responde_ok_e_usa_template_correto(self):
        """
        GET em /explorar/ deve responder 200, usar o template correto
        e exibir os textos principais da página.
        """
        self.client.force_login(self.user)

        response = self.client.get(self.url_explorar)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "trilhas/explorar.html")

        html = response.content.decode()
        self.assertIn("Trilhas de Aprendizagem", html)
        # 🔹 aqui ajustamos para o subtítulo REAL do template
        self.assertIn("Explore Trilhas Publicas Feitas Por Usuários", html)


# ==========================================================
# 🧭 TESTE FUNCIONAL - FLUXO COMPLETO (SEM SELENIUM)
# ==========================================================
class FluxoCompletoFunctionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user_func",
            email="user_func@example.com",
            password="senha123",
            nickname="Func User",
        )

        self.categoria = Categoria.objects.create(nome="Fullstack")
        self.trilha = Trilha.objects.create(
            titulo="Trilha Fullstack",
            descricao="Frontend + Backend",
            categoria=self.categoria,
            visibilidade=True,
            dificuldade="intermediario",
        )

        self.etapa = Etapa.objects.create(
            trilha=self.trilha, titulo="Setup", ordem=1
        )
        self.topico = Topico.objects.create(
            etapa=self.etapa, texto="Instalar VSCode", ordem=1
        )

        self.url_explorar = reverse("trilhas:todas_trilhas")
        self.url_detalhes = reverse("trilhas:ver_etapas")
        self.url_toggle = reverse("trilhas:toggle_topico")

    def test_fluxo_usuario_salva_trilha_e_conclui_topico(self):
        """
        Fluxo funcional completo (sem Selenium):
        1) Usuário loga
        2) Acessa explorar
        3) "Salva" a trilha (simulado criando ProgressoTrilha)
        4) Acessa detalhes
        5) Marca um tópico como concluído
        6) Verifica progresso atualizado
        """
        self.client.force_login(self.user)

        # 1) Acessa explorar
        resp_explorar = self.client.get(self.url_explorar)
        self.assertEqual(resp_explorar.status_code, 200)

        # 2) Simula que o usuário salvou a trilha (cria ProgressoTrilha)
        ProgressoTrilha.objects.create(
            user=self.user,
            trilha=self.trilha,
            status="em_progresso",
            progresso_percentual=Decimal("0.00"),
        )
        self.assertTrue(
            ProgressoTrilha.objects.filter(
                user=self.user, trilha=self.trilha
            ).exists()
        )

        # 3) Abre detalhes da trilha
        resp_detalhes = self.client.get(
            self.url_detalhes, {"id": self.trilha.id}
        )
        self.assertEqual(resp_detalhes.status_code, 200)
        self.assertTemplateUsed(resp_detalhes, "trilhas/detalhes-da-trilha.html")

        # 4) Marca tópico como concluído
        resp_toggle = self.client.post(
            self.url_toggle,
            data={"topico_id": self.topico.id, "completed": "true"},
        )
        self.assertEqual(resp_toggle.status_code, 200)
        data_toggle = resp_toggle.json()
        self.assertTrue(data_toggle["success"])

        # 5) Confere progresso no banco
        progresso_trilha = ProgressoTrilha.objects.get(
            user=self.user, trilha=self.trilha
        )
        self.assertEqual(float(progresso_trilha.progresso_percentual), 100.0)

        progresso_topico = ProgressoTopico.objects.get(
            user=self.user, topico=self.topico
        )
        self.assertTrue(progresso_topico.concluido)
