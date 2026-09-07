"""Véu com título e instruções, desenhado por cima da cena de baixo.

É o fim de rodada e o fim de campeonato. Antes, isso eram cinquenta linhas
dentro do `draw()` da partida, com dois blocos quase idênticos. Como cena
transparente, a partida continua visível e congelada atrás — ela nem é
atualizada, porque o App só atualiza o topo da pilha.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from .. import recursos
from .base import Cena, Transicao


class CenaSobreposicao(Cena):
    transparente = True

    def __init__(
        self,
        titulo: str,
        cor_titulo: tuple[int, int, int],
        cor_veu: tuple[int, int, int],
        opacidade: int,
        linhas: list[str],
        acoes: dict[int, Callable[[], Transicao | None]],
        tamanho_titulo: int = 42,
        ao_cancelar: Callable[[], Transicao | None] | None = None,
    ):
        self.titulo = titulo
        self.cor_titulo = cor_titulo
        self.cor_veu = cor_veu
        self.opacidade = opacidade
        self.linhas = linhas
        self.acoes = acoes
        self.tamanho_titulo = tamanho_titulo
        self.ao_cancelar = ao_cancelar
        self._veu: pygame.Surface | None = None

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        if evento.type != pygame.KEYDOWN:
            return None
        if evento.key == pygame.K_ESCAPE and self.ao_cancelar is not None:
            return self.ao_cancelar()
        if evento.key == pygame.K_ESCAPE:
            return super().processar_evento(evento)
        if evento.key in self.acoes:
            return self.acoes[evento.key]()
        return None

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self._obter_veu(superficie.get_size()), (0, 0))

        largura, altura = superficie.get_size()

        titulo = recursos.fonte(self.tamanho_titulo, negrito=True).render(
            self.titulo, True, self.cor_titulo
        )
        y = (altura - titulo.get_height()) // 2 - 20
        superficie.blit(titulo, ((largura - titulo.get_width()) // 2, y))

        fonte = recursos.fonte(22)
        for i, linha in enumerate(self.linhas):
            texto = fonte.render(linha, True, (255, 255, 255))
            superficie.blit(texto, ((largura - texto.get_width()) // 2, y + 50 + i * 25))

    def _obter_veu(self, tamanho: tuple[int, int]) -> pygame.Surface:
        """O véu é montado uma vez, não a cada frame como antes."""
        if self._veu is None or self._veu.get_size() != tamanho:
            self._veu = pygame.Surface(tamanho)
            self._veu.set_alpha(self.opacidade)
            self._veu.fill(self.cor_veu)
        return self._veu
