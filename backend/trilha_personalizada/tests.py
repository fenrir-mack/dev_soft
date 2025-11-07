from django.test import TestCase, Client
from django.urls import reverse, resolve
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
import json
from trilha_personalizada import views
from trilha_personalizada.prompt import build_prompt
from trilhas.models import Categoria, Trilha, Etapa, Topico, Projeto

User = get_user_model()

# ==============================
# Testes de URLs
# ==============================
class UrlsTests(TestCase):
    def test_trilha_personalizada_url_resolves(self):
        url = reverse('trilha_personalizada:trilha_personalizada')
        self.assertEqual(resolve(url).func, views.custom_path_view)

    def test_salvar_trilha_url_resolves(self):
        url = reverse('trilha_personalizada:salvar_trilha')
        self.assertEqual(resolve(url).func, views.salvar_trilha_view)


# ==============================
# Testes de Prompt
# ==============================
class PromptTests(TestCase):
    def test_build_prompt_includes_theme_and_difficulty(self):
        theme = "Python"
        dificuldade = "iniciante"
        prompt = build_prompt(theme, dificuldade)
        self.assertIn(theme, prompt)
        self.assertIn(dificuldade, prompt)
        self.assertIn('"trilha"', prompt)


# ==============================
# Testes da view custom_path_view
# ==============================
class CustomPathViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='teste', password='1234')
        self.client.login(username='teste', password='1234')

    @patch('trilha_personalizada.views.model')
    def test_post_generates_valid_json(self, mock_model):
        # Mock IA
        fake_response = MagicMock()
        fake_response.text = '{"trilha": {"titulo": "Teste", "descricao": "desc", "dificuldade": "iniciante"}, "etapas": [{"ordem":1,"titulo":"Intro","topicos":[{"ordem":1,"texto":"A"}]}], "projetos": [{"ordem":2,"titulo":"Projeto Final","descricao":"desc"}]}'
        mock_model.generate_content.return_value = fake_response

        response = self.client.post(reverse('trilha_personalizada:trilha_personalizada'), {
            'tema_trilha': 'Python',
            'dificuldade': 'iniciante'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("trilha", data)
        self.assertIn("conteudo_ordenado", data)
        self.assertIsInstance(data["conteudo_ordenado"], list)

    def test_post_without_tema_returns_error(self):
        response = self.client.post(reverse('trilha_personalizada:trilha_personalizada'), {
            'tema_trilha': ''
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch('trilha_personalizada.views.model')
    def test_post_with_invalid_json_returns_500(self, mock_model):
        fake_response = MagicMock()
        fake_response.text = 'invalid json text'
        mock_model.generate_content.return_value = fake_response

        response = self.client.post(reverse('trilha_personalizada:trilha_personalizada'), {
            'tema_trilha': 'Python',
            'dificuldade': 'iniciante'
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())


# ==============================
# Testes da view salvar_trilha_view
# ==============================
class SalvarTrilhaViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='teste', password='1234')
        self.client.login(username='teste', password='1234')

    def test_salvar_trilha_view_saves_correctly(self):
        # Cria uma categoria real para associar à trilha
        categoria = Categoria.objects.create(nome="Programação")

        data = {
            "trilha": {
                "titulo": "Minha Trilha",
                "descricao": "Descrição teste",
                "dificuldade": "iniciante",
                "categoria": categoria.id
            },
            "conteudo_ordenado": [
                {
                    "ordem": 1,
                    "titulo": "Etapa 1",
                    "topicos": [{"ordem": 1, "texto": "Tópico 1"}]
                },
                {
                    "ordem": 2,
                    "titulo": "Projeto Final",
                    "descricao": "Projeto de teste"
                }
            ]
        }

        response = self.client.post(
            reverse('trilha_personalizada:salvar_trilha'),
            data=json.dumps(data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("redirect_url", response.json())

        # Verifica se a trilha foi criada no banco de teste
        trilha = Trilha.objects.get(titulo="Minha Trilha")
        self.assertEqual(trilha.dificuldade, "iniciante")
        self.assertEqual(trilha.etapas.count(), 1)
        self.assertEqual(trilha.projetos.count(), 1)

        # Verifica se o tópico foi criado
        etapa = trilha.etapas.first()
        self.assertEqual(etapa.topicos.count(), 1)
        self.assertEqual(etapa.topicos.first().texto, "Tópico 1")

    def test_salvar_trilha_view_invalid_method(self):
        response = self.client.get(reverse('trilha_personalizada:salvar_trilha'))
        self.assertEqual(response.status_code, 405)