"""Entrada: normalização de direção e tradução de tecla para Comando."""

from __future__ import annotations

import math

import pygame
import pytest

from brawl.entrada import (
    PARADO,
    TECLADO_P1,
    TECLADO_P2,
    Comando,
    ControleTeclado,
    normalizar,
    pediu_para_sair,
)

from .apoio import Teclas

RAIZ_DE_DOIS_SOBRE_2 = math.sqrt(2) / 2


class TestNormalizar:
    """A normalização é o conserto do bug da velocidade diagonal.

    Antes, a velocidade era aplicada inteira no eixo X e de novo no eixo Y, e
    andar na diagonal cobria v*raiz(2) por frame — 41% a mais que andar reto.
    """

    @pytest.mark.parametrize("dx,dy", [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)])
    def test_vetor_curto_passa_intacto(self, dx, dy):
        assert normalizar(dx, dy) == (dx, dy)

    @pytest.mark.parametrize("dx,dy", [(1, 1), (1, -1), (-1, 1), (-1, -1)])
    def test_diagonal_encolhe_para_comprimento_um(self, dx, dy):
        nx, ny = normalizar(dx, dy)
        assert math.isclose(math.hypot(nx, ny), 1.0)
        assert math.isclose(abs(nx), RAIZ_DE_DOIS_SOBRE_2)
        assert math.isclose(abs(ny), RAIZ_DE_DOIS_SOBRE_2)

    @pytest.mark.parametrize("dx,dy", [(1, 1), (3, 4), (-5, 12)])
    def test_nunca_devolve_vetor_maior_que_um(self, dx, dy):
        assert math.hypot(*normalizar(dx, dy)) <= 1.0 + 1e-9

    def test_preserva_a_direcao(self):
        nx, ny = normalizar(3, 4)
        assert math.isclose(nx / ny, 3 / 4)


class TestComando:
    def test_parado_e_o_comando_neutro(self):
        assert PARADO == Comando()
        assert PARADO.esta_parado

    def test_comando_com_direcao_nao_esta_parado(self):
        assert not Comando(dx=1.0).esta_parado

    def test_e_imutavel(self):
        """Comando é congelado para não haver dúvida sobre quem alterou o quê."""
        with pytest.raises(Exception):
            Comando().dx = 1.0


class TestControleTeclado:
    def test_traduz_cada_direcao(self):
        assert TECLADO_P1.ler(Teclas(pygame.K_d)) == Comando(1.0, 0.0, False)
        assert TECLADO_P1.ler(Teclas(pygame.K_a)) == Comando(-1.0, 0.0, False)
        assert TECLADO_P1.ler(Teclas(pygame.K_w)) == Comando(0.0, -1.0, False)
        assert TECLADO_P1.ler(Teclas(pygame.K_s)) == Comando(0.0, 1.0, False)

    def test_sem_tecla_fica_parado(self):
        assert TECLADO_P1.ler(Teclas()).esta_parado

    def test_diagonal_sai_normalizada_do_controle(self):
        comando = TECLADO_P1.ler(Teclas(pygame.K_w, pygame.K_d))
        assert math.isclose(math.hypot(comando.dx, comando.dy), 1.0)

    @pytest.mark.parametrize("opostas", [
        (pygame.K_a, pygame.K_d),
        (pygame.K_w, pygame.K_s),
    ])
    def test_teclas_opostas_se_cancelam(self, opostas):
        """Antes o `elif` fazia a primeira direção sempre ganhar."""
        assert TECLADO_P1.ler(Teclas(*opostas)).esta_parado

    def test_tecla_de_tiro_nao_vira_movimento_nem_disparo_sozinha(self):
        """O disparo é por toque (KEYDOWN), não por tecla segurada.

        Se `atirar` saísse de get_pressed(), segurar a tecla viraria rajada.
        """
        comando = TECLADO_P1.ler(Teclas(TECLADO_P1.atirar))
        assert comando.esta_parado
        assert comando.atirar is False

    def test_disparo_chega_por_parametro(self):
        assert TECLADO_P1.ler(Teclas(), atirar=True).atirar is True

    def test_os_dois_jogadores_nao_compartilham_tecla(self):
        teclas_p1 = {TECLADO_P1.esquerda, TECLADO_P1.direita, TECLADO_P1.cima,
                     TECLADO_P1.baixo, TECLADO_P1.atirar}
        teclas_p2 = {TECLADO_P2.esquerda, TECLADO_P2.direita, TECLADO_P2.cima,
                     TECLADO_P2.baixo, TECLADO_P2.atirar}
        assert teclas_p1.isdisjoint(teclas_p2)

    def test_controle_e_remapeavel(self):
        """A tecla de tiro vem do controle; não está fixa no código da partida."""
        controle = ControleTeclado(
            esquerda=pygame.K_j, direita=pygame.K_l,
            cima=pygame.K_i, baixo=pygame.K_k, atirar=pygame.K_f,
        )
        assert controle.ler(Teclas(pygame.K_l)) == Comando(1.0, 0.0, False)
        assert controle.atirar == pygame.K_f


class TestPediuParaSair:
    def test_fechar_janela(self):
        assert pediu_para_sair(pygame.event.Event(pygame.QUIT))

    def test_esc(self):
        assert pediu_para_sair(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

    def test_outra_tecla_nao(self):
        assert not pediu_para_sair(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
