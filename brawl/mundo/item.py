"""Item coletável no mapa: vida, dano ou velocidade."""

from __future__ import annotations

import pygame

from .. import recursos
from ..config import gameplay as regras


class Item:
    ordem_no_empate = 0

    def __init__(self, x: int, y: int, tipo: str):
        arquivo = regras.ITEM_ARQUIVOS.get(tipo)
        if arquivo is None:
            raise ValueError(
                f"Tipo de item desconhecido: {tipo!r}. "
                f"Tipos válidos: {list(regras.ITEM_ARQUIVOS)}"
            )

        self.tipo = tipo
        self.rect = pygame.Rect(x, y, regras.ITEM_TAMANHO, regras.ITEM_TAMANHO)
        self.imagem = recursos.imagem(
            "coletaveis", arquivo, tamanho=(regras.ITEM_TAMANHO, regras.ITEM_TAMANHO)
        )

    @property
    def profundidade(self) -> int:
        return self.rect.bottom

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.imagem, self.rect)
