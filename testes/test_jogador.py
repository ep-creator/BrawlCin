"""Jogador: hitboxes, movimento, colisão e ocultação."""

from __future__ import annotations

import math

import pygame
import pytest

from brawl.config import depuracao
from brawl.config import gameplay as regras
from brawl.entrada import Comando, normalizar
from brawl.mundo.jogador import Jogador1, Jogador2

from .apoio import MapaFalso


def andar(jogador, dx, dy, mapa, frames=30):
    """Anda `frames` frames numa direção e devolve a distância percorrida."""
    origem = jogador.hitbox_entidade.midbottom
    comando = Comando(*normalizar(dx, dy))
    for _ in range(frames):
        jogador.mover(comando, mapa)
    destino = jogador.hitbox_entidade.midbottom
    return math.hypot(destino[0] - origem[0], destino[1] - origem[1])


class TestHitboxes:
    """Trava o bug da hitbox de largura negativa.

    O tamanho vinha de um ajuste RELATIVO ao sprite: inflate(-53, -30) sobre um
    sprite de 40x60 dava 40 - 53 = -13 de largura. O jogo só funcionava porque o
    pygame normaliza retângulos negativos por baixo dos panos, e a hitbox
    efetiva virava 13x30 — 13 px para um personagem desenhado com 40.
    """

    def test_o_corpo_tem_tamanho_positivo(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        assert jogador.hitbox_entidade.width > 0
        assert jogador.hitbox_entidade.height > 0

    def test_os_pes_tem_tamanho_positivo(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        assert jogador.hitbox_mapa.width > 0
        assert jogador.hitbox_mapa.height > 0

    def test_a_area_do_corpo_e_positiva(self, personagem):
        """A área negativa era o que quebrava a regra dos arbustos."""
        jogador = Jogador1(300, 400, personagem)
        assert jogador.hitbox_entidade.width * jogador.hitbox_entidade.height > 0

    def test_o_corpo_nao_e_absurdamente_estreito_para_o_sprite(self, personagem):
        """Guarda contra uma futura troca de escala de sprite reintroduzir o bug."""
        jogador = Jogador1(300, 400, personagem)
        assert jogador.hitbox_entidade.width >= jogador.rect.width / 3

    def test_os_pes_passam_por_um_vao_de_um_tile(self, personagem):
        """Com tiles de 20 px, pés mais largos que isso travariam corredores."""
        jogador = Jogador1(300, 400, personagem)
        assert jogador.hitbox_mapa.width < 20

    def test_tudo_ancorado_nos_pes(self, personagem):
        """Corpo, faixa de mapa e sprite compartilham a mesma base.

        Antes a faixa de colisão pendurava no centro do sprite e ficava 15 px
        acima do chão.
        """
        jogador = Jogador1(300, 400, personagem)
        assert jogador.hitbox_entidade.midbottom == jogador.hitbox_mapa.midbottom
        assert jogador.hitbox_entidade.midbottom == jogador.rect.midbottom

    def test_nasce_exatamente_na_posicao_pedida(self, personagem):
        assert Jogador1(300, 400, personagem).hitbox_entidade.midbottom == (300, 400)


class TestMovimento:
    def test_diagonal_cobre_a_mesma_distancia_dos_eixos(self, personagem):
        """O bug marcado como URGENTE no INSTRUCTIONS original.

        Medido antes do conserto: 60,0 px na horizontal contra 84,9 px na
        diagonal — exatamente raiz(2). A folga de 1 px aqui é arredondamento de
        subpixel, não erro de direção.
        """
        mapa = MapaFalso()
        horizontal = andar(Jogador1(300, 300, personagem), 1, 0, mapa)
        vertical = andar(Jogador1(300, 300, personagem), 0, 1, mapa)
        diagonal = andar(Jogador1(300, 300, personagem), 1, 1, mapa)

        assert horizontal == pytest.approx(vertical, abs=1)
        assert diagonal == pytest.approx(horizontal, abs=1)

    def test_distancia_bate_com_a_velocidade_configurada(self, personagem):
        distancia = andar(Jogador1(300, 300, personagem), 1, 0, MapaFalso(), frames=30)
        assert distancia == pytest.approx(30 * regras.VELOCIDADE_BASE, abs=1)

    def test_subpixel_acumula_em_vez_de_truncar(self, personagem):
        """Sem posição em float, a diagonal seria pior que o bug original.

        pygame.Rect só guarda inteiro. Com velocidade 2, cada eixo da diagonal
        anda 1,41 px por frame; truncado a cada frame viraria 1 px, e a diagonal
        ficaria mais LENTA que os eixos.
        """
        jogador = Jogador1(300, 300, personagem)
        x_inicial = jogador.hitbox_entidade.x
        comando = Comando(*normalizar(1, 1))
        for _ in range(10):
            jogador.mover(comando, MapaFalso())
        andado = jogador.hitbox_entidade.x - x_inicial
        esperado = 10 * regras.VELOCIDADE_BASE * math.sqrt(2) / 2
        assert andado == pytest.approx(esperado, abs=1)

    def test_bonus_de_velocidade_acelera(self, personagem):
        mapa = MapaFalso()
        normal = andar(Jogador1(300, 300, personagem), 1, 0, mapa)
        rapido = Jogador1(300, 300, personagem)
        rapido.bonus_velocidade = 2
        assert andar(rapido, 1, 0, mapa) > normal

    def test_parede_bloqueia(self, personagem):
        mapa = MapaFalso(paredes=[pygame.Rect(320, 0, 200, 800)])
        jogador = Jogador1(300, 400, personagem)
        andar(jogador, 1, 0, mapa, frames=60)
        assert jogador.hitbox_mapa.right <= 320

    def test_agua_bloqueia(self, personagem):
        mapa = MapaFalso(aguas=[pygame.Rect(320, 0, 200, 800)])
        jogador = Jogador1(300, 400, personagem)
        andar(jogador, 1, 0, mapa, frames=60)
        assert jogador.hitbox_mapa.right <= 320

    def test_desliza_rente_a_parede(self, personagem):
        """Colisão resolvida eixo a eixo: bater na horizontal não trava o vertical."""
        mapa = MapaFalso(paredes=[pygame.Rect(320, 0, 200, 800)])
        jogador = Jogador1(300, 400, personagem)
        y_inicial = jogador.hitbox_entidade.y
        andar(jogador, 1, 1, mapa, frames=40)
        assert jogador.hitbox_mapa.right <= 320       # barrado na horizontal
        assert jogador.hitbox_entidade.y > y_inicial  # mas desceu

    def test_arbusto_nao_bloqueia(self, personagem):
        """Vegetação só esconde."""
        mapa = MapaFalso(arbustos=[pygame.Rect(320, 0, 200, 800)])
        jogador = Jogador1(300, 400, personagem)
        assert andar(jogador, 1, 0, mapa, frames=60) > 0


class TestBordaDoMapa:
    """A borda do mapa bloqueia como parede.

    O mapa antigo tinha um cinturão de nove paredes desenhadas à mão só para
    isso. Como regra do código, mapa nenhum precisa desenhar a moldura — o que
    torna jogável o mapa novo, que não tem nada sólido.
    """

    @pytest.mark.parametrize("dx,dy", [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1)])
    def test_nao_da_para_sair_do_mapa(self, personagem, dx, dy):
        mapa = MapaFalso(tamanho=(960, 540))
        jogador = Jogador1(480, 270, personagem)
        andar(jogador, dx, dy, mapa, frames=400)
        assert mapa.rect.contains(jogador.hitbox_mapa)


class TestOcultacao:
    """A regra dos 50% de cobertura pela vegetação.

    Ela existia no código mas não funcionava: a área do jogador era calculada
    como largura * altura, e a largura era -13. A comparação virava
    `area >= -195`, que qualquer sobreposição satisfaz — um arbusto cobrindo 8%
    do jogador já o deixava invisível.
    """

    @staticmethod
    def _cobrir(jogador, fracao):
        corpo = jogador.hitbox_entidade
        largura = max(1, round(corpo.width * fracao))
        return pygame.Rect(corpo.left, corpo.top, largura, corpo.height)

    @pytest.mark.parametrize("fracao,escondido", [
        (0.08, False), (0.25, False), (0.45, False),
        (0.55, True), (0.80, True), (1.00, True),
    ])
    def test_esconde_a_partir_da_fracao_configurada(self, personagem, fracao, escondido):
        jogador = Jogador1(300, 400, personagem)
        mapa = MapaFalso(arbustos=[self._cobrir(jogador, fracao)])
        jogador._atualizar_ocultacao(mapa)
        assert jogador.escondido is escondido

    def test_sem_arbusto_nao_esconde(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        jogador._atualizar_ocultacao(MapaFalso())
        assert jogador.escondido is False

    def test_escondido_nao_desenha(self, personagem):
        """Ficar escondido é o que tira o sprite da tela.

        A superfície é justa de propósito: numa tela grande o sprite ocuparia
        0,5% da área e a cor média arredondaria para preto nos dois casos,
        fazendo o teste passar sem testar nada.
        """
        jogador = Jogador1(50, 110, personagem)
        jogador.modo_de_teste = False   # no modo de teste ele nunca some de vez
        tela = pygame.Surface((100, 120))

        tela.fill((0, 0, 0))
        jogador.fracao_oculta = 0.0
        jogador.desenhar(tela)
        visivel = pygame.transform.average_color(tela)

        tela.fill((0, 0, 0))
        jogador.fracao_oculta = 1.0
        jogador.desenhar(tela)
        oculto = pygame.transform.average_color(tela)

        assert visivel[:3] != (0, 0, 0)
        assert oculto[:3] == (0, 0, 0)


class TestVidaERenascimento:
    def test_dano_reduz_a_vida(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        vida = jogador.vida
        assert jogador.receber_dano(2) is False
        assert jogador.vida == vida - 2

    def test_dano_letal_avisa(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        assert jogador.receber_dano(jogador.vida) is True

    def test_renascer_restaura_tudo(self, personagem):
        jogador = Jogador1(*regras.SPAWN_JOGADOR_1, personagem=personagem)
        jogador.vida = 1
        jogador.balas = 0
        jogador.bonus_dano = 2
        jogador.bonus_velocidade = 3
        andar(jogador, 1, 0, MapaFalso(), frames=50)

        jogador.renascer()

        assert jogador.vida == personagem.vida_maxima
        assert jogador.balas == regras.BALAS_MAXIMAS
        assert jogador.bonus_dano == 0
        assert jogador.bonus_velocidade == 0
        assert jogador.hitbox_entidade.midbottom == tuple(regras.SPAWN_JOGADOR_1)

    def test_renascer_preserva_a_ancoragem(self, personagem):
        jogador = Jogador1(*regras.SPAWN_JOGADOR_1, personagem=personagem)
        andar(jogador, 1, 1, MapaFalso(), frames=30)
        jogador.renascer()
        assert jogador.hitbox_entidade.midbottom == jogador.rect.midbottom
        assert jogador.hitbox_entidade.midbottom == jogador.hitbox_mapa.midbottom


class TestIdentidadeDosJogadores:
    def test_numeros_e_lados_do_hud_sao_distintos(self, personagem):
        p1 = Jogador1(0, 0, personagem)
        p2 = Jogador2(0, 0, personagem)
        assert (p1.numero, p2.numero) == (1, 2)
        assert p1.direcao_hud == -p2.direcao_hud
        assert p1.cor != p2.cor

    def test_jogador_nao_sabe_o_que_e_teclado(self, personagem):
        """O acoplamento que o refactor da entrada removeu."""
        jogador = Jogador1(0, 0, personagem)
        assert not hasattr(jogador, "controles")


class TestCoberturaSomada:
    """A cobertura soma as áreas de vegetação, em vez de olhar uma a uma.

    Antes bastava um único arbusto passar de 50%: quem estivesse na junção de
    dois, com 30% em cada, ficava visível apesar de 60% coberto. As áreas vêm
    da fusão de tiles e não se sobrepõem, então somar é exato.
    """

    def test_dois_arbustos_parciais_somam(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        corpo = jogador.hitbox_entidade
        terco = corpo.width // 3
        esquerda = pygame.Rect(corpo.left, corpo.top, terco, corpo.height)
        direita = pygame.Rect(corpo.right - terco, corpo.top, terco, corpo.height)

        jogador._atualizar_ocultacao(MapaFalso(arbustos=[esquerda]))
        assert not jogador.escondido

        jogador._atualizar_ocultacao(MapaFalso(arbustos=[esquerda, direita]))
        assert jogador.fracao_oculta == pytest.approx(2 / 3, abs=0.05)
        assert jogador.escondido

    def test_a_fracao_nunca_passa_de_um(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        enorme = pygame.Rect(0, 0, 5000, 5000)
        jogador._atualizar_ocultacao(MapaFalso(arbustos=[enorme, enorme]))
        assert jogador.fracao_oculta == 1.0


class TestOpacidadeNoModoDeTeste:
    """No modo de teste o jogador não some: fica translúcido."""

    @pytest.mark.parametrize("fracao,opacidade", [
        (0.0, 1.0), (0.25, 1.0), (0.49, 1.0),   # antes do limite, cheio
        (0.5, 1.0),                              # no limite, começa a cair
    ])
    def test_fora_da_grama_fica_opaco(self, personagem, fracao, opacidade):
        jogador = Jogador1(300, 400, personagem)
        jogador.fracao_oculta = fracao
        assert jogador.opacidade == pytest.approx(opacidade)

    def test_cai_gradualmente_depois_do_limite(self, personagem):
        jogador = Jogador1(300, 400, personagem)
        anteriores = []
        for fracao in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            jogador.fracao_oculta = fracao
            anteriores.append(jogador.opacidade)
        assert anteriores == sorted(anteriores, reverse=True)
        assert anteriores[0] == pytest.approx(1.0)

    def test_nunca_chega_a_zero(self, personagem):
        """O objetivo do modo de teste é ver o que está acontecendo."""
        jogador = Jogador1(300, 400, personagem)
        jogador.fracao_oculta = 1.0
        assert jogador.opacidade == pytest.approx(depuracao.OPACIDADE_MINIMA_DO_JOGADOR)
        assert jogador.opacidade > 0

    def test_desenha_retangulos_e_nao_sprite(self, personagem):
        """O corpo vira um bloco cheio da cor do jogador."""
        jogador = Jogador1(50, 110, personagem)
        jogador.modo_de_teste = True
        jogador.fracao_oculta = 0.0
        tela = pygame.Surface((100, 120))
        tela.fill((0, 0, 0))
        jogador.desenhar(tela)
        assert tela.get_at(jogador.hitbox_entidade.center)[:3] == jogador.cor

    def test_translucido_dentro_da_grama(self, personagem):
        jogador = Jogador1(50, 110, personagem)
        jogador.modo_de_teste = True
        tela = pygame.Surface((100, 120))

        tela.fill((0, 0, 0))
        jogador.fracao_oculta = 0.0
        jogador.desenhar(tela)
        cheio = tela.get_at(jogador.hitbox_entidade.center)[:3]

        tela.fill((0, 0, 0))
        jogador.fracao_oculta = 1.0
        jogador.desenhar(tela)
        apagado = tela.get_at(jogador.hitbox_entidade.center)[:3]

        assert apagado != cheio
        assert apagado != (0, 0, 0)      # ainda visível
        assert sum(apagado) < sum(cheio)  # mas mais fraco
