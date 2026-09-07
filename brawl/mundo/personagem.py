"""Catálogo de personagens jogáveis.

Cada personagem é uma instância de `Personagem`, guardada em PERSONAGENS por
chave (ex: "shelly"). A chave existe SÓ como chave do dicionário — não é
repetida dentro do objeto, para não haver duas fontes da mesma informação
divergindo em silêncio.

Os stats hoje são iguais para todos: são valores padrão pensados para quando o
balanceamento por personagem for implementado. Até lá o gameplay pode assumir
que todo personagem tem o mesmo desempenho.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import gameplay as regras


@dataclass(frozen=True)
class Personagem:
    nome: str           # nome exibido na tela de seleção, ex: "Shelly"
    pasta_assets: str   # pasta em assets/ com os sprites deste personagem
    sprite_parado: str  # arquivo do sprite parado, ex: "shelly.png"

    # Stats — hoje iguais para todos, prontos para diferenciação futura
    vida_maxima: int = regras.VIDA_MAXIMA
    velocidade: int = regras.VELOCIDADE_BASE
    dano_base: int = regras.PROJETIL_DANO_BASE


PERSONAGENS: dict[str, Personagem] = {
    "shelly": Personagem(nome="Shelly", pasta_assets="shelly", sprite_parado="shelly.png"),
    "piper": Personagem(nome="Piper", pasta_assets="piper", sprite_parado="piper.png"),
    "colt": Personagem(nome="Colt", pasta_assets="colt", sprite_parado="colt.png"),
    "iyoda": Personagem(nome="Iyoda", pasta_assets="iyoda", sprite_parado="iyoda.png"),
}
