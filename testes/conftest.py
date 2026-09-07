"""Configuração comum dos testes.

O jogo é todo pygame, e pygame precisa de um display inicializado antes de
qualquer `convert_alpha()`. Aqui o display é criado uma vez por sessão de teste
com o driver "dummy", que não abre janela nenhuma — é o que permite a suíte
rodar em terminal, em CI, ou por SSH.

As variáveis de ambiente precisam ser definidas ANTES de importar o pygame,
por isso estão no topo do arquivo e não dentro de uma fixture.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402  (precisa vir depois das variáveis acima)
import pytest  # noqa: E402

from brawl.app import App  # noqa: E402
from brawl.config import tela as config_tela  # noqa: E402
from brawl.mundo.personagem import PERSONAGENS  # noqa: E402


@pytest.fixture(scope="session")
def _pygame_iniciado():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(scope="session")
def _app_da_sessao(_pygame_iniciado):
    """Um App para a sessão inteira — e com ele, o display.

    Precisa ser um só: App cria a janela com SCALED | FULLSCREEN, e um segundo
    set_mode com essas flags falha ("failed to create renderer"). Quem precisa
    de App recebe este mesmo, com a pilha zerada.
    """
    return App()


@pytest.fixture(autouse=True)
def display(_app_da_sessao):
    """Garante um display pronto: convert_alpha() não funciona sem ele."""
    return _app_da_sessao.superficie


@pytest.fixture
def app(_app_da_sessao):
    _app_da_sessao.pilha = []
    return _app_da_sessao


@pytest.fixture(autouse=True)
def fila_de_eventos_limpa():
    """Impede que evento postado por um teste vaze para o seguinte."""
    pygame.event.clear()
    yield
    pygame.event.clear()


@pytest.fixture
def personagem():
    return PERSONAGENS["shelly"]
