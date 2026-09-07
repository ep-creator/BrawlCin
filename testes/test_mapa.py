"""Mapa: carga do .tmx e as áreas de regra."""

from __future__ import annotations

import pygame
import pytest

from brawl.mundo.mapa import Mapa


@pytest.fixture(scope="module")
def mapa():
    return Mapa()


class TestCarga:
    def test_o_fundo_vem_do_proprio_tmx(self, mapa):
        """O caminho da imagem não é repetido no código: o .tmx já o declara."""
        assert isinstance(mapa.imagem, pygame.Surface)

    def test_expoe_o_tamanho_do_mundo(self, mapa):
        assert mapa.tamanho == mapa.imagem.get_size()
        assert mapa.rect.size == mapa.tamanho

    def test_carrega_as_tres_areas_de_regra(self, mapa):
        assert mapa.paredes and mapa.aguas and mapa.arbustos
        for area in (*mapa.paredes, *mapa.aguas, *mapa.arbustos):
            assert isinstance(area, pygame.Rect)

    def test_desenha_a_partir_da_origem(self, mapa):
        superficie = pygame.Surface(mapa.tamanho)
        superficie.fill((0, 0, 0))
        mapa.desenhar(superficie)
        assert pygame.transform.average_color(superficie)[:3] != (0, 0, 0)

    def test_arquivo_inexistente_falha_alto(self):
        with pytest.raises(Exception):
            Mapa("nao_existe.tmx")
