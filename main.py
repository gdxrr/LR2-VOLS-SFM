"""
Компьютерное структурно-функциональное моделирование ВОЛС и оценка качества.
Светлый интерфейс с боковой навигацией (PyQt5).
"""

import os
import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QLineEdit, QSpinBox,
    QScrollArea, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QInputDialog, QSizePolicy, QListWidget,
    QListWidgetItem, QDoubleSpinBox, QGridLayout, QAbstractItemView,
    QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem, QGraphicsPathItem,
    QGraphicsEllipseItem, QGraphicsOpacityEffect,
)
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF, pyqtSignal, QEvent, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QIcon, QFontDatabase,
    QPainter, QPen, QBrush, QPainterPath,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from calculations import SFMData, run_full_analysis
from io_utils import load_sfm_csv, load_sfm_xlsx, save_sfm_csv, save_sfm_xlsx

# ─── Цвета (светлая тема) ───
BG      = "#f2f3f7"
PANEL   = "#e6e8ef"
CARD    = "#ffffff"
ACCENT  = "#5b4cdb"
ACCENT2 = "#2a9d8f"
TEXT    = "#1a1d26"
SUB     = "#5c6370"
OK_CLR  = "#1b9e3e"
ERR_CLR = "#d32f2f"
WARN    = "#c77d0a"
ENTRY   = "#ffffff"
BORDER  = "#c5c9d4"

# Размеры интерфейса (крупнее — легче читать)
UI_FONT_PT = 14
UI_FONT_SMALL = 12
UI_ROW_H = 36
UI_NAV_W = 260

# Семейство шрифта после addApplicationFont (см. _load_phosphor в main())
PHOSPHOR_FAMILY = None

# Phosphor Icons regular (@phosphor-icons/web 2.1.2), коды из style.css
PH_GEAR = "\ue270"
PH_CLIPBOARD = "\ue198"
PH_FOLDERS = "\ue260"
PH_CHART_BAR = "\ue150"
PH_CHART_LINE_UP = "\ue156"
PH_FLOPPY = "\ue248"
PH_FOLDER_OPEN = "\ue256"
PH_PLUS = "\ue3d4"
PH_MINUS = "\ue35a"
PH_CHECK = "\ue182"
PH_X = "\ue4f6"
PH_TABLE = "\ue476"
PH_CARET_RIGHT = "\ue13a"
PH_NUM_1 = "\ue36a"
PH_NUM_2 = "\ue382"
PH_NUM_3 = "\ue37c"


def _load_phosphor():
    global PHOSPHOR_FAMILY
    root = os.path.dirname(os.path.abspath(__file__))
    ttf = os.path.join(root, "Phosphor.ttf")
    if os.path.isfile(ttf):
        fid = QFontDatabase.addApplicationFont(ttf)
        fams = QFontDatabase.applicationFontFamilies(fid)
        if fams:
            PHOSPHOR_FAMILY = fams[0]


def _ui_font(ptsize=UI_FONT_PT, bold=False):
    f = QFont()
    fam = ["Segoe UI"]
    if PHOSPHOR_FAMILY:
        fam.append(PHOSPHOR_FAMILY)
    try:
        f.setFamilies(fam)
    except AttributeError:
        f.setFamily("Segoe UI")
    f.setPointSize(ptsize)
    if bold:
        f.setBold(True)
    return f


STYLE = f"""
QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; font-size: {UI_FONT_PT}px; }}
QLabel {{ background: transparent; color: {TEXT}; font-size: {UI_FONT_PT}px; }}
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background: {ENTRY}; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 6px; padding: 10px 12px; font-size: {UI_FONT_PT}px;
    selection-background-color: {ACCENT}; min-height: 22px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {ACCENT};
    background: {CARD};
}}
QScrollArea {{ border: none; background: {BG}; }}
QScrollBar:vertical {{
    background: {PANEL}; width: 16px; border-radius: 8px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 8px; min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {PANEL}; height: 16px; border-radius: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 8px; min-width: 40px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QTableWidget {{
    background: {CARD}; color: {TEXT}; gridline-color: {BORDER};
    border: 1px solid {BORDER}; border-radius: 6px;
    selection-background-color: {ACCENT}; font-size: {UI_FONT_PT}px;
}}
QHeaderView::section {{
    background: {PANEL}; color: {SUB}; border: 1px solid {BORDER};
    padding: 6px 10px; font-size: {UI_FONT_SMALL}px; font-weight: bold;
    min-height: 52px;
}}
QHeaderView {{
    min-height: 52px;
}}
QListWidget {{
    background: {ENTRY}; color: {TEXT}; border: none; border-radius: 6px;
    font-size: {UI_FONT_PT}px; outline: none;
}}
QListWidget::item {{
    padding: 10px 12px; min-height: 28px;
    border-radius: 4px;
}}
QListWidget::item:hover {{
    background: {PANEL};
}}
QListWidget::item:selected {{
    background: {ACCENT}; color: white;
}}
"""


def _btn(text, color=ACCENT, width=None, bold=False):
    b = QPushButton(text)
    fw = "bold" if bold else "normal"
    w_css = f"min-width: {width}px;" if width else ""
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: white; border: none; border-radius: 8px;
            padding: 12px 22px; font-size: {UI_FONT_PT}px; font-weight: {fw}; {w_css}
        }}
        QPushButton:hover {{ background: {color}cc; }}
        QPushButton:pressed {{ background: {color}dd; }}
    """)
    b.setCursor(Qt.PointingHandCursor)
    b.setMinimumHeight(44)
    return b


def _card():
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background: {CARD}; border-radius: 8px; }}")
    return f


def _heading(text, color=ACCENT, size=22):
    l = QLabel(text)
    l.setFont(_ui_font(size, bold=True))
    l.setStyleSheet(f"color: {color};")
    return l


def _sub(text):
    l = QLabel(text)
    l.setFont(_ui_font(13))
    l.setStyleSheet(f"color: {SUB};")
    l.setWordWrap(True)
    return l


def _configure_sfm_data_table(table, col0_w=280, col1_w=280):
    """Колонки показателей — по ширине содержимого (заголовок целиком), без обрезки Stretch."""
    hdr = table.horizontalHeader()
    hdr.setMinimumHeight(56)
    hdr.setDefaultAlignment(Qt.AlignCenter | Qt.AlignVCenter | Qt.TextWordWrap)
    n = table.columnCount()
    for c in range(n):
        if c == 0:
            hdr.setSectionResizeMode(c, QHeaderView.Interactive)
            table.setColumnWidth(c, col0_w)
        elif c == 1:
            hdr.setSectionResizeMode(c, QHeaderView.Interactive)
            table.setColumnWidth(c, col1_w)
        else:
            hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
    hdr.setMinimumSectionSize(88)
    for c in range(2, n):
        table.resizeColumnToContents(c)


# ═══════════════════════════════════════════
#  Данные ВОЛС по умолчанию
# ═══════════════════════════════════════════

DEFAULT_PARAMS = [
    "Скорость передачи данных",
    "Затухание сигнала",
    "Время устойчивой работы",
    "Полоса пропускания",
    "Коэффициент ошибок (BER)",
    "Мощность сигнала",
    "Дисперсия",
]
DEFAULT_UNITS  = ["Гбит/с", "дБ/км", "часы", "ТГц", "×10⁻⁹", "дБм", "пс/нм·км"]
DEFAULT_TS     = [
    "Источник излучения (лазер)",
    "Оптоволоконный кабель",
    "Приёмник сигнала (фотодиод)",
    "Оптический усилитель",
    "Мультиплексор DWDM",
    "Система мониторинга ВОЛС",
    "Регенератор сигнала",
    "Оптический переключатель",
    "ИБП (источник бесперебойного питания)",
    "Оптический дисперсионный компенсатор",
    "Волоконно-оптический разветвитель",
]
DEFAULT_FUNC   = [
    "Генерация оптического сигнала",
    "Передача оптического сигнала",
    "Приём и преобразование сигнала",
    "Усиление сигнала",
    "Уплотнение каналов",
    "Мониторинг параметров ВОЛС",
    "Восстановление формы сигнала",
    "Коммутация оптических каналов",
    "Обеспечение бесперебойного электропитания",
    "Компенсация хроматической дисперсии",
    "Разветвление и объединение потоков",
]

# Формат строк: [p0_min, p0_max, ..., p6_min, p6_max]  (7 параметров × 2 = 14 значений)
# P0 — Скорость (Гбит/с), P1 — Затухание (дБ/км), P2 — Время работы (ч),
# P3 — Полоса (ТГц), P4 — BER (×10⁻⁹), P5 — Мощность (дБм), P6 — Дисперсия (пс/нм·км)
IDEAL_VALUES = [
    [10, 100, 0.1,  0.5,  8000, 20000,  1.0, 10.0, 0.0, 1.0,    0,  13,  0,   0],  # Лазер
    [0,    0, 0.2,  0.4,  0,    0,     10.0, 40.0, 0.0, 0.0,  -20,   0,  0,  17],  # Кабель
    [10,  80, 0.0,  0.1,  6000, 18000,  1.0, 10.0, 0.0, 0.5,  -30, -10,  0,   0],  # Фотодиод
    [5,   60, 0.0,  0.0,  5000, 15000,  0.5,  5.0, 0.0, 0.0,  -10,  10,  0,   0],  # Усилитель
    [40, 200, 0.5,  2.0,  4000, 12000, 10.0, 50.0, 0.0, 0.0,   -5,   5,  0,   2],  # Мультиплексор
    [0,    0, 0.0,  0.0,  7000, 16000,  0.0,  0.0, 0.0, 0.0,    0,   0,  0,   0],  # Мониторинг
    [0,    0, 0.0,  0.05, 5500, 17000,  0.0,  0.0, 0.0, 0.0,   -5,   5,  0,   0],  # Регенератор
    [0,    0, 0.0,  0.3,  4000, 14000,  5.0, 20.0, 0.0, 0.0,  -10,   0,  0,   0],  # Переключатель
    [0,    0, 0.0,  0.0,  8000, 25000,  0.0,  0.0, 0.0, 0.0,    0,   0,  0,   0],  # ИБП
    [0,    0, 0.0,  0.0,  6000, 18000,  0.0,  0.0, 0.0, 0.0,    0,   0,-17,   0],  # Дисп. компенсатор
    [0,    0, 0.0,  1.0,  5000, 16000,  5.0, 30.0, 0.0, 0.0,  -15,  -3,  0,   0],  # Разветвитель
]

REAL_PRESETS = [
    {
        "name": "Участок А",
        "values": [
            [12,  95,  0.15, 0.45, 9000, 19000,  1.2,  9.5,  0.0, 0.9,    1,  12,  0,    0],
            [0,    0,  0.25, 0.38, 0,    0,     12.0, 38.0,  0.0, 0.0,  -18,   0,  0,   16],
            [11,  75,  0.0,  0.08, 6500, 17000,  1.1,  9.0,  0.0, 0.45, -28, -11,  0,    0],
            [6,   55,  0.0,  0.0,  5500, 14000,  0.6,  4.5,  0.0, 0.0,   -9,   9,  0,    0],
            [45, 190,  0.6,  1.8,  4500, 11500, 11.0, 48.0,  0.0, 0.0,   -4,   4,  0,  1.8],
            [0,    0,  0.0,  0.0,  7500, 15500,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.04, 5800, 16500,  0.0,  0.0,  0.0, 0.0,   -4,   4,  0,    0],
            [0,    0,  0.0,  0.25, 4200, 13500,  5.5, 19.0,  0.0, 0.0,   -9,   0,  0,    0],
            [0,    0,  0.0,  0.0,  8500, 24000,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.0,  6200, 17500,  0.0,  0.0,  0.0, 0.0,    0,   0,-16,    0],
            [0,    0,  0.0,  0.9,  5200, 15500,  5.5, 28.0,  0.0, 0.0,  -14,  -3,  0,    0],
        ],
        "budget": 9000000, "period": 400,
    },
    {
        "name": "Участок Б",
        "values": [
            [11,  98,  0.12, 0.48, 8500, 19500,  1.1,  9.8,  0.0, 0.95,   0,  12,  0,    0],
            [0,    0,  0.22, 0.40, 0,    0,     11.0, 40.0,  0.0, 0.0,  -19,   0,  0, 16.5],
            [12,  78,  0.0,  0.09, 6200, 17500,  1.2,  9.2,  0.0, 0.48, -29, -11,  0,    0],
            [5,   58,  0.0,  0.0,  5200, 14500,  0.5,  4.8,  0.0, 0.0,   -9,   9,  0,    0],
            [42, 195,  0.55, 1.85, 4200, 11800, 10.5, 49.0,  0.0, 0.0,   -5,   5,  0,  1.9],
            [0,    0,  0.0,  0.0,  7200, 15800,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.03, 5600, 16800,  0.0,  0.0,  0.0, 0.0,   -4,   4,  0,    0],
            [0,    0,  0.0,  0.28, 4000, 13800,  5.2, 19.5,  0.0, 0.0,   -9,   0,  0,    0],
            [0,    0,  0.0,  0.0,  7800, 23000,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.0,  5900, 17000,  0.0,  0.0,  0.0, 0.0,    0,   0,-16.5,  0],
            [0,    0,  0.0,  0.95, 5000, 15200,  5.2, 29.0,  0.0, 0.0,  -14,  -4,  0,    0],
        ],
        "budget": 8500000, "period": 380,
    },
    {
        "name": "Участок В",
        "values": [
            [14,  90,  0.18, 0.42, 8200, 18500,  1.4,  9.0,  0.0, 0.85,   1,  11,  0,    0],
            [0,    0,  0.28, 0.35, 0,    0,     10.5, 35.0,  0.0, 0.0,  -17,   0,  0, 15.5],
            [9,   70,  0.0,  0.10, 5800, 16500,  0.9,  8.5,  0.0, 0.42, -27, -12,  0,    0],
            [4,   52,  0.0,  0.0,  4800, 13500,  0.4,  4.2,  0.0, 0.0,   -8,   8,  0,    0],
            [38, 185,  0.65, 1.70, 3800, 11000,  9.5, 46.0,  0.0, 0.0,   -6,   4,  0,  1.6],
            [0,    0,  0.0,  0.0,  6800, 15000,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.06, 5300, 16200,  0.0,  0.0,  0.0, 0.0,   -5,   4,  0,    0],
            [0,    0,  0.0,  0.32, 3800, 13200,  4.8, 18.5,  0.0, 0.0,  -10,   0,  0,    0],
            [0,    0,  0.0,  0.0,  8200, 22000,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.0,  5800, 16500,  0.0,  0.0,  0.0, 0.0,    0,   0,-15.5,  0],
            [0,    0,  0.0,  0.85, 4800, 14800,  4.8, 27.0,  0.0, 0.0,  -13,  -4,  0,    0],
        ],
        "budget": 9500000, "period": 370,
    },
    {
        "name": "Участок Г",
        "values": [
            [10,  88,  0.16, 0.44, 8000, 18000,  1.3,  9.2,  0.0, 0.88,   1,  11,  0,    0],
            [0,    0,  0.24, 0.37, 0,    0,     11.5, 37.0,  0.0, 0.0,  -17,   0,  0, 15.8],
            [10,  72,  0.0,  0.09, 6000, 16500,  1.0,  8.8,  0.0, 0.44, -27, -11,  0,    0],
            [5,   54,  0.0,  0.0,  5000, 14000,  0.5,  4.5,  0.0, 0.0,   -9,   8,  0,    0],
            [40, 188,  0.62, 1.75, 4000, 11200, 10.0, 47.0,  0.0, 0.0,   -5,   5,  0,  1.7],
            [0,    0,  0.0,  0.0,  7000, 15200,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.05, 5500, 16000,  0.0,  0.0,  0.0, 0.0,   -5,   4,  0,    0],
            [0,    0,  0.0,  0.30, 4000, 13500,  5.0, 19.0,  0.0, 0.0,   -9,   0,  0,    0],
            [0,    0,  0.0,  0.0,  8000, 22500,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.0,  6000, 17000,  0.0,  0.0,  0.0, 0.0,    0,   0,-16.0,  0],
            [0,    0,  0.0,  0.88, 5000, 15000,  5.0, 28.0,  0.0, 0.0,  -13,  -4,  0,    0],
        ],
        "budget": 9200000, "period": 385,
    },
    {
        "name": "Участок Д",
        "values": [
            [13,  92,  0.17, 0.43, 8300, 18800,  1.3,  9.3,  0.0, 0.87,   1,  12,  0,    0],
            [0,    0,  0.26, 0.36, 0,    0,     11.0, 36.0,  0.0, 0.0,  -18,   0,  0, 16.0],
            [11,  74,  0.0,  0.09, 6100, 17000,  1.0,  8.7,  0.0, 0.43, -28, -11,  0,    0],
            [5,   56,  0.0,  0.0,  4900, 14200,  0.5,  4.4,  0.0, 0.0,   -9,   9,  0,    0],
            [39, 190,  0.63, 1.72, 3900, 11500,  9.8, 47.5,  0.0, 0.0,   -5,   4,  0,  1.7],
            [0,    0,  0.0,  0.0,  7100, 15400,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.05, 5400, 16400,  0.0,  0.0,  0.0, 0.0,   -4,   4,  0,    0],
            [0,    0,  0.0,  0.29, 3900, 13400,  5.0, 18.8,  0.0, 0.0,  -10,   0,  0,    0],
            [0,    0,  0.0,  0.0,  8100, 23000,  0.0,  0.0,  0.0, 0.0,    0,   0,  0,    0],
            [0,    0,  0.0,  0.0,  5900, 16800,  0.0,  0.0,  0.0, 0.0,    0,   0,-15.8,  0],
            [0,    0,  0.0,  0.87, 4900, 15100,  4.9, 27.5,  0.0, 0.0,  -14,  -4,  0,    0],
        ],
        "budget": 8800000, "period": 375,
    },
]


def _app_icon() -> QIcon:
    """Значок приложения (guap-sign.png рядом с main.py)."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "guap-sign.png")
    if os.path.isfile(path):
        return QIcon(path)
    return QIcon()


