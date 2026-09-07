"""Cenas: a pilha, as transições e o fluxo entre telas."""

from __future__ import annotations

import pygame
import pytest

from brawl.cenas.abertura import CenaAbertura, _Etapa
from brawl.cenas.base import (
    Cena,
    Desempilhar,
    Empilhar,
    Sair,
    SubstituirPilha,
    Trocar,
)
from brawl.cenas.controles import CenaControles, nome_da_tecla
from brawl.cenas.menu import CenaMenu
from brawl.cenas.partida import CenaPartida
from brawl.cenas.selecao import CenaSelecao
from brawl.cenas.sobreposicao import CenaSobreposicao
from brawl.config import gameplay as regras

from .apoio import CenaBoba, avancar_frame, teclar


class TestPilha:
    """Pilha, e não só 'próxima cena', porque o fim de rodada precisa desenhar
    a partida congelada atrás do véu."""

    def test_empilhar_preserva_a_de_baixo(self, app):
        base, veu = CenaBoba("base"), CenaBoba("veu", transparente=True)
        app.pilha = [base]
        app._aplicar(Empilhar(veu))
        assert app.pilha == [base, veu]

    def test_cena_transparente_deixa_a_de_baixo_aparecer(self, app):
        base, veu = CenaBoba("base"), CenaBoba("veu", transparente=True)
        app.pilha = [base, veu]
        app._desenhar()
        assert (base.desenhos, veu.desenhos) == (1, 1)

    def test_cena_opaca_corta_o_desenho_de_baixo(self, app):
        base, topo = CenaBoba("base"), CenaBoba("topo")
        app.pilha = [base, topo]
        app._desenhar()
        assert (base.desenhos, topo.desenhos) == (0, 1)

    def test_trocar_substitui_so_o_topo(self, app):
        base, antiga, nova = CenaBoba("base"), CenaBoba("antiga"), CenaBoba("nova")
        app.pilha = [base, antiga]
        app._aplicar(Trocar(nova))
        assert app.pilha == [base, nova]

    def test_desempilhar_devolve_o_controle(self, app):
        base, veu = CenaBoba("base"), CenaBoba("veu")
        app.pilha = [base, veu]
        app._aplicar(Desempilhar())
        assert app.pilha == [base]

    def test_substituir_pilha_descarta_tudo(self, app):
        """`Trocar` só troca o topo. Para "voltar ao menu" pedido de dentro de
        uma sobreposição, é preciso descartar também o que está embaixo."""
        base, veu, nova = CenaBoba("base"), CenaBoba("veu"), CenaBoba("nova")
        app.pilha = [base, veu]
        app._aplicar(SubstituirPilha(nova))
        assert app.pilha == [nova]

    def test_substituir_pilha_com_um_so_elemento(self, app):
        base, nova = CenaBoba("base"), CenaBoba("nova")
        app.pilha = [base]
        app._aplicar(SubstituirPilha(nova))
        assert app.pilha == [nova]

    def test_substituir_pilha_nao_encerra_o_jogo(self, app):
        app.pilha = [CenaBoba()]
        assert app._aplicar(SubstituirPilha(CenaBoba("nova"))) is not False

    def test_sair_esvazia_e_encerra(self, app):
        app.pilha = [CenaBoba()]
        assert app._aplicar(Sair()) is False
        assert app.pilha == []

    def test_so_o_topo_e_atualizado(self, app):
        """É o que congela a partida sob o véu, sem nenhuma flag na partida."""
        partida = CenaPartida("shelly", "colt")
        app.pilha = [partida, CenaBoba("veu", transparente=True)]
        posicao = partida.jogador1.hitbox_entidade.midbottom
        for _ in range(10):
            avancar_frame(app)
        assert partida.jogador1.hitbox_entidade.midbottom == posicao


class TestCenaBase:
    def test_esc_encerra_por_padrao(self):
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        assert isinstance(Cena().processar_evento(evento), Sair)

    def test_outros_eventos_nao_transicionam(self):
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)
        assert Cena().processar_evento(evento) is None

    def test_fechar_a_janela_e_tratado_pelo_app(self, app):
        """Nenhuma cena precisa lembrar de tratar QUIT."""
        app.pilha = [CenaBoba()]
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        assert app._processar_eventos() is False


class TestAbertura:
    def test_comeca_no_fade(self, app):
        assert CenaAbertura().etapa is _Etapa.FADE

    def test_chega_sozinha_a_espera(self, app):
        abertura = CenaAbertura()
        app.pilha = [abertura]
        for _ in range(150):
            avancar_frame(app)
        assert abertura.etapa is _Etapa.ESPERA

    def test_espaco_pula_a_animacao(self, app):
        abertura = CenaAbertura()
        app.pilha = [abertura]
        avancar_frame(app)
        teclar(pygame.K_SPACE)
        avancar_frame(app)
        assert abertura.etapa is _Etapa.ESPERA

    def test_enter_leva_para_o_menu(self, app):
        abertura = CenaAbertura()
        app.pilha = [abertura]
        avancar_frame(app)
        teclar(pygame.K_SPACE)
        avancar_frame(app)
        teclar(pygame.K_RETURN)
        for _ in range(50):
            avancar_frame(app)
        assert isinstance(app.topo, CenaMenu)


