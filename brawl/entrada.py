"""Entrada do jogador.

Por enquanto só o teste de saída. No passo seguinte deste refactor é aqui que
entram `Comando` e `ControleTeclado`, para que as entidades parem de chamar
`pygame.key.get_pressed()` por conta própria.
"""

from __future__ import annotations

import pygame


def pediu_para_sair(evento: pygame.event.Event) -> bool:
    """True se o evento é um pedido de saída (fechar a janela ou ESC)."""
    if evento.type == pygame.QUIT:
        return True
    return evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE
