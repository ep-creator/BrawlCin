"""O mapa: desenho e áreas de colisão, ambos vindos do mesmo .tmx.

Antes havia duas fontes de verdade: um PNG pintado à mão para o desenho e
retângulos desenhados à mão na camada de objetos para a colisão. Mover uma
parede no desenho exigia lembrar de mover o retângulo junto, e era assim que
elas divergiam — o mapa antigo tinha 38 retângulos, nenhum alinhado a grade, e
um deles com tamanho 0x0.

Agora as duas coisas saem das mesmas células. Uma camada de tiles chamada
"agua" é ao mesmo tempo o que se vê e o que bloqueia. Mover a água no Tiled
move a colisão junto, porque são a mesma informação.
"""

from __future__ import annotations

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from .. import recursos

# Nome da camada no Tiled -> papel no jogo.
CAMADA_PAREDE = "parede"
CAMADA_AGUA = "agua"
CAMADA_VEGETACAO = "grama"


class Mapa:
    def __init__(self, arquivo_tmx: str = "mapa.tmx"):
        self.tmx = load_pygame(str(recursos.caminho(arquivo_tmx)))

        self.tamanho = (
            self.tmx.width * self.tmx.tilewidth,
            self.tmx.height * self.tmx.tileheight,
        )
        self.rect = pygame.Rect((0, 0), self.tamanho)

        self.imagem = self._achatar_camadas()

        # Paredes e água bloqueiam; vegetação só esconde. Uma camada ausente
        # vira lista vazia: o mapa atual ainda não tem paredes, e a borda do
        # mundo é regra do jogador, não desenho do mapa.
        self.paredes = self._areas_da_camada(CAMADA_PAREDE)
        self.aguas = self._areas_da_camada(CAMADA_AGUA)
        self.arbustos = self._areas_da_camada(CAMADA_VEGETACAO)

    # ---------------------------------------------------------------- desenho

    def _achatar_camadas(self) -> pygame.Surface:
        """Desenha todas as camadas de tiles numa superfície só, na carga.

        São ~1.900 blits uma vez, em vez de 1.900 por frame.
        """
        superficie = pygame.Surface(self.tamanho).convert()
        superficie.fill(self._cor_de_fundo())

        camadas = [c for c in self.tmx.visible_layers if isinstance(c, TiledTileLayer)]
        if not camadas:
            raise ValueError(
                f"O mapa {self.tmx.filename!r} não tem nenhuma camada de tiles visível."
            )

        largura, altura = self.tmx.tilewidth, self.tmx.tileheight
        for camada in camadas:
            for coluna, linha, imagem in camada.tiles():
                superficie.blit(imagem, (coluna * largura, linha * altura))

        return superficie

    def _cor_de_fundo(self) -> pygame.Color:
        declarada = getattr(self.tmx, "background_color", None)
        return pygame.Color(declarada) if declarada else pygame.Color(0, 0, 0)

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.imagem, (0, 0))

    # --------------------------------------------------------------- colisão

    def _areas_da_camada(self, nome: str) -> list[pygame.Rect]:
        """Retângulos de colisão da camada `nome`, ou [] se ela não existir."""
        camada = next(
            (c for c in self.tmx.layers
             if isinstance(c, TiledTileLayer) and c.name == nome),
            None,
        )
        if camada is None:
            return []

        ocupadas = {(coluna, linha) for coluna, linha, _ in camada.tiles()}
        return self._juntar_em_retangulos(ocupadas)

    def _juntar_em_retangulos(self, ocupadas: set[tuple[int, int]]) -> list[pygame.Rect]:
        """Funde células vizinhas em retângulos maiores.

        Um retângulo por tile daria centenas de itens para cada `collidelist`
        percorrer a cada frame. A varredura gulosa (estica para a direita, depois
        para baixo enquanto a faixa inteira couber) reduz a ordem de grandeza sem
        mudar a geometria da colisão.
        """
        largura_tile, altura_tile = self.tmx.tilewidth, self.tmx.tileheight
        restantes = set(ocupadas)
        retangulos: list[pygame.Rect] = []

        for celula in sorted(ocupadas, key=lambda c: (c[1], c[0])):
            if celula not in restantes:
                continue
            coluna, linha = celula

            largura = 1
            while (coluna + largura, linha) in restantes:
                largura += 1

            altura = 1
            while all((coluna + i, linha + altura) in restantes for i in range(largura)):
                altura += 1

            for j in range(altura):
                for i in range(largura):
                    restantes.discard((coluna + i, linha + j))

            retangulos.append(pygame.Rect(
                coluna * largura_tile, linha * altura_tile,
                largura * largura_tile, altura * altura_tile,
            ))

        return retangulos