class TestSelecao:
    def test_confirmar_os_dois_comeca_a_partida(self, app):
        app.pilha = [CenaSelecao()]
        teclar(pygame.K_SPACE)
        teclar(pygame.K_RETURN)
        for _ in range(45):
            avancar_frame(app)
        assert isinstance(app.topo, CenaPartida)

    def test_confirmar_so_um_nao_comeca(self, app):
        app.pilha = [CenaSelecao()]
        teclar(pygame.K_SPACE)
        for _ in range(45):
            avancar_frame(app)
        assert isinstance(app.topo, CenaSelecao)

    def test_as_setas_trocam_de_personagem(self, app):
        selecao = CenaSelecao()
        app.pilha = [selecao]
        indice = selecao.escolhas["P1"].indice
        teclar(pygame.K_d)
        avancar_frame(app)
        assert selecao.escolhas["P1"].indice != indice


class TestFimDeRodadaEDeJogo:
    def test_o_veu_de_rodada_devolve_para_a_partida(self, app):
        partida = CenaPartida("shelly", "colt")
        app.pilha = [partida]
        partida._pontuar(vencedor=1)
        avancar_frame(app)
        assert isinstance(app.topo, CenaSobreposicao)

        partida.jogador1.vida = 1
        teclar(pygame.K_SPACE)
        avancar_frame(app)
        assert app.topo is partida
        assert partida.jogador1.vida == partida.jogador1.personagem.vida_maxima

    def test_r_reinicia_o_campeonato(self, app):
        partida = CenaPartida("shelly", "colt")
        app.pilha = [partida]
        for _ in range(regras.PONTOS_PARA_VENCER_CAMPEONATO):
            partida._pontuar(vencedor=2)
        avancar_frame(app)
        teclar(pygame.K_r)
        avancar_frame(app)
        assert app.topo is partida
        assert partida.pontos == {1: 0, 2: 0}

    def test_t_volta_para_a_selecao_sem_empilhar_partida(self, app):
        """A tecla T instanciava um Game dentro do laço de eventos do anterior.

        Hoje o véu devolve SubstituirPilha, então a troca é imediata: um frame,
        e nem o véu nem a partida sobram na pilha.
        """
        partida = CenaPartida("shelly", "colt")
        app.pilha = [partida]
        for _ in range(regras.PONTOS_PARA_VENCER_CAMPEONATO):
            partida._pontuar(vencedor=1)
        avancar_frame(app)
        teclar(pygame.K_t)
        avancar_frame(app)
        assert isinstance(app.topo, CenaSelecao)
        assert len(app.pilha) == 1

    def test_o_veu_cobre_a_tela_inteira(self, app):
        partida = CenaPartida("shelly", "colt")
        app.pilha = [partida]
        partida._pontuar(vencedor=1)
        avancar_frame(app)
        avancar_frame(app)
        canto = app.superficie.get_at((5, app.superficie.get_height() // 2))[:3]
        assert canto != partida.camera.cor_das_barras


@pytest.mark.parametrize("construtor", [
    CenaAbertura,
    CenaSelecao,
    lambda: CenaPartida("shelly", "colt"),
])
def test_esc_encerra_de_qualquer_cena(app, construtor):
    app.pilha = [construtor()]
    teclar(pygame.K_ESCAPE)
    assert avancar_frame(app) is False


class TestMenu:
    """O menu principal, entre a abertura e a seleção."""

    def test_comeca_no_primeiro_item(self):
        assert CenaMenu().indice == 0

    @pytest.mark.parametrize("tecla_baixo", [pygame.K_s, pygame.K_DOWN])
    def test_desce_com_qualquer_dos_dois_teclados(self, tecla_baixo):
        """Quem está no teclado da direita também precisa conseguir navegar."""
        menu = CenaMenu()
        menu.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla_baixo))
        assert menu.indice == 1

    @pytest.mark.parametrize("tecla_cima", [pygame.K_w, pygame.K_UP])
    def test_sobe_com_qualquer_dos_dois_teclados(self, tecla_cima):
        menu = CenaMenu()
        menu.indice = 1
        menu.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla_cima))
        assert menu.indice == 0

    def test_a_selecao_da_a_volta(self):
        menu = CenaMenu()
        menu.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
        assert menu.indice == len(menu.opcoes) - 1
        menu.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
        assert menu.indice == 0

    @pytest.mark.parametrize("confirma", [pygame.K_SPACE, pygame.K_RETURN])
    def test_jogar_vai_para_a_selecao(self, app, confirma):
        menu = CenaMenu()
        menu.indice = 0
        transicao = menu.processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=confirma)
        )
        assert isinstance(transicao, Trocar)
        assert isinstance(transicao.cena, CenaSelecao)

    def test_controles_empilha_sem_perder_o_menu(self, app):
        menu = CenaMenu()
        menu.indice = 1
        transicao = menu.processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        )
        assert isinstance(transicao, Empilhar)
        assert isinstance(transicao.cena, CenaControles)

    def test_sair_encerra(self):
        menu = CenaMenu()
        menu.indice = 2
        transicao = menu.processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        )
        assert isinstance(transicao, Sair)

    def test_esc_encerra(self):
        transicao = CenaMenu().processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        assert isinstance(transicao, Sair)

    def test_o_fluxo_inteiro_do_menu_ate_a_partida(self, app):
        """Menu -> seleção -> partida, sem acumular cena na pilha."""
        app.pilha = [CenaMenu()]
        teclar(pygame.K_RETURN)          # JOGAR
        avancar_frame(app)
        assert isinstance(app.topo, CenaSelecao)

        teclar(pygame.K_SPACE)
        teclar(pygame.K_RETURN)
        for _ in range(45):
            avancar_frame(app)
        assert isinstance(app.topo, CenaPartida)
        assert len(app.pilha) == 1


