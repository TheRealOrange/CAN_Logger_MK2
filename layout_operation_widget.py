import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QDateTimeEdit,
    QLabel,
    QComboBox, QSpinBox, QSizePolicy, QMessageBox
)

from PyQt6.QtGui import QPalette, QColor, QFont

from config import Config
from widget_state_label import StateLabel

import matplotlib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from driver_mk2 import *

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
        self.timer = None
        self.config = config

        self.hlayout = QHBoxLayout()

        self.left_col = QVBoxLayout()
        self.right_col = QVBoxLayout()

        self.sel_ecu_row = QHBoxLayout()
        self.status_row = QHBoxLayout()
        self.errors_row1 = QHBoxLayout()
        self.errors_row2 = QHBoxLayout()
        self.init_stop_row = QHBoxLayout()
        self.start_stop_row = QHBoxLayout()
        self.set_time_row = QHBoxLayout()

        self.logging_ind_row = QHBoxLayout()
        self.logging_period_row = QHBoxLayout()

        self.ecu_sel_combo = QComboBox()
        self.ecu_sel_combo.addItems(['ECU 1', 'ECU 2'])

        self.init_label = StateLabel(["Uninitialised", "Initialised"], ["#ff4040", "#63ff6b"], curr=0, parent=self)
        self.start_label = StateLabel(["Stopped", "Started"], ["#ff4040", "#63ff6b"], curr=0, parent=self)

        self.error_vector1_label = QLabel(f"0x{0:0>4X}", parent=self)
        self.error_vector1_label.setFont(QFont('Consolas'))

        self.error_vector2_label = QLabel(f"0x{0:0>4X}", parent=self)
        self.error_vector2_label.setFont(QFont('Consolas'))

        self.test_mode_check = QCheckBox("Test Mode", parent=self)

        self.init_button = QPushButton("Init Payload", parent=self)
        self.start_operation = QPushButton("Start Operation", parent=self)
        self.stop_operation = QPushButton("Stop Operation", parent=self)
        self.stop_payl_button = QPushButton("Stop Payload", parent=self)

        self.current_time_check = QCheckBox("Current Time", parent=self)
        self.set_time_button = QPushButton("Set Time", parent=self)
        self.date_picker = QDateTimeEdit(parent=self)

        self.logging_ind_label = QLabel("Logging", parent=self)
        self.logging_label = StateLabel(["Stopped", "Started"], ["#ff4040", "#63ff6b"], curr=0, parent=self)
        self.logging_period1_label = QLabel("Period: ")
        self.logging_period = QSpinBox()
        self.logging_period.setMinimum(50)
        self.logging_period.setValue(500)
        self.logging_period.setMaximum(10000)
        self.logging_period2_label = QLabel("ms")
        self.logging_period2_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.logging_period2_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.logging_period2_label.setFixedWidth(30)

        self.logging_toggle = QPushButton("Start Log")

        self.sel_ecu_row.addWidget(QLabel("Selected ECU", parent=self))
        self.sel_ecu_row.addWidget(self.ecu_sel_combo)

        self.status_row.addWidget(self.init_label)
        self.status_row.addWidget(self.start_label)

        self.errors_row1.addWidget(QLabel("Error Vector 1:", parent=self))
        self.errors_row1.addWidget(self.error_vector1_label)

        self.errors_row2.addWidget(QLabel("Error Vector 2:", parent=self))
        self.errors_row2.addWidget(self.error_vector2_label)

        self.init_stop_row.addWidget(self.init_button)
        self.init_stop_row.addWidget(self.stop_payl_button)

        self.start_stop_row.addWidget(self.start_operation)
        self.start_stop_row.addWidget(self.stop_operation)

        self.set_time_row.addWidget(self.set_time_button)
        self.set_time_row.addWidget(self.current_time_check)

        self.logging_ind_row.addWidget(self.logging_ind_label)
        self.logging_ind_row.addWidget(self.logging_label)

        self.logging_period_row.addWidget(self.logging_period1_label)
        self.logging_period_row.addWidget(self.logging_period)
        self.logging_period_row.addWidget(self.logging_period2_label)

        self.left_col.addLayout(self.sel_ecu_row)
        self.left_col.addLayout(self.status_row)
        self.left_col.addLayout(self.errors_row1)
        self.left_col.addLayout(self.errors_row2)
        self.left_col.addWidget(self.test_mode_check)
        self.left_col.addLayout(self.init_stop_row)
        self.left_col.addLayout(self.start_stop_row)
        self.left_col.addLayout(self.set_time_row)
        self.left_col.addWidget(self.date_picker)
        self.left_col.addStretch()
        self.left_col.addLayout(self.logging_ind_row)
        self.left_col.addLayout(self.logging_period_row)
        self.left_col.addWidget(self.logging_toggle)

        self.param_select_row = QHBoxLayout()

        self.param_select_label = QLabel("Parameter: ", parent=self)
        self.param_select_label.setAlignment(Qt.AlignmentFlag.AlignRight)
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

        self.param_select_combo.addItems(self.config.get_parameters.parameter_names)

        self.timestamps = []
        self.data = {}
        self.recv = None

        self.selected_param = self.param_select_combo.currentText()
        self.on_param_sel_change(self.selected_param)

        self.param_select_combo.currentTextChanged.connect(self.on_param_sel_change)
        self.ecu_sel_combo.currentTextChanged.connect(self.on_sel_ecu_change)

        self.live_log = False
        self.init = False
        self.start = False

        self.start_operation.setDisabled(True)
        self.stop_operation.setDisabled(True)
        self.set_time_button.setDisabled(True)

        self.init_button.clicked.connect(self.on_init_payload)
        self.stop_payl_button.clicked.connect(self.on_stop_payload)
        self.start_operation.clicked.connect(self.on_start_operation)
        self.stop_operation.clicked.connect(self.on_stop_operation)

        self.current_time_check.clicked.connect(self.on_change_currtime_setting)

        self.current_time_check.setChecked(False)
        self.date_picker.setDisabled(False)

        self.selected_ecu = 0

        self.logging_toggle.setText("Start Log")
        self.logging_toggle.setDisabled(True)
        self.logging_toggle.clicked.connect(self.on_log_button_press)

        self.set_time_button.clicked.connect(self.on_set_time)

        self.logging_period.setValue(500)

    def on_log_button_press(self):
        self.logging_enable(not self.live_log)

    def on_sel_ecu_change(self, sel):
        if (sel == 'ECU 1'):
            self.selected_ecu = 0
        else:
            self.selected_ecu = 1

    def is_test_checked(self):
        return self.test_mode_check.isChecked()

    def is_currtime_checked(self):
        return self.current_time_check.isChecked()

    def on_init_payload(self):
        self.config.send_frames(init_payload_send(self.is_test_checked(), subsys=self.selected_ecu))
        resp = init_payload_receive(self.config.poll_frames(), subsys=self.selected_ecu)

        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            self.init = True
            self.ecu_sel_combo.setDisabled(True)
            self.init_button.setDisabled(True)

            self.start_operation.setDisabled(False)
            self.stop_operation.setDisabled(True)

            self.set_time_button.setDisabled(False)

            self.test_mode_check.setDisabled(True)
            self.logging_toggle.setDisabled(False)
            self.init_label.curr = 1
        else:
            QMessageBox.warning(self, 'Error',
                                f'INIT_PAYL failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def on_stop_payload(self):
        self.logging_enable(False)
        self.config.send_frames(stop_payload_send(subsys=self.selected_ecu))
        resp = stop_payload_receive(self.config.poll_frames(), subsys=self.selected_ecu)

        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            self.init = False
            self.start = False

            self.ecu_sel_combo.setDisabled(False)
            self.init_button.setDisabled(True)

            self.start_operation.setDisabled(True)
            self.stop_operation.setDisabled(True)

            self.set_time_button.setDisabled(True)

            self.test_mode_check.setDisabled(True)
            self.logging_toggle.setDisabled(True)
            self.init_label.curr = 0
            self.start_label.curr = 0
        else:
            QMessageBox.warning(self, 'Error',
                                f'STOP_PAYL failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def on_start_operation(self):
        print(self.config.sent_parameters)
        self.config.send_frames(data_send_send(self.config.sent_parameters.pack(), test=self.is_test_checked(), subsys=self.selected_ecu))
        resp = data_send_receive(self.config.poll_frames(), test=self.is_test_checked(), subsys=self.selected_ecu)

        if (isinstance(resp, str)) or resp[:2].hex() != '0000':
            QMessageBox.warning(self, 'Error',
                                f'DATA_SEND failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')
            return
        elif (self.is_test_checked()):
            self.start = True
            self.init_button.setDisabled(True)

            self.start_operation.setDisabled(True)
            self.stop_operation.setDisabled(False)

            self.start_label.curr = 1

        if (not self.is_test_checked()):
            self.config.send_frames(start_operation_send(subsys=self.selected_ecu))
            resp = start_operation_receive(self.config.poll_frames(), subsys=self.selected_ecu)
            if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
                self.start = True
                self.init_button.setDisabled(True)

                self.start_operation.setDisabled(True)
                self.stop_operation.setDisabled(False)

                self.start_label.curr = 1
                #self.logging_enable(True)
            else:
                QMessageBox.warning(self, 'Error',
                                    f'START_OPERATION failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def on_stop_operation(self):
        self.logging_enable(False)
        self.config.send_frames(stop_operation_send(test=self.is_test_checked(), subsys=self.selected_ecu))
        resp = stop_operation_receive(self.config.poll_frames(), test=self.is_test_checked(), subsys=self.selected_ecu)
        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            self.start = False
            self.init = False
            self.init_button.setDisabled(False)

            self.start_operation.setDisabled(True)
            self.stop_operation.setDisabled(True)
            self.logging_toggle.setDisabled(True)
            self.set_time_button.setDisabled(True)

            self.start_label.curr = 0
            self.init_label.curr = 0
        else:
            QMessageBox.warning(self, 'Error',
                                f'STOP_OPERATION failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def on_set_time(self):
        dt = datetime.now() if self.is_currtime_checked() else self.date_picker.dateTime()
        self.config.send_frames(set_time_send(dt.date().year,
                                              dt.date().month,
                                              dt.date().day,
                                              dt.time().hour,
                                              dt.time().minute,
                                              dt.time().second,
                                              subsys=self.selected_ecu))
        resp = set_time_receive(self.config.poll_frames(), subsys=self.selected_ecu)

        if (isinstance(resp, str)) or resp[:2].hex() != '0000':
            QMessageBox.warning(self, 'Error',
                                f'SET_TIME failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')
            return
        else:
            QMessageBox.information(self, 'Success', 'Success')

    def on_change_currtime_setting(self):
        self.date_picker.setDisabled(self.is_currtime_checked())

    def logging_enable(self, start: bool):
        if (start):
            if not self.live_log:
                self.config.new_log()
                self.timer = QTimer()
                self.timer.setInterval(self.logging_period.value())
                self.timer.timeout.connect(self.update_plot)
                self.timer.start()
                self.live_log = True
                self.logging_label.curr = 1
                self.logging_toggle.setText("Stop Log")
        else:
            self.timer.stop()
            self.live_log = False
            self.logging_label.curr = 0
            self.logging_toggle.setText("Start Log")

    def load_recv(self) -> bool:
        """Load data get into receive buffer and check if output is valid"""
        fr = data_get_receive(self.config.poll_frames())
        if isinstance(fr, str):
            print(fr)
            self.recv = None
            return False

        if not fr[:2].hex() == '0000':
            # we have an error
            print(f"DATA_GET Response Error: {fr[:2].hex()}")
            self.recv = None
            return False
        self.recv = fr[8:]
        return True

    def update_plot(self) -> None:
        """
        Query data from ECU, cache data and replot graph
        """

        # data get frames
        self.config.send_frames(data_get_send(subsys=self.selected_ecu))

        if not self.load_recv():
            return

        self.config.get_log.log_datapoint(self.recv, t=time.time())

        self.error_vector1_label.setText(f"0x{self.config.get_parameters['Error Vector 1'].value:0>4X}")
        self.error_vector2_label.setText(f"0x{self.config.get_parameters['Error Vector 2'].value:0>8X}")

        self.plot_data()

    def plot_data(self):
        if (not self.config.get_log is None):
            self.canvas.axes.cla()
            self.canvas.axes.set_ylabel(self.selected_param)
            self.canvas.axes.set_xlabel('time (s)')
            data = self.config.get_log.get_data_series(self.selected_param, elapsed=True)
            range_min = min(self.config.get_parameters[self.selected_param].min, min(data[0]))
            range_max = max(self.config.get_parameters[self.selected_param].max, max(data[0]))
            self.canvas.axes.set_ylim([range_min, range_max])
            self.canvas.axes.plot(data[1], data[0])
            self.canvas.draw()

    def on_param_sel_change(self, param):
        self.selected_param = param
        self.plot_data()

