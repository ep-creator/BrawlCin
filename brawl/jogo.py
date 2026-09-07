"""A partida: laço de jogo, regras de rodada e desenho.

Esta classe ainda faz coisas demais — entrada, simulação, placar e desenho no
mesmo lugar. Quebrá-la é o assunto dos próximos passos do refactor. O que mudou
agora foi o que impedia o jogo de rodar, mais duas correções estruturais que
não dava para deixar passar:

- `run()` não chama mais `sys.exit()`. Uma classe de domínio não derruba o
  processo: ela devolve o motivo de ter terminado e quem chamou decide.
- Trocar de personagem (tecla T) não instancia mais um `Jogo` dentro do laço
  de eventos do `Jogo` anterior. Aquilo empilhava um laço principal dentro do
  outro a cada troca; agora a partida simplesmente termina pedindo nova seleção.
"""

from __future__ import annotations

import enum
import random

import pygame

from . import recursos
from .config import gameplay as regras
from .config import tela as config_tela
from .mundo.item import Item
from .mundo.jogador import Jogador1, Jogador2
from .mundo.mapa import Mapa
from .mundo.personagem import PERSONAGENS
from .mundo.projetil import Projetil


class ResultadoDaPartida(enum.Enum):
    """Por que o laço da partida terminou."""

    SAIR = enum.auto()
    NOVA_SELECAO = enum.auto()


COR_BALA_P1 = (0, 150, 255)
COR_BALA_P2 = (255, 50, 50)


