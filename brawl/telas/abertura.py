"""Tela de abertura: fade da logo do CIn, queda da logo do Brawl e espera."""

from __future__ import annotations

import pygame

from .. import recursos
from ..config import tela as config_tela
from ..entrada import pediu_para_sair
from ..render.efeitos import deve_desenhar_piscando, escala_de_respiracao

CENTRO_X = config_tela.LARGURA // 2
CENTRO_Y = config_tela.ALTURA // 2


def mostrar_abertura(superficie: pygame.Surface) -> bool:
    """Roda a abertura. Devolve True se o jogador quer começar, False se saiu."""
    relogio = pygame.time.Clock()

    # `copia=True` porque o fade chama set_alpha na superfície — sem a cópia a
    # alteração ficaria gravada na imagem em cache e vazaria para outros usos.
    logo_cin = recursos.imagem("telainicial", "logo_cin.png", tamanho=(820, 480), copia=True)
    logo_brawl = recursos.imagem("telainicial", "logo_brawl.png", tamanho=(600, 225))
    fundo = recursos.imagem_opcional(
        "telainicial", "tela_inicio_background.png",
        tamanho=config_tela.RESOLUCAO, alpha=False,
    )
    botao = recursos.imagem_opcional("telainicial", "btn.png")

    rect_logo_cin = logo_cin.get_rect(center=(CENTRO_X, CENTRO_Y))

    def desenhar_cenario() -> None:
        if fundo is not None:
            superficie.blit(fundo, (0, 0))
        else:
            superficie.fill((40, 40, 40))
        superficie.blit(logo_cin, rect_logo_cin)

    def desenhar_logo_brawl(escala: float) -> None:
        redimensionada = pygame.transform.scale(
            logo_brawl,
            (int(logo_brawl.get_width() * escala), int(logo_brawl.get_height() * escala)),
        )
        superficie.blit(redimensionada, redimensionada.get_rect(center=(CENTRO_X, CENTRO_Y + 40)))

    pulou = False

    def checar_eventos() -> bool | None:
        """None = seguir; False = sair do jogo. Marca `pulou` ao apertar espaço."""
        nonlocal pulou
        for evento in pygame.event.get():
            if pediu_para_sair(evento):
                return False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                pulou = True
        return None

    # --- Etapa 1: fade in da logo do CIn ---
    opacidade = 0
    while opacidade < 255 and not pulou:
        if checar_eventos() is False:
            return False
        superficie.fill((0, 0, 0))
        logo_cin.set_alpha(opacidade)
        superficie.blit(logo_cin, rect_logo_cin)
        pygame.display.flip()
        opacidade += 5
        relogio.tick(config_tela.FPS)

    logo_cin.set_alpha(255)
    if not pulou:
        pygame.time.delay(300)

    # --- Etapa 2: queda e ricochete da logo do Brawl ---
    escala, velocidade, gravidade, elasticidade = 6.0, 0.0, 0.18, 0.55
    while not pulou:
        if checar_eventos() is False:
            return False

        desenhar_cenario()
        velocidade += gravidade
        escala -= velocidade

        if escala <= 1.0:
            escala = 1.0
            velocidade = -velocidade * elasticidade
            if abs(velocidade) < 0.05:
                break

        desenhar_logo_brawl(escala)
        pygame.display.flip()
        relogio.tick(config_tela.FPS)

    # --- Etapa 3: espera pelo ENTER ---
    tempo = 0.0
    contador_pisca = 0

    while True:
        for evento in pygame.event.get():
            if pediu_para_sair(evento):
                return False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
                _piscar_confirmacao(superficie, relogio, desenhar_cenario,
                                    desenhar_logo_brawl, botao)
                return True

        desenhar_cenario()
        desenhar_logo_brawl(escala_de_respiracao(tempo, amplitude=0.05))

        contador_pisca += 1
        if botao is not None and deve_desenhar_piscando(contador_pisca, 15):
            superficie.blit(botao, botao.get_rect(center=(CENTRO_X, config_tela.ALTURA - 40)))

        pygame.display.flip()
        tempo += 0.2
        relogio.tick(config_tela.FPS)


def _piscar_confirmacao(superficie, relogio, desenhar_cenario, desenhar_logo_brawl, botao) -> None:
    """Pisca rápido o botão ao confirmar, antes de sair da tela."""
    if botao is None:
        return
    rect_botao = botao.get_rect(center=(CENTRO_X, config_tela.ALTURA - 40))
    for i in range(36):
        desenhar_cenario()
        desenhar_logo_brawl(1.0)
        if deve_desenhar_piscando(i, 2):
            superficie.blit(botao, rect_botao)
        pygame.display.flip()
        relogio.tick(config_tela.FPS)
