from django.test import TestCase
from django.contrib.auth import get_user_model
from trilhas.models import Trilha, Etapa, Topico, ProgressoTrilha, ProgressoTopico, Categoria

User = get_user_model()

class ProgressoTrilhaUnitarioTests(TestCase):
    """
    Testes UNITÁRIOS do método atualizar_progresso() de ProgressoTrilha.
    Não envolve views nem requisições HTTP — apenas lógica de cálculo.
    """

    def setUp(self):
        # Usuário e trilha base
        self.user = User.objects.create_user(username="lucas", password="12345")
        self.categoria = Categoria.objects.create(nome="Programação")

        # Cria trilha e etapa
        self.trilha = Trilha.objects.create(
            titulo="Trilha de Teste Unitário",
            descricao="Teste da função atualizar_progresso",
            categoria=self.categoria,
            dificuldade="iniciante"
        )
        self.etapa = Etapa.objects.create(trilha=self.trilha, titulo="Etapa 1", ordem=1)

        # Cria tópicos
        self.topico1 = Topico.objects.create(etapa=self.etapa, texto="Tópico 1", ordem=1)
        self.topico2 = Topico.objects.create(etapa=self.etapa, texto="Tópico 2", ordem=2)

        # Cria progresso inicial
        self.progresso = ProgressoTrilha.objects.create(user=self.user, trilha=self.trilha)

    def test_progresso_inicial_zero(self):
        """Deve iniciar com 0% de progresso quando nenhum tópico está concluído."""
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