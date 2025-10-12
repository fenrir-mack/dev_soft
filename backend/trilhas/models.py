from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

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
    total_salvos = models.PositiveIntegerField(default=0, help_text="Número de usuários que salvaram a trilha")

    def __str__(self):
        return self.titulo

class Etapa(models.Model):
    texto = models.CharField(max_length=200)
    ordem = models.PositiveIntegerField(help_text="Ordem do projeto dentro da trilha")
    trilha = models.ForeignKey(Trilha, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.ordem} - {self.texto}"

class Projeto(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    trilha = models.ForeignKey(Trilha, on_delete=models.CASCADE, related_name="projetos")
    ordem = models.PositiveIntegerField(help_text="Ordem do projeto dentro da trilha")

    def __str__(self):
        return f"{self.trilha.titulo} - {self.titulo}"

class ProgressoEtapa(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    etapa = models.ForeignKey('Etapa', on_delete=models.CASCADE)
    concluida = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'etapa')

    def __str__(self):
        return f"{self.user.full_name} - {self.etapa.texto} - {'Concluída' if self.concluida else 'Pendente'}"
