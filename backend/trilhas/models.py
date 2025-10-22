from django.db import models
from django.conf import settings
from django.utils import timezone

# -------------------------------
# MODELOS PRINCIPAIS
# -------------------------------
class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self):
        return self.nome

class Trilha(models.Model):
    DIFICULDADE_CHOICES = [
        ('iniciante', 'Iniciante'),
        ('intermediario', 'Intermediário'),
        ('avancado', 'Avançado'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    visibilidade = models.BooleanField(default=True)
    dificuldade = models.CharField(max_length=20, choices=DIFICULDADE_CHOICES, default='iniciante')
    usuarios_salvos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="trilhas_salvas"
    )

    def __str__(self):
        return self.titulo

    @property
    def total_salvos(self):
        """Número de usuários que salvaram esta trilha"""
        return self.usuarios_salvos.count()

    def itens_ordenados(self):
        etapas = list(self.etapas.all())
        projetos = list(self.projetos.all())
        todos = etapas + projetos
        return sorted(todos, key=lambda item: item.ordem)


class Etapa(models.Model):
    trilha = models.ForeignKey(Trilha, on_delete=models.CASCADE, related_name='etapas')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    ordem = models.PositiveIntegerField(help_text="Ordem da etapa dentro da trilha")

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return f"{self.trilha.titulo} - Etapa {self.ordem}: {self.titulo}"


class Topico(models.Model):
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE, related_name='topicos')
    texto = models.TextField()
    ordem = models.PositiveIntegerField(help_text="Ordem do tópico dentro da etapa")

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return f"{self.etapa.titulo} - Tópico {self.ordem}"


class Projeto(models.Model):
    trilha = models.ForeignKey(Trilha, on_delete=models.CASCADE, related_name='projetos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(help_text="Ordem do projeto dentro da trilha")

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return f"{self.trilha.titulo} - Projeto {self.titulo}"


# -------------------------------
# PROGRESSO DO USUÁRIO
# -------------------------------
class ProgressoTrilha(models.Model):
    STATUS_CHOICES = [
        ('em_progresso', 'Em Progresso'),
        ('pausada', 'Pausada'),
        ('concluida', 'Concluída'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trilha = models.ForeignKey(Trilha, on_delete=models.CASCADE, related_name='progresso_usuarios')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_progresso')
    progresso_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_ultima_modificacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'trilha')

    def __str__(self):
        return f"{self.user.username} - {self.trilha.titulo} ({self.get_status_display()})"

    def atualizar_progresso(self):
        """Recalcula o progresso com base nos tópicos concluídos"""
        total_topicos = Topico.objects.filter(etapa__trilha=self.trilha).count()
        concluidos = ProgressoTopico.objects.filter(
            user=self.user,
            topico__etapa__trilha=self.trilha,
            concluido=True
        ).count()

        if total_topicos > 0:
            self.progresso_percentual = (concluidos / total_topicos) * 100
        else:
            self.progresso_percentual = 0

        # Atualiza status e data
        if self.progresso_percentual == 100:
            self.status = 'concluida'
        else:
            self.status = 'em_progresso'

        self.data_ultima_modificacao = timezone.now()
        self.save()


class ProgressoTopico(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progresso_topicos')
    topico = models.ForeignKey(Topico, on_delete=models.CASCADE, related_name='progresso_usuarios')
    concluido = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'topico')
        ordering = ['topico__ordem']

    def __str__(self):
        return f"{self.user.username} - {self.topico}"

    def salvar_conclusao(self, concluido=True):
        """Marca o tópico como concluído e atualiza a trilha automaticamente"""
        self.concluido = concluido
        self.data_conclusao = timezone.now() if concluido else None
        self.save()

        # Atualiza progresso da trilha
        progresso_trilha, _ = ProgressoTrilha.objects.get_or_create(
            user=self.user,
            trilha=self.topico.etapa.trilha
        )
        progresso_trilha.atualizar_progresso()
