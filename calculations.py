"""
Модуль расчётов для метода оценки качества ВОЛС
на основе сравнения «идеальной» и реальных СФМ.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class SFMData:
    """Данные одной СФМ (базовой или реальной)."""
    name: str
    goal: str
    date: str
    functions: List[str]
    ts_names: List[List[str]]
    param_names: List[str]
    param_units: List[str]
    values: np.ndarray          # shape (total_ts, 2*k) — чередование min/max
    total_budget: float
    budget_real: float
    eval_period: float
    period_real: float


@dataclass
class ComparisonResult:
    """Результат сравнения одной реальной СФМ с базовой."""
    real_name: str
    B_Q: np.ndarray
    B_Q1: np.ndarray
    B_Q2: np.ndarray
    R_Q: np.ndarray
    R_Q1: np.ndarray
    R_Q2: np.ndarray
    C_Q1: np.ndarray
    C_Q2: np.ndarray
    C_Q: np.ndarray
    has_negative: bool
    negative_positions: List[Tuple[int, int]]
    q_weights: np.ndarray
    weighted_table: np.ndarray
    Q_ke: float
    budget_ok: bool
    period_ok: bool


@dataclass
class RatingEntry:
    index: int
    name: str
    Q_ke: float
    place: int


def build_BQ(base: SFMData) -> np.ndarray:
    """Из таблицы базовой СФМ собрать матрицу B_Q.

    values имеет форму (m_total_ts, 2*k), где столбцы чередуются:
    [Q_1_min, Q_1_max, Q_2_min, Q_2_max, ..., Q_k_min, Q_k_max]
    """
    return base.values.copy()


def split_BQ(B_Q: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Разбить B_Q на B_Q1 (min-группа) и B_Q2 (max-группа).

    B_Q1: столбцы min (0, 2, 4, ...) сохраняются, столбцы max (1, 3, 5, ...) сохраняются,
          но значения в столбцах min обнуляются (лучшее = минимум -> базовое = 0).
    B_Q2: аналогично, но обнуляются столбцы max.

    По методичке:
    - B_Q1 (первая группа, лучшее = min): нечётные позиции (min) обнуляются
    - B_Q2 (вторая группа, лучшее = max): чётные позиции (max) обнуляются
    """
    m, n = B_Q.shape
    B_Q1 = B_Q.copy()
    B_Q2 = B_Q.copy()

    for col in range(0, n, 2):
        B_Q1[:, col] = 0       # min-столбцы -> 0 в B_Q1
    for col in range(1, n, 2):
        B_Q2[:, col] = 0       # max-столбцы -> 0 в B_Q2

    return B_Q1, B_Q2


def build_RQ(real: SFMData) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Построить R_Q, R_Q1, R_Q2 для реальной СФМ."""
    R_Q = real.values.copy()
    R_Q1, R_Q2 = split_RQ(R_Q)
    return R_Q, R_Q1, R_Q2


def split_RQ(R_Q: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Аналогично split_BQ, но для реальной СФМ."""
    m, n = R_Q.shape
    R_Q1 = R_Q.copy()
    R_Q2 = R_Q.copy()

    for col in range(0, n, 2):
        R_Q1[:, col] = 0
    for col in range(1, n, 2):
        R_Q2[:, col] = 0

    return R_Q1, R_Q2


def compute_CQ(
    B_Q1: np.ndarray, B_Q2: np.ndarray,
    R_Q1: np.ndarray, R_Q2: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool, List[Tuple[int, int]]]:
    """
    C_Q1 = B_Q1 - R_Q1  (для min-группы: чем меньше реальное, тем лучше)
    C_Q2 = R_Q2 - B_Q2  (для max-группы: чем больше реальное, тем лучше)
    C_Q  = C_Q1 + C_Q2
    """
    C_Q1 = B_Q1 - R_Q1
    C_Q2 = R_Q2 - B_Q2
    C_Q = C_Q1 + C_Q2

    negative_positions = []
    has_negative = False

    for i in range(C_Q1.shape[0]):
        for j in range(C_Q1.shape[1]):
            if C_Q1[i, j] < 0:
                has_negative = True
                negative_positions.append((i, j))

    for i in range(C_Q2.shape[0]):
        for j in range(C_Q2.shape[1]):
            if C_Q2[i, j] < 0:
                has_negative = True
                negative_positions.append((i, j))

    return C_Q1, C_Q2, C_Q, has_negative, negative_positions


