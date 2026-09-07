"""O laço principal: o único dono do relógio, dos eventos e da pilha de cenas."""

from __future__ import annotations

import pygame

from .cenas.base import (
    Cena,
    Desempilhar,
    Empilhar,
    Sair,
    SubstituirPilha,
    Transicao,
    Trocar,
)
from .config import tela as config_tela
from .render.transicao import Esmaecimento


class App:
    """Cria a janela e roda a pilha de cenas.

    A janela nasce no __init__ e a cena inicial só chega no `rodar()` de
    propósito: as cenas carregam imagens com `convert_alpha()`, que exige um
    display já inicializado. Construir a cena antes do App seria carregar
    assets sem tela.
    """

    def __init__(self) -> None:
        self.superficie = self._criar_janela()
        self.relogio = pygame.time.Clock()
        self.pilha: list[Cena] = []
        self._esmaecimento: Esmaecimento | None = None

    @staticmethod
    def _criar_janela() -> pygame.Surface:
        bandeiras = pygame.SCALED | (pygame.FULLSCREEN if config_tela.TELA_CHEIA else 0)
        superficie = pygame.display.set_mode(config_tela.RESOLUCAO, bandeiras)
        pygame.display.set_caption(config_tela.TITULO)
        return superficie

    @property
    def topo(self) -> Cena:
        return self.pilha[-1]

    def rodar(self, cena_inicial: Cena) -> None:
        self.pilha = [cena_inicial]

        while self.pilha:
            dt = self.relogio.tick(config_tela.FPS) / 1000.0

            if not self._processar_eventos():
                break
            if not self.pilha:
                break

            if not self._aplicar(self.topo.atualizar(dt)):
                break

            self._desenhar()
            self._desenhar_transicao(dt)
            pygame.display.flip()

    def _processar_eventos(self) -> bool:
        """False se o jogo deve terminar."""
        for evento in pygame.event.get():
            # Fechar a janela é do App: nenhuma cena precisa lembrar disso.
            if evento.type == pygame.QUIT:
                return False
            if not self._aplicar(self.topo.processar_evento(evento)):
                return False
            if not self.pilha:
                return True
        return True

    def _aplicar(self, transicao: Transicao | None) -> bool:
        """Aplica a transição pedida. False se o jogo deve terminar."""
        match transicao:
            case None:
                return True
            case Sair():
                self.pilha.clear()
                return False
            case Empilhar(cena):
                self.pilha.append(cena)
            case Trocar(cena):
                self._iniciar_transicao()
                self.pilha[-1] = cena
            case SubstituirPilha(cena):
                self._iniciar_transicao()
                self.pilha = [cena]
            case Desempilhar():
                self.pilha.pop()
        return True

    def _iniciar_transicao(self) -> None:
        """Guarda o quadro atual para ele esmaecer por cima da cena nova.

        Só trocas de contexto entram aqui. Empilhar e Desempilhar são
        sobreposições — a pausa abrindo com meio segundo de atraso seria pior
        do que ela abrir seca.
        """
        if config_tela.DURACAO_DA_TRANSICAO <= 0:
            return
        self._esmaecimento = Esmaecimento(
            self.superficie.copy(), config_tela.DURACAO_DA_TRANSICAO
        )

    def _desenhar_transicao(self, dt: float) -> None:
        """A transição é puramente visual: a cena nova já está viva embaixo e
        recebendo eventos, então nada fica travado durante o esmaecimento."""
        if self._esmaecimento is None:
            return
        self._esmaecimento.desenhar(self.superficie)
        self._esmaecimento.avancar(dt)
        if self._esmaecimento.terminou:
            self._esmaecimento = None

    def _desenhar(self) -> None:
        """Desenha da última cena opaca para cima.

        Uma cena transparente (um véu de fim de rodada, por exemplo) não apaga
        o que está embaixo — ela é desenhada por cima.
        """
        primeira = 0
        for i in range(len(self.pilha) - 1, -1, -1):
            if not self.pilha[i].transparente:
                primeira = i
                break

        for cena in self.pilha[primeira:]:
            cena.desenhar(self.superficie)
