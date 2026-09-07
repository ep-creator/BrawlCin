"""Ponto de entrada. Rodar com:  python -m brawl"""

from __future__ import annotations

import sys

import pygame

from .app import App
from .cenas.abertura import CenaAbertura

VERSAO_MINIMA_DO_PYTHON = (3, 10)


def main() -> None:
    if sys.version_info < VERSAO_MINIMA_DO_PYTHON:
        alvo = ".".join(map(str, VERSAO_MINIMA_DO_PYTHON))
        sys.exit(f"Este jogo precisa do Python {alvo} ou mais novo.")

    pygame.init()
    try:
        app = App()                 # cria a janela primeiro
        app.rodar(CenaAbertura())   # só então as cenas podem carregar assets
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
