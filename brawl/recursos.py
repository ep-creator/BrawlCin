"""Acesso a arquivos de assets: uma âncora de caminho e um cache.

Motivo de existir
-----------------
Antes deste módulo o projeto tinha três convenções de caminho ao mesmo tempo:

    entidades/players.py   BASE_DIR do próprio arquivo  -> entidades/assets/  (não existe)
    telas/tela_selecao.py  BASE_DIR do próprio arquivo  -> telas/assets/      (não existe)
    core/mapa.py           caminho relativo ao CWD      -> depende de onde rodou

E as fontes eram construídas dentro do `draw()`: cerca de onze
`pygame.font.SysFont` alocados por frame.

Aqui a raiz do projeto é resolvida uma única vez, a partir da localização
deste arquivo, e todo carregamento é memorizado. Carregar a mesma imagem no
mesmo tamanho duas vezes devolve o mesmo objeto.

Cuidado com o cache
-------------------
`imagem()` devolve a superfície compartilhada. Quem for **modificar** a
superfície (`set_alpha`, `fill`, blit por cima) precisa pedir `copia=True`,
senão a alteração vaza para todos os outros usuários daquela imagem.
"""

from __future__ import annotations

from pathlib import Path

import pygame

# brawl/recursos.py -> brawl/ -> raiz do projeto
RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"

FONTE_DO_JOGO = "LilitaOne-Regular.ttf"

_imagens: dict[tuple, pygame.Surface] = {}
_fontes: dict[tuple, pygame.font.Font] = {}


def caminho(*partes: str) -> Path:
    """Caminho absoluto de um asset. `caminho("shelly", "L1.png")`."""
    return ASSETS.joinpath(*partes)


def imagem(
    *partes: str,
    tamanho: tuple[int, int] | None = None,
    alpha: bool = True,
    copia: bool = False,
) -> pygame.Surface:
    """Carrega (uma vez) uma imagem de `assets/` e devolve a superfície.

    Levanta FileNotFoundError se o arquivo não existir — um asset obrigatório
    ausente é erro de programação, não algo para descobrir por um quadrado
    preto na tela. Para assets opcionais, use `imagem_opcional`.
    """
    chave = (partes, tamanho, alpha)

    if chave not in _imagens:
        arquivo = caminho(*partes)
        if not arquivo.exists():
            raise FileNotFoundError(f"Asset não encontrado: {arquivo}")

        superficie = pygame.image.load(arquivo)
        superficie = superficie.convert_alpha() if alpha else superficie.convert()

        if tamanho is not None:
            superficie = pygame.transform.scale(superficie, tamanho)

        _imagens[chave] = superficie

    return _imagens[chave].copy() if copia else _imagens[chave]


def imagem_opcional(
    *partes: str,
    tamanho: tuple[int, int] | None = None,
    alpha: bool = True,
    copia: bool = False,
) -> pygame.Surface | None:
    """Como `imagem`, mas devolve None (com aviso) se o arquivo não existir.

    Para elementos decorativos cuja ausência não impede o jogo de rodar.
    """
    if not caminho(*partes).exists():
        print(f"Aviso: asset opcional ausente -> {caminho(*partes)}")
        return None
    return imagem(*partes, tamanho=tamanho, alpha=alpha, copia=copia)


def fonte(tamanho: int, negrito: bool = False) -> pygame.font.Font:
    """Fonte do sistema, memorizada. Use para HUD e textos utilitários."""
    chave = ("sistema", tamanho, negrito)
    if chave not in _fontes:
        _fontes[chave] = pygame.font.SysFont(None, tamanho, bold=negrito)
    return _fontes[chave]


def fonte_do_jogo(tamanho: int) -> pygame.font.Font:
    """Fonte de identidade do jogo (LilitaOne), memorizada.

    Cai para a fonte do sistema se o arquivo .ttf não estiver presente.
    """
    chave = ("jogo", tamanho)
    if chave not in _fontes:
        arquivo = caminho(FONTE_DO_JOGO)
        if arquivo.exists():
            _fontes[chave] = pygame.font.Font(arquivo, tamanho)
        else:
            _fontes[chave] = pygame.font.SysFont("Arial", tamanho, bold=True)
    return _fontes[chave]


def limpar_cache() -> None:
    """Descarta tudo. Necessário se o display for reinicializado, porque as
    superfícies convertidas ficam presas ao formato de pixel do display antigo."""
    _imagens.clear()
    _fontes.clear()
