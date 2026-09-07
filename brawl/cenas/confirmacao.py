"""Confirmação de saída.

Encerrar o jogo passa a exigir uma resposta, por qualquer caminho: ESC no menu,
a opção Sair do menu e a opção Sair da pausa. É uma regra só — não faria sentido
o caminho fácil (ESC, apertado sem querer) perguntar e o caminho deliberado não.
"""

from __future__ import annotations

import pygame

from .base import Desempilhar, Sair, Transicao
from .opcoes import CenaDeOpcoes, Opcao

COR_VEU = (10, 8, 16)


class CenaConfirmacao(CenaDeOpcoes):
    """Empilhada por cima de quem perguntou, que continua visível atrás."""

    transparente = True
    titulo = "SAIR DO JOGO?"
    y_do_titulo = 420
    y_da_primeira_opcao = 570
    espaco_entre_opcoes = 74

    def __init__(self):
        super().__init__([
            Opcao("NÃO", self._cancelar),
            Opcao("SIM", self._confirmar),
        ])
        self._veu: pygame.Surface | None = None

    @staticmethod
    def _confirmar() -> Transicao:
        return Sair()

    @staticmethod
    def _cancelar() -> Transicao:
        return Desempilhar()

    def _ao_cancelar(self) -> Transicao:
        """ESC aqui é 'não', e não 'sim': a tecla de recuar não pode encerrar
        justamente a pergunta que existe para proteger contra recuo acidental."""
        return Desempilhar()

    def _desenhar_fundo(self, superficie: pygame.Surface) -> None:
        superficie.blit(self._obter_veu(superficie.get_size()), (0, 0))

    def _obter_veu(self, tamanho: tuple[int, int]) -> pygame.Surface:
        if self._veu is None or self._veu.get_size() != tamanho:
            self._veu = pygame.Surface(tamanho)
            self._veu.set_alpha(215)
            self._veu.fill(COR_VEU)
        return self._veu
