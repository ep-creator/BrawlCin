"""Ponto de entrada. Rodar com:  python -m brawl"""

from __future__ import annotations

import pygame

from .config import tela as config_tela
from .jogo import Jogo, ResultadoDaPartida
from .telas.abertura import mostrar_abertura
from .telas.selecao import escolher_personagens


def criar_janela() -> pygame.Surface:
    bandeiras = pygame.SCALED | (pygame.FULLSCREEN if config_tela.TELA_CHEIA else 0)
    superficie = pygame.display.set_mode(config_tela.RESOLUCAO, bandeiras)
    pygame.display.set_caption(config_tela.TITULO)
    return superficie


def main() -> None:
    pygame.init()
    try:
        superficie = criar_janela()

        if not mostrar_abertura(superficie):
            return

        # Cada volta é uma ida à seleção de personagens. Antes, trocar de
        # personagem instanciava um Jogo dentro do laço de eventos do Jogo
        # anterior — um laço principal empilhado dentro do outro a cada troca.
        while True:
            chave_p1, chave_p2 = escolher_personagens(superficie)
            if chave_p1 is None or chave_p2 is None:
                return

            resultado = Jogo(superficie, chave_p1, chave_p2).rodar()
            if resultado is not ResultadoDaPartida.NOVA_SELECAO:
                return
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
