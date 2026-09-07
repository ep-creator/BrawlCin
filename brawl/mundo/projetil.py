"""Projétil: uma bala viajando em linha reta até um alvo."""

from __future__ import annotations

import math

import pygame

from ..config import gameplay as regras


class Projetil:
    def __init__(
        self,
        x: float,
        y: float,
        alvo_x: float,
        alvo_y: float,
        cor: tuple[int, int, int],
        raio: int = regras.PROJETIL_RAIO,
        velocidade: float = regras.PROJETIL_VELOCIDADE,
        dano: int = regras.PROJETIL_DANO_BASE,
        alcance_maximo: float = regras.PROJETIL_ALCANCE_MAXIMO,
    ):
        self.x = float(x)
        self.y = float(y)
        self.raio = raio
        self.cor = cor
        self.dano = dano  # já inclui o bônus de quem atirou

        self.origem_x = float(x)
        self.origem_y = float(y)
        self.alcance_maximo = alcance_maximo

        self.rect = pygame.Rect(x - raio, y - raio, raio * 2, raio * 2)

        dx = alvo_x - x
        dy = alvo_y - y
        distancia = math.hypot(dx, dy) or 1.0  # evita divisão por zero
        self.vel_x = (dx / distancia) * velocidade
        self.vel_y = (dy / distancia) * velocidade

    @property
    def distancia_percorrida(self) -> float:
        return math.hypot(self.x - self.origem_x, self.y - self.origem_y)

    @property
    def passou_do_alcance(self) -> bool:
        return self.distancia_percorrida > self.alcance_maximo

    def mover(self) -> None:
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.center = (int(self.x), int(self.y))

    def desenhar(self, superficie: pygame.Surface) -> None:
        pygame.draw.circle(superficie, self.cor, (int(self.x), int(self.y)), self.raio)
