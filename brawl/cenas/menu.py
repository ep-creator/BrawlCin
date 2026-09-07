"""Menu principal: Jogar, Controles e Sair."""

from __future__ import annotations

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..render.efeitos import escala_de_respiracao
from .base import Empilhar, Transicao, Trocar
from .opcoes import COR_NORMAL, CenaDeOpcoes, Opcao


class CenaMenu(CenaDeOpcoes):
    def __init__(self):
        super().__init__([
            Opcao("JOGAR", self._jogar),
            Opcao("CONTROLES", self._controles),
            Opcao("SAIR", self._sair),
        ])
        self.fundo = recursos.imagem_opcional(
            "telainicial", "tela_inicio_background.png",
            tamanho=config_tela.RESOLUCAO, alpha=False,
        )
        self.logo = recursos.imagem_opcional(
            "telainicial", "logo_brawl.png", tamanho=(600, 225)
        )
        self.tempo = 0.0

    # ----------------------------------------------------------------- ações

    @staticmethod
    def _jogar() -> Transicao:
        from .selecao import CenaSelecao  # importado aqui para evitar ciclo

        return Trocar(CenaSelecao())

    @staticmethod
    def _controles() -> Transicao:
        from .controles import CenaControles

        return Empilhar(CenaControles())

    @staticmethod
    def _sair() -> Transicao:
        from .confirmacao import CenaConfirmacao

        return Empilhar(CenaConfirmacao())

    def _ao_cancelar(self) -> Transicao:
        """ESC no menu não encerra direto: pergunta.

        É a tecla mais fácil de apertar sem querer, e aqui ela seria a última
        antes de fechar o jogo. Sair pela opção também pergunta, para não haver
        dois comportamentos para a mesma decisão.
        """
        return self._sair()

    # -------------------------------------------------------------- simulação

    def atualizar(self, dt: float) -> Transicao | None:
        self.tempo += dt
        return None

    # --------------------------------------------------------------- desenho

    def _desenhar_fundo(self, superficie: pygame.Surface) -> None:
        if self.fundo is not None:
            superficie.blit(self.fundo, (0, 0))
        else:
            super()._desenhar_fundo(superficie)

        if self.logo is not None:
            superficie.blit(
                self.logo, self.logo.get_rect(center=(config_tela.LARGURA // 2, 330))
            )

    def desenhar(self, superficie: pygame.Surface) -> None:
        super().desenhar(superficie)
        self._desenhar_dica(superficie)

    def _desenhar_dica(self, superficie: pygame.Surface) -> None:
        """Pisca a instrução de navegação, para o menu se explicar sozinho."""
        opacidade = 150 + 105 * escala_de_respiracao(
            self.tempo, amplitude=1.0, velocidade=3.0, base=0.0
        )
        texto = recursos.fonte(26).render(
            "W/S ou setas para escolher  ·  ESPAÇO ou ENTER para confirmar",
            True, COR_NORMAL,
        )
        texto.set_alpha(int(max(0, min(255, opacidade))))
        superficie.blit(
            texto,
            texto.get_rect(center=(config_tela.LARGURA // 2, config_tela.ALTURA - 60)),
        )
