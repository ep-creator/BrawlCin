"""Tela de controles.

Os nomes das teclas são lidos dos próprios controles em `brawl.entrada`, e não
digitados aqui. Remapear um controle muda esta tela junto — uma tela de ajuda
que mente sobre as teclas é pior do que não ter tela de ajuda.
"""

from __future__ import annotations

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..entrada import TECLADO_P1, TECLADO_P2
from ..render.texto import desenhar_texto_contornado
from .base import Cena, Desempilhar, Transicao

COR_TITULO = (255, 205, 60)
COR_TEXTO = (235, 235, 235)
COR_APAGADA = (170, 170, 180)
COR_CONTORNO = (25, 20, 40)
COR_VEU = (12, 10, 20)

#: pygame.key.name() devolve nomes em inglês e minúsculos ("space", "return").
NOMES_AMIGAVEIS = {
    "space": "ESPAÇO",
    "return": "ENTER",
    "up": "CIMA",
    "down": "BAIXO",
    "left": "ESQUERDA",
    "right": "DIREITA",
    "escape": "ESC",
}


def nome_da_tecla(codigo: int) -> str:
    bruto = pygame.key.name(codigo)
    return NOMES_AMIGAVEIS.get(bruto, bruto.upper())


LINHAS_DOS_JOGADORES = [
    ("Cima", TECLADO_P1.cima, TECLADO_P2.cima),
    ("Baixo", TECLADO_P1.baixo, TECLADO_P2.baixo),
    ("Esquerda", TECLADO_P1.esquerda, TECLADO_P2.esquerda),
    ("Direita", TECLADO_P1.direita, TECLADO_P2.direita),
    ("Atirar", TECLADO_P1.atirar, TECLADO_P2.atirar),
]

LINHAS_GERAIS = [
    ("ESPAÇO", "Próxima rodada, no fim de uma rodada"),
    ("R", "Reiniciar o campeonato, no fim do jogo"),
    ("T", "Escolher outros personagens, no fim do jogo"),
    ("F1", "Modo de teste: mostra as hitboxes"),
    ("ESC", "Voltar ou sair"),
]

# Colunas escolhidas para o bloco inteiro ficar centrado na tela, e não só o
# título: a coluna de ações é alinhada à direita, as dos jogadores ao centro.
X_ACAO = 670
X_P1 = 955
X_P2 = 1275

# A lista de teclas gerais tem descrições alinhadas à esquerda, de larguras
# diferentes, então ela não pode compartilhar a coluna da tabela: alinhada lá,
# o bloco inteiro puxava mais de 100 px para a esquerda do centro da tela.
X_TECLA_GERAL = 800


class CenaControles(Cena):
    """Empilhada por cima do menu: o menu continua visível atrás do véu."""

    transparente = True

    def __init__(self):
        self.fonte_titulo = recursos.fonte_do_jogo(58)
        self.fonte_cabecalho = recursos.fonte_do_jogo(34)
        self.fonte = recursos.fonte(30)
        self.fonte_pequena = recursos.fonte(26)
        self._veu: pygame.Surface | None = None

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        """ESC aqui volta para o menu, em vez de sair do jogo."""
        if evento.type == pygame.KEYDOWN:
            return Desempilhar()
        return None

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.blit(self._obter_veu(superficie.get_size()), (0, 0))
        meio = config_tela.LARGURA // 2

        desenhar_texto_contornado(
            superficie, "CONTROLES", self.fonte_titulo,
            COR_TITULO, COR_CONTORNO, meio, 130,
        )

        for rotulo, x in (("PLAYER 1", X_P1), ("PLAYER 2", X_P2)):
            desenhar_texto_contornado(
                superficie, rotulo, self.fonte_cabecalho,
                COR_TEXTO, COR_CONTORNO, x, 250,
            )

        y = 330
        for acao, tecla_p1, tecla_p2 in LINHAS_DOS_JOGADORES:
            self._escrever(superficie, acao, X_ACAO, y, alinhar_a_direita=True)
            self._escrever(superficie, nome_da_tecla(tecla_p1), X_P1, y, centrado=True)
            self._escrever(superficie, nome_da_tecla(tecla_p2), X_P2, y, centrado=True)
            y += 56

        y += 40
        for tecla, descricao in LINHAS_GERAIS:
            self._escrever(superficie, tecla, X_TECLA_GERAL, y,
                           alinhar_a_direita=True, cor=COR_TITULO)
            self._escrever(superficie, descricao, X_TECLA_GERAL + 40, y,
                           fonte=self.fonte_pequena, cor=COR_APAGADA)
            y += 44

        self._escrever(
            superficie, "Qualquer tecla para voltar", meio, config_tela.ALTURA - 70,
            centrado=True, fonte=self.fonte_pequena, cor=COR_APAGADA,
        )

    def _escrever(self, superficie, texto, x, y, *, centrado=False,
                  alinhar_a_direita=False, fonte=None, cor=COR_TEXTO) -> None:
        imagem = (fonte or self.fonte).render(texto, True, cor)
        if centrado:
            destino = imagem.get_rect(center=(x, y))
        elif alinhar_a_direita:
            destino = imagem.get_rect(midright=(x, y))
        else:
            destino = imagem.get_rect(midleft=(x, y))
        superficie.blit(imagem, destino)

    def _obter_veu(self, tamanho: tuple[int, int]) -> pygame.Surface:
        if self._veu is None or self._veu.get_size() != tamanho:
            self._veu = pygame.Surface(tamanho)
            self._veu.set_alpha(242)   # o menu atrás não pode competir com a leitura
            self._veu.fill(COR_VEU)
        return self._veu
