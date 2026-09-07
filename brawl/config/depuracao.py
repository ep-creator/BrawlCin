"""Modo de teste: desenho por retângulos e ocultação por opacidade.

Serve para enxergar as hitboxes e afinar o comportamento da vegetação. Não é o
jogo final — no modo normal os personagens voltam a ser sprites e a ocultação
volta a ser binária (o jogador some por completo).

Liga e desliga com F1 durante a partida.
"""

# Estado inicial da partida. F1 alterna em tempo real.
MODO_DE_TESTE = True

# Opacidade do jogador quando ele está INTEIRAMENTE dentro da vegetação.
# Entre o limite de ocultação (FRACAO_PARA_ESCONDER) e 100% de cobertura, a
# opacidade cai suavemente de 1,0 até aqui. Nunca chega a zero: no modo de
# teste o objetivo é ver o que está acontecendo.
OPACIDADE_MINIMA_DO_JOGADOR = 0.25

# Quanto da vegetação continua visível na janela ao redor de um jogador oculto.
# É o que deixa você enxergar para onde está indo dentro do mato.
OPACIDADE_DA_GRAMA_NA_JANELA = 0.35

# Raio da janela, em pixels além da hitbox do corpo.
RAIO_DA_JANELA = 40

# Em quantos anéis concêntricos a janela é montada. Mais anéis, borda mais
# suave e mais blits por frame. Um só devolve o retângulo de borda dura.
PASSOS_DA_JANELA = 6

# Cores do desenho de teste.
COR_DA_HITBOX_DOS_PES = (255, 255, 255)
