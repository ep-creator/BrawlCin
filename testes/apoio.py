"""Dublês e utilitários usados pelos testes."""

from __future__ import annotations

import pygame

from brawl.cenas.base import Cena


class MapaFalso:
    """Um mapa sem depender do arquivo .tmx.

    Precisa expor `rect`, `paredes`, `aguas` e `arbustos` — é a interface que o
    jogador consome. `rect` é grande por padrão para que a borda não interfira
    em testes que só querem medir movimento.
    """

    def __init__(self, paredes=None, aguas=None, arbustos=None, tamanho=(10_000, 10_000)):
        self.paredes = paredes or []
        self.aguas = aguas or []
        self.arbustos = arbustos or []
        self.rect = pygame.Rect((0, 0), tamanho)


class Teclas:
    """Substitui o retorno de pygame.key.get_pressed()."""

    def __init__(self, *teclas_pressionadas: int):
        self._pressionadas = set(teclas_pressionadas)

    def __getitem__(self, tecla: int) -> bool:
        return tecla in self._pressionadas


class CenaBoba(Cena):
    """Cena mínima que só conta quantas vezes foi desenhada."""

    def __init__(self, nome: str = "boba", transparente: bool = False):
        self.nome = nome
        self.transparente = transparente
        self.desenhos = 0

    def desenhar(self, superficie: pygame.Surface) -> None:
        self.desenhos += 1


def teclar(tecla: int) -> None:
    """Enfileira um KEYDOWN, como se o jogador tivesse apertado a tecla."""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla))


def avancar_frame(app, dt: float = 1 / 30) -> bool:
    """Roda um frame do App à mão. False quando o jogo pediu para encerrar.

    É o corpo de App.rodar() sem o laço, o relógio e o flip — assim o teste
    controla o tempo em vez de esperar por ele.
    """
    if not app._processar_eventos():
        return False
    if not app.pilha:
        return False
    if not app._aplicar(app.topo.atualizar(dt)):
        return False
    app._desenhar()
    return True
