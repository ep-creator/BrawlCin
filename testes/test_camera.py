"""Câmera: a superfície de mundo e a escala até a janela."""

from __future__ import annotations

import pygame
import pytest

from brawl.render.camera import Camera

JANELA = (1920, 1080)


class TestEscala:
    """O mapa era desenhado em (0,0) de uma janela 1920x1080, sem escala.

    O mundo jogável ocupava o canto superior esquerdo da tela.
    """

    @pytest.mark.parametrize("mundo,escala", [
        ((960, 540), 2.0),
        ((640, 360), 3.0),
        ((480, 270), 4.0),
        ((384, 216), 5.0),
    ])
    def test_mundos_16_por_9_dao_escala_inteira(self, mundo, escala):
        """Escala inteira é o que mantém a arte em pixel nítida."""
        assert Camera(mundo).escala_para(JANELA) == escala

    def test_mapa_16_por_9_preenche_a_tela_sem_barras(self):
        assert Camera((960, 540)).area_na_tela(JANELA).size == JANELA

    def test_mapa_fora_do_16_por_9_ganha_barras(self):
        """O mapa atual, 791x500, cabe pela altura e sobra nas laterais."""
        area = Camera((791, 500)).area_na_tela(JANELA)
        assert area.height == JANELA[1]
        assert area.width < JANELA[0]

    def test_nunca_estoura_a_janela(self):
        for mundo in [(791, 500), (960, 540), (2000, 100), (100, 2000)]:
            area = Camera(mundo).area_na_tela(JANELA)
            assert area.width <= JANELA[0] and area.height <= JANELA[1]

    def test_preserva_a_proporcao(self):
        mundo = (791, 500)
        area = Camera(mundo).area_na_tela(JANELA)
        assert area.width / area.height == pytest.approx(mundo[0] / mundo[1], abs=0.01)

    def test_fica_centralizado(self):
        area = Camera((791, 500)).area_na_tela(JANELA)
        assert area.center == (JANELA[0] // 2, JANELA[1] // 2)


class TestApresentacao:
    def test_pinta_as_barras_e_desenha_o_mundo(self):
        camera = Camera((791, 500), cor_das_barras=(12, 12, 14))
        camera.mundo.fill((200, 30, 30))
        tela = pygame.Surface(JANELA)

        area = camera.apresentar(tela)

        assert tela.get_at((5, JANELA[1] // 2))[:3] == (12, 12, 14)   # barra
        assert tela.get_at(area.center)[:3] == (200, 30, 30)          # mundo

    def test_sem_barras_quando_a_escala_e_exata(self):
        camera = Camera((960, 540))
        camera.mundo.fill((200, 30, 30))
        tela = pygame.Surface(JANELA)

        camera.apresentar(tela)

        for ponto in [(0, 0), (JANELA[0] - 1, 0), (0, JANELA[1] - 1), (960, 540)]:
            assert tela.get_at(ponto)[:3] == (200, 30, 30)

    def test_a_superficie_de_mundo_tem_o_tamanho_pedido(self):
        assert Camera((791, 500)).tamanho_do_mundo == (791, 500)
