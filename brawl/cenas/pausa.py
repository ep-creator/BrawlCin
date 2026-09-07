"""Menu de pausa, aberto com ESC durante a partida.

Empilhado por cima da partida, que continua visível atrás do véu e para de ser
atualizada — o App só atualiza a cena do topo, então a pausa congela o jogo sem
precisar de nenhuma flag.
"""

from __future__ import annotations

import pygame

from .base import Desempilhar, Empilhar, SubstituirPilha, Transicao
from .confirmacao import CenaConfirmacao
from .opcoes import CenaDeOpcoes, Opcao

COR_VEU = (8, 8, 16)


class CenaPausa(CenaDeOpcoes):
    transparente = True
    titulo = "PAUSA"
    y_do_titulo = 250
    y_da_primeira_opcao = 400
    espaco_entre_opcoes = 78
    tamanho_das_opcoes = 46

    def __init__(self, partida):
        super().__init__([
            Opcao("VOLTAR AO JOGO", self._voltar),
            Opcao("CONTROLES", self._controles),
            Opcao("REINICIAR JOGO", self._reiniciar),
            Opcao("TROCAR PERSONAGENS", self._trocar_personagens),
            Opcao("MENU PRINCIPAL", self._menu_principal),
            Opcao("SAIR DO JOGO", self._sair),
        ])
        self.partida = partida
        self._veu: pygame.Surface | None = None

    # ----------------------------------------------------------------- ações

    @staticmethod
    def _voltar() -> Transicao:
        return Desempilhar()

    @staticmethod
    def _controles() -> Transicao:
        from .controles import CenaControles

        return Empilhar(CenaControles())

    def _reiniciar(self) -> Transicao:
        """Zera o placar e recomeça a rodada, sem sair da partida."""
        self.partida.reiniciar_campeonato()
        return Desempilhar()

    @staticmethod
    def _trocar_personagens() -> Transicao:
        from .selecao import CenaSelecao

        # SubstituirPilha e não Trocar: Trocar substituiria a própria pausa e
        # deixaria a partida viva embaixo dela.
        return SubstituirPilha(CenaSelecao())

    @staticmethod
    def _menu_principal() -> Transicao:
        from .menu import CenaMenu

        return SubstituirPilha(CenaMenu())

    @staticmethod
    def _sair() -> Transicao:
        return Empilhar(CenaConfirmacao())

    def _ao_cancelar(self) -> Transicao:
        """ESC fecha a pausa e devolve o jogo, em vez de encerrar."""
        return Desempilhar()

    # --------------------------------------------------------------- desenho

    def _desenhar_fundo(self, superficie: pygame.Surface) -> None:
        superficie.blit(self._obter_veu(superficie.get_size()), (0, 0))

    def _obter_veu(self, tamanho: tuple[int, int]) -> pygame.Surface:
        if self._veu is None or self._veu.get_size() != tamanho:
            self._veu = pygame.Surface(tamanho)
            self._veu.set_alpha(205)
            self._veu.fill(COR_VEU)
        return self._veu
