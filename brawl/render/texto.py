"""Desenho de texto.

Esta função existia duplicada: uma versão otimizada em `utils.py` e uma cópia
antiga em `telas/tela_selecao.py` que renderizava a borda oito vezes. A tela de
seleção importava o utils e, ainda assim, usava a cópia local. Agora há uma só.
"""

from __future__ import annotations

import pygame

_DESLOCAMENTOS_DA_BORDA = [
    (-2, -2), (0, -2), (2, -2),
    (-2, 0), (2, 0),
    (-2, 2), (0, 2), (2, 2),
]


def desenhar_texto_contornado(
    tela: pygame.Surface,
    texto: str,
    fonte: pygame.font.Font,
    cor_texto: tuple[int, int, int],
    cor_contorno: tuple[int, int, int],
    x: int,
    y: int,
) -> None:
    """Desenha `texto` centrado em (x, y) com contorno, para ficar legível
    sobre qualquer fundo.

    A borda é renderizada uma única vez e reaproveitada nos oito deslocamentos
    — `fonte.render()` com os mesmos argumentos produz sempre o mesmo resultado.
    """
    superficie_borda = fonte.render(texto, True, cor_contorno)
    for dx, dy in _DESLOCAMENTOS_DA_BORDA:
        tela.blit(superficie_borda, superficie_borda.get_rect(center=(x + dx, y + dy)))

    superficie_texto = fonte.render(texto, True, cor_texto)
    tela.blit(superficie_texto, superficie_texto.get_rect(center=(x, y)))
