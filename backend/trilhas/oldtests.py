from django.test import TestCase
# import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from trilhas.models import Trilha, Categoria


User = get_user_model()


@pytest.mark.django_db
def test_rota_todas_trilhas(client):
    """
    Testa se a rota de listagem de todas as trilhas (explorar) responde corretamente.
    """
    # cria usuário de teste e faz login
    user = User.objects.create_user(username="teste", password="12345")
    client.login(username="teste", password="12345")

    url = reverse('trilhas:todas_trilhas')
    response = client.get(url)
    assert response.status_code == 200  # agora deve responder normalmente

@pytest.mark.django_db
def test_rota_detalhes_trilha(client):
    user = User.objects.create_user(username="teste2", password="12345")
    client.login(username="teste2", password="12345")

    categoria = Categoria.objects.create(nome="Backend")
    trilha = Trilha.objects.create(
        titulo="Trilha Django",
        descricao="Aprenda Django criando um projeto real",
        categoria=categoria,
        dificuldade="intermediario"
    )

    url = reverse('trilhas:ver_etapas', args=[trilha.id])
    response = client.get(url)
    assert response.status_code == 200
