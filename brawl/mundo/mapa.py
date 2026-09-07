"""O mapa: imagem de fundo e as áreas de colisão exportadas do Tiled."""

from __future__ import annotations

import pygame
from pytmx.util_pygame import load_pygame

from .. import recursos


class Mapa:
    """Carrega um .tmx e expõe o fundo já desenhado e as áreas de regra.

    O fundo vem da própria camada de imagem do .tmx, e não de um caminho
    repetido no código: o arquivo do Tiled já declara qual imagem ele usa, e
    duas fontes para a mesma informação é como elas divergem.
    """

    NOME_CAMADA_FUNDO = "mapa"

    def __init__(self, arquivo_tmx: str = "mapa_brawl.tmx"):
        self.tmx = load_pygame(str(recursos.caminho(arquivo_tmx)))

        # Áreas de regra. Paredes e água bloqueiam movimento; arbustos só
        # escondem quem estiver dentro.
        self.paredes: list[pygame.Rect] = []
        self.aguas: list[pygame.Rect] = []
        self.arbustos: list[pygame.Rect] = []

        self.imagem = self._carregar_fundo()
        self._carregar_areas()

    def _carregar_fundo(self) -> pygame.Surface:
        for camada in self.tmx.layers:
            if camada.name == self.NOME_CAMADA_FUNDO:
                imagem = getattr(camada, "image", None)
                if isinstance(imagem, pygame.Surface):
                    return imagem.convert()
        raise ValueError(
            f"O .tmx não tem uma camada de imagem chamada {self.NOME_CAMADA_FUNDO!r}."
        )

    def _carregar_areas(self) -> None:
        destino_por_camada = {
            "wall": self.paredes,
            "water": self.aguas,
            "bush": self.arbustos,
        }
        for camada in self.tmx.layers:
            destino = destino_por_camada.get(camada.name)
            if destino is None:
                continue
            for obj in camada:
                destino.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

    @property
    def tamanho(self) -> tuple[int, int]:
        """Tamanho do mundo em pixels — o tamanho da imagem de fundo."""
        return self.imagem.get_size()

    @property
    def rect(self) -> pygame.Rect:
        return self.imagem.get_rect()

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.imagem, (0, 0))
