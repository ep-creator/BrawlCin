"""O jogador: sprites, movimento, colisão com o mapa, vida e munição.

O jogador não lê teclado. Ele recebe um `Comando` por frame (ver brawl.entrada)
e o executa. É o que torna possível testar movimento sem abrir janela — e o que
abre espaço para bot, replay e gamepad sem mexer aqui.
"""

from __future__ import annotations

import pygame

from .. import recursos
from ..config import depuracao
from ..config import gameplay as regras
from ..entrada import Comando
from .personagem import Personagem


class Jogador:
    """Classe base. Não instanciar diretamente — use `Jogador1` ou `Jogador2`,
    que definem cor, número e o lado para onde o HUD cresce."""

    direcao_hud: int = 1
    cor: tuple[int, int, int] = (255, 255, 255)
    numero: int = 0

    #: Desempate quando duas coisas têm a mesma base. A vegetação usa 1 e ganha
    #: do jogador, de modo que pisar dentro dela a deixa por cima.
    ordem_no_empate = 0

    def __init__(self, x: int, y: int, personagem: Personagem):
        """(x, y) é a posição dos PÉS do personagem, em coordenadas de mundo."""
        self.personagem = personagem

        pasta = personagem.pasta_assets
        tamanho = regras.TAMANHO_FRAME_JOGADOR

        def frame(nome: str) -> pygame.Surface:
            return recursos.imagem(pasta, nome, tamanho=tamanho)

        self.frames_esquerda = [frame("L1.png"), frame("L2.png")]
        self.frames_direita = [frame("R1.png"), frame("R2.png")]
        self.frames_cima = [frame("U1.png"), frame("U2.png")]
        self.frames_baixo = [frame("B1.png"), frame("B2.png")]
        self.sprite_parado = frame(personagem.sprite_parado)

        # self.rect é só para desenho — desenhar() posiciona o sprite por ele.
        self.rect = self.sprite_parado.get_rect()

        # hitbox_entidade: o corpo. É o que balas e itens acertam.
        self.hitbox_entidade = pygame.Rect((0, 0), regras.TAMANHO_HITBOX_ENTIDADE)

        # hitbox_mapa: a faixa dos pés, só para colisão com parede e água.
        # Tem largura própria, e não a do corpo: pés estreitos deixam a
        # navegação tolerante sem deixar o jogador difícil de acertar.
        self.hitbox_mapa = pygame.Rect((0, 0), regras.TAMANHO_HITBOX_MAPA)

        # Posição real, em ponto flutuante, do canto da hitbox do corpo.
        # pygame.Rect só guarda inteiro, e truncar a cada frame quebraria o
        # movimento diagonal: com a direção normalizada, cada eixo anda 0,707 da
        # velocidade, e 1,41 px por frame viraria 1 px.
        self._x = 0.0
        self._y = 0.0

        self.spawn_x = x
        self.spawn_y = y
        self.teleportar_para(x, y)

        self.vida = personagem.vida_maxima
        self.balas = regras.BALAS_MAXIMAS
        self.bonus_velocidade = 0
        self.bonus_dano = 0

        #: Fração do corpo coberta por vegetação, de 0 a 1.
        self.fracao_oculta = 0.0
        #: Ligado pela cena. No modo de teste o jogador vira retângulos e a
        #: ocultação vira opacidade, em vez de sumiço.
        self.modo_de_teste = depuracao.MODO_DE_TESTE

        self.indo_esquerda = False
        self.indo_direita = False
        self.indo_cima = False
        self.indo_baixo = False
        self.contador_animacao = 0

    # ------------------------------------------------------------------ mapa

    def _sincronizar_hitboxes(self) -> None:
        """Projeta a posição em float nos Rect inteiros.

        As três caixas são ancoradas nos pés: a base da hitbox do corpo, a base
        da faixa de mapa e a base do sprite coincidem.
        """
        self.hitbox_entidade.topleft = (round(self._x), round(self._y))
        self.hitbox_mapa.midbottom = self.hitbox_entidade.midbottom
        self.rect.midbottom = self.hitbox_entidade.midbottom

    def _colide_com_mapa(self, mapa) -> bool:
        """Paredes e água bloqueiam. Arbustos não — eles só escondem.

        A borda do mapa conta como parede. O mapa antigo tinha um cinturão de
        nove paredes desenhadas à mão para isso, todas extrapolando o próprio
        mapa; sendo regra do código, mapa nenhum precisa desenhar a moldura.

        É uma checagem de contenção e não um clamp de posição: assim a borda
        passa pelo mesmo mecanismo de reverter das paredes, e o jogador desliza
        rente a ela em vez de grudar.
        """
        if not mapa.rect.contains(self.hitbox_mapa):
            return True
        return (
            self.hitbox_mapa.collidelist(mapa.paredes) != -1
            or self.hitbox_mapa.collidelist(mapa.aguas) != -1
        )

    def _atualizar_ocultacao(self, mapa) -> None:
        """Calcula quanto do corpo está coberto por vegetação.

        A cobertura é SOMADA entre as áreas de vegetação, e não avaliada uma a
        uma. Antes bastava um único arbusto passar de 50% — quem estivesse na
        junção de dois, com 30% em cada, ficava visível apesar de 60% coberto.
        As áreas vêm da fusão de tiles e não se sobrepõem, então somar é exato.
        """
        area_jogador = self.hitbox_entidade.width * self.hitbox_entidade.height
        coberto = 0
        for arbusto in mapa.arbustos:
            if not self.hitbox_entidade.colliderect(arbusto):
                continue
            intersecao = self.hitbox_entidade.clip(arbusto)
            coberto += intersecao.width * intersecao.height

        self.fracao_oculta = min(1.0, coberto / area_jogador) if area_jogador else 0.0

    @property
    def escondido(self) -> bool:
        """Regra de jogo: some da vista do adversário. Vale nos dois modos."""
        return self.fracao_oculta >= regras.FRACAO_PARA_ESCONDER

    @property
    def opacidade(self) -> float:
        """Opacidade de desenho no modo de teste, de 1,0 a OPACIDADE_MINIMA.

        Só começa a cair depois do limite de ocultação: vindo de fora, o jogador
        continua cheio até estar 50% dentro da grama, e a partir daí some
        gradualmente em vez de piscar para invisível.
        """
        limite = regras.FRACAO_PARA_ESCONDER
        if self.fracao_oculta < limite:
            return 1.0
        avanco = (self.fracao_oculta - limite) / (1.0 - limite) if limite < 1.0 else 1.0
        return 1.0 - avanco * (1.0 - depuracao.OPACIDADE_MINIMA_DO_JOGADOR)

    # -------------------------------------------------------------- simulação

    @property
    def profundidade(self) -> int:
        """Onde o jogador pisa. É por isto que ele é ordenado no desenho:
        quem tem a base mais embaixo na tela aparece na frente."""
        return self.hitbox_entidade.bottom

    @property
    def velocidade(self) -> int:
        return self.personagem.velocidade + self.bonus_velocidade

    def mover(self, comando: Comando, mapa) -> None:
        """Executa o comando deste frame, resolvendo colisão eixo a eixo.

        Um eixo de cada vez para que bater numa parede na horizontal não trave
        o movimento vertical — é o que permite deslizar rente à parede.
        """
        self.indo_esquerda = comando.dx < 0
        self.indo_direita = comando.dx > 0
        self.indo_cima = comando.dy < 0
        self.indo_baixo = comando.dy > 0

        velocidade = self.velocidade

        anterior = self._x
        self._x += comando.dx * velocidade
        self._sincronizar_hitboxes()
        if self._colide_com_mapa(mapa):
            self._x = anterior
            self._sincronizar_hitboxes()

        anterior = self._y
        self._y += comando.dy * velocidade
        self._sincronizar_hitboxes()
        if self._colide_com_mapa(mapa):
            self._y = anterior
            self._sincronizar_hitboxes()

        self._atualizar_ocultacao(mapa)

    def teleportar_para(self, pes_x: float, pes_y: float) -> None:
        """Reposiciona o jogador pelos pés, mantendo float e Rect coerentes."""
        largura, altura = self.hitbox_entidade.size
        self._x = float(pes_x) - largura / 2
        self._y = float(pes_y) - altura
        self._sincronizar_hitboxes()

    def receber_dano(self, quantidade: int = 1) -> bool:
        """Aplica dano. Devolve True se o jogador morreu."""
        self.vida -= quantidade
        return self.vida <= 0

    def renascer(self) -> None:
        self.vida = self.personagem.vida_maxima
        self.balas = regras.BALAS_MAXIMAS
        self.bonus_velocidade = 0
        self.bonus_dano = 0

        self.teleportar_para(self.spawn_x, self.spawn_y)

    # ---------------------------------------------------------------- desenho

    def desenhar(self, superficie: pygame.Surface) -> None:
        if self.modo_de_teste:
            self._desenhar_como_retangulos(superficie)
            return

        if self.escondido:
            return

        if self.contador_animacao + 1 > 20:
            self.contador_animacao = 0

        direcoes = (
            (self.indo_esquerda, self.frames_esquerda),
            (self.indo_direita, self.frames_direita),
            (self.indo_cima, self.frames_cima),
            (self.indo_baixo, self.frames_baixo),
        )

        sprite = self.sprite_parado
        andando = False
        for ativo, frames in direcoes:
            if ativo:
                sprite = frames[self.contador_animacao // 10]
                andando = True
                break

        self.contador_animacao = self.contador_animacao + 1 if andando else 0

        superficie.blit(sprite, sprite.get_rect(midbottom=self.rect.midbottom))
        self._desenhar_acima_da_cabeca(superficie)

    def _desenhar_como_retangulos(self, superficie: pygame.Surface) -> None:
        """Desenho de teste: as duas hitboxes, com a opacidade da ocultação.

        O corpo é o retângulo cheio — é ele que as balas acertam. Os pés são o
        contorno branco — é ele que colide com parede e água. Ver os dois na
        tela é o ponto: as hitboxes deixam de ser abstração.
        """
        corpo, pes = self.hitbox_entidade, self.hitbox_mapa
        topo = min(corpo.top, self.rect.top) - 22
        caixa = pygame.Rect(
            min(corpo.left, pes.left) - 12, topo,
            max(corpo.width, pes.width) + 24, max(corpo.bottom, pes.bottom) - topo,
        )

        camada = pygame.Surface(caixa.size, pygame.SRCALPHA)
        deslocamento = (-caixa.x, -caixa.y)
        pygame.draw.rect(camada, self.cor, corpo.move(deslocamento))
        pygame.draw.rect(
            camada, depuracao.COR_DA_HITBOX_DOS_PES, pes.move(deslocamento), 2
        )
        self._desenhar_municao(camada, deslocamento)

        camada.set_alpha(round(255 * self.opacidade))
        superficie.blit(camada, caixa)

    def _desenhar_municao(self, superficie: pygame.Surface, deslocamento=(0, 0)) -> None:
        lado, espaco = 5, 3
        largura_total = regras.BALAS_MAXIMAS * (lado + espaco)
        x = self.rect.centerx - largura_total // 2 + deslocamento[0]
        y = self.rect.top - 5 + deslocamento[1]
        for i in range(regras.BALAS_MAXIMAS):
            cor = self.cor if i < self.balas else (70, 70, 70)
            pygame.draw.rect(
                superficie, cor, (x + i * (lado + espaco), y, lado, lado), border_radius=1
            )

    def _desenhar_acima_da_cabeca(self, superficie: pygame.Surface) -> None:
        """Munição restante e etiqueta P1/P2, logo acima do sprite."""
        self._desenhar_municao(superficie)
        y_inicial = self.rect.top - 5

        texto = recursos.fonte(12, negrito=True).render(
            f"P{self.numero}", True, (255, 255, 255)
        )
        largura_fundo, altura_fundo = texto.get_width() + 8, 12
        x = self.rect.centerx - largura_fundo // 2
        y = y_inicial - 15

        pygame.draw.rect(
            superficie, self.cor, (x, y, largura_fundo, altura_fundo), border_radius=1
        )
        superficie.blit(texto, (x + 4, y + 2))

    def desenhar_hud(self, superficie: pygame.Surface, x: int, y: int) -> None:
        """HUD do canto: etiqueta, vida e bônus.

        `direcao_hud` define se cresce para a direita (P1) ou esquerda (P2).
        """
        fonte = recursos.fonte(20)
        fonte_bonus = recursos.fonte(16)

        lado_coracao, espaco = 12, 4
        total_coracoes = max(self.personagem.vida_maxima, self.vida)
        d = self.direcao_hud

        etiqueta = fonte.render(f"P{self.numero}", True, self.cor)
        superficie.blit(etiqueta, (x if d == 1 else x + 110, y))

        origem = x + 28 if d == 1 else x + 90
        for i in range(total_coracoes):
            if i < self.vida:
                # O excedente à vida máxima (vindo de orbes) aparece em verde.
                cor = (0, 255, 0) if i >= self.personagem.vida_maxima else self.cor
            else:
                cor = (80, 80, 80)
            pygame.draw.rect(
                superficie, cor,
                (origem + d * i * (lado_coracao + espaco), y, lado_coracao, lado_coracao),
            )

        texto_bonus = fonte_bonus.render(
            f"Dano: +{self.bonus_dano}  Vel: +{self.bonus_velocidade}",
            True, (255, 255, 255),
        )
        if d == 1:
            superficie.blit(texto_bonus, (x, y + 16))
        else:
            superficie.blit(texto_bonus, (x + 130 - texto_bonus.get_width(), y + 16))


class Jogador1(Jogador):
    direcao_hud = 1
    cor = (0, 0, 255)
    numero = 1


class Jogador2(Jogador):
    direcao_hud = -1
    cor = (255, 0, 0)
    numero = 2
