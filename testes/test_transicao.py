"""Esmaecimento entre cenas."""

from __future__ import annotations

import pygame
import pytest

from brawl.cenas.base import Desempilhar, Empilhar, SubstituirPilha, Trocar
from brawl.config import tela as config_tela
from brawl.render.transicao import Esmaecimento

from .apoio import CenaBoba, avancar_frame


class CenaColorida(CenaBoba):
    def __init__(self, cor):
        super().__init__(str(cor))
        self.cor = cor

    def desenhar(self, superficie):
        super().desenhar(superficie)
        superficie.fill(self.cor)


class TestEsmaecimento:
    def test_comeca_opaco_e_termina_transparente(self):
        quadro = pygame.Surface((10, 10))
        fade = Esmaecimento(quadro, 1.0)
        assert fade.opacidade == 1.0
        fade.avancar(0.5)
        assert fade.opacidade == pytest.approx(0.5)
        fade.avancar(0.5)
        assert fade.opacidade == 0.0
        assert fade.terminou

    def test_nao_passa_de_zero(self):
        fade = Esmaecimento(pygame.Surface((10, 10)), 0.2)
        fade.avancar(10.0)
        assert fade.opacidade == 0.0

    def test_duracao_zero_ja_nasce_terminada(self):
        assert Esmaecimento(pygame.Surface((10, 10)), 0.0).terminou


class TestQuandoOAppAnima:
    """Trocas de contexto esmaecem; sobreposições entram secas.

    A pausa abrindo com meio segundo de atraso seria pior do que ela abrir seca.
    """

    def test_trocar_inicia(self, app):
        app.pilha = [CenaBoba("a")]
        app._aplicar(Trocar(CenaBoba("b")))
        assert app._esmaecimento is not None

    def test_substituir_pilha_inicia(self, app):
        app.pilha = [CenaBoba("a"), CenaBoba("b")]
        app._aplicar(SubstituirPilha(CenaBoba("c")))
        assert app._esmaecimento is not None

    def test_empilhar_nao_inicia(self, app):
        app.pilha = [CenaBoba("a")]
        app._esmaecimento = None
        app._aplicar(Empilhar(CenaBoba("veu")))
        assert app._esmaecimento is None

    def test_desempilhar_nao_inicia(self, app):
        app.pilha = [CenaBoba("a"), CenaBoba("veu")]
        app._esmaecimento = None
        app._aplicar(Desempilhar())
        assert app._esmaecimento is None


class TestNoLaco:
    def test_termina_sozinho_depois_da_duracao(self, app):
        app.pilha = [CenaBoba("a")]
        app._aplicar(Trocar(CenaBoba("b")))
        assert app._esmaecimento is not None

        passos = int(config_tela.DURACAO_DA_TRANSICAO / (1 / 30)) + 2
        for _ in range(passos):
            avancar_frame(app)
        assert app._esmaecimento is None

    def test_a_cena_nova_continua_viva_durante_o_esmaecimento(self, app):
        """A transição é só visual: nada fica travado esperando ela acabar."""
        nova = CenaBoba("nova")
        app.pilha = [CenaBoba("velha")]
        app._aplicar(Trocar(nova))
        avancar_frame(app)
        assert app._esmaecimento is not None
        assert nova.desenhos > 0

    def test_o_quadro_antigo_aparece_por_cima_do_novo(self, app):
        """A prova de que há mistura: no primeiro frame o que se vê ainda é a
        cena antiga, mesmo com a nova já desenhada embaixo."""
        antiga, nova = CenaColorida((255, 0, 0)), CenaColorida((0, 0, 255))
        app.pilha = [antiga]
        app._desenhar()                      # deixa o vermelho na tela
        app._aplicar(Trocar(nova))
        avancar_frame(app)

        meio = (app.superficie.get_width() // 2, app.superficie.get_height() // 2)
        cor = app.superficie.get_at(meio)[:3]
        assert cor[0] > cor[2], f"esperava predominar o vermelho antigo, veio {cor}"

    def test_no_fim_so_resta_a_cena_nova(self, app):
        antiga, nova = CenaColorida((255, 0, 0)), CenaColorida((0, 0, 255))
        app.pilha = [antiga]
        app._desenhar()
        app._aplicar(Trocar(nova))
        for _ in range(int(config_tela.DURACAO_DA_TRANSICAO * 30) + 3):
            avancar_frame(app)

        meio = (app.superficie.get_width() // 2, app.superficie.get_height() // 2)
        assert app.superficie.get_at(meio)[:3] == (0, 0, 255)