class Jogo:
    def __init__(self, superficie: pygame.Surface, chave_p1: str, chave_p2: str):
        self.superficie = superficie
        self.relogio = pygame.time.Clock()

        personagem_p1 = PERSONAGENS[chave_p1]
        personagem_p2 = PERSONAGENS[chave_p2]

        self.mapa = Mapa()
        self.jogador1 = Jogador1(*regras.SPAWN_JOGADOR_1, personagem=personagem_p1)
        self.jogador2 = Jogador2(*regras.SPAWN_JOGADOR_2, personagem=personagem_p2)

        self.balas: list[Projetil] = []
        self.itens: list[Item] = []

        self.pontos_p1 = 0
        self.pontos_p2 = 0

        self.fim_de_jogo = False
        self.fim_de_rodada = False
        self.texto_vencedor = ""
        self.texto_vencedor_da_rodada = ""

        # Instante em que a recarga de cada jogador começou, por número.
        # Um dicionário em vez de inicio_recarga_p1/p2 — o par gêmeo é
        # justamente o que impede o jogo de ter um terceiro jogador.
        self.inicio_recarga = {1: 0, 2: 0}

        self.rodando = True
        self.resultado = ResultadoDaPartida.SAIR

        self._espalhar_itens()

    # ------------------------------------------------------------------ itens

    def _posicionar_item(self, tipo: str) -> None:
        """Sorteia uma posição livre para um item novo. Desiste em silêncio se
        não achar depois de ITEM_TENTATIVAS_SPAWN tentativas."""
        margem = regras.ITEM_MARGEM_SPAWN
        ocupados = [item.rect for item in self.itens]

        for _ in range(regras.ITEM_TENTATIVAS_SPAWN):
            candidato = Item(
                random.randint(margem, config_tela.LARGURA - margem),
                random.randint(margem, config_tela.ALTURA - margem),
                tipo,
            )
            atrapalha = (
                candidato.rect.collidelist(self.mapa.paredes) != -1
                or candidato.rect.collidelist(self.mapa.aguas) != -1
                or candidato.rect.collidelist(self.mapa.arbustos) != -1
                or candidato.rect.collidelist(ocupados) != -1
            )
            if not atrapalha:
                self.itens.append(candidato)
                return

    def _espalhar_itens(self) -> None:
        self.itens.clear()
        for tipo in regras.ITEM_ARQUIVOS:
            self._posicionar_item(tipo)

    def _coletar(self, jogador, item: Item) -> None:
        if item.tipo == "vida":
            jogador.vida = min(jogador.vida + 1, regras.VIDA_TETO_COM_ITENS)
        elif item.tipo == "dano":
            jogador.bonus_dano = min(jogador.bonus_dano + 1, regras.BONUS_DANO_MAXIMO)
        elif item.tipo == "velocidade":
            jogador.bonus_velocidade = min(
                jogador.bonus_velocidade + 1, regras.BONUS_VELOCIDADE_MAXIMO
            )

    # ----------------------------------------------------------------- eventos

    def _tentar_atirar(self, atirador, alvo, cor: tuple[int, int, int]) -> None:
        """Dispara, se houver munição. Zerou a munição, começa a recarga."""
        if atirador.balas <= 0:
            return

        self.balas.append(
            Projetil(
                atirador.rect.centerx, atirador.rect.centery,
                alvo.rect.centerx, alvo.rect.centery,
                cor=cor,
                dano=regras.PROJETIL_DANO_BASE + atirador.bonus_dano,
            )
        )
        atirador.balas -= 1
        if atirador.balas == 0:
            self.inicio_recarga[atirador.numero] = pygame.time.get_ticks()

    def _processar_eventos(self) -> None:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self._terminar(ResultadoDaPartida.SAIR)
                return

            if evento.type != pygame.KEYDOWN:
                continue

            if evento.key == pygame.K_ESCAPE:
                self._terminar(ResultadoDaPartida.SAIR)
                return

            if self.fim_de_jogo:
                if evento.key == pygame.K_r:
                    self._reiniciar_campeonato()
                elif evento.key == pygame.K_t:
                    self._terminar(ResultadoDaPartida.NOVA_SELECAO)
                    return

            elif self.fim_de_rodada:
                if evento.key == pygame.K_SPACE:
                    self.fim_de_rodada = False
                    self.texto_vencedor_da_rodada = ""
                    self._reiniciar_rodada()

            else:
                if evento.key == self.jogador1.controles["atirar"]:
                    self._tentar_atirar(self.jogador1, self.jogador2, COR_BALA_P1)
                if evento.key == self.jogador2.controles["atirar"]:
                    self._tentar_atirar(self.jogador2, self.jogador1, COR_BALA_P2)

    def _terminar(self, resultado: ResultadoDaPartida) -> None:
        self.resultado = resultado
        self.rodando = False

    # ------------------------------------------------------------------ regras

    def _resolver_bala(self, bala: Projetil) -> bool:
        """True se a bala deve ser removida neste frame."""
        if bala.passou_do_alcance:
            return True

        if not (0 <= bala.x <= config_tela.LARGURA and 0 <= bala.y <= config_tela.ALTURA):
            return True

        if bala.rect.collidelist(self.mapa.paredes) != -1:
            return True

        # Quem tomou o tiro ainda é decidido pela cor da bala. É frágil, e o
        # passo do refactor que troca isso por uma referência ao atirador está
        # registrado no design-alvo (D4).
        if bala.cor == COR_BALA_P2 and bala.rect.colliderect(self.jogador1.hitbox_entidade):
            if self.jogador1.receber_dano(bala.dano):
                self._pontuar(vencedor=2)
            return True

        if bala.cor == COR_BALA_P1 and bala.rect.colliderect(self.jogador2.hitbox_entidade):
            if self.jogador2.receber_dano(bala.dano):
                self._pontuar(vencedor=1)
            return True

        return False

    def _pontuar(self, vencedor: int) -> None:
        if vencedor == 1:
            self.pontos_p1 += 1
            pontos = self.pontos_p1
        else:
            self.pontos_p2 += 1
            pontos = self.pontos_p2

        if pontos >= regras.PONTOS_PARA_VENCER_CAMPEONATO:
            self.fim_de_jogo = True
            self.texto_vencedor = f"PLAYER {vencedor} VENCEU O JOGO!"
        else:
            self.fim_de_rodada = True
            self.texto_vencedor_da_rodada = f"PLAYER {vencedor} VENCEU A RODADA!"

    def _reiniciar_rodada(self) -> None:
        self.jogador1.renascer()
        self.jogador2.renascer()
        self.balas.clear()
        self._espalhar_itens()
        self.inicio_recarga = {1: 0, 2: 0}

    def _reiniciar_campeonato(self) -> None:
        self.pontos_p1 = 0
        self.pontos_p2 = 0
        self.fim_de_jogo = False
        self.texto_vencedor = ""
        self._reiniciar_rodada()

    # --------------------------------------------------------------- simulação

    def atualizar(self) -> None:
        if self.fim_de_jogo or self.fim_de_rodada:
            return

        agora = pygame.time.get_ticks()
        for jogador in (self.jogador1, self.jogador2):
            inicio = self.inicio_recarga[jogador.numero]
            if jogador.balas == 0 and agora - inicio >= regras.TEMPO_RECARGA_MS:
                jogador.balas = regras.BALAS_MAXIMAS
                self.inicio_recarga[jogador.numero] = 0

        self.jogador1.mover(self.mapa)
        self.jogador2.mover(self.mapa)

        for item in list(self.itens):
            for jogador in (self.jogador1, self.jogador2):
                if jogador.hitbox_entidade.colliderect(item.rect):
                    self._coletar(jogador, item)
                    self.itens.remove(item)
                    self._posicionar_item(item.tipo)
                    break

        for bala in list(self.balas):
            bala.mover()

        # _resolver_bala aplica dano e pontua, então não pode viver dentro de
        # uma list comprehension: o filtro fica ilegível quando tem efeito.
        sobreviventes = []
        for bala in self.balas:
            if not self._resolver_bala(bala):
                sobreviventes.append(bala)
        self.balas = sobreviventes

    # ----------------------------------------------------------------- desenho

    def desenhar(self) -> None:
        self.superficie.fill((30, 30, 30))
        self.mapa.desenhar(self.superficie)

        for item in self.itens:
            item.desenhar(self.superficie)

        self.jogador1.desenhar(self.superficie)
        self.jogador2.desenhar(self.superficie)

        for bala in self.balas:
            bala.desenhar(self.superficie)

        self.jogador1.desenhar_hud(self.superficie, 10, 10)
        self.jogador2.desenhar_hud(self.superficie, config_tela.LARGURA - 130, 10)

        self._desenhar_placar()

        if self.fim_de_jogo:
            self._desenhar_sobreposicao(
                (0, 0, 0), 200, self.texto_vencedor, 46, (0, 255, 128),
                [
                    "Pressione 'R' para reiniciar o campeonato",
                    "Pressione 'T' para selecionar outros personagens",
                ],
            )
        elif self.fim_de_rodada:
            self._desenhar_sobreposicao(
                (10, 10, 20), 160, self.texto_vencedor_da_rodada, 42, (255, 140, 0),
                ["Pressione ESPAÇO para o próximo round"],
            )

        pygame.display.flip()

    def _desenhar_placar(self) -> None:
        texto = recursos.fonte(32, negrito=True).render(
            f"{self.pontos_p1}  X  {self.pontos_p2}", True, (255, 215, 0)
        )
        self.superficie.blit(texto, ((config_tela.LARGURA - texto.get_width()) // 2, 10))

    def _desenhar_sobreposicao(self, cor_fundo, opacidade, titulo, tamanho_titulo,
                               cor_titulo, linhas) -> None:
        veu = pygame.Surface(self.superficie.get_size())
        veu.set_alpha(opacidade)
        veu.fill(cor_fundo)
        self.superficie.blit(veu, (0, 0))

        largura, altura = self.superficie.get_size()

        texto_titulo = recursos.fonte(tamanho_titulo, negrito=True).render(
            titulo, True, cor_titulo
        )
        y_titulo = (altura - texto_titulo.get_height()) // 2 - 20
        self.superficie.blit(texto_titulo, ((largura - texto_titulo.get_width()) // 2, y_titulo))

        fonte_linha = recursos.fonte(22)
        for i, linha in enumerate(linhas):
            texto = fonte_linha.render(linha, True, (255, 255, 255))
            self.superficie.blit(
                texto, ((largura - texto.get_width()) // 2, y_titulo + 50 + i * 25)
            )

    # -------------------------------------------------------------------- laço

    def rodar(self) -> ResultadoDaPartida:
        while self.rodando:
            self._processar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(config_tela.FPS)
        return self.resultado
