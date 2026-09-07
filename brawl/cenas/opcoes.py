"""Cena de opções: uma lista navegável pelos dois teclados.

Base compartilhada pelo menu principal, pelo menu de pausa, pela tela de fim de
jogo e pela confirmação de saída. Todas fazem a mesma coisa — mostrar opções,
mover a seleção, executar a escolhida — e mudam apenas o fundo, o título e as
ações.

As teclas saem dos controles dos jogadores, e não são digitadas de novo aqui:
qualquer um dos dois navega com as próprias teclas, e remapear um controle
remapeia todos os menus junto.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..entrada import TECLADO_P1, TECLADO_P2
from ..render.texto import desenhar_texto_contornado
from .base import Cena, Sair, Transicao

TECLAS_CIMA = (TECLADO_P1.cima, TECLADO_P2.cima)
TECLAS_BAIXO = (TECLADO_P1.baixo, TECLADO_P2.baixo)
TECLAS_CONFIRMA = (TECLADO_P1.atirar, TECLADO_P2.atirar)

COR_NORMAL = (235, 235, 235)
COR_SELECIONADA = (255, 205, 60)
COR_CONTORNO = (25, 20, 40)
COR_FUNDO = (18, 16, 28)


@dataclass(frozen=True)
class Opcao:
    rotulo: str
    acao: Callable[[], Transicao | None]


class CenaDeOpcoes(Cena):
    """Lista de opções navegável. Subclasses definem fundo, título e ações."""

    titulo: str | None = None
    tamanho_do_titulo = 58
    tamanho_das_opcoes = 52
    y_do_titulo = 260
    y_da_primeira_opcao = 620
    espaco_entre_opcoes = 78

    def __init__(self, opcoes: Iterable[Opcao]):
        self.opcoes = list(opcoes)
        self.indice = 0

    # --------------------------------------------------------------- eventos

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        if evento.type != pygame.KEYDOWN:
            return None

        if evento.key == pygame.K_ESCAPE:
            return self._ao_cancelar()
        if evento.key in TECLAS_CIMA:
            self._mover(-1)
        elif evento.key in TECLAS_BAIXO:
            self._mover(1)
        elif evento.key in TECLAS_CONFIRMA:
            return self.opcoes[self.indice].acao()

        return None

    def _ao_cancelar(self) -> Transicao | None:
        """O que ESC faz. Encerrar é o padrão herdado da classe Cena; quem tem
        um passo atrás — a pausa, a confirmação — sobrescreve."""
        return Sair()

    def _mover(self, passo: int) -> None:
        self.indice = (self.indice + passo) % len(self.opcoes)

    # --------------------------------------------------------------- desenho

    def desenhar(self, superficie: pygame.Surface) -> None:
        self._desenhar_fundo(superficie)
        self._desenhar_titulo(superficie)
        self._desenhar_opcoes(superficie)

    def _desenhar_fundo(self, superficie: pygame.Surface) -> None:
        superficie.fill(COR_FUNDO)

    def _desenhar_titulo(self, superficie: pygame.Surface) -> None:
        if not self.titulo:
            return
        desenhar_texto_contornado(
            superficie, self.titulo, recursos.fonte_do_jogo(self.tamanho_do_titulo),
            COR_SELECIONADA, COR_CONTORNO, config_tela.LARGURA // 2, self.y_do_titulo,
        )

    def _desenhar_opcoes(self, superficie: pygame.Surface) -> None:
        fonte = recursos.fonte_do_jogo(self.tamanho_das_opcoes)
        for i, opcao in enumerate(self.opcoes):
            selecionada = i == self.indice
            desenhar_texto_contornado(
                superficie,
                f"> {opcao.rotulo} <" if selecionada else opcao.rotulo,
                fonte,
                COR_SELECIONADA if selecionada else COR_NORMAL,
                COR_CONTORNO,
                config_tela.LARGURA // 2,
                self.y_da_primeira_opcao + i * self.espaco_entre_opcoes,
            )
