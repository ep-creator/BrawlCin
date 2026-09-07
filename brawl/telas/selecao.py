"""Tela de seleção de personagens: cada jogador escolhe e confirma o seu."""

from __future__ import annotations

import math

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..mundo.personagem import PERSONAGENS
from ..render.texto import desenhar_texto_contornado

COR_BRANCA = (255, 255, 255)
COR_FUNDO = (15, 15, 20)
COR_P1 = (0, 255, 255)
COR_P2 = (255, 80, 80)
COR_CONFIRMADO = (50, 255, 50)

ALTURA_SPRITE = 220
Y_PERSONAGEM = 295
FRAMES_DE_CONFIRMACAO = 30


class _EscolhaDoJogador:
    """Estado da escolha de um jogador nesta tela."""

    def __init__(self, indice: int, x: int, cor, teclas):
        self.indice = indice
        self.x = x
        self.cor = cor
        self.tecla_esquerda, self.tecla_direita, self.tecla_acao = teclas
        self.frames_confirmando = 0
        self.confirmado = False

    def processar(self, tecla, total: int) -> None:
        if tecla == self.tecla_acao:
            if self.confirmado:
                self.confirmado = False
                self.frames_confirmando = 0
            elif self.frames_confirmando == 0:
                self.frames_confirmando = FRAMES_DE_CONFIRMACAO
        elif self.frames_confirmando == 0 and not self.confirmado:
            if tecla == self.tecla_esquerda:
                self.indice = (self.indice - 1) % total
            elif tecla == self.tecla_direita:
                self.indice = (self.indice + 1) % total

    def atualizar(self) -> None:
        if self.frames_confirmando > 0:
            self.frames_confirmando -= 1
            if self.frames_confirmando == 0:
                self.confirmado = True

    @property
    def piscando(self) -> bool:
        return self.frames_confirmando > 0 and self.frames_confirmando % 4 < 2


def _carregar_recursos() -> tuple[dict, pygame.Surface | None, pygame.Surface | None, dict]:
    fontes = {
        "titulo": recursos.fonte_do_jogo(42),
        "nome": recursos.fonte_do_jogo(36),
        "setas": recursos.fonte_do_jogo(60),
    }

    fundo = recursos.imagem_opcional(
        "telaselecao", "background.png", tamanho=config_tela.RESOLUCAO, alpha=False
    )

    titulo = recursos.imagem_opcional("telaselecao", "escolham_brawlers.png")
    if titulo is not None:
        titulo = pygame.transform.scale(
            titulo, (int(titulo.get_width() * 0.8), int(titulo.get_height() * 0.8))
        )

    sprites = {}
    for chave, personagem in PERSONAGENS.items():
        original = recursos.imagem(personagem.pasta_assets, personagem.sprite_parado)
        fator = ALTURA_SPRITE / original.get_height()
        sprites[chave] = pygame.transform.scale(
            original, (int(original.get_width() * fator), ALTURA_SPRITE)
        )

    return fontes, fundo, titulo, sprites


def escolher_personagens(superficie: pygame.Surface) -> tuple[str | None, str | None]:
    """Devolve as chaves escolhidas por P1 e P2, ou (None, None) se o jogador saiu."""
    relogio = pygame.time.Clock()
    chaves = list(PERSONAGENS)
    fontes, fundo, titulo, sprites = _carregar_recursos()

    escolhas = {
        "P1": _EscolhaDoJogador(
            0, config_tela.LARGURA // 4, COR_P1,
            (pygame.K_a, pygame.K_d, pygame.K_SPACE),
        ),
        "P2": _EscolhaDoJogador(
            min(1, len(chaves) - 1), (3 * config_tela.LARGURA) // 4, COR_P2,
            (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN),
        ),
    }

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or (
                evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE
            ):
                return None, None
            if evento.type == pygame.KEYDOWN:
                for escolha in escolhas.values():
                    escolha.processar(evento.key, len(chaves))

        for escolha in escolhas.values():
            escolha.atualizar()

        if all(escolha.confirmado for escolha in escolhas.values()):
            return chaves[escolhas["P1"].indice], chaves[escolhas["P2"].indice]

        _desenhar(superficie, fontes, fundo, titulo, sprites, escolhas, chaves)
        pygame.display.flip()
        relogio.tick(config_tela.FPS)


def _desenhar(superficie, fontes, fundo, titulo, sprites, escolhas, chaves) -> None:
    if fundo is not None:
        superficie.blit(fundo, (0, 0))
    else:
        superficie.fill(COR_FUNDO)

    if titulo is not None:
        fator = 1.0 + math.sin(pygame.time.get_ticks() * 0.004) * 0.04
        animado = pygame.transform.scale(
            titulo, (int(titulo.get_width() * fator), int(titulo.get_height() * fator))
        )
        superficie.blit(animado, animado.get_rect(center=(config_tela.LARGURA // 2, 50)))

    for identificador, escolha in escolhas.items():
        desenhar_texto_contornado(
            superficie, f"PLAYER {identificador[-1]}", fontes["titulo"],
            COR_BRANCA, escolha.cor, escolha.x, 160,
        )

        if escolha.piscando:
            continue

        if not escolha.confirmado:
            for texto, deslocamento in (("<", -120), (">", 120)):
                seta = fontes["setas"].render(texto, True, escolha.cor)
                superficie.blit(
                    seta, seta.get_rect(center=(escolha.x + deslocamento, Y_PERSONAGEM))
                )

        chave = chaves[escolha.indice]
        sprite = sprites[chave]
        if identificador == "P2":
            sprite = pygame.transform.flip(sprite, True, False)
        superficie.blit(sprite, sprite.get_rect(center=(escolha.x, Y_PERSONAGEM)))

        cor_nome = COR_CONFIRMADO if escolha.confirmado else COR_BRANCA
        nome = fontes["nome"].render(PERSONAGENS[chave].nome, True, cor_nome)
        superficie.blit(nome, nome.get_rect(center=(escolha.x, Y_PERSONAGEM + 110)))
