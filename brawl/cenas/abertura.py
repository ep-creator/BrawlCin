"""Cena de abertura: fade da logo do CIn, queda da logo do Brawl e espera.

Eram três laços `while` em sequência dentro de uma função. Como cena, viram
quatro etapas de uma máquina de estados — o que também elimina o
`pygame.time.delay(300)`, que travava o processo inteiro por 300 ms.
"""

from __future__ import annotations

import enum

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..render.efeitos import deve_desenhar_piscando, escala_de_respiracao
from .base import Cena, Trocar, Transicao

CENTRO_X = config_tela.LARGURA // 2
CENTRO_Y = config_tela.ALTURA // 2

VELOCIDADE_DO_FADE = 5          # opacidade por frame
PAUSA_APOS_FADE = 0.3           # segundos
GRAVIDADE = 0.18
ELASTICIDADE = 0.55
ESCALA_INICIAL = 6.0
FRAMES_DE_CONFIRMACAO = 36
VELOCIDADE_DA_RESPIRACAO = 6.0  # unidades de fase por segundo


class _Etapa(enum.Enum):
    FADE = enum.auto()
    PAUSA = enum.auto()
    QUEDA = enum.auto()
    ESPERA = enum.auto()
    CONFIRMANDO = enum.auto()


class CenaAbertura(Cena):
    def __init__(self):
        # copia=True porque o fade chama set_alpha na superfície — sem a cópia
        # a alteração ficaria gravada na imagem em cache.
        self.logo_cin = recursos.imagem(
            "telainicial", "logo_cin.png", tamanho=(820, 480), copia=True
        )
        self.logo_brawl = recursos.imagem("telainicial", "logo_brawl.png", tamanho=(600, 225))
        self.fundo = recursos.imagem_opcional(
            "telainicial", "tela_inicio_background.png",
            tamanho=config_tela.RESOLUCAO, alpha=False,
        )
        self.botao = recursos.imagem_opcional("telainicial", "btn.png")

        self.rect_logo_cin = self.logo_cin.get_rect(center=(CENTRO_X, CENTRO_Y))

        self.etapa = _Etapa.FADE
        self.opacidade = 0
        self.pausa_restante = PAUSA_APOS_FADE

        self.escala = ESCALA_INICIAL
        self.velocidade_da_queda = 0.0

        self.fase_da_respiracao = 0.0
        self.contador_pisca = 0
        self.frames_confirmando = 0

    # ----------------------------------------------------------------- eventos

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        if (saida := super().processar_evento(evento)) is not None:
            return saida

        if evento.type != pygame.KEYDOWN:
            return None

        if evento.key == pygame.K_SPACE and self.etapa in (
            _Etapa.FADE, _Etapa.PAUSA, _Etapa.QUEDA
        ):
            self._pular_animacoes()

        elif evento.key == pygame.K_RETURN and self.etapa is _Etapa.ESPERA:
            self.etapa = _Etapa.CONFIRMANDO
            self.frames_confirmando = FRAMES_DE_CONFIRMACAO

        return None

    def _pular_animacoes(self) -> None:
        self.logo_cin.set_alpha(255)
        self.opacidade = 255
        self.escala = 1.0
        self.etapa = _Etapa.ESPERA

    # --------------------------------------------------------------- simulação

    def atualizar(self, dt: float) -> Transicao | None:
        if self.etapa is _Etapa.FADE:
            self.opacidade = min(255, self.opacidade + VELOCIDADE_DO_FADE)
            self.logo_cin.set_alpha(self.opacidade)
            if self.opacidade >= 255:
                self.etapa = _Etapa.PAUSA

        elif self.etapa is _Etapa.PAUSA:
            self.pausa_restante -= dt
            if self.pausa_restante <= 0:
                self.etapa = _Etapa.QUEDA

        elif self.etapa is _Etapa.QUEDA:
            self.velocidade_da_queda += GRAVIDADE
            self.escala -= self.velocidade_da_queda
            if self.escala <= 1.0:
                self.escala = 1.0
                self.velocidade_da_queda = -self.velocidade_da_queda * ELASTICIDADE
                if abs(self.velocidade_da_queda) < 0.05:
                    self.etapa = _Etapa.ESPERA

        elif self.etapa is _Etapa.ESPERA:
            self.fase_da_respiracao += VELOCIDADE_DA_RESPIRACAO * dt
            self.contador_pisca += 1

        elif self.etapa is _Etapa.CONFIRMANDO:
            self.frames_confirmando -= 1
            if self.frames_confirmando <= 0:
                from .selecao import CenaSelecao  # importado aqui para evitar ciclo

                return Trocar(CenaSelecao())

        return None

    # ----------------------------------------------------------------- desenho

    def desenhar(self, superficie: pygame.Surface) -> None:
        if self.etapa is _Etapa.FADE:
            superficie.fill((0, 0, 0))
            superficie.blit(self.logo_cin, self.rect_logo_cin)
            return

        self._desenhar_cenario(superficie)

        escala = self.escala
        if self.etapa is _Etapa.ESPERA:
            escala = escala_de_respiracao(self.fase_da_respiracao, amplitude=0.05)
        self._desenhar_logo_brawl(superficie, escala)

        if self.botao is None:
            return

        rect_botao = self.botao.get_rect(center=(CENTRO_X, config_tela.ALTURA - 40))
        if self.etapa is _Etapa.ESPERA and deve_desenhar_piscando(self.contador_pisca, 15):
            superficie.blit(self.botao, rect_botao)
        elif self.etapa is _Etapa.CONFIRMANDO and deve_desenhar_piscando(
            FRAMES_DE_CONFIRMACAO - self.frames_confirmando, 2
        ):
            superficie.blit(self.botao, rect_botao)

    def _desenhar_cenario(self, superficie: pygame.Surface) -> None:
        if self.fundo is not None:
            superficie.blit(self.fundo, (0, 0))
        else:
            superficie.fill((40, 40, 40))
        superficie.blit(self.logo_cin, self.rect_logo_cin)

    def _desenhar_logo_brawl(self, superficie: pygame.Surface, escala: float) -> None:
        redimensionada = pygame.transform.scale(
            self.logo_brawl,
            (int(self.logo_brawl.get_width() * escala),
             int(self.logo_brawl.get_height() * escala)),
        )
        superficie.blit(
            redimensionada, redimensionada.get_rect(center=(CENTRO_X, CENTRO_Y + 40))
        )
