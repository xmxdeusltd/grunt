from typing import Type
from ..base import BaseStrategy
from .ma_crossover import MACrossoverStrategy


def get_strategy_class(strategy_type: str) -> Type[BaseStrategy]:
    """Get strategy class based on strategy type"""
    strategy_map = {
        "ma_crossover": MACrossoverStrategy,
    }

    if strategy_type not in strategy_map:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    return strategy_map[strategy_type]


__all__ = [
    'get_strategy_class',
    'MACrossoverStrategy'
]
