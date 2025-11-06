from django.test import LiveServerTestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from trilhas.models import Trilha, Categoria, ProgressoTrilha


User = get_user_model()


class MinhasTrilhasFunctionalTests(LiveServerTestCase):
    """Testes funcionais que simulam o comportamento real do usuário no navegador."""

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
        """Simula o usuário navegando e interagindo com as trilhas."""

        # Acessa a página de exploração
        response = self.client.get(reverse('trilhas:todas_trilhas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trilha Django Funcional")

        # Inicia a trilha (resume)
        response = self.client.post(reverse('trilhas:minhas_trilhas'), {
            "action": "resume",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("retomada", response.json()["message"])

        progresso = ProgressoTrilha.objects.get(user=self.user, trilha=self.trilha)
        self.assertEqual(progresso.status, "em_progresso")

        #Pausa a trilha
        response = self.client.post(reverse('trilhas:minhas_trilhas'), {
            "action": "pause",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(response.status_code, 200)
        progresso.refresh_from_db()
        self.assertEqual(progresso.status, "pausada")

        #Retoma a trilha
        response = self.client.post(reverse('trilhas:minhas_trilhas'), {
            "action": "resume",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(response.status_code, 200)
        progresso.refresh_from_db()
        self.assertEqual(progresso.status, "em_progresso")

        # Conclui a trilha
        response = self.client.post(reverse('trilhas:minhas_trilhas'), {
            "action": "complete",
            "trilha_id": self.trilha.id
        })
        self.assertEqual(response.status_code, 200)
        progresso.refresh_from_db()
        self.assertEqual(progresso.status, "concluida")
        self.assertEqual(float(progresso.progresso_percentual), 100.0)

        # Abre a página "Minhas Trilhas" e verifica se a trilha concluída aparece
        response = self.client.get(reverse('trilhas:todas_trilhas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trilha Django Funcional")
