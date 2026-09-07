"""Navegabilidade do mapa, medida com a colisão real do jogo.

Estes testes fazem uma busca em largura pixel a pixel sobre o mapa inteiro, o
que leva alguns segundos — por isso estão marcados como `lento` e ficam fora da
rodada padrão. Para rodá-los:

    python -m pytest -m lento

Vale rodar sempre que a hitbox dos pés, o mapa ou os spawns mudarem. Foi o que
provou que alargar a hitbox de 13 para 16 px não fechou nenhuma passagem.
"""

from __future__ import annotations

from collections import deque

import pygame
import pytest

from brawl.config import gameplay as regras
from brawl.mundo.jogador import Jogador1
from brawl.mundo.mapa import Mapa

pytestmark = pytest.mark.lento


@pytest.fixture(scope="module")
def mapa():
    return Mapa()


def _posicao_valida(mapa, tamanho_dos_pes):
    largura, altura = tamanho_dos_pes

    def valida(x, y):
        pes = pygame.Rect(0, 0, largura, altura)
        pes.midbottom = (x, y)
        return (
            mapa.rect.contains(pes)
            and pes.collidelist(mapa.paredes) == -1
            and pes.collidelist(mapa.aguas) == -1
        )

    return valida


def _alcancavel_a_partir_de(origem, valida):
    if not valida(*origem):
        return set()
    visto = {origem}
    fila = deque([origem])
    while fila:
        x, y = fila.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            vizinho = (x + dx, y + dy)
            if vizinho not in visto and valida(*vizinho):
                visto.add(vizinho)
                fila.append(vizinho)
    return visto


@pytest.fixture(scope="module")
def area_alcancavel(mapa):
    valida = _posicao_valida(mapa, regras.TAMANHO_HITBOX_MAPA)
    return _alcancavel_a_partir_de(tuple(regras.SPAWN_JOGADOR_1), valida)


def test_os_spawns_estao_em_posicao_valida(mapa):
    valida = _posicao_valida(mapa, regras.TAMANHO_HITBOX_MAPA)
    assert valida(*regras.SPAWN_JOGADOR_1)
    assert valida(*regras.SPAWN_JOGADOR_2)


def test_um_jogador_alcanca_o_outro(area_alcancavel):
    """Se a arena estivesse partida em ilhas, a partida seria injogável."""
    assert tuple(regras.SPAWN_JOGADOR_2) in area_alcancavel


def test_a_arena_nao_e_um_corredor_estreito(area_alcancavel, mapa):
    """Guarda contra uma hitbox futura estrangular o mapa sem ninguém notar."""
    area_do_mapa = mapa.rect.width * mapa.rect.height
    assert len(area_alcancavel) > area_do_mapa * 0.5


def test_os_pes_cabem_em_um_tile_do_mapa_novo():
    """O mapa novo tem tiles de 20 px; pés mais largos travariam corredores."""
    assert regras.TAMANHO_HITBOX_MAPA[0] < 20


def test_o_jogador_realmente_percorre_a_area_alcancavel(mapa, personagem, area_alcancavel):
    """Amarra a conta acima ao movimento de verdade, e não só à geometria."""
    jogador = Jogador1(*regras.SPAWN_JOGADOR_1, personagem=personagem)
    assert jogador.hitbox_entidade.midbottom in area_alcancavel
