from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

class LoginAndSignupTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.url = reverse("login")
        self.pw = "Secreta123"

        # Usuário existente para testes de login e duplicidades
        self.existing = self.User.objects.create_user(
            username="exist@ex.com",
            email="exist@ex.com",
            password=self.pw,
            full_name="Pessoa Existente",
            nickname="existente",
        )

    # ==== LOGIN ====

    def test_login_sucesso_normaliza_email_e_rotaciona_sessao(self):
        # visita inicial: cria sessão
        self.client.get(self.url)
        session_antes = self.client.session.session_key

        # email com espaços e maiúsculas deve funcionar
        resp = self.client.post(
            self.url,
            {"action": "login", "email": "  EXIST@EX.COM  ", "password": self.pw},
        )
        # sucesso redireciona
        self.assertEqual(resp.status_code, 302)

        # sessão rotacionada
        session_depois = self.client.session.session_key
        self.assertNotEqual(session_antes, session_depois)

        # autenticado
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.existing.id))

    def test_login_email_inexistente_ou_senha_errada_mesma_mensagem(self):
        # email inexistente
        r1 = self.client.post(self.url, {"action": "login", "email": "nada@ex.com", "password": "qq"})
        self.assertEqual(r1.status_code, 200)
        msgs1 = [m.message for m in r1.context["messages"]]
        self.assertIn("Email ou senha incorretos.", msgs1)
        self.assertIsNone(self.client.session.get("_auth_user_id"))

        # email existe, senha errada
        r2 = self.client.post(self.url, {"action": "login", "email": "exist@ex.com", "password": "Errada"})
        self.assertEqual(r2.status_code, 200)
        msgs2 = [m.message for m in r2.context["messages"]]
        self.assertIn("Email ou senha incorretos.", msgs2)
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    # ==== CADASTRO ====

    def test_signup_senhas_diferentes(self):
        resp = self.client.post(
            self.url,
            {
                "action": "signup",
                "email": "novo@ex.com",
                "name": "joao da silva",
                "nickname": "novo",
                "password": "abc123",
                "confirm_password": "abc321",
            },
        )
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in resp.context["messages"]]
        self.assertIn("As senhas não coincidem.", msgs)
        self.assertFalse(self.User.objects.filter(username="novo@ex.com").exists())

    def test_signup_email_ja_existente(self):
        resp = self.client.post(
            self.url,
            {
                "action": "signup",
                "email": "exist@ex.com",
                "name": "x",
                "nickname": "qualquer",
                "password": "abc123",
                "confirm_password": "abc123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in resp.context["messages"]]
        self.assertIn("Email já registrado.", msgs)

    def test_signup_nickname_ja_existente(self):
        resp = self.client.post(
            self.url,
            {
                "action": "signup",
                "email": "outro@ex.com",
                "name": "y",
                "nickname": "existente",  # já usado no setUp
                "password": "abc123",
                "confirm_password": "abc123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in resp.context["messages"]]
        self.assertIn("Nickname já registrado.", msgs)
        # usuário com esse email NÃO deve ter sido criado
        self.assertFalse(self.User.objects.filter(username="outro@ex.com").exists())

    def test_signup_sucesso_normaliza_email_e_nome_preserva_nickname_e_senha(self):
        raw_email = "  NEW@EX.COM  "
        raw_name = "joÃO da   sIlVa"   # com espaços extras e mix de caixa
        nickname = "NiCk-MaisDoido"   # deve ser preservado como veio
        password = "Abc123!"

        resp = self.client.post(
            self.url,
            {
                "action": "signup",
                "email": raw_email,
                "name": raw_name,
                "nickname": nickname,
                "password": password,
                "confirm_password": password,
            },
        )
        # sucesso redireciona (e faz login)
        self.assertEqual(resp.status_code, 302)

        # usuário criado com email/username minúsculos e nome Title Case
        created = self.User.objects.get(username="new@ex.com")
        self.assertEqual(created.email, "new@ex.com")
        self.assertEqual(created.full_name, "João Da Silva")
        self.assertEqual(created.nickname, nickname)  # preserva
        # senha preservada (só dá para verificar autenticando)
        self.assertIsNotNone(authenticate(username="new@ex.com", password=password))
