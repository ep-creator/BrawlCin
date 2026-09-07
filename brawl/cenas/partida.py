"""A cena de partida: simulação da rodada e desenho do mundo.

Esta classe ainda faz simulação e desenho no mesmo lugar — separá-los é assunto
de um passo seguinte. O que saiu daqui agora foi o laço principal (que é do App)
e as duas telas de sobreposição, que eram cinquenta linhas dentro do `draw()` e
agora são cenas empilhadas por cima desta.
"""

from __future__ import annotations

import random

import pygame

from .. import recursos
from ..config import gameplay as regras
from ..config import tela as config_tela
from ..mundo.item import Item
from ..mundo.jogador import Jogador1, Jogador2
from ..mundo.mapa import Mapa
from ..mundo.personagem import PERSONAGENS
from ..mundo.projetil import Projetil
from .base import Cena, Desempilhar, Empilhar, Transicao, Trocar
from .sobreposicao import CenaSobreposicao

COR_BALA_P1 = (0, 150, 255)
COR_BALA_P2 = (255, 50, 50)

COR_VEU_RODADA = (10, 10, 20)
COR_VEU_JOGO = (0, 0, 0)
COR_TITULO_RODADA = (255, 140, 0)
COR_TITULO_JOGO = (0, 255, 128)


class CenaPartida(Cena):
    def __init__(self, chave_p1: str, chave_p2: str):
        self.mapa = Mapa()
        self.jogador1 = Jogador1(*regras.SPAWN_JOGADOR_1, personagem=PERSONAGENS[chave_p1])
        self.jogador2 = Jogador2(*regras.SPAWN_JOGADOR_2, personagem=PERSONAGENS[chave_p2])

        self.balas: list[Projetil] = []
        self.itens: list[Item] = []

        self.pontos = {1: 0, 2: 0}

        # Instante em que a recarga de cada jogador começou, por número.
        # Um dicionário em vez de inicio_recarga_p1/p2 — o par gêmeo é
        # justamente o que impede o jogo de ter um terceiro jogador.
        self.inicio_recarga = {1: 0, 2: 0}

        self._transicao_pendente: Transicao | None = None

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

    def _coletar(self, jogador, item) -> None:
        if item.tipo == "vida":
            jogador.vida = min(jogador.vida + 1, regras.VIDA_TETO_COM_ITENS)
        elif item.tipo == "dano":
            jogador.bonus_dano = min(jogador.bonus_dano + 1, regras.BONUS_DANO_MAXIMO)
        elif item.tipo == "velocidade":
            jogador.bonus_velocidade = min(
                jogador.bonus_velocidade + 1, regras.BONUS_VELOCIDADE_MAXIMO
            )

    # ---------------------------------------------------------------- eventos

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        if (saida := super().processar_evento(evento)) is not None:
            return saida

        if evento.type != pygame.KEYDOWN:
            return None

        if evento.key == self.jogador1.controles["atirar"]:
            self._tentar_atirar(self.jogador1, self.jogador2, COR_BALA_P1)
        if evento.key == self.jogador2.controles["atirar"]:
            self._tentar_atirar(self.jogador2, self.jogador1, COR_BALA_P2)

        return None

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

    # ----------------------------------------------------------------- regras

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
        self.pontos[vencedor] += 1

        if self.pontos[vencedor] >= regras.PONTOS_PARA_VENCER_CAMPEONATO:
            self._transicao_pendente = Empilhar(self._veu_de_fim_de_jogo(vencedor))
        else:
            self._transicao_pendente = Empilhar(self._veu_de_fim_de_rodada(vencedor))

    # ------------------------------------------------------------ sobreposições

    def _veu_de_fim_de_rodada(self, vencedor: int) -> CenaSobreposicao:
        def proxima_rodada() -> Transicao:
            self._reiniciar_rodada()
            return Desempilhar()

        return CenaSobreposicao(
            titulo=f"PLAYER {vencedor} VENCEU A RODADA!",
            cor_titulo=COR_TITULO_RODADA,
            cor_veu=COR_VEU_RODADA,
            opacidade=160,
            linhas=["Pressione ESPAÇO para o próximo round"],
            acoes={pygame.K_SPACE: proxima_rodada},
        )

    def _veu_de_fim_de_jogo(self, vencedor: int) -> CenaSobreposicao:
        def reiniciar_campeonato() -> Transicao:
            self.pontos = {1: 0, 2: 0}
            self._reiniciar_rodada()
            return Desempilhar()

        def nova_selecao() -> Transicao:
            # Desempilha o véu e deixa a partida pedir a troca no frame
            # seguinte. Antes, a tecla T instanciava um Game inteiro dentro do
            # laço de eventos do Game anterior.
            self._pedir_nova_selecao()
            return Desempilhar()

        return CenaSobreposicao(
            titulo=f"PLAYER {vencedor} VENCEU O JOGO!",
            cor_titulo=COR_TITULO_JOGO,
            cor_veu=COR_VEU_JOGO,
            opacidade=200,
            tamanho_titulo=46,
            linhas=[
                "Pressione 'R' para reiniciar o campeonato",
                "Pressione 'T' para selecionar outros personagens",
            ],
            acoes={pygame.K_r: reiniciar_campeonato, pygame.K_t: nova_selecao},
        )

    def _pedir_nova_selecao(self) -> None:
        from .selecao import CenaSelecao  # importado aqui para evitar ciclo

        self._transicao_pendente = Trocar(CenaSelecao())

    def _reiniciar_rodada(self) -> None:
        self.jogador1.renascer()
        self.jogador2.renascer()
        self.balas.clear()
        self._espalhar_itens()
        self.inicio_recarga = {1: 0, 2: 0}

    # --------------------------------------------------------------- simulação

    def atualizar(self, dt: float) -> Transicao | None:
        if self._transicao_pendente is not None:
            transicao, self._transicao_pendente = self._transicao_pendente, None
            return transicao

        self._recarregar()

        self.jogador1.mover(self.mapa)
        self.jogador2.mover(self.mapa)

        self._coletar_itens()
        self._mover_balas()

        # Uma bala pode ter matado alguém e agendado a sobreposição.
        if self._transicao_pendente is not None:
            transicao, self._transicao_pendente = self._transicao_pendente, None
            return transicao
        return None

    def _recarregar(self) -> None:
        agora = pygame.time.get_ticks()
        for jogador in (self.jogador1, self.jogador2):
            inicio = self.inicio_recarga[jogador.numero]
            if jogador.balas == 0 and agora - inicio >= regras.TEMPO_RECARGA_MS:
                jogador.balas = regras.BALAS_MAXIMAS
                self.inicio_recarga[jogador.numero] = 0

    def _coletar_itens(self) -> None:
        for item in list(self.itens):
            for jogador in (self.jogador1, self.jogador2):
                if jogador.hitbox_entidade.colliderect(item.rect):
                    self._coletar(jogador, item)
                    self.itens.remove(item)
                    self._posicionar_item(item.tipo)
                    break

    def _mover_balas(self) -> None:
        for bala in self.balas:
            bala.mover()

        # _resolver_bala aplica dano e pontua, então não pode viver dentro de
        # uma list comprehension: o filtro fica ilegível quando tem efeito.
        sobreviventes = []
        for bala in self.balas:
            if not self._resolver_bala(bala):
                sobreviventes.append(bala)
        self.balas = sobreviventes

    # ----------------------------------------------------------------- desenho

    def desenhar(self, superficie: pygame.Surface) -> None:
        superficie.fill((30, 30, 30))
        self.mapa.desenhar(superficie)

        for item in self.itens:
            item.desenhar(superficie)

        self.jogador1.desenhar(superficie)
        self.jogador2.desenhar(superficie)

        for bala in self.balas:
            bala.desenhar(superficie)

        self.jogador1.desenhar_hud(superficie, 10, 10)
        self.jogador2.desenhar_hud(superficie, config_tela.LARGURA - 130, 10)

        self._desenhar_placar(superficie)

    def _desenhar_placar(self, superficie: pygame.Surface) -> None:
        texto = recursos.fonte(32, negrito=True).render(
            f"{self.pontos[1]}  X  {self.pontos[2]}", True, (255, 215, 0)
        )
        superficie.blit(texto, ((config_tela.LARGURA - texto.get_width()) // 2, 10))
