"""O jogador: sprites, movimento, colisão com o mapa, vida e munição."""

from __future__ import annotations

import pygame

from .. import recursos
from ..config import gameplay as regras
from .personagem import Personagem


class Jogador:
    """Classe base. Não instanciar diretamente — use `Jogador1` ou `Jogador2`,
    que definem controles, cor e número."""

    # Definido nas subclasses: 1 = HUD cresce para a direita, -1 = para a esquerda
    direcao_hud: int = 1

    def __init__(self, x: int, y: int, personagem: Personagem, controles: dict):
        self.personagem = personagem
        self.controles = controles

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
        self.rect = self.sprite_parado.get_rect(topleft=(x, y))

        # hitbox_entidade: colisão "real" (balas, itens). É ela que se move a
        # cada frame e dita a posição final de self.rect.
        self.hitbox_entidade = self.rect.inflate(*regras.HITBOX_ENTIDADE_AJUSTE)

        # hitbox_mapa: faixa fina colada na base da hitbox_entidade, só para
        # colisão com paredes e água. Não guarda posição própria — é recalculada
        # a cada frame a partir da hitbox_entidade.
        self.hitbox_mapa = pygame.Rect(
            0, 0, self.hitbox_entidade.width, regras.HITBOX_MAPA_ALTURA
        )
        self._recolar_hitbox_mapa()

        self.spawn_x = x
        self.spawn_y = y

        self.vida = personagem.vida_maxima
        self.balas = regras.BALAS_MAXIMAS
        self.bonus_velocidade = 0
        self.bonus_dano = 0

        self.escondido = False
        self.indo_esquerda = False
        self.indo_direita = False
        self.indo_cima = False
        self.indo_baixo = False
        self.contador_animacao = 0

    # ------------------------------------------------------------------ mapa

    def _recolar_hitbox_mapa(self) -> None:
        self.hitbox_mapa.midbottom = self.hitbox_entidade.midbottom

    def _colide_com_mapa(self, mapa) -> bool:
        """Paredes e água bloqueiam. Arbustos não — eles só escondem."""
        return (
            self.hitbox_mapa.collidelist(mapa.paredes) != -1
            or self.hitbox_mapa.collidelist(mapa.aguas) != -1
        )

    def _atualizar_ocultacao(self, mapa) -> None:
        """Fica escondido quando metade da hitbox está dentro de um arbusto."""
        self.escondido = False
        area_jogador = self.hitbox_entidade.width * self.hitbox_entidade.height

        for arbusto in mapa.arbustos:
            if not self.hitbox_entidade.colliderect(arbusto):
                continue
            intersecao = self.hitbox_entidade.clip(arbusto)
            if intersecao.width * intersecao.height >= area_jogador / 2:
                self.escondido = True
                return

    # -------------------------------------------------------------- simulação

    @property
    def velocidade(self) -> int:
        return self.personagem.velocidade + self.bonus_velocidade

    def mover(self, mapa) -> None:
        teclas = pygame.key.get_pressed()
        velocidade = self.velocidade

        # --- Eixo X ---
        x_anterior = self.hitbox_entidade.x
        if teclas[self.controles["esquerda"]]:
            self.hitbox_entidade.x -= velocidade
            self.indo_esquerda, self.indo_direita = True, False
        elif teclas[self.controles["direita"]]:
            self.hitbox_entidade.x += velocidade
            self.indo_direita, self.indo_esquerda = True, False
        else:
            self.indo_esquerda = self.indo_direita = False

        self._recolar_hitbox_mapa()
        if self._colide_com_mapa(mapa):
            self.hitbox_entidade.x = x_anterior
            self._recolar_hitbox_mapa()

        # --- Eixo Y ---
        y_anterior = self.hitbox_entidade.y
        if teclas[self.controles["cima"]]:
            self.hitbox_entidade.y -= velocidade
            self.indo_cima, self.indo_baixo = True, False
        elif teclas[self.controles["baixo"]]:
            self.hitbox_entidade.y += velocidade
            self.indo_baixo, self.indo_cima = True, False
        else:
            self.indo_cima = self.indo_baixo = False

        self._recolar_hitbox_mapa()
        if self._colide_com_mapa(mapa):
            self.hitbox_entidade.y = y_anterior
            self._recolar_hitbox_mapa()

        self._atualizar_ocultacao(mapa)

        # A posição visual só é atualizada depois que a colisão foi resolvida.
        self.rect.center = self.hitbox_entidade.center

    def receber_dano(self, quantidade: int = 1) -> bool:
        """Aplica dano. Devolve True se o jogador morreu."""
        self.vida -= quantidade
        return self.vida <= 0

    def renascer(self) -> None:
        self.vida = self.personagem.vida_maxima
        self.balas = regras.BALAS_MAXIMAS
        self.bonus_velocidade = 0
        self.bonus_dano = 0

        self.rect.topleft = (self.spawn_x, self.spawn_y)
        self.hitbox_entidade = self.rect.inflate(*regras.HITBOX_ENTIDADE_AJUSTE)
        self.hitbox_mapa = pygame.Rect(
            0, 0, self.hitbox_entidade.width, regras.HITBOX_MAPA_ALTURA
        )
        self._recolar_hitbox_mapa()

    # ---------------------------------------------------------------- desenho

    def desenhar(self, superficie: pygame.Surface) -> None:
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

    def _desenhar_acima_da_cabeca(self, superficie: pygame.Surface) -> None:
        """Munição restante e etiqueta P1/P2, logo acima do sprite."""
        tamanho, espaco = 5, 3
        largura_total = regras.BALAS_MAXIMAS * (tamanho + espaco)
        x_inicial = self.rect.centerx - largura_total // 2
        y_inicial = self.rect.top - 5

        for i in range(regras.BALAS_MAXIMAS):
            cor = self.cor if i < self.balas else (70, 70, 70)
            pygame.draw.rect(
                superficie, cor,
                (x_inicial + i * (tamanho + espaco), y_inicial, tamanho, tamanho),
                border_radius=1,
            )

        texto = recursos.fonte(12, negrito=True).render(f"P{self.numero}", True, (255, 255, 255))
        largura_fundo, altura_fundo = texto.get_width() + 8, 12
        x = self.rect.centerx - largura_fundo // 2
        y = y_inicial - 15

        pygame.draw.rect(superficie, self.cor, (x, y, largura_fundo, altura_fundo), border_radius=1)
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
            f"Dano: +{self.bonus_dano}  Vel: +{self.bonus_velocidade}", True, (255, 255, 255)
        )
        if d == 1:
            superficie.blit(texto_bonus, (x, y + 16))
        else:
            superficie.blit(texto_bonus, (x + 130 - texto_bonus.get_width(), y + 16))


class Jogador1(Jogador):
    direcao_hud = 1

    def __init__(self, x: int, y: int, personagem: Personagem):
        super().__init__(x, y, personagem, controles={
            "esquerda": pygame.K_a, "direita": pygame.K_d,
            "cima": pygame.K_w, "baixo": pygame.K_s,
            "atirar": pygame.K_SPACE,
        })
        self.cor = (0, 0, 255)
        self.numero = 1


class Jogador2(Jogador):
    direcao_hud = -1

    def __init__(self, x: int, y: int, personagem: Personagem):
        super().__init__(x, y, personagem, controles={
            "esquerda": pygame.K_LEFT, "direita": pygame.K_RIGHT,
            "cima": pygame.K_UP, "baixo": pygame.K_DOWN,
            "atirar": pygame.K_RETURN,
        })
        self.cor = (255, 0, 0)
        self.numero = 2