class TestControles:
    """A tela de ajuda lê as teclas dos controles de verdade."""

    def test_e_transparente_e_o_menu_fica_atras(self, app):
        menu = CenaMenu()
        app.pilha = [menu, CenaControles()]
        app._desenhar()
        assert app.topo.transparente is True

    def test_qualquer_tecla_volta(self):
        transicao = CenaControles().processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j)
        )
        assert isinstance(transicao, Desempilhar)

    def test_esc_volta_em_vez_de_sair(self):
        """Aqui ESC não pode encerrar o jogo: ele é o botão de voltar."""
        transicao = CenaControles().processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        assert isinstance(transicao, Desempilhar)

    def test_volta_para_o_menu_pela_pilha(self, app):
        app.pilha = [CenaMenu(), CenaControles()]
        teclar(pygame.K_ESCAPE)
        avancar_frame(app)
        assert isinstance(app.topo, CenaMenu)
        assert len(app.pilha) == 1

    @pytest.mark.parametrize("codigo,esperado", [
        (pygame.K_w, "W"),
        (pygame.K_SPACE, "ESPAÇO"),
        (pygame.K_RETURN, "ENTER"),
        (pygame.K_UP, "CIMA"),
    ])
    def test_nomes_de_tecla_legiveis(self, codigo, esperado):
        assert nome_da_tecla(codigo) == esperado

    def test_as_teclas_exibidas_vem_do_controle(self):
        """Se a tela repetisse as teclas à mão, ela mentiria ao remapear."""
        from brawl.cenas.controles import LINHAS_DOS_JOGADORES
        from brawl.entrada import TECLADO_P1, TECLADO_P2

        pares = {(p1, p2) for _, p1, p2 in LINHAS_DOS_JOGADORES}
        assert (TECLADO_P1.atirar, TECLADO_P2.atirar) in pares
        assert (TECLADO_P1.cima, TECLADO_P2.cima) in pares


class TestCenaDeOpcoes:
    """A base compartilhada pelos menus, exercitada sem passar por nenhum deles."""

    @staticmethod
    def _cena(registro=None):
        from brawl.cenas.opcoes import CenaDeOpcoes, Opcao

        registro = registro if registro is not None else []

        class Falsa(CenaDeOpcoes):
            titulo = "TÍTULO"

            def __init__(self):
                super().__init__([
                    Opcao("UM", lambda: registro.append("um")),
                    Opcao("DOIS", lambda: registro.append("dois")),
                    Opcao("TRES", lambda: Sair()),
                ])

        return Falsa()

    @pytest.mark.parametrize("tecla,esperado", [
        (pygame.K_s, 1), (pygame.K_DOWN, 1),
        (pygame.K_w, 2), (pygame.K_UP, 2),   # sobe do 0 e dá a volta
    ])
    def test_navega_pelos_dois_teclados_e_da_a_volta(self, tecla, esperado):
        cena = self._cena()
        cena.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla))
        assert cena.indice == esperado

    @pytest.mark.parametrize("confirma", [pygame.K_SPACE, pygame.K_RETURN])
    def test_confirmar_executa_a_opcao_selecionada(self, confirma):
        registro = []
        cena = self._cena(registro)
        cena.indice = 1
        cena.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=confirma))
        assert registro == ["dois"]

    def test_a_acao_pode_devolver_uma_transicao(self):
        cena = self._cena()
        cena.indice = 2
        transicao = cena.processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        )
        assert isinstance(transicao, Sair)

    def test_esc_encerra_por_padrao(self):
        transicao = self._cena().processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        assert isinstance(transicao, Sair)

    def test_a_subclasse_pode_redefinir_o_esc(self):
        """É o gancho de que a pausa e a confirmação vão precisar."""
        cena = self._cena()
        cena._ao_cancelar = lambda: Desempilhar()
        transicao = cena.processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        assert isinstance(transicao, Desempilhar)

    def test_tecla_qualquer_nao_faz_nada(self):
        cena = self._cena()
        assert cena.processar_evento(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j)
        ) is None
        assert cena.indice == 0

    def test_desenha_titulo_e_opcoes(self):
        cena = self._cena()
        tela = pygame.Surface((1920, 1080))
        tela.fill((0, 0, 0))
        cena.desenhar(tela)
        assert pygame.transform.average_color(tela)[:3] != (0, 0, 0)
