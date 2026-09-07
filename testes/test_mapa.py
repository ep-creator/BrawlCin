"""Mapa: carga do .tmx, desenho achatado e colisão vinda das camadas."""

from __future__ import annotations

import pygame
import pytest

from brawl.mundo.mapa import CAMADA_AGUA, CAMADA_VEGETACAO, Mapa


@pytest.fixture(scope="module")
def mapa():
    return Mapa()


class TestCarga:
    def test_o_mundo_tem_o_tamanho_declarado_no_tmx(self, mapa):
        esperado = (
            mapa.tmx.width * mapa.tmx.tilewidth,
            mapa.tmx.height * mapa.tmx.tileheight,
        )
        assert mapa.tamanho == esperado
        assert mapa.rect.size == mapa.tamanho

    def test_o_mundo_e_16_por_9(self, mapa):
        """É o que faz a escala dar inteira em 1920x1080."""
        largura, altura = mapa.tamanho
        assert largura / altura == pytest.approx(16 / 9)

    def test_as_camadas_sao_achatadas_numa_imagem_so(self, mapa):
        """Uma superfície pronta na carga, em vez de ~1.900 blits por frame."""
        assert isinstance(mapa.imagem, pygame.Surface)
        assert mapa.imagem.get_size() == mapa.tamanho

    def test_o_desenho_cobre_o_mundo_inteiro(self, mapa):
        """A camada de chão preenche 100% das células; nada fica no vazio."""
        superficie = pygame.Surface(mapa.tamanho)
        superficie.fill((255, 0, 255))
        mapa.desenhar(superficie)
        cantos = [(0, 0), (mapa.rect.right - 1, 0),
                  (0, mapa.rect.bottom - 1), (mapa.rect.right - 1, mapa.rect.bottom - 1)]
        for ponto in cantos:
            assert superficie.get_at(ponto)[:3] != (255, 0, 255)

    def test_arquivo_inexistente_falha_alto(self):
        with pytest.raises(Exception):
            Mapa("nao_existe.tmx")


class TestColisaoVindaDasCamadas:
    """Desenho e colisão saem das mesmas células.

    Antes eram duas fontes: um PNG pintado à mão e retângulos desenhados à mão
    na camada de objetos — 38 deles, nenhum alinhado a grade, um com tamanho 0x0.
    """

    def test_agua_e_vegetacao_viram_areas(self, mapa):
        assert mapa.aguas
        assert mapa.arbustos

    def test_camada_ausente_vira_lista_vazia(self, mapa):
        """O mapa ainda não tem paredes, e isso não pode ser um erro:
        a borda do mundo é regra do jogador, não desenho do mapa."""
        assert mapa.paredes == []

    def test_as_areas_ficam_dentro_do_mundo(self, mapa):
        for area in (*mapa.aguas, *mapa.arbustos):
            assert mapa.rect.contains(area)

    def test_as_areas_estao_alinhadas_a_grade(self, mapa):
        """Vindo dos tiles, o desalinhamento do mapa antigo é impossível."""
        largura, altura = mapa.tmx.tilewidth, mapa.tmx.tileheight
        for area in (*mapa.aguas, *mapa.arbustos):
            assert area.x % largura == 0 and area.y % altura == 0
            assert area.width % largura == 0 and area.height % altura == 0

    def test_nenhuma_area_degenerada(self, mapa):
        """O mapa antigo tinha uma parede 0x0, um clique perdido no Tiled."""
        for area in (*mapa.aguas, *mapa.arbustos):
            assert area.width > 0 and area.height > 0


