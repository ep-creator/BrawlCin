"""A interface de cena e as transições entre cenas.

Antes deste módulo o jogo tinha três laços principais independentes — um em
`tela_inicial`, um em `tela_selecao` e um em `Game.run` — cada um com a sua
cópia de `for evento in pygame.event.get()`, `display.flip()` e `clock.tick()`.
A transição entre eles era feita por valor de retorno, e trocar de personagem
instanciava um `Game` dentro do laço de eventos do `Game` anterior.

Agora existe um laço só (`brawl.app.App`) e as telas são cenas: objetos que
sabem responder a um evento, avançar um frame e se desenhar, e que pedem
transições em vez de chamar umas às outras.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame


class Cena:
    """Uma tela do jogo.

    Os três métodos devolvem uma `Transicao` para pedir mudança de cena, ou
    None para continuar onde estão. Nenhuma cena chama `display.flip()`,
    `clock.tick()` nem `pygame.event.get()` — isso é do App.
    """

    #: Cena transparente é desenhada por cima da de baixo, que continua visível
    #: (é assim que o fim de rodada mostra a partida congelada atrás do véu).
    transparente: bool = False

    def processar_evento(self, evento: pygame.event.Event) -> "Transicao | None":
        """Por padrão, ESC sai do jogo. Sobrescreva chamando super() primeiro."""
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            return Sair()
        return None

    def atualizar(self, dt: float) -> "Transicao | None":
        """Avança um frame. `dt` é o tempo desde o frame anterior, em segundos."""
        return None

    def desenhar(self, superficie: pygame.Surface) -> None:
        raise NotImplementedError


# --------------------------------------------------------------- transições


@dataclass(frozen=True)
class Empilhar:
    """Põe uma cena por cima. A de baixo continua na pilha, congelada."""

    cena: Cena


@dataclass(frozen=True)
class Trocar:
    """Substitui a cena do topo. A anterior é descartada."""

    cena: Cena


@dataclass(frozen=True)
class Desempilhar:
    """Remove a cena do topo e devolve o controle para a de baixo."""


@dataclass(frozen=True)
class Sair:
    """Encerra o jogo."""


Transicao = Empilhar | Trocar | Desempilhar | Sair
