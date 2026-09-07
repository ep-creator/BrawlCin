"""Tela de fim de campeonato.

Era um véu com dois atalhos escondidos: R para reiniciar e T para trocar de
personagens, escritos como instrução na tela. Agora é o mesmo menu navegável do
resto do jogo — um jeito só de escolher, em vez de teclas para decorar.
"""

from __future__ import annotations

import pygame

from .base import Desempilhar, Empilhar, SubstituirPilha, Transicao
from .confirmacao import CenaConfirmacao
from .opcoes import CenaDeOpcoes, Opcao

COR_VEU = (0, 0, 0)
COR_VENCEDOR = (0, 255, 128)


class CenaFimDeJogo(CenaDeOpcoes):
    transparente = True
    y_do_titulo = 330
    y_da_primeira_opcao = 500
    espaco_entre_opcoes = 78
    tamanho_do_titulo = 62
    tamanho_das_opcoes = 46

    def __init__(self, partida, vencedor: int):
        super().__init__([
            Opcao("JOGAR DE NOVO", self._jogar_de_novo),
            Opcao("TROCAR PERSONAGENS", self._trocar_personagens),
            Opcao("MENU PRINCIPAL", self._menu_principal),
            Opcao("SAIR DO JOGO", self._sair),
        ])
        self.partida = partida
        self.vencedor = vencedor
        self.titulo = f"PLAYER {vencedor} VENCEU!"
        self._veu: pygame.Surface | None = None

    def _jogar_de_novo(self) -> Transicao:
        self.partida.reiniciar_campeonato()
        return Desempilhar()

    @staticmethod
    def _trocar_personagens() -> Transicao:
        from .selecao import CenaSelecao

        return SubstituirPilha(CenaSelecao())

    @staticmethod
    def _menu_principal() -> Transicao:
        from .menu import CenaMenu

        return SubstituirPilha(CenaMenu())

    @staticmethod
    def _sair() -> Transicao:
        return Empilhar(CenaConfirmacao())

    def _ao_cancelar(self) -> Transicao:
        """Não há jogo para voltar: a partida acabou. ESC vai para o menu."""
        return self._menu_principal()

    def _desenhar_titulo(self, superficie: pygame.Surface) -> None:
        from ..config import tela as config_tela
        from ..render.texto import desenhar_texto_contornado
        from .opcoes import COR_CONTORNO
        from .. import recursos

        desenhar_texto_contornado(
            superficie, self.titulo, recursos.fonte_do_jogo(self.tamanho_do_titulo),
            COR_VENCEDOR, COR_CONTORNO, config_tela.LARGURA // 2, self.y_do_titulo,
        )

    def _desenhar_fundo(self, superficie: pygame.Surface) -> None:
        superficie.blit(self._obter_veu(superficie.get_size()), (0, 0))

    def _obter_veu(self, tamanho: tuple[int, int]) -> pygame.Surface:
        if self._veu is None or self._veu.get_size() != tamanho:
            self._veu = pygame.Surface(tamanho)
            self._veu.set_alpha(215)
            self._veu.fill(COR_VEU)
        return self._veu
