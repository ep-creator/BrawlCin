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


class FaixaDeVegetacao:
    """Uma linha de tiles de vegetação, pronta para ser desenhada por profundidade.

    `ordem_no_empate = 1` faz a vegetação ganhar do jogador quando as duas bases
    coincidem — é o caso de quem está pisando dentro dela, e o esperado é que ela
    passe na frente.
    """

    ordem_no_empate = 1

    def __init__(self, imagem: pygame.Surface, posicao: tuple[int, int], base: int):
        self.imagem = imagem
        self.posicao = posicao
        #: A base da célula no mapa, e não do desenho: arte alta continua
        #: pertencendo à linha em que foi pintada.
        self.profundidade = base

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.imagem, self.posicao)


class Mapa:
    def __init__(self, arquivo_tmx: str = "mapa.tmx"):
        self.tmx = load_pygame(str(recursos.caminho(arquivo_tmx)))

        self.tamanho = (
            self.tmx.width * self.tmx.tilewidth,
            self.tmx.height * self.tmx.tileheight,
        )
        self.rect = pygame.Rect((0, 0), self.tamanho)

        # O chão e a água ficam achatados no fundo. A vegetação não: ela
        # precisa ser desenhada intercalada com os personagens, por
        # profundidade, para poder passar na frente de quem está atrás dela.
        self.imagem = self._achatar_camadas(exceto={CAMADA_VEGETACAO})
        self.faixas_de_vegetacao = self._faixas_da_camada(CAMADA_VEGETACAO)

        # Paredes e água bloqueiam; vegetação só esconde. Uma camada ausente
        # vira lista vazia: o mapa atual ainda não tem paredes, e a borda do
        # mundo é regra do jogador, não desenho do mapa.
        self.paredes = self._areas_da_camada(CAMADA_PAREDE)
        self.aguas = self._areas_da_camada(CAMADA_AGUA)
        self.arbustos = self._areas_da_camada(CAMADA_VEGETACAO)

    # ---------------------------------------------------------------- desenho

    def _camadas_de_tiles(self) -> list[TiledTileLayer]:
        camadas = [c for c in self.tmx.visible_layers if isinstance(c, TiledTileLayer)]
        if not camadas:
            raise ValueError(
                f"O mapa {self.tmx.filename!r} não tem nenhuma camada de tiles visível."
            )
        return camadas

    def _achatar_camadas(self, exceto: set[str] = frozenset()) -> pygame.Surface:
        """Desenha as camadas de fundo numa superfície só, na carga.

        São ~1.500 blits uma vez, em vez de 1.500 por frame.
        """
        superficie = pygame.Surface(self.tamanho).convert()
        superficie.fill(self._cor_de_fundo())

        largura, altura = self.tmx.tilewidth, self.tmx.tileheight
        for camada in self._camadas_de_tiles():
            if camada.name in exceto:
                continue
            for coluna, linha, imagem in camada.tiles():
                superficie.blit(imagem, (coluna * largura, linha * altura))

        return superficie

    def _faixas_da_camada(self, nome: str) -> list[FaixaDeVegetacao]:
        """Uma faixa por linha de tiles, pré-renderizada.

        Tiles da mesma linha compartilham a mesma base, logo a mesma
        profundidade — não há como um ficar na frente do outro. Agrupá-los troca
        centenas de blits por frame por algumas dezenas, sem mudar a ordem.
        """
        camada = self._camada_chamada(nome)
        if camada is None:
            return []

        largura, altura = self.tmx.tilewidth, self.tmx.tileheight

        por_linha: dict[int, list[tuple[int, pygame.Surface]]] = {}
        for coluna, linha, imagem in camada.tiles():
            por_linha.setdefault(linha, []).append((coluna, imagem))

        faixas = []
        for linha, tiles in sorted(por_linha.items()):
            colunas = [coluna for coluna, _ in tiles]
            x_inicial = min(colunas) * largura

            # A arte pode ser MAIS ALTA que o tile: uma moita de 60 px numa
            # grade de 20 px fica ancorada na base da célula e cresce para
            # cima, cobrindo quem está atrás. É assim que a vegetação esconde
            # de verdade — com arte da altura do tile ela mal encosta no sprite.
            altura_faixa = max(imagem.get_height() for _, imagem in tiles)
            base = linha * altura + altura

            faixa = pygame.Surface(
                ((max(colunas) + 1) * largura - x_inicial, altura_faixa), pygame.SRCALPHA
            )
            for coluna, imagem in tiles:
                faixa.blit(
                    imagem,
                    (coluna * largura - x_inicial, altura_faixa - imagem.get_height()),
                )

            faixas.append(FaixaDeVegetacao(
                faixa.convert_alpha(), (x_inicial, base - altura_faixa), base,
            ))
        return faixas

    def _cor_de_fundo(self) -> pygame.Color:
        declarada = getattr(self.tmx, "background_color", None)
        return pygame.Color(declarada) if declarada else pygame.Color(0, 0, 0)

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.imagem, (0, 0))

    # --------------------------------------------------------------- colisão

    def _camada_chamada(self, nome: str) -> TiledTileLayer | None:
        return next(
            (c for c in self.tmx.layers
             if isinstance(c, TiledTileLayer) and c.name == nome),
            None,
        )

    def _areas_da_camada(self, nome: str) -> list[pygame.Rect]:
        """Retângulos de colisão da camada `nome`, ou [] se ela não existir."""
        camada = self._camada_chamada(nome)
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
