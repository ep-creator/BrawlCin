"""Esmaecimento entre cenas.

Fica no App, e não numa cena intermediária. O App já é o único dono das trocas
de cena, então ele consegue animar a passagem sem que nenhuma cena saiba que
existe transição. Como cena, toda transição precisaria saber quem vem antes e
quem vem depois — e as trocas pedidas de dentro da pausa, que descartam a pilha
inteira, ficariam difíceis de encaixar.

A técnica é a mais barata que dá o resultado: guarda-se o último quadro da cena
antiga e ele é desenhado por cima da cena nova, com opacidade caindo. Não é
preciso manter a cena antiga viva nem desenhá-la duas vezes.
"""

from __future__ import annotations

import pygame


class Esmaecimento:
    """O quadro anterior desaparecendo por cima do atual."""

    def __init__(self, quadro_anterior: pygame.Surface, duracao: float):
        self.quadro = quadro_anterior
        self.duracao = duracao
        self.restante = duracao

    @property
    def terminou(self) -> bool:
        return self.restante <= 0

    @property
    def opacidade(self) -> float:
        """De 1,0 no começo a 0,0 no fim."""
        if self.duracao <= 0:
            return 0.0
        return max(0.0, self.restante / self.duracao)

    def avancar(self, dt: float) -> None:
        self.restante -= dt

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.terminou:
            return
        self.quadro.set_alpha(round(255 * self.opacidade))
        tela.blit(self.quadro, (0, 0))
