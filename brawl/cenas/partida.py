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
from ..config import depuracao
from ..config import gameplay as regras
from ..entrada import Comando, TECLADO_P1, TECLADO_P2
from ..mundo.item import Item
from ..mundo.jogador import Jogador1, Jogador2
from ..mundo.mapa import Mapa
from ..mundo.personagem import PERSONAGENS
from ..mundo.projetil import Projetil
from ..render.camera import Camera
from .base import Cena, Desempilhar, Empilhar, SubstituirPilha, Transicao
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

        # O mundo é desenhado no tamanho nativo do mapa e escalado uma vez por
        # frame. Nenhuma coordenada de gameplay conhece a resolução da janela.
        self.camera = Camera(self.mapa.tamanho)
        self.jogador1 = Jogador1(*regras.SPAWN_JOGADOR_1, personagem=PERSONAGENS[chave_p1])
        self.jogador2 = Jogador2(*regras.SPAWN_JOGADOR_2, personagem=PERSONAGENS[chave_p2])

        # Os controles são da cena, não do jogador: o jogador só recebe
        # Comando e nem sabe que existe teclado.
        self.controles = {1: TECLADO_P1, 2: TECLADO_P2}
        self._disparos_pendentes: set[int] = set()

        self.balas: list[Projetil] = []
        self.itens: list[Item] = []

        self.pontos = {1: 0, 2: 0}

        # Segundos de recarga que faltam para cada jogador, por número.
        # Um dicionário em vez de um par gêmeo p1/p2 — o par é justamente o que
        # impede o jogo de ter um terceiro jogador.
        #
        # Conta tempo de jogo, e não relógio de parede: só desce quando a
        # partida é atualizada. Com o relógio de parede, qualquer pausa maior
        # que TEMPO_RECARGA devolvia munição cheia — inclusive pausar de
        # propósito para recarregar na hora.
        self.recarga_restante = {1: 0.0, 2: 0.0}

        self._transicao_pendente: Transicao | None = None

        # A cena é dona do modo de teste e o empurra para os jogadores, em vez
        # de todo mundo ler uma variável global de configuração.
        self.modo_de_teste = depuracao.MODO_DE_TESTE
        self._propagar_modo_de_teste()

        self._espalhar_itens()

    # ------------------------------------------------------------------ itens

    def _posicionar_item(self, tipo: str) -> None:
        """Sorteia uma posição livre para um item novo. Desiste em silêncio se
        não achar depois de ITEM_TENTATIVAS_SPAWN tentativas."""
        margem = regras.ITEM_MARGEM_SPAWN
        ocupados = [item.rect for item in self.itens]

        for _ in range(regras.ITEM_TENTATIVAS_SPAWN):
            candidato = Item(
                random.randint(margem, self.mapa.rect.width - margem - regras.ITEM_TAMANHO),
                random.randint(margem, self.mapa.rect.height - margem - regras.ITEM_TAMANHO),
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

    def _propagar_modo_de_teste(self) -> None:
        for jogador in (self.jogador1, self.jogador2):
            jogador.modo_de_teste = self.modo_de_teste

    # ---------------------------------------------------------------- eventos

    def processar_evento(self, evento: pygame.event.Event) -> Transicao | None:
        if (saida := super().processar_evento(evento)) is not None:
            return saida

        if evento.type != pygame.KEYDOWN:
            return None

        if evento.key == pygame.K_F1:
            self.modo_de_teste = not self.modo_de_teste
            self._propagar_modo_de_teste()
            return None

        # O tiro é por toque, não por tecla segurada: por isso ele nasce de um
        # KEYDOWN e fica pendente até o frame ser processado, em vez de sair de
        # pygame.key.get_pressed(), que dispararia em rajada.
        for jogador in (self.jogador1, self.jogador2):
            if evento.key == self.controles[jogador.numero].atirar:
                self._disparos_pendentes.add(jogador.numero)

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
            self.recarga_restante[atirador.numero] = regras.TEMPO_RECARGA

    # ----------------------------------------------------------------- regras

    def _resolver_bala(self, bala: Projetil) -> bool:
        """True se a bala deve ser removida neste frame."""
        if bala.passou_do_alcance:
            return True

        if not self.mapa.rect.collidepoint(int(bala.x), int(bala.y)):
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
            from .selecao import CenaSelecao  # importado aqui para evitar ciclo

            # SubstituirPilha e não Trocar: Trocar substituiria o próprio véu e
            # deixaria a partida viva embaixo dele.
            return SubstituirPilha(CenaSelecao())

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

    def _reiniciar_rodada(self) -> None:
        self.jogador1.renascer()
        self.jogador2.renascer()
        self.balas.clear()
        self._espalhar_itens()
        self.recarga_restante = {1: 0.0, 2: 0.0}
        self._disparos_pendentes.clear()

    # --------------------------------------------------------------- simulação

    def atualizar(self, dt: float) -> Transicao | None:
        if self._transicao_pendente is not None:
            transicao, self._transicao_pendente = self._transicao_pendente, None
            return transicao

        self._recarregar(dt)

        comandos = self._ler_comandos()
        self.jogador1.mover(comandos[1], self.mapa)
        self.jogador2.mover(comandos[2], self.mapa)

        if comandos[1].atirar:
            self._tentar_atirar(self.jogador1, self.jogador2, COR_BALA_P1)
        if comandos[2].atirar:
            self._tentar_atirar(self.jogador2, self.jogador1, COR_BALA_P2)

        self._coletar_itens()
        self._mover_balas()

        # Uma bala pode ter matado alguém e agendado a sobreposição.
        if self._transicao_pendente is not None:
            transicao, self._transicao_pendente = self._transicao_pendente, None
            return transicao
        return None

    def _ler_comandos(self) -> dict[int, Comando]:
        """Um comando por jogador para este frame. Consome os disparos pendentes."""
        teclas = pygame.key.get_pressed()
        comandos = {
            jogador.numero: self.controles[jogador.numero].ler(
                teclas, atirar=jogador.numero in self._disparos_pendentes
            )
            for jogador in (self.jogador1, self.jogador2)
        }
        self._disparos_pendentes.clear()
        return comandos

    def _recarregar(self, dt: float) -> None:
        for jogador in self._jogadores():
            if jogador.balas > 0:
                continue
            restante = self.recarga_restante[jogador.numero] - dt
            if restante <= 0:
                jogador.balas = regras.BALAS_MAXIMAS
                restante = 0.0
            self.recarga_restante[jogador.numero] = restante

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
        self._desenhar_mundo(self.camera.mundo)
        area = self.camera.apresentar(superficie)
        self._desenhar_hud(superficie, area)

    def _desenhar_mundo(self, mundo: pygame.Surface) -> None:
        """Tudo que vive em coordenadas de mapa.

        O chão e a água são o fundo. Vegetação, itens e jogadores são desenhados
        na ordem da base de cada um: quem pisa mais embaixo na tela aparece na
        frente. É o que faz a grama cobrir quem está atrás dela e ficar atrás de
        quem passa na frente — e, de brinde, faz os dois jogadores se
        sobreporem corretamente em vez de o P2 estar sempre por cima.

        As balas ficam fora da ordenação: elas voam, não pisam.
        """
        self.mapa.desenhar(mundo)

        # No modo de teste, quem está dentro do mato sai da ordenação: ele é
        # desenhado depois, junto com a janela que clareia a grama ao redor.
        com_janela = [j for j in self._jogadores() if self._tem_janela(j)]

        for desenhavel in self._por_profundidade():
            if desenhavel in com_janela:
                continue
            desenhavel.desenhar(mundo)

        for jogador in com_janela:
            self._clarear_vegetacao_ao_redor(mundo, jogador)
            jogador.desenhar(mundo)

        for bala in self.balas:
            bala.desenhar(mundo)

    def _jogadores(self):
        return (self.jogador1, self.jogador2)

    def _tem_janela(self, jogador) -> bool:
        return self.modo_de_teste and jogador.fracao_oculta > 0

    def _clarear_vegetacao_ao_redor(self, mundo: pygame.Surface, jogador) -> None:
        """Reduz a opacidade da vegetação numa janela em volta do jogador.

        Feito redesenhando o fundo por cima, translúcido: a grama daquela área
        some parcialmente e o chão reaparece por baixo. É o que permite enxergar
        para onde se está indo dentro do mato — sem isso, o modo de teste
        mostraria o jogador translúcido sobre um tapete opaco de folhagem.
        """
        raio = depuracao.RAIO_DA_JANELA
        passos = depuracao.PASSOS_DA_JANELA

        # A janela é montada em anéis concêntricos, cada um repintando o fundo
        # com uma fatia da opacidade. O efeito acumula em direção ao centro, o
        # que dá um esmaecimento gradual em vez de um retângulo de borda dura —
        # que na tela parecia defeito de renderização.
        alvo = 1.0 - depuracao.OPACIDADE_DA_GRAMA_NA_JANELA
        alfa_por_passo = round(255 * (1.0 - (1.0 - alvo) ** (1 / passos)))

        for k in range(passos):
            encolhimento = round(raio * k / passos)
            anel = jogador.hitbox_entidade.inflate(
                (raio - encolhimento) * 2, (raio - encolhimento) * 2
            ).clip(self.mapa.rect)
            if not anel.width or not anel.height:
                continue
            veu = self.mapa.imagem.subsurface(anel).copy()
            veu.set_alpha(alfa_por_passo)
            mundo.blit(veu, anel)

    def _por_profundidade(self):
        desenhaveis = [
            *self.mapa.faixas_de_vegetacao,
            *self.itens,
            self.jogador1,
            self.jogador2,
        ]
        return sorted(desenhaveis, key=lambda d: (d.profundidade, d.ordem_no_empate))

    def _desenhar_hud(self, superficie: pygame.Surface, area: pygame.Rect) -> None:
        """Desenhado depois da escala, em resolução cheia, para não borrar.

        Ancorado na área ocupada pelo mundo e não na janela, para o HUD ficar
        colado no campo de jogo mesmo quando sobram barras nas laterais.
        """
        self.jogador1.desenhar_hud(superficie, area.left + 10, area.top + 10)
        self.jogador2.desenhar_hud(superficie, area.right - 140, area.top + 10)

        texto = recursos.fonte(32, negrito=True).render(
            f"{self.pontos[1]}  X  {self.pontos[2]}", True, (255, 215, 0)
        )
        superficie.blit(texto, (area.centerx - texto.get_width() // 2, area.top + 10))