# ═══════════════════════════════════════════
#  Виджет-схема ВОЛС (QGraphicsView, zoom)
# ═══════════════════════════════════════════

class _SchemaGraphicsView(QGraphicsView):
    """QGraphicsView с перехватом кликов для создания рёбер и показа info."""
    point_clicked = pyqtSignal(int)      # Клик по участку (индекс участка)
    segment_clicked = pyqtSignal(int)    # Клик по участку (индекс участка)
    dev_clicked = pyqtSignal(int, int)   # Клик по устройству (sfm_idx, ts_idx)

    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self._schema = parent
        self._panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        self._hovered_item = None

    def mousePressEvent(self, event):
        # Панорамирование средней кнопкой или Ctrl+ЛКМ
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() & Qt.ControlModifier):
            self._panning = True
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        # Находим элемент под курсором
        pos = self.mapToScene(event.pos())
        item = self.scene().itemAt(pos, self.transform())
        if item and item.data(0) is not None:
            data = item.data(0)
            kind = data[0]
            if kind == "dev":
                self.dev_clicked.emit(data[1], data[2])
            elif kind == "segment":
                self.segment_clicked.emit(data[1])
            elif kind == "point":
                self.point_clicked.emit(data[1])
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta_x = event.x() - self._pan_start_x
            delta_y = event.y() - self._pan_start_y
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            event.accept()
            return

        # Подсветка устройств при наведении
        pos = self.mapToScene(event.pos())
        item = self.scene().itemAt(pos, self.transform())

        # Убираем подсветку с предыдущего элемента
        if self._hovered_item and self._hovered_item != item:
            if hasattr(self._hovered_item, '_original_pen'):
                self._hovered_item.setPen(self._hovered_item._original_pen)
            if hasattr(self._hovered_item, '_original_brush'):
                self._hovered_item.setBrush(self._hovered_item._original_brush)
            self._hovered_item = None

        # Подсвечиваем новый элемент
        if item and item.data(0) is not None:
            data = item.data(0)
            kind = data[0]
            if kind == "dev":
                # Ищем PathItem устройства среди siblings
                sfm_idx, ts_idx = data[1], data[2]
                parent_block = item.parentItem()

                if parent_block:
                    # Ищем PathItem с теми же координатами устройства
                    for child in parent_block.childItems():
                        if isinstance(child, QGraphicsPathItem) and child.data(0):
                            child_data = child.data(0)
                            if child_data[0] == "dev" and child_data[1] == sfm_idx and child_data[2] == ts_idx:
                                if not hasattr(child, '_original_pen'):
                                    child._original_pen = child.pen()
                                    child._original_brush = child.brush()

                                # Подсветка
                                highlight_pen = QPen(QColor(ACCENT), 3)
                                child.setPen(highlight_pen)

                                # Немного осветляем фон
                                brush_color = child.brush().color()
                                lighter = brush_color.lighter(110)
                                child.setBrush(QBrush(lighter))

                                self._hovered_item = child
                                break

                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and self._panning):
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class _DraggablePoint(QGraphicsEllipseItem):
    """Участок (узел сети) - НЕ перетаскиваемый, только для отображения."""
    def __init__(self, x, y, r, schema, node_idx):
        super().__init__(x - r, y - r, r * 2, r * 2)
        self._schema = schema
        self._node_idx = node_idx
        # Убираем возможность перетаскивания
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


