"""Pequenos efeitos de animação usados pelas telas."""

from __future__ import annotations

import math


def escala_de_respiracao(tempo: float, amplitude: float, velocidade: float = 1.0,
                         base: float = 1.0) -> float:
    """Fator de escala que sobe e desce suavemente, para uma imagem 'respirar'."""
    return base + math.sin(tempo * velocidade) * amplitude


def deve_desenhar_piscando(contador: int, intervalo: int) -> bool:
    """Alterna entre True e False a cada `intervalo` frames."""
    return (contador // intervalo) % 2 == 0
