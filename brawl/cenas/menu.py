"""Menu principal: Jogar, Controles e Sair.

Antes a abertura ia direto para a seleção de personagens — não havia menu, nem
como sair sem ESC, nem onde descobrir os controles.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..entrada import TECLADO_P1, TECLADO_P2
from ..render.efeitos import escala_de_respiracao
from ..render.texto import desenhar_texto_contornado
from .base import Cena, Empilhar, Sair, Transicao, Trocar

# As teclas do menu saem dos controles dos jogadores: qualquer um dos dois
# navega com as próprias teclas, e remapear um controle remapeia o menu junto.
TECLAS_CIMA = (TECLADO_P1.cima, TECLADO_P2.cima)
TECLAS_BAIXO = (TECLADO_P1.baixo, TECLADO_P2.baixo)
TECLAS_CONFIRMA = (TECLADO_P1.atirar, TECLADO_P2.atirar)

COR_NORMAL = (235, 235, 235)
COR_SELECIONADA = (255, 205, 60)
COR_CONTORNO = (25, 20, 40)
COR_FUNDO = (18, 16, 28)

Y_DA_PRIMEIRA_OPCAO = 620
ESPACO_ENTRE_OPCOES = 78


@dataclass(frozen=True)
class Opcao:
    rotulo: str
    acao: Callable[[], Transicao | None]


class CenaMenu(Cena):
    def __init__(self):
        self.fundo = recursos.imagem_opcional(
            "telainicial", "tela_inicio_background.png",
            tamanho=config_tela.RESOLUCAO, alpha=False,
        )
        self.logo = recursos.imagem_opcional(
            "telainicial", "logo_brawl.png", tamanho=(600, 225)
        )
        self.fonte = recursos.fonte_do_jogo(52)

        self.opcoes = [
            Opcao("JOGAR", self._jogar),
            Opcao("CONTROLES", self._controles),
            Opcao("SAIR", self._sair),
        ]
        self.indice = 0
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
        return Sair()

    # --------------------------------------------------------------- eventos

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        if (saida := super().processar_evento(evento)) is not None:
            return saida

        if evento.type != pygame.KEYDOWN:
            return None

        if evento.key in TECLAS_CIMA:
            self._mover(-1)
        elif evento.key in TECLAS_BAIXO:
            self._mover(1)
        elif evento.key in TECLAS_CONFIRMA:
            return self.opcoes[self.indice].acao()

        return None

    def _mover(self, passo: int) -> None:
        self.indice = (self.indice + passo) % len(self.opcoes)

    def atualizar(self, dt: float) -> Transicao | None:
        self.tempo += dt
        return None

    # --------------------------------------------------------------- desenho

    def desenhar(self, superficie: pygame.Surface) -> None:
        if self.fundo is not None:
            superficie.blit(self.fundo, (0, 0))
        else:
            superficie.fill(COR_FUNDO)

        if self.logo is not None:
            superficie.blit(
                self.logo, self.logo.get_rect(center=(config_tela.LARGURA // 2, 330))
            )

        for i, opcao in enumerate(self.opcoes):
            selecionada = i == self.indice
            cor = COR_SELECIONADA if selecionada else COR_NORMAL
            rotulo = f"> {opcao.rotulo} <" if selecionada else opcao.rotulo
            desenhar_texto_contornado(
                superficie, rotulo, self.fonte, cor, COR_CONTORNO,
                config_tela.LARGURA // 2,
                Y_DA_PRIMEIRA_OPCAO + i * ESPACO_ENTRE_OPCOES,
            )

        self._desenhar_dica(superficie)

    def _desenhar_dica(self, superficie: pygame.Surface) -> None:
        """Pisca a instrução de navegação, para o menu se explicar sozinho."""
        opacidade = 150 + 105 * escala_de_respiracao(self.tempo, amplitude=1.0,
                                                     velocidade=3.0, base=0.0)
        fonte = recursos.fonte(26)
        texto = fonte.render(
            "W/S ou setas para escolher  ·  ESPAÇO ou ENTER para confirmar",
            True, COR_NORMAL,
        )
        texto.set_alpha(int(max(0, min(255, opacidade))))
        superficie.blit(
            texto,
            texto.get_rect(center=(config_tela.LARGURA // 2, config_tela.ALTURA - 60)),
        )