class TestFusaoDeTiles:
    """A fusão reduz a contagem sem mudar a geometria."""

    @staticmethod
    def _celulas_da_camada(mapa, nome):
        camada = next(c for c in mapa.tmx.layers if c.name == nome)
        return {(coluna, linha) for coluna, linha, _ in camada.tiles()}

    @pytest.mark.parametrize("nome,atributo", [
        (CAMADA_AGUA, "aguas"),
        (CAMADA_VEGETACAO, "arbustos"),
    ])
    def test_a_area_total_e_preservada(self, mapa, nome, atributo):
        celulas = self._celulas_da_camada(mapa, nome)
        area_dos_tiles = len(celulas) * mapa.tmx.tilewidth * mapa.tmx.tileheight
        area_fundida = sum(r.width * r.height for r in getattr(mapa, atributo))
        assert area_fundida == area_dos_tiles

    @pytest.mark.parametrize("atributo", ["aguas", "arbustos"])
    def test_os_retangulos_nao_se_sobrepoem(self, mapa, atributo):
        """Se houvesse sobreposição, a área bateria por acaso mas a fusão
        estaria errada."""
        areas = getattr(mapa, atributo)
        for i, area in enumerate(areas):
            assert area.collidelist(areas[i + 1:]) == -1

    @pytest.mark.parametrize("nome,atributo", [
        (CAMADA_AGUA, "aguas"),
        (CAMADA_VEGETACAO, "arbustos"),
    ])
    def test_reduz_bastante_a_contagem(self, mapa, nome, atributo):
        celulas = self._celulas_da_camada(mapa, nome)
        assert len(getattr(mapa, atributo)) < len(celulas) / 2

    @pytest.mark.parametrize("nome,atributo", [
        (CAMADA_AGUA, "aguas"),
        (CAMADA_VEGETACAO, "arbustos"),
    ])
    def test_cobre_exatamente_as_celulas_originais(self, mapa, nome, atributo):
        """A prova que importa: cada célula da camada, e só elas, está coberta."""
        largura, altura = mapa.tmx.tilewidth, mapa.tmx.tileheight
        areas = getattr(mapa, atributo)
        celulas = self._celulas_da_camada(mapa, nome)

        cobertas = set()
        for area in areas:
            for coluna in range(area.left // largura, area.right // largura):
                for linha in range(area.top // altura, area.bottom // altura):
                    cobertas.add((coluna, linha))

        assert cobertas == celulas


class TestVegetacaoEmFaixas:
    """A vegetação sai do fundo achatado para poder ser desenhada por profundidade."""

    def test_ha_uma_faixa_por_linha_com_vegetacao(self, mapa):
        camada = next(c for c in mapa.tmx.layers if c.name == CAMADA_VEGETACAO)
        linhas = {linha for _, linha, _ in camada.tiles()}
        assert len(mapa.faixas_de_vegetacao) == len(linhas)

    def test_a_profundidade_e_a_base_da_celula(self, mapa):
        altura = mapa.tmx.tileheight
        for faixa in mapa.faixas_de_vegetacao:
            assert faixa.profundidade % altura == 0

    def test_a_vegetacao_nao_esta_no_fundo(self, mapa):
        """Se estivesse, nada poderia passar na frente dela.

        Comparar contra uma cor fixa não serviria: bastaria trocar a arte para o
        teste passar sem testar nada. Aqui o fundo é comparado consigo mesmo
        acrescido das faixas — se a vegetação já estivesse achatada no fundo, as
        duas imagens seriam iguais.
        """
        so_fundo = pygame.Surface(mapa.tamanho)
        mapa.desenhar(so_fundo)

        com_vegetacao = so_fundo.copy()
        for faixa in mapa.faixas_de_vegetacao:
            faixa.desenhar(com_vegetacao)

        diferentes = sum(
            1
            for area in mapa.arbustos
            for x in range(area.left, area.right, 4)
            for y in range(area.top, area.bottom, 4)
            if so_fundo.get_at((x, y)) != com_vegetacao.get_at((x, y))
        )
        assert diferentes > 0

    def test_arte_mais_alta_que_o_tile_e_ancorada_na_base(self, mapa):
        """Uma moita de 60 px numa grade de 20 px cresce para cima.

        É o que permite trocar a arte por vegetação alta sem mexer no código.
        """
        altura = mapa.tmx.tileheight
        for faixa in mapa.faixas_de_vegetacao:
            topo = faixa.posicao[1]
            assert topo + faixa.imagem.get_height() == faixa.profundidade
            assert faixa.imagem.get_height() >= altura
