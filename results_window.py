"""
Обёртка обратной совместимости.
Результаты теперь отображаются встроенно в главном окне (страницы 3-4).
Этот модуль сохранён для совместимости импортов.
"""

from calculations import SFMData, ComparisonResult, RatingEntry
from typing import List
import numpy as np


class ResultsWindow:
    """Заглушка — результаты показываются в главном окне."""
    def __init__(self, base=None, reals=None, comparisons=None, rating=None, q_weights=None, parent=None):
        pass

    def show(self):
        pass
