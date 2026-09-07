"""Regras e balanceamento.

Regra do projeto: nenhum literal de balanceamento fora deste arquivo.

Antes deste refactor o `core/game.py` não importava este módulo — os mesmos
valores viviam duplicados como literais espalhados pelo código, e as duas
cópias já tinham divergido (o campeonato terminava em 2 pontos enquanto
PONTOS_PARA_VENCER_CAMPEONATO dizia 3; a vida era limitada a 10 enquanto
VIDA_MAXIMA dizia 8).
"""

# --- PARTIDA ---
PONTOS_PARA_VENCER_CAMPEONATO = 3

# --- JOGADOR ---
VIDA_MAXIMA = 8
# Teto de vida quando o jogador coleta orbes de vida: pode passar da vida
# máxima inicial, e o HUD desenha o excedente em verde.
VIDA_TETO_COM_ITENS = 10

VELOCIDADE_BASE = 2
BONUS_VELOCIDADE_MAXIMO = 3
BONUS_DANO_MAXIMO = 2

# Posição inicial de cada jogador, em coordenadas de mundo, medida nos PÉS do
# personagem (é onde ele pisa, e é o que as duas hitboxes ancoram).
# Equivalem aos antigos (-1, 205) e (760, 205), que eram o canto superior
# esquerdo do sprite.
SPAWN_JOGADOR_1 = (19, 265)
SPAWN_JOGADOR_2 = (780, 265)

# Tamanho dos frames de sprite do jogador (largura, altura em pixels)
TAMANHO_FRAME_JOGADOR = (40, 60)

# --- HITBOXES ---
# Tamanho ABSOLUTO, e não deslocamento relativo ao sprite.
#
# O ajuste relativo anterior era (-53, -30) aplicado com Rect.inflate() sobre um
# sprite de 40x60: 40 - 53 = -13, ou seja, LARGURA NEGATIVA. O jogo só funcionava
# porque o pygame normaliza retângulos de tamanho negativo por baixo dos panos —
# a hitbox efetiva virava 13x30, 13 px de largura para um personagem desenhado
# com 40. E _atualizar_ocultacao calculava área -13 * 30 = -390, o que fazia a
# regra "esconde se metade do jogador estiver no arbusto" virar "esconde com
# qualquer encostada".
#
# Tamanho absoluto não pode quebrar em silêncio quando o sprite mudar de escala.
# As duas são ancoradas nos PÉS do sprite.
TAMANHO_HITBOX_ENTIDADE = (24, 40)  # corpo: o que balas e itens acertam
TAMANHO_HITBOX_MAPA = (16, 12)      # pés: o que colide com parede e água

# A hitbox dos pés é de propósito mais estreita que a do corpo: navegar por
# corredores fica tolerante (16 px passa por um vão de 1 tile de 20 px) sem
# tornar o jogador difícil de acertar.

# Fração do corpo que precisa estar dentro da vegetação para o jogador sumir.
FRACAO_PARA_ESCONDER = 0.5

# --- MUNIÇÃO ---
BALAS_MAXIMAS = 4
TEMPO_RECARGA_MS = 3000

# --- PROJÉTIL ---
PROJETIL_RAIO = 6
PROJETIL_VELOCIDADE = 10
PROJETIL_ALCANCE_MAXIMO = 315
PROJETIL_DANO_BASE = 1

# --- ITENS COLETÁVEIS ---
ITEM_TAMANHO = 32
ITEM_ARQUIVOS = {
    "vida": "orb_vida.png",
    "dano": "orb_dano.png",
    "velocidade": "orb_velocidade.png",
}
ITEM_TENTATIVAS_SPAWN = 200  # quantas posições aleatórias tentar antes de desistir
ITEM_MARGEM_SPAWN = 40  # distância mínima das bordas ao sortear posição
