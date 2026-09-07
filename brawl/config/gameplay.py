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

# Posição inicial de cada jogador, em coordenadas de mundo (o mapa tem 791x500).
SPAWN_JOGADOR_1 = (-1, 205)
SPAWN_JOGADOR_2 = (760, 205)

# Tamanho dos frames de sprite do jogador (largura, altura em pixels)
TAMANHO_FRAME_JOGADOR = (40, 60)

# --- HITBOXES (duas, para efeito de profundidade "down-top") ---
HITBOX_ENTIDADE_AJUSTE = (-53, -30)  # (dx, dy) aplicado com Rect.inflate()

HITBOX_MAPA_ALTURA = 20  # altura fixa da faixa de colisão com o mapa

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