def compute_weights(m: int, n: int) -> np.ndarray:
    """Нормированные весовые коэффициенты q_l.

    q_l = (m*n - l + 1) / S_mn
    S_mn = m*n * (m*n + 1) / 2

    l нумеруется от 1 до m*n (по строкам таблицы, слева направо, сверху вниз).
    Возвращает 1D массив длины m*n.
    """
    total = m * n
    S_mn = total * (total + 1) / 2
    q = np.array([(total - l + 1) / S_mn for l in range(1, total + 1)])
    return q


def compute_Qke(C_Q: np.ndarray, q_weights: np.ndarray) -> Tuple[np.ndarray, float]:
    """Комплексный показатель качества Q_кэ.

    Таблица произведений q_l * ΔQ_l,
    затем сумма всех элементов = Q_кэ.
    """
    flat_CQ = C_Q.flatten()
    min_len = min(len(flat_CQ), len(q_weights))
    flat_CQ = flat_CQ[:min_len]
    q = q_weights[:min_len]

    products = q * flat_CQ
    weighted_table = products.reshape(C_Q.shape) if min_len == C_Q.size else products.reshape(-1)
    Q_ke = float(np.sum(products))
    return weighted_table, Q_ke


def build_rating(results: List[Tuple[int, str, float]]) -> List[RatingEntry]:
    """Построить рейтинг по убыванию Q_кэ с учётом равных мест.

    results: [(index, name, Q_ke), ...]
    """
    sorted_results = sorted(results, key=lambda x: -x[2])
    rating = []
    place = 1
    for i, (idx, name, qke) in enumerate(sorted_results):
        if i > 0 and abs(qke - sorted_results[i - 1][2]) < 1e-9:
            rating.append(RatingEntry(idx, name, qke, rating[-1].place))
        else:
            rating.append(RatingEntry(idx, name, qke, place))
        place += 1
    return rating


def run_full_analysis(
    base: SFMData,
    reals: List[SFMData],
) -> Tuple[List[ComparisonResult], List[RatingEntry], np.ndarray]:
    """Полный цикл анализа: базовая СФМ vs все реальные.

    Возвращает:
    - список ComparisonResult для каждой реальной СФМ
    - рейтинг
    - матрицу весов q_l
    """
    B_Q = build_BQ(base)
    B_Q1, B_Q2 = split_BQ(B_Q)

    m_rows, n_cols = B_Q.shape
    q_weights = compute_weights(m_rows, n_cols)

    comparisons = []
    rating_input = []

    for i, real in enumerate(reals):
        R_Q, R_Q1, R_Q2 = build_RQ(real)
        C_Q1, C_Q2, C_Q, has_neg, neg_pos = compute_CQ(B_Q1, B_Q2, R_Q1, R_Q2)
        weighted_table, Q_ke = compute_Qke(C_Q, q_weights)

        budget_ok = real.budget_real <= base.total_budget
        period_ok = real.period_real >= base.eval_period

        comp = ComparisonResult(
            real_name=real.name,
            B_Q=B_Q, B_Q1=B_Q1, B_Q2=B_Q2,
            R_Q=R_Q, R_Q1=R_Q1, R_Q2=R_Q2,
            C_Q1=C_Q1, C_Q2=C_Q2, C_Q=C_Q,
            has_negative=has_neg,
            negative_positions=neg_pos,
            q_weights=q_weights.reshape(C_Q.shape) if len(q_weights) == C_Q.size else q_weights,
            weighted_table=weighted_table.reshape(C_Q.shape) if weighted_table.size == C_Q.size else weighted_table,
            Q_ke=Q_ke,
            budget_ok=budget_ok,
            period_ok=period_ok,
        )
        comparisons.append(comp)

        if not has_neg and budget_ok and period_ok:
            rating_input.append((i + 1, real.name, Q_ke))

    rating = build_rating(rating_input)

    return comparisons, rating, q_weights
