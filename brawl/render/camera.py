"""A superfície de mundo e a escala até a janela.

O jogo desenhava o mapa (791x500) em (0, 0) de uma janela 1920x1080, sem escala,
e prendia o jogador ao retângulo da TELA. O mundo jogável ocupava o canto
superior esquerdo e dava para andar pelo cinza fora do mapa. Os spawns
(-1, 205) e (760, 205) pareciam absurdos porque eram coordenadas de mundo
interpretadas como coordenadas de tela.

Aqui o mundo é desenhado numa Surface do tamanho nativo do mapa e escalado UMA
vez por frame para a janela. Nenhuma coordenada de gameplay volta a conhecer
1920x1080 — trocar a resolução da janela, ou o mapa, deixa de ser assunto do
código de jogo.

O HUD não passa por aqui: ele é desenhado depois, direto na tela, em resolução
cheia, para o texto não sair escalado e borrado.
"""

from __future__ import annotations

import pygame


class Camera:
    """Uma superfície de mundo e a projeção dela na janela.

    A escala preserva a proporção e é a mesma nos dois eixos: o mundo é
    ampliado até caber inteiro na janela e centralizado, com barras onde sobra.
    Quando o mundo é uma fração exata da janela (960x540 em 1920x1080, por
    exemplo), a escala dá inteira e não há barra nenhuma.
    """

    def __init__(self, tamanho_do_mundo: tuple[int, int],
                 cor_das_barras: tuple[int, int, int] = (12, 12, 14)):
        self.mundo = pygame.Surface(tamanho_do_mundo).convert()
        self.cor_das_barras = cor_das_barras
        self._destino: pygame.Rect | None = None
        self._destino_para: tuple[int, int] | None = None
        self._escalado: pygame.Surface | None = None

    @property
    def tamanho_do_mundo(self) -> tuple[int, int]:
        return self.mundo.get_size()

    def escala_para(self, tamanho_da_tela: tuple[int, int]) -> float:
        largura_mundo, altura_mundo = self.tamanho_do_mundo
        largura_tela, altura_tela = tamanho_da_tela
        return min(largura_tela / largura_mundo, altura_tela / altura_mundo)

    def area_na_tela(self, tamanho_da_tela: tuple[int, int]) -> pygame.Rect:
        """Onde o mundo aparece na janela, já centralizado."""
        if self._destino_para != tamanho_da_tela:
            escala = self.escala_para(tamanho_da_tela)
            largura_mundo, altura_mundo = self.tamanho_do_mundo
            self._destino = pygame.Rect(
                (0, 0), (int(largura_mundo * escala), int(altura_mundo * escala))
            )
            self._destino.center = (tamanho_da_tela[0] // 2, tamanho_da_tela[1] // 2)
            self._destino_para = tamanho_da_tela
        return self._destino

    def apresentar(self, tela: pygame.Surface) -> pygame.Rect:
        """Escala a superfície de mundo para a janela. Devolve a área ocupada."""
        destino = self.area_na_tela(tela.get_size())

        if destino.size != tela.get_size():
            tela.fill(self.cor_das_barras)

        if destino.size == self.tamanho_do_mundo:
            # Escala 1:1 — nem vale chamar o transform.
            tela.blit(self.mundo, destino)
            return destino

        # scale (vizinho mais próximo) e não smoothscale: para arte em pixel,
        # borrar é pior do que ter pixel de tamanho irregular quando a escala
        # não dá inteira.
        if self._escalado is None or self._escalado.get_size() != destino.size:
            self._escalado = pygame.Surface(destino.size).convert()
        pygame.transform.scale(self.mundo, destino.size, self._escalado)
        tela.blit(self._escalado, destino)
        return destino
