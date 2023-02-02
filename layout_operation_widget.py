from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QDateTimeEdit,
    QLabel,
    QComboBox
)

from PyQt6.QtGui import QPalette, QColor

from config import Config
from widget_state_label import StateLabel

import matplotlib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

matplotlib.use('Qt5Agg')


# Utilities
class MplCanvas(FigureCanvasQTAgg):
    """
    Matplotlib helper function
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class OperationWindow(QWidget):

    def __init__(self, config: Config):
        super(OperationWindow, self).__init__()
        self.hlayout = QHBoxLayout()

        self.left_col = QVBoxLayout()
        self.right_col = QVBoxLayout()

        self.status_row = QHBoxLayout()
        self.errors_row = QHBoxLayout()
        self.init_stop_row = QHBoxLayout()
        self.start_stop_row = QHBoxLayout()
        self.set_time_row = QHBoxLayout()

        self.init_label = StateLabel(["Uninitialised", "Initialised"], ["#ff4040", "#63ff6b"], curr=0, parent=self)
        self.start_label = StateLabel(["Stopped", "Started"], ["#ff4040", "#63ff6b"], curr=0, parent=self)

        self.test_mode_check = QCheckBox("Test Mode", parent=self)

        self.init_button = QPushButton("Init Payload", parent=self)
        self.start_operation = QPushButton("Start Operation", parent=self)
        self.stop_operation = QPushButton("Stop Operation", parent=self)
        self.stop_payl_button = QPushButton("Stop Payload", parent=self)

        self.current_time_check = QCheckBox("Current Time", parent=self)
        self.set_time_button = QPushButton("Set Time", parent=self)
        self.date_picker = QDateTimeEdit(parent=self)

        self.status_row.addWidget(self.init_label)
        self.status_row.addWidget(self.start_label)

        self.init_stop_row.addWidget(self.init_button)
        self.init_stop_row.addWidget(self.stop_payl_button)

        self.start_stop_row.addWidget(self.start_operation)
        self.start_stop_row.addWidget(self.stop_operation)

        self.set_time_row.addWidget(self.set_time_button)
        self.set_time_row.addWidget(self.current_time_check)

        self.left_col.addLayout(self.status_row)
        self.left_col.addWidget(self.test_mode_check)
        self.left_col.addLayout(self.init_stop_row)
        self.left_col.addLayout(self.start_stop_row)
        self.left_col.addLayout(self.set_time_row)
        self.left_col.addWidget(self.date_picker)
        self.left_col.addStretch()

        self.param_select_row = QHBoxLayout()

        self.param_select_label = QLabel("Parameter: ", parent=self)
        self.param_select_combo = QComboBox(parent=self)
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.param_select_row.addWidget(self.param_select_label)
        self.param_select_row.addWidget(self.param_select_combo)

        self.right_col.addLayout(self.param_select_row)
        self.right_col.addWidget(self.toolbar)
        self.right_col.addWidget(self.canvas)

        self.hlayout.addLayout(self.left_col)
        self.hlayout.addLayout(self.right_col)

        self.setLayout(self.hlayout)
