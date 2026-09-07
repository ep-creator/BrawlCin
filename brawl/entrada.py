"""Entrada do jogador: da tecla para a intenção.

Antes, `Player.move()` chamava `pygame.key.get_pressed()` e lia o teclado
inteiro por conta própria, enquanto o tiro estava fixo como K_SPACE/K_RETURN
dentro do game.py — apesar de o Player já carregar `controls["atirar"]`, que
nunca era usado.

Agora o jogador não sabe o que é um teclado. Ele recebe um `Comando` por frame,
e quem produz `Comando` é um `ControleTeclado`. Um bot, um replay gravado ou um
gamepad entram como outro produtor de `Comando`, sem tocar no jogador.

É também o único lugar onde a direção é normalizada, o que conserta o bug da
velocidade diagonal: antes, `velocidade` era aplicada inteira no eixo X e de
novo no eixo Y, e andar na diagonal dava um deslocamento de v·raiz(2) — medido
em 2,83 px por frame contra 2,00 px nos eixos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class Comando:
    """O que um jogador quer fazer neste frame.

    `dx`/`dy` formam um vetor de comprimento no máximo 1 — quem consome
    multiplica pela velocidade da entidade e não precisa saber de normalização.
    `atirar` vale para um frame só: é disparo por toque, não por tecla segurada.
    """

    dx: float = 0.0
    dy: float = 0.0
    atirar: bool = False

    @property
    def esta_parado(self) -> bool:
        return self.dx == 0.0 and self.dy == 0.0


PARADO = Comando()


def normalizar(dx: float, dy: float) -> tuple[float, float]:
    """Encolhe o vetor para comprimento 1 quando ele for maior que isso.

    É o conserto da diagonal, num lugar só: (1, 1) vira (0.707, 0.707), de modo
    que andar na diagonal cobre a mesma distância por frame que andar num eixo.
    """
    comprimento = math.hypot(dx, dy)
    if comprimento <= 1.0:
        return dx, dy
    return dx / comprimento, dy / comprimento


class ControleTeclado:
    """Mapeia teclas para `Comando`. Um por jogador."""

    def __init__(self, esquerda: int, direita: int, cima: int, baixo: int, atirar: int):
        self.esquerda = esquerda
        self.direita = direita
        self.cima = cima
        self.baixo = baixo
        self.atirar = atirar

    def ler(self, teclas, atirar: bool = False) -> Comando:
        """Monta o comando deste frame a partir das teclas pressionadas.

        Teclas opostas se cancelam — segurar esquerda e direita ao mesmo tempo
        deixa o jogador parado. Antes, o `elif` fazia a esquerda sempre ganhar.
        """
        dx = float(bool(teclas[self.direita]) - bool(teclas[self.esquerda]))
        dy = float(bool(teclas[self.baixo]) - bool(teclas[self.cima]))
        dx, dy = normalizar(dx, dy)
        return Comando(dx=dx, dy=dy, atirar=atirar)


TECLADO_P1 = ControleTeclado(
    esquerda=pygame.K_a, direita=pygame.K_d,
    cima=pygame.K_w, baixo=pygame.K_s,
    atirar=pygame.K_SPACE,
)

TECLADO_P2 = ControleTeclado(
    esquerda=pygame.K_LEFT, direita=pygame.K_RIGHT,
    cima=pygame.K_UP, baixo=pygame.K_DOWN,
    atirar=pygame.K_RETURN,
)


def pediu_para_sair(evento: pygame.event.Event) -> bool:
    """True se o evento é um pedido de saída (fechar a janela ou ESC)."""
    if evento.type == pygame.QUIT:
        return True
    return evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE
