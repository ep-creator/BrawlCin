"""Partida: munição, disparo, itens e regra de campeonato."""

from __future__ import annotations

import random
from unittest import mock

import pygame
import pytest

from brawl.cenas.partida import COR_BALA_P1, CenaPartida
from brawl.cenas.sobreposicao import CenaSobreposicao
from brawl.config import gameplay as regras

from .apoio import Teclas, avancar_frame, teclar


@pytest.fixture
def partida():
    """Os itens nascem em posição sorteada; a semente fixa deixa os testes
    reproduzíveis em vez de falharem uma vez a cada tantas execuções."""
    random.seed(20260908)
    return CenaPartida("shelly", "colt")


class TestMontagem:
    def test_comeca_com_a_municao_e_a_vida_cheias(self, partida):
        for jogador in (partida.jogador1, partida.jogador2):
            assert jogador.balas == regras.BALAS_MAXIMAS
            assert jogador.vida == jogador.personagem.vida_maxima

    def test_placar_zerado(self, partida):
        assert partida.pontos == {1: 0, 2: 0}

    def test_espalha_um_item_de_cada_tipo(self, partida):
        assert sorted(i.tipo for i in partida.itens) == sorted(regras.ITEM_ARQUIVOS)


class TestItens:
    def test_nascem_dentro_do_mapa(self, partida):
        """Antes o sorteio ia até 1920x1080 e ~81% caía fora da arena.

        Fora do mapa não há paredes, então o teste de colisão aprovava a posição
        e o item nascia inalcançável.
        """
        for _ in range(30):
            partida._espalhar_itens()
            for item in partida.itens:
                assert partida.mapa.rect.contains(item.rect)

    def test_nao_nascem_sobre_obstaculo(self, partida):
        for _ in range(30):
            partida._espalhar_itens()
            for item in partida.itens:
                assert item.rect.collidelist(partida.mapa.paredes) == -1
                assert item.rect.collidelist(partida.mapa.aguas) == -1

    @pytest.mark.parametrize("tipo,atributo,teto", [
        ("vida", "vida", regras.VIDA_TETO_COM_ITENS),
        ("dano", "bonus_dano", regras.BONUS_DANO_MAXIMO),
        ("velocidade", "bonus_velocidade", regras.BONUS_VELOCIDADE_MAXIMO),
    ])
    def test_coleta_respeita_o_teto(self, partida, tipo, atributo, teto):
        item = mock.Mock(tipo=tipo)
        for _ in range(30):
            partida._coletar(partida.jogador1, item)
        assert getattr(partida.jogador1, atributo) == teto


class TestDisparo:
    def test_um_toque_gera_uma_bala(self, app, partida):
        app.pilha = [partida]
        teclar(partida.controles[1].atirar)
        avancar_frame(app)
        assert len(partida.balas) == 1
        assert partida.jogador1.balas == regras.BALAS_MAXIMAS - 1

    def test_segurar_a_tecla_nao_vira_rajada(self, app, partida):
        """A armadilha do refactor de entrada: ler o tiro de get_pressed()."""
        app.pilha = [partida]
        teclar(partida.controles[1].atirar)
        avancar_frame(app)
        with mock.patch("pygame.key.get_pressed",
                        lambda: Teclas(partida.controles[1].atirar)):
            for _ in range(20):
                avancar_frame(app)
        assert partida.jogador1.balas == regras.BALAS_MAXIMAS - 1

    def test_sem_municao_nao_dispara(self, partida):
        partida.jogador1.balas = 0
        partida._tentar_atirar(partida.jogador1, partida.jogador2, COR_BALA_P1)
        assert partida.balas == []

    def test_zerar_a_municao_inicia_a_recarga(self, partida):
        for _ in range(regras.BALAS_MAXIMAS):
            partida._tentar_atirar(partida.jogador1, partida.jogador2, COR_BALA_P1)
        assert partida.jogador1.balas == 0
        assert partida.inicio_recarga[1] > 0

    def test_recarrega_depois_do_tempo(self, partida):
        for _ in range(regras.BALAS_MAXIMAS):
            partida._tentar_atirar(partida.jogador1, partida.jogador2, COR_BALA_P1)
        instante = partida.inicio_recarga[1]
        with mock.patch("pygame.time.get_ticks",
                        lambda: instante + regras.TEMPO_RECARGA_MS + 1):
            partida._recarregar()
        assert partida.jogador1.balas == regras.BALAS_MAXIMAS
        assert partida.inicio_recarga[1] == 0

    def test_nao_recarrega_antes_da_hora(self, partida):
        for _ in range(regras.BALAS_MAXIMAS):
            partida._tentar_atirar(partida.jogador1, partida.jogador2, COR_BALA_P1)
        instante = partida.inicio_recarga[1]
        with mock.patch("pygame.time.get_ticks",
                        lambda: instante + regras.TEMPO_RECARGA_MS - 1):
            partida._recarregar()
        assert partida.jogador1.balas == 0

    def test_a_bala_acerta_e_causa_dano(self, partida):
        # Sem itens no chão: um orbe de vida sob o alvo curaria o dano da bala
        # e o teste mediria a coleta em vez do disparo.
        partida.itens.clear()
        partida.jogador1.teleportar_para(300, 250)
        partida.jogador2.teleportar_para(360, 250)
        vida = partida.jogador2.vida
        partida._tentar_atirar(partida.jogador1, partida.jogador2, COR_BALA_P1)
        for _ in range(30):
            partida.atualizar(1 / 30)
        assert partida.jogador2.vida < vida

    def test_o_bonus_de_dano_entra_na_bala(self, partida):
        partida.jogador1.bonus_dano = 2
        partida._tentar_atirar(partida.jogador1, partida.jogador2, COR_BALA_P1)
        assert partida.balas[0].dano == regras.PROJETIL_DANO_BASE + 2


class TestCampeonato:
    def test_um_ponto_encerra_a_rodada_e_nao_o_jogo(self, partida):
        partida._pontuar(vencedor=1)
        assert partida.pontos[1] == 1
        veu = partida._transicao_pendente.cena
        assert isinstance(veu, CenaSobreposicao)
        assert "RODADA" in veu.titulo

    def test_o_ponto_decisivo_encerra_o_jogo(self, partida):
        for _ in range(regras.PONTOS_PARA_VENCER_CAMPEONATO):
            partida._pontuar(vencedor=2)
        veu = partida._transicao_pendente.cena
        assert "JOGO" in veu.titulo

    def test_a_regra_vem_da_configuracao(self, partida):
        """O game.py antigo comparava com 2 enquanto a config dizia 3."""
        for _ in range(regras.PONTOS_PARA_VENCER_CAMPEONATO - 1):
            partida._pontuar(vencedor=1)
        assert "RODADA" in partida._transicao_pendente.cena.titulo

    def test_reiniciar_rodada_preserva_o_placar(self, partida):
        partida._pontuar(vencedor=1)
        partida.jogador1.vida = 1
        partida._reiniciar_rodada()
        assert partida.pontos[1] == 1
        assert partida.jogador1.vida == partida.jogador1.personagem.vida_maxima
        assert partida.balas == []


class TestLaco:
    def test_muitos_frames_sem_excecao_e_sem_vazar_projetil(self, app, partida):
        app.pilha = [partida]
        with mock.patch("pygame.key.get_pressed",
                        lambda: Teclas(pygame.K_d, pygame.K_s, pygame.K_LEFT, pygame.K_UP)):
            for i in range(300):
                if i % 7 == 0:
                    teclar(partida.controles[1].atirar)
                assert avancar_frame(app) is not False
        assert len(partida.balas) < 40

    def test_os_jogadores_continuam_dentro_do_mapa(self, app, partida):
        app.pilha = [partida]
        with mock.patch("pygame.key.get_pressed",
                        lambda: Teclas(pygame.K_a, pygame.K_w, pygame.K_RIGHT, pygame.K_DOWN)):
            for _ in range(300):
                avancar_frame(app)
        for jogador in (partida.jogador1, partida.jogador2):
            assert partida.mapa.rect.contains(jogador.hitbox_mapa)

    def test_a_partida_nao_conhece_a_resolucao_da_janela(self):
        """O mundo é desenhado em resolução nativa e escalado uma vez."""
        from brawl.cenas import partida as modulo
        assert "config_tela" not in open(modulo.__file__, encoding="utf-8").read()