class SchemaWidget(QWidget):
    """Визуальная схема ВОЛС: точки (узлы) соединены участками с устройствами."""

    DEV_SIZE = 52
    DEV_GAP = 8
    BLOCK_PAD = 40
    LABEL_H = 28
    COLS = 4
    POINT_RADIUS = 35

    def __init__(self, parent_window):
        super().__init__()
        self.mw = parent_window
        self._point_positions = {}  # sfm_idx -> QPointF (позиция участка)
        self._segment_items = {}    # sfm_idx -> dict (блок участка)
        self._point_items = {}      # sfm_idx -> QGraphicsEllipseItem (перетаскиваемая точка)
        self._edge_lines = {}       # (from_idx, to_idx) -> QGraphicsLineItem
        self._dev_colors = {}
        self._edit_edges = False
        self._edge_select = None

        # ── Layout ──
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        # Кнопки зума
        zoom_bar = QHBoxLayout()

        # Кнопка плюс
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFont(_ui_font(20, bold=True))
        zoom_in_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT2}; color: white; border: none; border-radius: 8px;
                padding: 8px; font-size: 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {ACCENT2}cc; }}
        """)
        zoom_in_btn.setCursor(Qt.PointingHandCursor)
        zoom_in_btn.setFixedSize(40, 44)
        zoom_in_btn.clicked.connect(lambda: self._apply_zoom(1.25))
        self._zoom_in_btn = zoom_in_btn
        zoom_bar.addWidget(self._zoom_in_btn)

        # Кнопка минус
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFont(_ui_font(20, bold=True))
        zoom_out_btn.setStyleSheet(f"""
            QPushButton {{
                background: #6b7280; color: white; border: none; border-radius: 8px;
                padding: 8px; font-size: 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #6b7280cc; }}
        """)
        zoom_out_btn.setCursor(Qt.PointingHandCursor)
        zoom_out_btn.setFixedSize(40, 44)
        zoom_out_btn.clicked.connect(lambda: self._apply_zoom(0.8))
        self._zoom_out_btn = zoom_out_btn
        zoom_bar.addWidget(self._zoom_out_btn)

        self._zoom_fit_btn = _btn("По размеру", ACCENT)
        self._zoom_fit_btn.clicked.connect(self._fit_in_view)
        zoom_bar.addWidget(self._zoom_fit_btn)

        zoom_bar.addStretch()
        lay.addLayout(zoom_bar)

        # QGraphicsView
        self._scene = QGraphicsScene()
        self._view = _SchemaGraphicsView(self._scene, self)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self._view.setDragMode(QGraphicsView.NoDrag)  # Изменено для поддержки перетаскивания элементов
        self._view.setMouseTracking(True)
        self._view.viewport().installEventFilter(self)
        self._view.segment_clicked.connect(self._on_segment_clicked)
        self._view.dev_clicked.connect(self._on_dev_clicked)
        self._view.point_clicked.connect(self._on_point_clicked)
        lay.addWidget(self._view, 1)

    def eventFilter(self, obj, event):
        """Перехватываем wheelEvent на viewport."""
        if obj is self._view.viewport() and event.type() == QEvent.Wheel:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self._view.scale(factor, factor)
            return True
        if obj is self._view.viewport() and event.type() in (QEvent.MouseMove, QEvent.MouseButtonRelease):
            self._update_segments_from_points()
            return False
        return super().eventFilter(obj, event)

    def _update_segments_from_points(self):
        """Обновить позиции линий связей на основе позиций участков."""
        # Обновляем линии между участками
        for from_idx, to_idx in self.mw.network_edges:
            if from_idx in self._point_positions and to_idx in self._point_positions:
                p1 = self._point_positions[from_idx]
                p2 = self._point_positions[to_idx]
                # Находим линию связи
                key = (from_idx, to_idx)
                if key in self._edge_lines:
                    line = self._edge_lines[key]
                    line.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    def _on_segment_clicked(self, idx):
        """Обработка клика по участку."""
        pass  # Можно добавить действия при клике на участок

    def _on_point_clicked(self, node_idx):
        """Обработка клика по участку."""
        pass  # Можно добавить действия при клике на участок

    def _on_dev_clicked(self, sfm_idx, ts_idx):
        """Обработка клика по устройству."""
        self.mw._show_device_info(sfm_idx, ts_idx)

    def _parse_segment(self, name):
        """Извлечь букву участка из названия типа 'Участок А'."""
        import re
        match = re.search(r'Участок\s+([А-Я])', name)
        if match:
            return match.group(1)
        return None

    # ── Размеры блока ──

    def _block_w(self):
        n_ts = self.mw.n_ts
        cols = min(self.COLS, n_ts)
        return cols * (self.DEV_SIZE + self.DEV_GAP) + self.BLOCK_PAD * 2 - self.DEV_GAP

    def _block_h(self):
        n_ts = self.mw.n_ts
        cols = min(self.COLS, n_ts)
        rows_ts = (n_ts + cols - 1) // cols
        return self.LABEL_H + rows_ts * (self.DEV_SIZE + self.DEV_GAP) + self.BLOCK_PAD - self.DEV_GAP

    # ── Авто-раскладка точек ──

    def _compute_point_layout(self):
        """Вычислить позиции участков на основе связей."""
        if not self.mw.real_sfms:
            return {}

        n = len(self.mw.real_sfms)

        # Строим граф связей между участками
        connections = {i: set() for i in range(n)}
        for from_idx, to_idx in self.mw.network_edges:
            if from_idx < n and to_idx < n:
                connections[from_idx].add(to_idx)
                connections[to_idx].add(from_idx)

        # BFS для определения уровней участков
        from collections import deque
        visited = {0}
        levels = {0: 0}
        queue = deque([0])

        while queue:
            current = queue.popleft()
            current_level = levels[current]
            for neighbor in connections[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    levels[neighbor] = current_level + 1
                    queue.append(neighbor)

        # Добавляем несвязанные узлы
        for i in range(n):
            if i not in visited:
                levels[i] = 0

        # Группируем участки по уровням
        level_nodes = {}
        for node, level in levels.items():
            level_nodes.setdefault(level, []).append(node)

        # Размещаем участки с увеличенными отступами
        positions = {}
        gap_x = 500  # Увеличено с 400
        gap_y = 300  # Увеличено с 250

        for level in sorted(level_nodes.keys()):
            nodes = sorted(level_nodes[level])
            total_h = len(nodes) * gap_y
            oy = -total_h / 2
            ox = 100 + level * gap_x

            for i, node_idx in enumerate(nodes):
                positions[node_idx] = QPointF(ox, oy + i * gap_y)

        return positions

    def _ensure_point_positions(self):
        """Убедиться, что все участки имеют позиции."""
        auto = self._compute_point_layout()
        for idx, pos in auto.items():
            if idx not in self._point_positions:
                self._point_positions[idx] = pos

    # ── Публичные методы ──

    def set_edges(self, edges):
        pass  # Рёбра теперь определяются автоматически из названий участков

    def get_edges(self):
        return []  # Рёбра не используются в новой схеме

    def set_colors(self, colors):
        self._dev_colors = colors
        self._redraw()

    def set_edit_mode(self, enabled):
        self._edit_edges = enabled
        self._redraw()

    # ── Zoom ──

    def _apply_zoom(self, factor):
        self._view.scale(factor, factor)

    def _fit_in_view(self):
        rect = self._scene.itemsBoundingRect()
        if rect.isEmpty():
            return
        self._view.fitInView(rect.adjusted(-40, -40, 40, 40), Qt.KeepAspectRatio)

    # ── Перерисовка ──

    def _redraw(self):
        self._scene.clear()
        self._segment_items = {}
        self._point_items = {}
        self._edge_lines = {}
        self._animations = []  # Сохраняем ссылки на анимации

        n = len(self.mw.real_sfms)
        if n == 0:
            txt = self._scene.addText("Нет реальных СФМ.\nДобавьте участки на странице «Реальные СФМ».")
            txt.setDefaultTextColor(QColor(SUB))
            return

        bw = self._block_w()
        bh = self._block_h()
        n_ts = self.mw.n_ts
        cols = min(self.COLS, n_ts)

        self._ensure_point_positions()

        # Рисуем линии связей между участками
        for from_idx, to_idx in self.mw.network_edges:
            if from_idx >= n or to_idx >= n:
                continue
            if from_idx not in self._point_positions or to_idx not in self._point_positions:
                continue

            p1 = self._point_positions[from_idx]
            p2 = self._point_positions[to_idx]

            line = self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y())
            line.setPen(QPen(QColor(BORDER), 3, Qt.SolidLine, Qt.RoundCap))
            line.setZValue(1)
            self._edge_lines[(from_idx, to_idx)] = line

        # Рисуем участки (блоки с устройствами)
        for idx, sfm in enumerate(self.mw.real_sfms):
            if idx not in self._point_positions:
                continue

            pos = self._point_positions[idx]

            # Блок участка
            block = QGraphicsRectItem(0, 0, bw, bh)
            block.setPen(QPen(QColor(BORDER), 2))
            block.setBrush(QBrush(QColor(CARD)))
            block.setPos(pos.x() - bw / 2, pos.y() - bh / 2)
            block.setZValue(5)
            block.setData(0, ("segment", idx))
            self._scene.addItem(block)

            # Имя участка
            name_label = QGraphicsTextItem(sfm["name"])
            name_label.setFont(_ui_font(12, bold=True))
            name_label.setDefaultTextColor(QColor(TEXT))
            name_label.setParentItem(block)
            name_label.setPos(10, 4)
            name_label.setZValue(6)

            # Устройства внутри блока
            for ts_i in range(n_ts):
                r = ts_i // cols
                c = ts_i % cols
                dx = self.BLOCK_PAD + c * (self.DEV_SIZE + self.DEV_GAP)
                dy = self.LABEL_H + 8 + r * (self.DEV_SIZE + self.DEV_GAP)
                path = QPainterPath()
                path.addRoundedRect(0, 0, self.DEV_SIZE, self.DEV_SIZE, 6, 6)
                dev_rect = QGraphicsPathItem(path)
                color = self._dev_colors.get((idx, ts_i), QColor(PANEL))
                dev_rect.setPen(QPen(QColor(BORDER), 1.5))
                dev_rect.setBrush(QBrush(color))
                dev_rect.setParentItem(block)
                dev_rect.setPos(dx, dy)
                dev_rect.setZValue(7)
                dev_rect.setData(0, ("dev", idx, ts_i))

                # Увеличенная невидимая область клика
                click_area = QGraphicsRectItem(0, 0, self.DEV_SIZE, self.DEV_SIZE)
                click_area.setPen(QPen(Qt.transparent))
                click_area.setBrush(QBrush(Qt.transparent))
                click_area.setParentItem(block)
                click_area.setPos(dx, dy)
                click_area.setZValue(8)
                click_area.setData(0, ("dev", idx, ts_i))
                click_area.setAcceptHoverEvents(True)

                lbl = QGraphicsTextItem(str(ts_i + 1))
                lbl.setFont(_ui_font(13, bold=True))
                lbl.setDefaultTextColor(QColor("#ffffff") if color != QColor(PANEL) else QColor(TEXT))
                lbl.setParentItem(block)
                lbl.setPos(dx + self.DEV_SIZE / 2 - 4, dy + self.DEV_SIZE / 2 - 8)
                lbl.setZValue(9)
                lbl.setData(0, ("dev", idx, ts_i))

            # Невидимая точка для клика (не перетаскиваемая)
            point_item = _DraggablePoint(0, 0, self.POINT_RADIUS, self, idx)
            transparent_color = QColor(ACCENT)
            transparent_color.setAlpha(0)
            point_item.setPen(QPen(transparent_color, 0))
            point_item.setBrush(QBrush(transparent_color))
            point_item.setPos(pos)
            point_item.setZValue(10)
            point_item.setData(0, ("point", idx))
            self._scene.addItem(point_item)
            self._point_items[idx] = point_item

            self._segment_items[idx] = {'block': block}

        # Автоматический масштаб с задержкой
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self._fit_in_view)


    # ── Mouse events на view ──


# ═══════════════════════════════════════════
#  Главное окно
# ═══════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("СФМ ВОЛС — Оценка качества")
        self.setWindowIcon(_app_icon())
        self.resize(1440, 900)
        self.setMinimumSize(1100, 720)

        self.n_params = 7
        self.n_ts = 11
        self.param_names = list(DEFAULT_PARAMS)
        self.param_units = list(DEFAULT_UNITS)
        self.ts_names = list(DEFAULT_TS)
        self.func_names = list(DEFAULT_FUNC)
        self.ideal_data = None
        self.real_sfms = []
        self.network_edges = []       # [(from_idx, to_idx), ...] — топология сети
        self.network_positions = {}   # sfm_idx -> (x, y) — сохранённые позиции узлов
        self.results = []
        self._cur_edit_idx = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Боковая панель ──
        nav = QFrame()
        nav.setFixedWidth(UI_NAV_W)
        nav.setStyleSheet(f"QFrame {{ background: {PANEL}; }}")
        nav_lay = QVBoxLayout(nav)
        nav_lay.setContentsMargins(0, 0, 0, 0)
        nav_lay.setSpacing(0)

        logo = QWidget()
        logo.setStyleSheet(f"background: {PANEL};")
        logo_lay = QVBoxLayout(logo)
        logo_lay.setContentsMargins(0, 24, 0, 16)
        l1 = QLabel("СФМ ВОЛС")
        l1.setFont(_ui_font(19, bold=True))
        l1.setStyleSheet(f"color: {ACCENT};")
        l1.setAlignment(Qt.AlignCenter)
        logo_lay.addWidget(l1)
        l2 = QLabel("Оценка качества")
        l2.setFont(_ui_font(12))
        l2.setStyleSheet(f"color: {SUB};")
        l2.setAlignment(Qt.AlignCenter)
        logo_lay.addWidget(l2)
        nav_lay.addWidget(logo)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        nav_lay.addWidget(sep)

        self.nav_btns = []
        pages = [
            (f"{PH_GEAR}  Настройка", 0),
            (f"{PH_CLIPBOARD} Идеальная СФМ", 1),
            (f"{PH_FOLDERS} Реальные СФМ", 2),
            (f"{PH_TABLE} Схема ВОЛС", 3),
            (f"{PH_CHART_BAR} Результаты", 4),
            (f"{PH_CHART_LINE_UP} Рейтинг", 5),
        ]
        for label, idx in pages:
            b = QPushButton(label)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {PANEL}; color: {TEXT}; border: none;
                    text-align: left; padding: 14px 22px; font-size: {UI_FONT_PT}px;
                }}
                QPushButton:hover {{ background: {CARD}; }}
            """)
            b.setMinimumHeight(48)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, i=idx: self._go(i))
            nav_lay.addWidget(b)
            self.nav_btns.append(b)

        nav_lay.addStretch()

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {BORDER};")
        nav_lay.addWidget(sep2)

        io_btns = QVBoxLayout()
        io_btns.setContentsMargins(12, 8, 12, 12)
        io_btns.setSpacing(4)
        save_b = _btn(f"{PH_FLOPPY} Сохранить", "#6b7280")
        save_b.clicked.connect(self._save_project)
        io_btns.addWidget(save_b)
        load_b = _btn(f"{PH_FOLDER_OPEN} Загрузить", "#6b7280")
        load_b.clicked.connect(self._load_project)
        io_btns.addWidget(load_b)
        nav_lay.addLayout(io_btns)

        root.addWidget(nav)

        # ── Область страниц ──
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        self._build_page_setup()      # 0
        self._build_page_ideal()      # 1
        self._build_page_real()        # 2
        self._build_page_schema()      # 3
        self._build_page_results()     # 4
        self._build_page_rating()      # 5

        self._go(0)

    # ─── Навигация ───

    def _go(self, idx):
        # Уход со страницы «Реальные СФМ» — сохранить открытую форму
        if self.pages.currentIndex() == 2 and idx != 2:
            self._flush_cur_real_sfm()
        # Уход со страницы «Идеальная СФМ» — сохранить таблицу без отдельной кнопки «Сохранить»
        if self.pages.currentIndex() == 1 and idx != 1:
            self._save_ideal(show_message=False)
        # Уход со страницы «Схема ВОЛС» — сохранить позиции точек
        if self.pages.currentIndex() == 3 and idx != 3:
            self._save_topology()

        for i, b in enumerate(self.nav_btns):
            if i == idx:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {ACCENT}; color: white; border: none;
                        text-align: left; padding: 14px 22px; font-size: {UI_FONT_PT}px; font-weight: bold;
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {PANEL}; color: {TEXT}; border: none;
                        text-align: left; padding: 14px 22px; font-size: {UI_FONT_PT}px;
                    }}
                    QPushButton:hover {{ background: {CARD}; }}
                """)
        if idx == 1:
            self._refresh_ideal_page()
        elif idx == 2:
            self._refresh_real_page()
        elif idx == 3:
            self._fill_schema_page()
        elif idx == 4:
            self._fill_results_page()
        elif idx == 5:
            self._fill_rating_page()
        self.pages.setCurrentIndex(idx)

    # ─────────────────────────────────────
    #  PAGE 0 — Настройка
    # ─────────────────────────────────────

    def _build_page_setup(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(12)

        lay.addWidget(_heading("Настройка параметров модели"))
        lay.addWidget(_sub("Задайте структуру ВОЛС: показатели качества и технические системы"))

        # Количества
        card = _card()
        cl = QGridLayout(card)
        cl.setContentsMargins(24, 18, 24, 18)
        cl.addWidget(QLabel("Количество показателей (n):"), 0, 0)
        self.spin_params = QSpinBox()
        self.spin_params.setRange(1, 15)
        self.spin_params.setValue(self.n_params)
        cl.addWidget(self.spin_params, 0, 1)
        cl.addWidget(QLabel("Количество технических систем (m):"), 1, 0)
        self.spin_ts = QSpinBox()
        self.spin_ts.setRange(1, 20)
        self.spin_ts.setValue(self.n_ts)
        cl.addWidget(self.spin_ts, 1, 1)
        cl.setColumnStretch(2, 1)
        lay.addWidget(card)

        # Показатели
        card2 = _card()
        c2l = QVBoxLayout(card2)
        c2l.setContentsMargins(24, 18, 24, 18)
        c2l.addWidget(_heading("Показатели качества", ACCENT2, 17))
        self.param_grid = QWidget()
        self.param_grid_lay = QVBoxLayout(self.param_grid)
        self.param_grid_lay.setContentsMargins(0, 0, 0, 0)
        c2l.addWidget(self.param_grid)
        lay.addWidget(card2)

        # ТС
        card3 = _card()
        c3l = QVBoxLayout(card3)
        c3l.setContentsMargins(24, 18, 24, 18)
        c3l.addWidget(_heading("Технические системы и функции", ACCENT2, 17))
        self.ts_grid = QWidget()
        self.ts_grid_lay = QVBoxLayout(self.ts_grid)
        self.ts_grid_lay.setContentsMargins(0, 0, 0, 0)
        c3l.addWidget(self.ts_grid)
        lay.addWidget(card3)

        btn_row = QHBoxLayout()
        upd = _btn("Обновить поля", ACCENT2)
        upd.clicked.connect(self._refresh_setup_fields)
        btn_row.addWidget(upd)
        nxt = _btn(f"Далее {PH_CARET_RIGHT}", ACCENT)
        nxt.clicked.connect(self._apply_setup)
        btn_row.addWidget(nxt)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        lay.addStretch()
        scroll.setWidget(inner)
        self.pages.addWidget(scroll)

        self._refresh_setup_fields()

    def _refresh_setup_fields(self):
        n = self.spin_params.value()
        m = self.spin_ts.value()

        # Очистка
        while self.param_grid_lay.count():
            w = self.param_grid_lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        while self.ts_grid_lay.count():
            w = self.ts_grid_lay.takeAt(0).widget()
            if w:
                w.deleteLater()

        all_pn = DEFAULT_PARAMS + [
            "Мощность сигнала", "Дисперсия", "Длина волны",
            "Кол-во отказов", "Надёжность", "Задержка передачи",
        ]
        all_pu = DEFAULT_UNITS + ["дБм", "пс/нм·км", "нм", "отказ/год", "%", "мкс"]

        self._setup_pn = []
        self._setup_pu = []
        hdr = QWidget()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(QLabel("№"), 0)
        l1 = QLabel("Название показателя")
        l1.setStyleSheet(f"color:{SUB};")
        hl.addWidget(l1, 3)
        l2 = QLabel("Ед. изм.")
        l2.setStyleSheet(f"color:{SUB};")
        hl.addWidget(l2, 1)
        self.param_grid_lay.addWidget(hdr)

        for i in range(n):
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(0, 2, 0, 2)
            lb = QLabel(f"P{i+1}")
            lb.setStyleSheet(f"color:{SUB};")
            lb.setFixedWidth(40)
            rl.addWidget(lb, 0)
            ne = QLineEdit(self.param_names[i] if i < len(self.param_names) else all_pn[i % len(all_pn)])
            rl.addWidget(ne, 3)
            ue = QLineEdit(self.param_units[i] if i < len(self.param_units) else all_pu[i % len(all_pu)])
            rl.addWidget(ue, 1)
            self.param_grid_lay.addWidget(row_w)
            self._setup_pn.append(ne)
            self._setup_pu.append(ue)

        all_ts = DEFAULT_TS + [
            "Оптический дисперсионный компенсатор",
            "Волоконно-оптический разветвитель",
            "Система защиты от перебоев питания",
        ]
        all_fn = DEFAULT_FUNC + [
            "Компенсация хроматической дисперсии",
            "Разветвление и объединение потоков",
            "Обеспечение бесперебойной работы",
        ]

        self._setup_tn = []
        self._setup_fn = []
        hdr2 = QWidget()
        h2l = QHBoxLayout(hdr2)
        h2l.setContentsMargins(0, 0, 0, 0)
        h2l.addWidget(QLabel("№"), 0)
        t1 = QLabel("Название ТС")
        t1.setStyleSheet(f"color:{SUB};")
        h2l.addWidget(t1, 3)
        t2 = QLabel("Функция")
        t2.setStyleSheet(f"color:{SUB};")
        h2l.addWidget(t2, 3)
        self.ts_grid_lay.addWidget(hdr2)

        for i in range(m):
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(0, 2, 0, 2)
            lb = QLabel(str(i + 1))
            lb.setStyleSheet(f"color:{SUB};")
            lb.setFixedWidth(40)
            rl.addWidget(lb, 0)
            te = QLineEdit(self.ts_names[i] if i < len(self.ts_names) else all_ts[i % len(all_ts)])
            rl.addWidget(te, 3)
            fe = QLineEdit(self.func_names[i] if i < len(self.func_names) else all_fn[i % len(all_fn)])
            rl.addWidget(fe, 3)
            self.ts_grid_lay.addWidget(row_w)
            self._setup_tn.append(te)
            self._setup_fn.append(fe)

    def _apply_setup(self):
        self.n_params = self.spin_params.value()
        self.n_ts = self.spin_ts.value()
        self.param_names = [e.text().strip() or f"P{i+1}" for i, e in enumerate(self._setup_pn)]
        self.param_units = [e.text().strip() or "—" for e in self._setup_pu]
        self.ts_names = [e.text().strip() or f"ТС {i+1}" for i, e in enumerate(self._setup_tn)]
        self.func_names = [e.text().strip() or f"Функция {i+1}" for i, e in enumerate(self._setup_fn)]
        self._go(1)

    # ─────────────────────────────────────
    #  PAGE 1 — Идеальная СФМ
    # ─────────────────────────────────────

    def _build_page_ideal(self):
        self._ideal_page = QWidget()
        self._ideal_scroll = QScrollArea()
        self._ideal_scroll.setWidgetResizable(True)
        self._ideal_scroll.setWidget(self._ideal_page)
        self.pages.addWidget(self._ideal_scroll)

    def _refresh_ideal_page(self):
        # Перед пересборкой страницы — сохранить текущую таблицу (в т.ч. при повторном входе на вкладку)
        if hasattr(self, "_ideal_table"):
            try:
                _ = self._ideal_table.rowCount()
                self._save_ideal(show_message=False)
            except RuntimeError:
                pass

        old = self._ideal_page
        self._ideal_page = QWidget()
        lay = QVBoxLayout(self._ideal_page)
        lay.setContentsMargins(30, 24, 30, 24)
        lay.setSpacing(10)

        lay.addWidget(_heading("Базовая («идеальная») СФМ ВОЛС"))
        lay.addWidget(_sub("Введите предельные значения показателей качества для каждой ТС"))

        table = QTableWidget(self.n_ts, self.n_params * 2 + 2)
        table.setStyleSheet(f"QTableWidget {{ background: {CARD}; }}")
        table.verticalHeader().setVisible(False)

        headers = ["Функция", "ТС"]
        for j in range(self.n_params):
            pn = self.param_names[j] if j < len(self.param_names) else f"P{j+1}"
            pu = self.param_units[j] if j < len(self.param_units) else ""
            headers += [f"{pn}\n({pu}) мин", f"{pn}\n({pu}) макс"]
        table.setHorizontalHeaderLabels(headers)

        self._ideal_entries = []
        for i in range(self.n_ts):
            fn = self.func_names[i] if i < len(self.func_names) else f"Функция {i+1}"
            ts = self.ts_names[i] if i < len(self.ts_names) else f"ТС {i+1}"
            fi = QTableWidgetItem(fn)
            fi.setFlags(fi.flags() & ~Qt.ItemIsEditable)
            fi.setForeground(QColor(SUB))
            table.setItem(i, 0, fi)
            ti = QTableWidgetItem(ts)
            ti.setFlags(ti.flags() & ~Qt.ItemIsEditable)
            ti.setForeground(QColor(SUB))
            table.setItem(i, 1, ti)

            row_ents = []
            for j in range(self.n_params):
                prev_min, prev_max = "", ""
                if self.ideal_data and i < len(self.ideal_data.get("rows", [])):
                    vm = self.ideal_data["rows"][i]["qmin"][j]
                    vx = self.ideal_data["rows"][i]["qmax"][j]
                    if vm is not None: prev_min = str(vm)
                    if vx is not None: prev_max = str(vx)
                elif i < len(IDEAL_VALUES) and j * 2 + 1 < len(IDEAL_VALUES[i]):
                    prev_min = str(IDEAL_VALUES[i][j * 2])
                    prev_max = str(IDEAL_VALUES[i][j * 2 + 1])

                item_min = QTableWidgetItem(prev_min)
                item_min.setTextAlignment(Qt.AlignCenter)
                item_max = QTableWidgetItem(prev_max)
                item_max.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, 2 + j * 2, item_min)
                table.setItem(i, 2 + j * 2 + 1, item_max)
                row_ents.append((2 + j * 2, 2 + j * 2 + 1))
            self._ideal_entries.append(row_ents)
        table.verticalHeader().setDefaultSectionSize(UI_ROW_H)
        _configure_sfm_data_table(table)
        self._ideal_table = table
        lay.addWidget(table, 1)

        lim = _card()
        ll = QGridLayout(lim)
        ll.setContentsMargins(20, 14, 20, 14)
        ll.addWidget(_heading("Общие ограничения", ACCENT2, 16), 0, 0, 1, 4)
        ll.addWidget(QLabel("Макс. бюджет (руб.):"), 1, 0)
        self._ideal_budget = QLineEdit()
        prev_b = str(self.ideal_data["budget"]) if self.ideal_data and self.ideal_data.get("budget") else "10000000"
        self._ideal_budget.setText(prev_b)
        ll.addWidget(self._ideal_budget, 1, 1)
        ll.addWidget(QLabel("Мин. период эксплуатации (дней):"), 1, 2)
        self._ideal_period = QLineEdit()
        prev_p = str(self.ideal_data["period"]) if self.ideal_data and self.ideal_data.get("period") else "365"
        self._ideal_period.setText(prev_p)
        ll.addWidget(self._ideal_period, 1, 3)
        lay.addWidget(lim)

        br = QHBoxLayout()
        sv = _btn("Сохранить идеальную СФМ", ACCENT, 200)
        sv.clicked.connect(lambda: self._save_ideal(show_message=True))
        br.addWidget(sv)
        nx = _btn(f"Далее {PH_CARET_RIGHT}", ACCENT2)
        nx.clicked.connect(self._ideal_next)
        br.addWidget(nx)
        br.addStretch()
        lay.addLayout(br)

        self._ideal_scroll.setWidget(self._ideal_page)

    def _ideal_next(self):
        """«Далее» с идеальной СФМ — автоматически сохраняет данные."""
        self._save_ideal(show_message=False)
        self._go(2)

    def _save_ideal(self, show_message=False):
        if not hasattr(self, "_ideal_table"):
            if show_message:
                QMessageBox.warning(self, "Ошибка", "Таблица не готова. Откройте страницу ещё раз.")
            return
        rows = []
        for i in range(self._ideal_table.rowCount()):
            qmin, qmax = [], []
            for j in range(self.n_params):
                cmin = 2 + j * 2
                cmax = 2 + j * 2 + 1
                def _p(c):
                    it = self._ideal_table.item(i, c)
                    if not it or not it.text().strip() or it.text().strip() == "-":
                        return None
                    try: return float(it.text())
                    except ValueError: return None
                qmin.append(_p(cmin))
                qmax.append(_p(cmax))
            rows.append({"qmin": qmin, "qmax": qmax})
        try:
            budget = float(self._ideal_budget.text().strip()) if self._ideal_budget.text().strip() else None
            period = float(self._ideal_period.text().strip()) if self._ideal_period.text().strip() else None
        except ValueError:
            budget, period = None, None
        self.ideal_data = {"rows": rows, "budget": budget, "period": period}
        if show_message:
            QMessageBox.information(self, "Сохранено", "Идеальная СФМ сохранена!")

    # ─────────────────────────────────────
    #  PAGE 2 — Реальные СФМ
    # ─────────────────────────────────────

    def _build_page_real(self):
        self._real_page = QWidget()
        self._real_outer = QVBoxLayout(self._real_page)
        self._real_outer.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(self._real_page)

        if not self.real_sfms:
            for rp in REAL_PRESETS:
                self.real_sfms.append({
                    "name": rp["name"],
                    "rows": [{"qmin": rp["values"][i][::2], "qmax": rp["values"][i][1::2]}
                             for i in range(len(rp["values"]))],
                    "budget": rp["budget"], "period": rp["period"],
                })
            # Топология по умолчанию: А-Б, Б-В, Б-Г, В-Д, Г-Д
            # Индексы: 0=А, 1=Б, 2=В, 3=Г, 4=Д
            if not self.network_edges:
                self.network_edges = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)]

    def _highlight_nav(self, idx):
        for i, b in enumerate(self.nav_btns):
            if i == idx:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {ACCENT}; color: white; border: none;
                        text-align: left; padding: 14px 22px; font-size: {UI_FONT_PT}px; font-weight: bold;
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {PANEL}; color: {TEXT}; border: none;
                        text-align: left; padding: 14px 22px; font-size: {UI_FONT_PT}px;
                    }}
                    QPushButton:hover {{ background: {CARD}; }}
                """)

    def _flush_cur_real_sfm(self):
        """Записать в память данные из открытой формы реальной СФМ (без диалога)."""
        if not hasattr(self, "_cur_edit_idx") or self._cur_edit_idx is None:
            return
        if not hasattr(self, "_cur_table") or self._cur_table is None:
            return
        try:
            _ = self._cur_table.rowCount()
        except RuntimeError:
            return
        self._save_cur_real_silent()

    def _refresh_real_page(self):
        if self.ideal_data is None:
            QMessageBox.warning(self, "Внимание", "Сначала заполните идеальную СФМ (кнопка «Далее» на предыдущей странице).")
            self.pages.setCurrentIndex(1)
            self._highlight_nav(1)
            return

        self._flush_cur_real_sfm()

        for i in reversed(range(self._real_outer.count())):
            w = self._real_outer.itemAt(i).widget()
            if w:
                w.deleteLater()

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        lay.addWidget(_heading("Реальные СФМ ВОЛС"))
        lay.addWidget(_sub("Добавьте системы для сравнения с идеальной моделью"))

        body = QHBoxLayout()

        # Список
        list_card = _card()
        list_card.setFixedWidth(280)
        lcl = QVBoxLayout(list_card)
        lcl.setContentsMargins(10, 12, 10, 12)
        lcl.addWidget(_heading("Список СФМ", ACCENT2, 16))

        self._real_list = QListWidget()
        for sfm in self.real_sfms:
            self._real_list.addItem(sfm["name"])
        self._real_list.currentRowChanged.connect(self._on_real_selected)
        lcl.addWidget(self._real_list, 1)

        add_b = _btn(f"{PH_PLUS} Добавить", OK_CLR)
        add_b.clicked.connect(self._add_real)
        lcl.addWidget(add_b)
        del_b = _btn("Удалить", ERR_CLR)
        del_b.clicked.connect(self._del_real)
        lcl.addWidget(del_b)

        body.addWidget(list_card)

        # Форма редактирования
        self._real_form_area = QScrollArea()
        self._real_form_area.setWidgetResizable(True)
        self._real_form_holder = QWidget()
        self._real_form_area.setWidget(self._real_form_holder)
        body.addWidget(self._real_form_area, 1)
        lay.addLayout(body, 1)

        br = QHBoxLayout()
        calc_b = _btn("Рассчитать результаты", ACCENT, 200, bold=True)
        calc_b.clicked.connect(self._calculate)
        br.addWidget(calc_b)
        br.addStretch()
        lay.addLayout(br)

        self._real_outer.addWidget(container)

        if self.real_sfms:
            self._real_list.setCurrentRow(0)

    def _on_real_selected(self, idx):
        if idx < 0 or idx >= len(self.real_sfms):
            return
        self._flush_cur_real_sfm()
        self._render_real_form(idx)

    def _render_real_form(self, idx):
        sfm = self.real_sfms[idx]
        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(8)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Название:"))
        self._cur_name = QLineEdit(sfm["name"])
        name_row.addWidget(self._cur_name, 1)
        fl.addLayout(name_row)

        # Кнопка редактирования связей
        conn_row = QHBoxLayout()
        conn_row.addWidget(QLabel("Связи с другими участками:"))

        # Показываем текущие связи
        connected = []
        for i, other_sfm in enumerate(self.real_sfms):
            if i != idx:
                if (idx, i) in self.network_edges or (i, idx) in self.network_edges:
                    connected.append(other_sfm["name"])

        conn_label = QLabel(", ".join(connected) if connected else "Нет связей")
        conn_label.setStyleSheet(f"color: {SUB}; padding: 8px;")
        conn_row.addWidget(conn_label, 1)

        edit_conn_btn = _btn("Редактировать связи", ACCENT2)
        edit_conn_btn.clicked.connect(lambda: self._edit_connections(idx))
        conn_row.addWidget(edit_conn_btn)
        fl.addLayout(conn_row)

        table = QTableWidget(self.n_ts, self.n_params * 2 + 2)
        table.setStyleSheet(f"QTableWidget {{ background: {CARD}; }}")
        table.verticalHeader().setVisible(False)

        headers = ["Функция", "ТС"]
        for j in range(self.n_params):
            pn = self.param_names[j] if j < len(self.param_names) else f"P{j+1}"
            pu = self.param_units[j] if j < len(self.param_units) else ""
            headers += [f"{pn}\n({pu}) мин", f"{pn}\n({pu}) макс"]
        table.setHorizontalHeaderLabels(headers)

        for i in range(self.n_ts):
            fn = self.func_names[i] if i < len(self.func_names) else ""
            ts = self.ts_names[i] if i < len(self.ts_names) else ""
            fi = QTableWidgetItem(fn)
            fi.setFlags(fi.flags() & ~Qt.ItemIsEditable)
            fi.setForeground(QColor(SUB))
            table.setItem(i, 0, fi)
            ti = QTableWidgetItem(ts)
            ti.setFlags(ti.flags() & ~Qt.ItemIsEditable)
            ti.setForeground(QColor(SUB))
            table.setItem(i, 1, ti)

            for j in range(self.n_params):
                vm = sfm["rows"][i]["qmin"][j] if i < len(sfm["rows"]) and j < len(sfm["rows"][i]["qmin"]) else None
                vx = sfm["rows"][i]["qmax"][j] if i < len(sfm["rows"]) and j < len(sfm["rows"][i]["qmax"]) else None
                im = QTableWidgetItem(str(vm) if vm is not None else "")
                im.setTextAlignment(Qt.AlignCenter)
                ix = QTableWidgetItem(str(vx) if vx is not None else "")
                ix.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, 2 + j * 2, im)
                table.setItem(i, 2 + j * 2 + 1, ix)

        table.verticalHeader().setDefaultSectionSize(UI_ROW_H)
        _configure_sfm_data_table(table)
        self._cur_table = table
        fl.addWidget(table, 1)

        lim = QHBoxLayout()
        lim.addWidget(QLabel("Бюджет (руб.):"))
        self._cur_budget = QLineEdit(str(sfm.get("budget", "")) if sfm.get("budget") is not None else "")
        lim.addWidget(self._cur_budget)
        lim.addWidget(QLabel("Период (дней):"))
        self._cur_period = QLineEdit(str(sfm.get("period", "")) if sfm.get("period") is not None else "")
        lim.addWidget(self._cur_period)
        fl.addLayout(lim)

        sv = _btn(f"{PH_FLOPPY} Сохранить СФМ", ACCENT)
        self._cur_edit_idx = idx
        sv.clicked.connect(lambda: self._save_cur_real(show_message=True))
        fl.addWidget(sv)

        self._real_form_area.setWidget(form)

    def _save_cur_real_silent(self):
        idx = self._cur_edit_idx
        if idx is None or idx < 0 or idx >= len(self.real_sfms):
            return
        rows = []
        for i in range(self._cur_table.rowCount()):
            qmin, qmax = [], []
            for j in range(self.n_params):
                def _p(c):
                    it = self._cur_table.item(i, c)
                    if not it or not it.text().strip() or it.text().strip() == "-":
                        return None
                    try: return float(it.text())
                    except ValueError: return None
                qmin.append(_p(2 + j * 2))
                qmax.append(_p(2 + j * 2 + 1))
            rows.append({"qmin": qmin, "qmax": qmax})
        try:
            budget = float(self._cur_budget.text().strip()) if self._cur_budget.text().strip() else None
            period = float(self._cur_period.text().strip()) if self._cur_period.text().strip() else None
        except ValueError:
            budget, period = None, None

        self.real_sfms[idx] = {
            "name": self._cur_name.text().strip() or f"Участок {idx+1}",
            "rows": rows, "budget": budget, "period": period,
        }
        if self._real_list.item(idx):
            self._real_list.item(idx).setText(self.real_sfms[idx]["name"])

    def _save_cur_real(self, show_message=True):
        self._save_cur_real_silent()
        if show_message:
            QMessageBox.information(self, "Сохранено", "Реальная СФМ сохранена!")

    def _add_real(self):
        self._flush_cur_real_sfm()

        # Генерируем имя для нового участка
        # Сначала буквы А-Я, потом номера 1, 2, 3...
        russian_letters = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ"
        existing_names = [sfm["name"] for sfm in self.real_sfms]

        new_name = None
        # Пробуем буквы
        for letter in russian_letters:
            candidate = f"Участок {letter}"
            if candidate not in existing_names:
                new_name = candidate
                break

        # Если буквы закончились, используем номера
        if new_name is None:
            num = 1
            while True:
                candidate = f"Участок {num}"
                if candidate not in existing_names:
                    new_name = candidate
                    break
                num += 1

        sfm = {
            "name": new_name,
            "rows": [{"qmin": [None]*self.n_params, "qmax": [None]*self.n_params} for _ in range(self.n_ts)],
            "budget": None, "period": None,
        }
        self.real_sfms.append(sfm)
        new_idx = len(self.real_sfms) - 1
        self._real_list.addItem(sfm["name"])
        self._real_list.setCurrentRow(new_idx)

        # Диалог выбора связей для нового участка
        if len(self.real_sfms) > 1:
            self._edit_connections(new_idx, is_new=True)

    def _edit_connections(self, idx, is_new=False):
        """Диалог редактирования связей участка."""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Связи участка: {self.real_sfms[idx]['name']}")
        dlg.setMinimumSize(400, 350)
        dlg.setStyleSheet(STYLE)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lay.addWidget(_heading("Выберите связанные участки", ACCENT2, 16))
        lay.addWidget(_sub("Отметьте участки, с которыми связан данный участок"))

        conn_list = QListWidget()
        conn_list.setSelectionMode(QAbstractItemView.MultiSelection)

        # Заполняем список всех участков (кроме текущего)
        for i, other_sfm in enumerate(self.real_sfms):
            if i != idx:
                item = QListWidgetItem(other_sfm["name"])
                item.setData(Qt.UserRole, i)
                conn_list.addItem(item)

                # Отмечаем уже существующие связи
                if (idx, i) in self.network_edges or (i, idx) in self.network_edges:
                    item.setSelected(True)

        lay.addWidget(conn_list, 1)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)

        if dlg.exec_() == QDialog.Accepted:
            # Удаляем старые связи для этого участка
            new_edges = []
            for f, t in self.network_edges:
                if f != idx and t != idx:
                    new_edges.append((f, t))

            # Собираем выбранные связи
            selected_indices = []
            for i in range(conn_list.count()):
                item = conn_list.item(i)
                if item.isSelected():
                    other_idx = item.data(Qt.UserRole)
                    selected_indices.append(other_idx)
                    # Добавляем ребро (меньший индекс первым для консистентности)
                    edge = (min(idx, other_idx), max(idx, other_idx))
                    if edge not in new_edges:
                        new_edges.append(edge)

            self.network_edges = new_edges

            # Если это новый участок, вычисляем оптимальную позицию
            if is_new and selected_indices:
                self._compute_new_node_position(idx, selected_indices)

            # Обновляем отображение связей в форме
            if self._cur_edit_idx == idx:
                self._render_real_form(idx)

    def _compute_new_node_position(self, new_idx, connected_indices):
        """Вычислить оптимальную позицию для нового участка на основе его связей."""
        if not connected_indices:
            return

        # Получаем позиции связанных участков
        connected_positions = []
        for conn_idx in connected_indices:
            if conn_idx in self.network_positions:
                pos = self.network_positions[conn_idx]
                connected_positions.append(QPointF(pos[0], pos[1]))

        if not connected_positions:
            # Если нет сохраненных позиций, используем дефолтную раскладку
            return

        # Вычисляем центр масс связанных участков
        avg_x = sum(p.x() for p in connected_positions) / len(connected_positions)
        avg_y = sum(p.y() for p in connected_positions) / len(connected_positions)

        # Пробуем разместить новый узел в разных позициях относительно центра
        gap = 500
        offset_y = 150

        # Варианты позиций: справа, справа-сверху, справа-снизу, слева, слева-сверху, слева-снизу
        candidate_positions = [
            QPointF(avg_x + gap, avg_y),
            QPointF(avg_x + gap, avg_y - offset_y),
            QPointF(avg_x + gap, avg_y + offset_y),
            QPointF(avg_x - gap, avg_y),
            QPointF(avg_x - gap, avg_y - offset_y),
            QPointF(avg_x - gap, avg_y + offset_y),
            QPointF(avg_x, avg_y + gap),
            QPointF(avg_x, avg_y - gap),
        ]

        # Находим свободную позицию (не слишком близко к существующим)
        min_distance = 400
        best_pos = candidate_positions[0]
        max_min_dist = 0

        for candidate in candidate_positions:
            # Вычисляем минимальное расстояние до существующих узлов
            min_dist_to_existing = float('inf')
            for existing_idx, existing_pos in self.network_positions.items():
                if existing_idx != new_idx:
                    ex_point = QPointF(existing_pos[0], existing_pos[1])
                    dist = ((candidate.x() - ex_point.x())**2 + (candidate.y() - ex_point.y())**2)**0.5
                    min_dist_to_existing = min(min_dist_to_existing, dist)

            # Выбираем позицию с максимальным минимальным расстоянием
            if min_dist_to_existing > max_min_dist:
                max_min_dist = min_dist_to_existing
                best_pos = candidate

        # Сохраняем позицию
        self.network_positions[new_idx] = (best_pos.x(), best_pos.y())

    def _del_real(self):
        idx = self._real_list.currentRow()
        if idx < 0:
            return
        if len(self.real_sfms) <= 1:
            QMessageBox.warning(self, "Ошибка", "Должна остаться хотя бы одна реальная СФМ.")
            return
        self._flush_cur_real_sfm()
        self.real_sfms.pop(idx)
        self._real_list.takeItem(idx)
        self._cur_edit_idx = None
        # Удаляем рёбра, связанные с этим узлом, и сдвигаем индексы
        new_edges = []
        for f, t in self.network_edges:
            if f == idx or t == idx:
                continue  # удаляем ребро
            new_f = f - 1 if f > idx else f
            new_t = t - 1 if t > idx else t
            new_edges.append((new_f, new_t))
        self.network_edges = new_edges
        # Сдвигаем позиции
        new_pos = {}
        for k, v in self.network_positions.items():
            if k == idx:
                continue
            new_k = k - 1 if k > idx else k
            new_pos[new_k] = v
        self.network_positions = new_pos

        if self.real_sfms:
            self._real_list.setCurrentRow(min(idx, len(self.real_sfms) - 1))

    # ─────────────────────────────────────
    #  Расчёт
    # ─────────────────────────────────────

    def _calculate(self):
        self._flush_cur_real_sfm()
        if not self.ideal_data:
            QMessageBox.warning(self, "Ошибка", "Заполните идеальную СФМ (страница «Идеальная СФМ», затем «Далее»).")
            return
        if not self.real_sfms:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну реальную СФМ!")
            return

        base_sfm = self._ideal_to_sfmdata()
        real_list = [self._real_to_sfmdata(r) for r in self.real_sfms]

        for i, r in enumerate(real_list):
            if r.values.shape != base_sfm.values.shape:
                QMessageBox.warning(self, "Ошибка",
                    f"Размерности таблиц не совпадают (реальная СФМ {i+1}).")
                return

        comparisons, rating, q_weights = run_full_analysis(base_sfm, real_list)
        self._last_base = base_sfm
        self._last_reals = real_list
        self._last_comps = comparisons
        self._last_rating = rating
        self._last_qw = q_weights

        self._update_schema_colors()

        n_valid = sum(1 for c in comparisons if not c.has_negative and c.budget_ok and c.period_ok)
        QMessageBox.information(self, "Расчёт завершён",
            f"Обработано СФМ: {len(comparisons)}\n"
            f"Допустимых: {n_valid}\n"
            f"Отбракованных: {len(comparisons) - n_valid}")
        self._go(3)  # Переход на страницу схемы

    def _ideal_to_sfmdata(self) -> SFMData:
        vals = []
        for row in self.ideal_data["rows"]:
            v = []
            for j in range(self.n_params):
                v.append(row["qmin"][j] if row["qmin"][j] is not None else 0.0)
                v.append(row["qmax"][j] if row["qmax"][j] is not None else 0.0)
            vals.append(v)
        return SFMData(
            name="Идеальная", goal="", date="",
            functions=self.func_names[:self.n_ts],
            ts_names=[[t] for t in self.ts_names[:self.n_ts]],
            param_names=self.param_names, param_units=self.param_units,
            values=np.array(vals, dtype=float),
            total_budget=self.ideal_data.get("budget") or 1e18,
            budget_real=self.ideal_data.get("budget") or 1e18,
            eval_period=self.ideal_data.get("period") or 0,
            period_real=self.ideal_data.get("period") or 0,
        )

    def _real_to_sfmdata(self, r) -> SFMData:
        vals = []
        for row in r["rows"]:
            v = []
            for j in range(self.n_params):
                v.append(row["qmin"][j] if j < len(row["qmin"]) and row["qmin"][j] is not None else 0.0)
                v.append(row["qmax"][j] if j < len(row["qmax"]) and row["qmax"][j] is not None else 0.0)
            vals.append(v)
        return SFMData(
            name=r["name"], goal="", date="",
            functions=self.func_names[:self.n_ts],
            ts_names=[[t] for t in self.ts_names[:self.n_ts]],
            param_names=self.param_names, param_units=self.param_units,
            values=np.array(vals, dtype=float),
            total_budget=self.ideal_data.get("budget") or 1e18,
            budget_real=r.get("budget") or 0,
            eval_period=self.ideal_data.get("period") or 0,
            period_real=r.get("period") or 1e18,
        )

    # ─────────────────────────────────────
    #  PAGE 3 — Результаты
    # ─────────────────────────────────────

    def _build_page_results(self):
        self._res_page = QWidget()
        self._res_lay = QVBoxLayout(self._res_page)
        self._res_lay.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(self._res_page)

    def _fill_results_page(self):
        for i in reversed(range(self._res_lay.count())):
            w = self._res_lay.itemAt(i).widget()
            if w: w.deleteLater()

        if not hasattr(self, "_last_comps") or not self._last_comps:
            lbl = QLabel("Нет данных. Сначала выполните расчёт.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {SUB}; font-size: 16px; padding: 60px;")
            self._res_lay.addWidget(lbl)
            b = _btn("Рассчитать", ACCENT)
            b.clicked.connect(self._calculate)
            self._res_lay.addWidget(b, 0, Qt.AlignCenter)
            return

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(12)

        cl.addWidget(_heading("Результаты сравнения СФМ"))
        cl.addWidget(_sub("Краткая сводка по каждой реальной системе"))

        # Сводная таблица
        n = len(self._last_comps)
        summary = QTableWidget(n, 3)
        summary.setHorizontalHeaderLabels(["Реальная СФМ", "Статус", "Qкэ"])
        summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary.verticalHeader().setVisible(False)
        summary.setEditTriggers(QAbstractItemView.NoEditTriggers)
        summary.setSelectionMode(QAbstractItemView.NoSelection)

        for idx, comp in enumerate(self._last_comps):
            is_valid = not comp.has_negative and comp.budget_ok and comp.period_ok

            name_item = QTableWidgetItem(comp.real_name)
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setForeground(QColor(TEXT))
            name_item.setFont(_ui_font(UI_FONT_PT))
            summary.setItem(idx, 0, name_item)

            if is_valid:
                s_text, s_clr = f"{PH_CHECK} Соответствует", OK_CLR
            else:
                reasons = []
                if comp.has_negative: reasons.append("ΔQ<0")
                if not comp.budget_ok: reasons.append("бюджет")
                if not comp.period_ok: reasons.append("период")
                s_text = f"{PH_X} Не соотв. ({', '.join(reasons)})"
                s_clr = ERR_CLR
            s_item = QTableWidgetItem(s_text)
            s_item.setTextAlignment(Qt.AlignCenter)
            s_item.setForeground(QColor(s_clr))
            s_item.setFont(_ui_font(UI_FONT_PT))
            summary.setItem(idx, 1, s_item)

            q_item = QTableWidgetItem(f"{comp.Q_ke:.6f}")
            q_item.setTextAlignment(Qt.AlignCenter)
            q_item.setForeground(QColor(ACCENT2))
            q_item.setFont(_ui_font(UI_FONT_PT))
            summary.setItem(idx, 2, q_item)

        summary.setFixedHeight(n * UI_ROW_H + 44)
        cl.addWidget(summary)

        # Кнопка «Показать все вычисления»
        show_btn = _btn(f"{PH_TABLE}  Показать все вычисления (матрицы)", ACCENT, 320, bold=True)
        show_btn.clicked.connect(self._open_detailed_calculations)
        cl.addWidget(show_btn, 0, Qt.AlignCenter)

        cl.addStretch()
        scroll.setWidget(content)
        self._res_lay.addWidget(scroll)

    def _open_detailed_calculations(self):
        """Открыть отдельное окно со всеми матрицами пошагово."""
        if not hasattr(self, "_last_comps") or not self._last_comps:
            return

        from PyQt5.QtWidgets import QTabWidget
        win = QWidget()
        win.setWindowTitle("Подробные вычисления — СФМ ВОЛС")
        win.setWindowIcon(_app_icon())
        win.setStyleSheet(STYLE)
        win.resize(1280, 880)
        win.setMinimumSize(960, 640)

        outer = QVBoxLayout(win)
        outer.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {BORDER}; background: {BG}; }}
            QTabBar::tab {{
                background: {PANEL}; color: {TEXT}; padding: 12px 20px; font-size: {UI_FONT_PT}px;
                border: 1px solid {BORDER}; border-bottom: none;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{ background: {ACCENT}; color: white; font-weight: bold; }}
        """)

        for idx, comp in enumerate(self._last_comps):
            tab_scroll = QScrollArea()
            tab_scroll.setWidgetResizable(True)
            tab_w = QWidget()
            tl = QVBoxLayout(tab_w)
            tl.setContentsMargins(20, 16, 20, 16)
            tl.setSpacing(6)

            is_valid = not comp.has_negative and comp.budget_ok and comp.period_ok
            color = OK_CLR if is_valid else ERR_CLR

            tl.addWidget(_heading(f"Вычисления: {comp.real_name}", ACCENT, 19))

            status = "СООТВЕТСТВУЕТ" if is_valid else "НЕ СООТВЕТСТВУЕТ"
            sl = QLabel(f"{PH_CHECK if is_valid else PH_X} {status} требованиям")
            sl.setFont(_ui_font(16, bold=True))
            sl.setStyleSheet(f"color: {color};")
            tl.addWidget(sl)

            if not is_valid:
                reasons = []
                if comp.has_negative: reasons.append("Отрицательные ΔQ")
                if not comp.budget_ok: reasons.append("Бюджет превышен")
                if not comp.period_ok: reasons.append("Период не выполнен")
                rl2 = QLabel("; ".join(reasons))
                rl2.setStyleSheet(f"color: {WARN}; font-size: {UI_FONT_SMALL}px;")
                tl.addWidget(rl2)

            ql = QLabel(f"Qкэ = {comp.Q_ke:.6f}")
            ql.setFont(_ui_font(17, bold=True))
            ql.setStyleSheet(f"color: {ACCENT2};")
            tl.addWidget(ql)

            m_r, n_c = comp.C_Q.shape
            row_lb = [self.ts_names[i] if i < len(self.ts_names) else f"ТС{i+1}" for i in range(m_r)]
            col_lb = []
            for j in range(self.n_params):
                pn = self.param_names[j][:12] if j < len(self.param_names) else f"P{j+1}"
                col_lb += [f"{pn} min", f"{pn} max"]

            tl.addWidget(_heading("Этап 1. Базовые матрицы", ACCENT2, 17))
            tl.addWidget(self._matrix_block("BQ1 (идеальная, группа 1 — мин.)", comp.B_Q1, row_lb, col_lb, ACCENT))
            tl.addWidget(self._matrix_block("BQ2 (идеальная, группа 2 — макс.)", comp.B_Q2, row_lb, col_lb, ACCENT))

            tl.addWidget(_heading("Этап 2. Реальные матрицы", ACCENT2, 17))
            tl.addWidget(self._matrix_block("RQ1 (реальная, группа 1)", comp.R_Q1, row_lb, col_lb, ACCENT2))
            tl.addWidget(self._matrix_block("RQ2 (реальная, группа 2)", comp.R_Q2, row_lb, col_lb, ACCENT2))

            tl.addWidget(_heading("Этап 3. Сравнение", ACCENT2, 17))
            tl.addWidget(self._matrix_block("CQ1 = BQ1 − RQ1", comp.C_Q1, row_lb, col_lb, WARN))
            tl.addWidget(self._matrix_block("CQ2 = RQ2 − BQ2", comp.C_Q2, row_lb, col_lb, WARN))
            tl.addWidget(self._matrix_block("CQ = CQ1 + CQ2 (итоговая разность)", comp.C_Q, row_lb, col_lb, color))

            tl.addWidget(_heading("Весовые коэффициенты и Qкэ", ACCENT2, 17))
            q2d = comp.q_weights.reshape(m_r, n_c) if comp.q_weights.size == m_r * n_c else comp.q_weights
            tl.addWidget(self._matrix_block("Весовые коэффициенты q_l", q2d, row_lb, col_lb, ACCENT2, fmt=".6f"))

            wt = comp.weighted_table.reshape(m_r, n_c) if comp.weighted_table.size == m_r * n_c else comp.weighted_table
            tl.addWidget(self._matrix_block("q_l × ΔQ_l", wt, row_lb, col_lb, ACCENT, fmt=".6f"))

            qke_box = QLabel(f"  Qкэ = Σ(q_l × ΔQ_l) = {comp.Q_ke:.6f}  ")
            qke_box.setFont(_ui_font(20, bold=True))
            qke_box.setAlignment(Qt.AlignCenter)
            qke_box.setStyleSheet(
                f"color: {TEXT}; background: {PANEL}; border: 2px solid {ACCENT};"
                f"border-radius: 8px; padding: 16px; margin: 12px 0;"
            )
            tl.addWidget(qke_box)

            tl.addStretch()
            tab_scroll.setWidget(tab_w)
            tabs.addTab(tab_scroll, comp.real_name[:20])

        outer.addWidget(tabs)

        self._detail_win = win
        win.show()

    def _matrix_block(self, title, matrix, row_labels, col_labels, color, fmt=".3f"):
        card = _card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(4)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: {UI_FONT_SMALL}px;")
        cl.addWidget(lbl)

        r, c = matrix.shape
        table = QTableWidget(r, c)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        if col_labels:
            table.setHorizontalHeaderLabels(col_labels[:c])
        mh = table.horizontalHeader()
        mh.setMinimumHeight(52)
        mh.setDefaultAlignment(Qt.AlignCenter | Qt.AlignVCenter | Qt.TextWordWrap)
        for col in range(c):
            mh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        mh.setMinimumSectionSize(72)
        table.verticalHeader().setDefaultSectionSize(UI_ROW_H)

        for i in range(r):
            for j in range(c):
                v = matrix[i, j]
                txt = f"{v:{fmt}}" if v != 0 else "0"
                item = QTableWidgetItem(txt)
                item.setFont(_ui_font(UI_FONT_SMALL))
                item.setTextAlignment(Qt.AlignCenter)
                if v < -1e-9:
                    item.setForeground(QColor(ERR_CLR))
                table.setItem(i, j, item)
        for col in range(c):
            table.resizeColumnToContents(col)
        table.setFixedHeight(r * UI_ROW_H + 58)
        cl.addWidget(table)
        return card

    # ─────────────────────────────────────
    #  PAGE 4 — Рейтинг
    # ─────────────────────────────────────

    def _build_page_rating(self):
        self._rat_page = QWidget()
        self._rat_lay = QVBoxLayout(self._rat_page)
        self._rat_lay.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(self._rat_page)

    def _fill_rating_page(self):
        for i in reversed(range(self._rat_lay.count())):
            w = self._rat_lay.itemAt(i).widget()
            if w: w.deleteLater()

        if not hasattr(self, "_last_comps") or not self._last_comps:
            lbl = QLabel("Нет данных. Сначала выполните расчёт.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {SUB}; font-size: 16px; padding: 60px;")
            self._rat_lay.addWidget(lbl)
            return

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(12)

        cl.addWidget(_heading("Рейтинг качества ВОЛС"))
        cl.addWidget(_sub("Чем выше Qкэ — тем лучше качество системы"))

        valid = [(c, c.Q_ke) for c in self._last_comps
                 if not c.has_negative and c.budget_ok and c.period_ok]
        invalid = [(c, None) for c in self._last_comps
                   if c.has_negative or not c.budget_ok or not c.period_ok]
        valid.sort(key=lambda x: -x[1])
        ranked = valid + invalid

        table = QTableWidget(len(ranked), 4)
        table.setHorizontalHeaderLabels(["Место", "Название СФМ", "Qкэ", "Статус"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        place = 1
        prev_qke = None
        for ri, (comp, qke) in enumerate(ranked):
            if qke is not None:
                if prev_qke is not None and abs(qke - prev_qke) > 1e-9:
                    place = ri + 1
                if place == 1:
                    pl_text = PH_NUM_1
                elif place == 2:
                    pl_text = PH_NUM_2
                elif place == 3:
                    pl_text = PH_NUM_3
                else:
                    pl_text = str(place)
                q_text = f"{qke:.6f}"
                s_text = f"{PH_CHECK} Допустима"
                s_color = OK_CLR
                prev_qke = qke
            else:
                pl_text = "—"
                q_text = "—"
                s_text = f"{PH_X} Отбракована"
                s_color = ERR_CLR

            items = [
                (pl_text, WARN if qke else SUB),
                (comp.real_name, TEXT),
                (q_text, ACCENT2 if qke else SUB),
                (s_text, s_color),
            ]
            for j, (txt, clr) in enumerate(items):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(clr))
                it.setFont(_ui_font(UI_FONT_PT))
                table.setItem(ri, j, it)

        table.setFixedHeight(len(ranked) * UI_ROW_H + 44)
        cl.addWidget(table)

        # Диаграмма
        valid_data = [(c.real_name, c.Q_ke) for c, q in valid]
        if valid_data:
            fig = Figure(figsize=(11, 4.2), dpi=100)
            fig.patch.set_facecolor(BG)

            ax1 = fig.add_subplot(121)
            ax1.set_facecolor(PANEL)
            names = [v[0][:18] for v in valid_data]
            qkes = [v[1] for v in valid_data]
            max_q = max(qkes)
            colors = [ACCENT if q == max_q else ACCENT2 for q in qkes]
            bars = ax1.bar(names, qkes, color=colors, edgecolor=BORDER, linewidth=0.8)
            ax1.set_title("Комплексный показатель Qкэ", color=TEXT, fontsize=13)
            ax1.set_ylabel("Qкэ", color=SUB, fontsize=12)
            ax1.tick_params(colors=SUB, labelsize=11)
            for sp in ax1.spines.values():
                sp.set_color(BORDER)
            for b, v in zip(bars, qkes):
                ax1.text(b.get_x() + b.get_width()/2, b.get_height(),
                         f"{v:.4f}", ha="center", va="bottom", color=TEXT, fontsize=10)

            ax2 = fig.add_subplot(122)
            ax2.set_facecolor(PANEL)
            if len(valid_data) > 1:
                pie_colors = [ACCENT, ACCENT2, OK_CLR, WARN, ERR_CLR, "#bd93f9", "#8be9fd"]
                ax2.pie(qkes, labels=names, autopct="%1.1f%%",
                        colors=pie_colors[:len(qkes)],
                        textprops={"color": TEXT, "fontsize": 10})
                ax2.set_title("Доля в суммарном Qкэ", color=TEXT, fontsize=13)
            else:
                ax2.text(0.5, 0.5, "Добавьте ≥2 СФМ\nдля сравнения",
                         ha="center", va="center", color=SUB, fontsize=13,
                         transform=ax2.transAxes)
                ax2.set_axis_off()

            fig.tight_layout(pad=1.5)
            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(420)
            cl.addWidget(canvas)

        cl.addStretch()
        scroll.setWidget(content)
        self._rat_lay.addWidget(scroll)

    # ─────────────────────────────────────
    #  PAGE 5 — Схема ВОЛС (топология с рёбрами)
    # ─────────────────────────────────────

    def _build_page_schema(self):
        self._schema_page = QWidget()
        self._schema_lay = QVBoxLayout(self._schema_page)
        self._schema_lay.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(self._schema_page)

    def _fill_schema_page(self):
        for i in reversed(range(self._schema_lay.count())):
            w = self._schema_lay.itemAt(i).widget()
            if w:
                w.deleteLater()

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        cl.addWidget(_heading("Схема ВОЛС — Топология сети"))
        cl.addWidget(_sub(
            "Участки (А, Б, В, Г, Д) — узлы сети с устройствами. Линии показывают связи между участками. "
            "Перетаскивайте участки мышью для изменения раскладки. "
            "Колёсико мыши — масштаб. "
            "Нажмите на устройство для просмотра подробностей."
        ))

        # Виджет схемы (со встроенным QGraphicsView + зум)
        self._schema_widget = SchemaWidget(self)
        self._schema_widget.setMinimumHeight(500)

        # Применяем сохранённые позиции точек
        if self.network_positions:
            self._schema_widget._point_positions = {
                k: QPointF(v[0], v[1]) for k, v in self.network_positions.items()
            }
        cl.addWidget(self._schema_widget, 1)
        # Цвета задаём до редрава
        self._update_schema_colors()  # вызывает set_colors -> _redraw

        # Автоматический масштаб при открытии
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._schema_widget._fit_in_view)

        # Легенда
        legend = QHBoxLayout()
        for lbl_text, clr in [("Норма", OK_CLR), ("Отклонение", ERR_CLR), ("Не рассчитано", PANEL)]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {clr}; font-size: 18px;")
            dot.setFixedWidth(22)
            legend.addWidget(dot)
            ll = QLabel(lbl_text)
            ll.setFont(_ui_font(12))
            ll.setStyleSheet(f"color: {SUB};")
            legend.addWidget(ll)
            legend.addSpacing(16)
        legend.addStretch()
        cl.addLayout(legend)

        cl.addStretch()
        self._schema_lay.addWidget(content)

    def _save_topology(self):
        """Сохранить позиции участков из SchemaWidget."""
        if hasattr(self, "_schema_widget") and hasattr(self._schema_widget, "_point_items"):
            for idx, item in self._schema_widget._point_items.items():
                self._schema_widget._point_positions[idx] = item.pos()
        self.network_positions = {}
        if hasattr(self, "_schema_widget"):
            for k, pos in self._schema_widget._point_positions.items():
                self.network_positions[k] = (pos.x(), pos.y())

    def _update_schema_colors(self):
        """Раскрасить устройства на схеме по результатам расчёта."""
        colors = {}
        if hasattr(self, "_last_comps") and self._last_comps:
            for sfm_idx, comp in enumerate(self._last_comps):
                is_valid_global = not comp.has_negative and comp.budget_ok and comp.period_ok
                for ts_i in range(comp.C_Q.shape[0]):
                    row = comp.C_Q[ts_i]
                    has_neg_in_row = any(v < -1e-9 for v in row)
                    if has_neg_in_row or not is_valid_global:
                        colors[(sfm_idx, ts_i)] = QColor(ERR_CLR)
                    else:
                        colors[(sfm_idx, ts_i)] = QColor(OK_CLR)
        if hasattr(self, "_schema_widget"):
            self._schema_widget.set_colors(colors)

    def _show_device_info(self, sfm_idx, ts_idx):
        """Диалог с подробной информацией об устройстве."""
        if sfm_idx >= len(self.real_sfms):
            return
        sfm = self.real_sfms[sfm_idx]
        ts_name = self.ts_names[ts_idx] if ts_idx < len(self.ts_names) else f"ТС {ts_idx+1}"
        func_name = self.func_names[ts_idx] if ts_idx < len(self.func_names) else "—"

        from PyQt5.QtWidgets import QDialog, QDialogButtonBox

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Устройство {ts_idx+1}: {ts_name}")
        dlg.setMinimumSize(700, 420)
        dlg.setStyleSheet(STYLE)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(8)

        lay.addWidget(_heading(f"{ts_idx+1}. {ts_name}", ACCENT, 18))
        lay.addWidget(_sub(f"Участок: {sfm['name']}"))
        lay.addWidget(_sub(f"Функция: {func_name}"))

        n_p = self.n_params
        has_results = hasattr(self, "_last_comps") and self._last_comps and sfm_idx < len(self._last_comps)
        n_cols = 5 if has_results else 4
        table = QTableWidget(n_p, n_cols)
        headers = ["Показатель", "Идеал мин", "Идеал макс", "Реал мин", "Реал макс"]
        if has_results:
            headers = ["Показатель", "Идеал мин", "Идеал макс", "Реал мин", "Реал макс"]
            n_cols = 6
            table = QTableWidget(n_p, n_cols)
            headers.append("ΔQ")
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for j in range(n_p):
            pn = self.param_names[j] if j < len(self.param_names) else f"P{j+1}"
            pu = self.param_units[j] if j < len(self.param_units) else ""
            name_item = QTableWidgetItem(f"{pn} ({pu})")
            name_item.setFont(_ui_font(UI_FONT_SMALL))
            table.setItem(j, 0, name_item)

            ideal_min_v = ideal_max_v = "—"
            if self.ideal_data and ts_idx < len(self.ideal_data.get("rows", [])):
                row_id = self.ideal_data["rows"][ts_idx]
                vm = row_id["qmin"][j] if j < len(row_id["qmin"]) else None
                vx = row_id["qmax"][j] if j < len(row_id["qmax"]) else None
                if vm is not None:
                    ideal_min_v = str(vm)
                if vx is not None:
                    ideal_max_v = str(vx)

            real_min_v = real_max_v = "—"
            if ts_idx < len(sfm["rows"]) and j < len(sfm["rows"][ts_idx]["qmin"]):
                rm = sfm["rows"][ts_idx]["qmin"][j]
                rx = sfm["rows"][ts_idx]["qmax"][j]
                if rm is not None:
                    real_min_v = str(rm)
                if rx is not None:
                    real_max_v = str(rx)

            for ci, val in [(1, ideal_min_v), (2, ideal_max_v), (3, real_min_v), (4, real_max_v)]:
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignCenter)
                it.setFont(_ui_font(UI_FONT_SMALL))
                table.setItem(j, ci, it)

            if has_results:
                comp = self._last_comps[sfm_idx]
                cq_min = comp.C_Q[ts_idx, j * 2] if ts_idx < comp.C_Q.shape[0] else 0
                cq_max = comp.C_Q[ts_idx, j * 2 + 1] if ts_idx < comp.C_Q.shape[0] else 0
                dq_text = f"{cq_min:+.3f} / {cq_max:+.3f}"
                dq_item = QTableWidgetItem(dq_text)
                dq_item.setTextAlignment(Qt.AlignCenter)
                dq_item.setFont(_ui_font(UI_FONT_SMALL))
                if cq_min < -1e-9 or cq_max < -1e-9:
                    dq_item.setForeground(QColor(ERR_CLR))
                else:
                    dq_item.setForeground(QColor(OK_CLR))
                table.setItem(j, 5, dq_item)

        table.setMinimumHeight(n_p * UI_ROW_H + 44)
        lay.addWidget(table, 1)

        if has_results:
            comp = self._last_comps[sfm_idx]
            row_cq = comp.C_Q[ts_idx] if ts_idx < comp.C_Q.shape[0] else None
            if row_cq is not None:
                has_neg = any(v < -1e-9 for v in row_cq)
                if has_neg:
                    status_text = f"{PH_X} Устройство НЕ соответствует требованиям"
                    status_clr = ERR_CLR
                else:
                    status_text = f"{PH_CHECK} Устройство соответствует требованиям"
                    status_clr = OK_CLR
                sl = QLabel(status_text)
                sl.setFont(_ui_font(14, bold=True))
                sl.setStyleSheet(f"color: {status_clr};")
                sl.setAlignment(Qt.AlignCenter)
                lay.addWidget(sl)

        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(dlg.accept)
        lay.addWidget(bb)
        dlg.exec_()

    # ─── IO ───

    def _save_project(self):
        import json
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить проект", "", "JSON (*.json)")
        if not path:
            return
        data = {
            "n_params": self.n_params, "n_ts": self.n_ts,
            "param_names": self.param_names, "param_units": self.param_units,
            "ts_names": self.ts_names, "func_names": self.func_names,
            "ideal_data": self.ideal_data, "real_sfms": self.real_sfms,
            "network_edges": [list(e) for e in self.network_edges],
            "network_positions": {str(k): list(v) for k, v in self.network_positions.items()},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "Сохранено", f"Проект: {path}")

    def _load_project(self):
        import json
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить проект", "", "JSON (*.json)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.n_params = data.get("n_params", 3)
        self.n_ts = data.get("n_ts", 3)
        self.param_names = data.get("param_names", [])
        self.param_units = data.get("param_units", [])
        self.ts_names = data.get("ts_names", [])
        self.func_names = data.get("func_names", [])
        self.ideal_data = data.get("ideal_data")
        self.real_sfms = data.get("real_sfms", [])
        self.network_edges = [tuple(e) for e in data.get("network_edges", [])]
        self.network_positions = {int(k): tuple(v) for k, v in data.get("network_positions", {}).items()}
        self.results = []
        QMessageBox.information(self, "Загружено", "Проект загружен!")
        self._go(0)


def main():
    app = QApplication(sys.argv)
    _load_phosphor()
    app.setWindowIcon(_app_icon())
    app.setStyle("Fusion")
    light = QPalette()
    light.setColor(QPalette.Window, QColor(BG))
    light.setColor(QPalette.WindowText, QColor(TEXT))
    light.setColor(QPalette.Base, QColor(ENTRY))
    light.setColor(QPalette.Text, QColor(TEXT))
    light.setColor(QPalette.Button, QColor(PANEL))
    light.setColor(QPalette.ButtonText, QColor(TEXT))
    light.setColor(QPalette.Highlight, QColor(ACCENT))
    light.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(light)
    app.setStyleSheet(STYLE)
    app.setFont(_ui_font(UI_FONT_PT))

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
