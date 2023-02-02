""" Code for CANLogger GUI Logic
"""

import sys
import matplotlib
from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
from canlib import canlib, Frame, connected_devices
from canlib.canlib import MessageFlag

from driver_mk1 import init_payload_send, data_get_send, \
    stop_payload_send, start_operation_send, \
    stop_operation_send, init_payload_receive, stop_payload_receive, start_operation_receive, \
    stop_operation_receive, data_get_receive, data_send_send, data_send_receive

matplotlib.use('Qt5Agg')

from PyQt6.QtWidgets import (
    QFileDialog, QVBoxLayout, QWidget, QPushButton, QComboBox, QLabel, QMessageBox, QMainWindow, QSpinBox, QHBoxLayout
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure


# Utilities
class MplCanvas(FigureCanvasQTAgg):
    """
    Matplotlib helper function
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


# Reading metadata, required information for parsing params
file = open('parameters_get.csv', encoding='utf-8-sig', mode='r')
params = []

byte_len = {}
offset = {}
unit = {}
is_send_param = {}
param_min = {}
param_max = {}
param_default = {}
for row in file.readlines():
    tokens = row.strip().split(',')
    name = tokens[0]
    params.append(name)
    unit[name] = tokens[2]
    byte_len[name] = int(tokens[1])
    offset[name] = int(tokens[3])
    is_send_param[name] = bool(int(tokens[4]))
    param_min[name] = int(tokens[5])
    param_max[name] = int(tokens[6])
    param_default[name] = int(tokens[7])

print(params)
print(unit)
print(byte_len)
print(offset)

init = False
operation_mode = False
live_log = False

frame_buffer = []
get_buffer = []
recv = None


class MainWindow(QMainWindow):
    """
    Class representing Main GUI Window, construction of GUI (widgets + layout) is done in constructor
    """
    curr_file = ''
    selected_param = 'ECU Temp'
    timestamps = []
    data = {}

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        for param in params:
            self.data[param] = []

        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        toolbar = NavigationToolbar2QT(self.canvas, self)
        self.fileText = QLabel()
        chooseButton = QPushButton()
        chooseButton.setText('Choose File')
        chooseButton.clicked.connect(self.onButtonChoose)
        layout = QVBoxLayout()
        layout.addWidget(self.fileText)
        layout.addWidget(chooseButton)

        textBox = QComboBox()
        textBox.addItems(params)
        textBox.currentTextChanged.connect(self.onParamSelectionChange)

        csvButton = QPushButton()
        csvButton.setText("Generate CSV")
        csvButton.clicked.connect(self.onButtonCSV)

        layout.addWidget(textBox)
        layout.addWidget(csvButton)
        self.error1 = QLabel('Error Vector 1: None')
        self.error2 = QLabel('Error Vector 2: None')
        layout.addWidget(self.error1)
        layout.addWidget(self.error2)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # Test sequences
        initButton = QPushButton('Init Payload')
        stopButton = QPushButton('Stop Payload')

        startOpButton = QPushButton('Start Operation')
        stopOpButton = QPushButton('Stop Operation')
        periodicText = QLabel('Logging period (ms):')
        self.periodInput = QSpinBox()
        self.periodInput.setMinimum(400)
        self.periodInput.setValue(500)
        self.periodInput.setMaximum(10000)
        logButton = QPushButton('Live Logging')
        getButton = QPushButton('Manual Data Get')

        initButton.clicked.connect(self.onInitPayload)
        stopButton.clicked.connect(self.onStopPayload)
        startOpButton.clicked.connect(self.onStartOperation)
        stopOpButton.clicked.connect(self.onStopOperation)
        logButton.clicked.connect(self.onLiveLog)
        getButton.clicked.connect(self.onDataGet)

        layout.addWidget(initButton)
        layout.addWidget(stopButton)
        layout.addWidget(startOpButton)
        layout.addWidget(stopOpButton)
        layout.addWidget(periodicText)
        layout.addWidget(self.periodInput)
        layout.addWidget(logButton)
        layout.addWidget(getButton)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setWindowTitle('CAN Data Logger')
        print("canlib version:", canlib.dllversion())
        self.show()

    def update_plot(self) -> None:
        """
        Query data from ECU, cache data and replot graph
        """

        # data get frames
        send_frames(data_get_send())

        if not load_recv():
            return

        self.timestamps.append(len(self.timestamps) * float(self.periodInput.value() / 1000))

        for param in params:
            self.data[param].append(int(recv[offset[param]: offset[param] + byte_len[param]].hex(), 16))

        self.error1.setText(f'Error Vector 1: {recv[offset["Error Vector 1"]: offset["Error Vector 1"] + byte_len["Error Vector 1"]].hex()}')
        self.error2.setText(
            f'Error Vector 2: {recv[offset["Error Vector 2"]: offset["Error Vector 2"] + byte_len["Error Vector 2"]].hex()}')

        self.canvas.axes.cla()
        self.canvas.axes.set_ylabel(self.selected_param)
        self.canvas.axes.set_xlabel('time (s)')
        self.canvas.axes.plot(self.timestamps, self.data[self.selected_param])
        self.canvas.draw()

    def onDataGet(self):
        self.data_get_window = DataGetWindow()
        self.data_get_window.show()

    def onButtonChoose(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Choose Log File")
        dialog.exec()
        if len(dialog.selectedFiles()) == 0:
            return
        self.curr_file = dialog.selectedFiles()[0]
        self.fileText.setText(f'Current File: {self.curr_file}')
        self.parseDataFromLogFile()

    def onButtonCSV(self) -> None:
        """
        Saves current parameter data as CSV
        """
        with open(self.selected_param + '.csv', 'w', encoding="utf-8") as f:
            for i in range(len(self.timestamps)):
                f.write(str(self.timestamps[i]))
                f.write(',')
                f.write(str(self.data[self.selected_param][i]))
                f.write('\n')
        QMessageBox.information(self, 'Success', f'Data saved to {self.selected_param}.csv!')

    def parseDataFromLogFile(self):
        self.clearCache()
        i = 0
        lines = open(self.curr_file, 'r').readlines()[1:]

        while i < len(lines):
            tokens = lines[i].split()
            time = tokens[-2]
            if tokens[1] != '198FA10C':
                i += 1
                continue
            raw = []
            j = 0
            while j < 13:
                tokens = lines[i + j].split()
                if tokens[1] == '00000000':
                    i += 1
                    continue
                dlc = int(tokens[3])
                for k in range(dlc):
                    raw.append(tokens[4 + k])
                j += 1

            self.timestamps.append(len(self.timestamps))

            for param in params:
                hx = ""
                for j in range(byte_len[param]):
                    hx += raw[offset[param] + j]
                self.data[param].append(int(hx, 16))
            i += 12

        self.onParamSelectionChange(self.selected_param)

    def onParamSelectionChange(self, param):
        self.selected_param = param
        self.canvas.axes.cla()
        self.canvas.axes.set_ylabel(param)
        self.canvas.axes.set_xlabel('time (s)')
        self.canvas.axes.plot(self.timestamps, self.data[param])
        self.canvas.draw()

    def onInitPayload(self):
        if not check_disabled_live_log(self):
            return
        if not check_not_init(self):
            return
        send_frames(init_payload_send(False))
        resp = init_payload_receive(poll_frames())

        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            global init
            init = True
            QMessageBox.information(self, 'Success', 'Success')
        else:
            QMessageBox.warning(self, 'Error',
                                f'Failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def onStopPayload(self):
        if not check_operation_state(self, False):
            return
        if not check_disabled_live_log(self):
            return
        if not check_init(self):
            return
        send_frames(stop_payload_send())
        resp = stop_payload_receive(poll_frames())

        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            global init
            init = False
            QMessageBox.information(self, 'Success', 'Success')
        else:
            QMessageBox.warning(self, 'Error',
                                f'Failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def onStartOperation(self):
        if not check_disabled_live_log(self):
            return
        if not check_init(self):
            return
        if not check_operation_state(self, False):
            return
        self.start_operation_window = StartOperationWindow(self)
        self.start_operation_window.show()

    def onStopOperation(self):
        if not check_disabled_live_log(self):
            return
        if not check_init(self):
            return
        if not check_operation_state(self, True):
            return
        send_frames(stop_operation_send())
        resp = stop_operation_receive(poll_frames())
        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            global operation_mode
            operation_mode = False
            QMessageBox.information(self, 'Success', 'Success')
        else:
            QMessageBox.warning(self, 'Error',
                                f'Failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')

    def onLiveLog(self):
        if not check_init(self):
            return False
        global live_log
        if not live_log:
            self.clearCache()
            self.timer = QTimer()
            self.timer.setInterval(self.periodInput.value())
            self.timer.timeout.connect(self.update_plot)
            self.timer.start()
            live_log = True
            QMessageBox.information(self, "Success", "Live logging has been enabled!")
        else:
            self.timer.stop()
            live_log = False
            QMessageBox.information(self, "Success", "Live logging has been disabled!")

    def clearCache(self):
        for param in params:
            self.data[param].clear()
        self.timestamps.clear()


def load_recv() -> bool:
    """Load data get into receive buffer and check if output is valid"""
    global recv
    fr = data_get_receive(poll_frames())
    if isinstance(fr, str):
        print(fr)
        recv = None
        return False

    if not fr[:2].hex() == '0000':
        # we have an error
        print(f"Data Get Response Error: {fr[:2].hex()}")
        recv = None
        return False
    recv = fr[8:]
    return True


class StartOperationWindow(QMainWindow):
    """Class for Data Get GUI"""
    param_inputs = {}

    def __init__(self, main):
        super().__init__()
        self.main = main

        layout = QHBoxLayout()
        sublayout = QVBoxLayout()
        cnt = 0
        for param in filter(lambda x: is_send_param[x], params):
            label0 = QLabel(param)
            sublayout.addWidget(label0)
            input0 = QSpinBox()
            input0.setMinimum(param_min[param])
            input0.setValue(0)
            input0.setMaximum(param_max[param])
            sublayout.addWidget(input0)
            self.param_inputs[param] = input0
            cnt += 1
            if cnt == 5:
                layout.addLayout(sublayout)
                sublayout = QVBoxLayout()
                cnt = 0

        send_button = QPushButton('Send')
        send_button.clicked.connect(self.onSend)
        sublayout.addWidget(send_button)
        layout.addLayout(sublayout)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setWindowTitle('Start Operation')
        self.show()

    def onSend(self) -> None:
        payload = bytearray(84)
        print(offset.keys())
        print(byte_len.keys())
        print(self.param_inputs.keys())
        for param in params:
            print(param)
            if not is_send_param[param]:
                payload[offset[param]: offset[param] + byte_len[param]] = \
                    param_default[param].to_bytes(byte_len[param], 'big')
            else:
                payload[offset[param]: offset[param] + byte_len[param]] = \
                    self.param_inputs[param].value().to_bytes(byte_len[param], 'big')

        send_frames(data_send_send(payload))
        resp = data_send_receive(poll_frames())

        if (isinstance(resp, str)) or resp[:2].hex() != '0000':
            QMessageBox.warning(self, 'Error',
                                f'Failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')
            return

        if not check_disabled_live_log(self):
            return
        if not check_init(self):
            return
        if not check_operation_state(self, False):
            return

        send_frames(start_operation_send())
        resp = start_operation_receive(poll_frames())
        if (not isinstance(resp, str)) and resp[:2].hex() == '0000':
            global operation_mode
            operation_mode = True
            self.main.onLiveLog()
            QMessageBox.information(self, 'Success', 'Success')
        else:
            QMessageBox.warning(self, 'Error',
                                f'Failed: {resp if isinstance(resp, str) else f"Error Vector: {resp[:2].hex()}"}')


class DataGetWindow(QMainWindow):
    """Class for Data Get GUI"""
    param_labels = {}

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        sublayout = QVBoxLayout()
        cnt = 0
        for param in params:
            label0 = QLabel(param)
            sublayout.addWidget(label0)
            label1 = QLabel('0')
            sublayout.addWidget(label1)
            self.param_labels[param] = label1
            cnt += 1
            if cnt == 5:
                layout.addLayout(sublayout)
                sublayout = QVBoxLayout()
                cnt = 0

        getButton = QPushButton('Get')
        getButton.clicked.connect(self.onGet)
        sublayout.addWidget(getButton)
        layout.addLayout(sublayout)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setWindowTitle('Data Get')
        self.show()

    def onGet(self) -> None:
        if not check_init(self):
            return
        if not check_disabled_live_log(self):
            return
        send_frames(data_get_send())
        if not load_recv():
            return

        for param in params:
            self.param_labels[param].setText(str(int(recv[offset[param]: offset[param] + byte_len[param]].hex(), 16)))


def check_init(window) -> bool:
    """Makes sure that ECU has been initialized
    returns true if initialized
    """
    if not init:
        QMessageBox.warning(window, "Warning", "ECU not initialized yet")
        return False
    return True


def check_operation_state(window, intended_state) -> bool:
    if not operation_mode == intended_state:
        QMessageBox.warning(window, "Warning",
                            f'ECU operation is currently {"started" if operation_mode else "stopped"}. '
                            f'Please {"stop" if operation_mode else "start"} it first.')
        return False
    return True


def check_not_init(window) -> bool:
    """Makes sure that ECU has NOT been initialized
    returns true if not initialized
    """
    if init:
        QMessageBox.warning(window, "Warning", "ECU already initialized")
        return False
    return True


def check_disabled_live_log(window) -> bool:
    """Makes sure that live logging is disabled
    returns true if disabled
    """
    if live_log:
        QMessageBox.warning(window, "Warning", "You need to disable live logging first")
        return False
    return True


def genFrame(hx_id: int, hx_data: bytes) -> Frame:
    """Create a Frame from CAN id in hex and data in bytearray"""
    return Frame(hx_id, hx_data, flags=MessageFlag.EXT)


def send_frames(frames):
    for frame in frames:
        print('sending', hex(frame[0]), frame[1].hex())
        ch.write(genFrame(frame[0], frame[1]))


def receive_frame(timeout: int) -> Frame:
    frame = ch.read(timeout)
    print('received', hex(frame.id), frame.data.hex())
    return frame


def setUpChannel():
    ch0 = canlib.openChannel(channel=0, bitrate=canlib.Bitrate.BITRATE_500K)
    ch0.busOn()
    return ch0


def tearDownChannel(ch0):
    ch0.busOff()
    ch0.close()


def poll_frames():
    frame = receive_frame(-1)
    buffer = frame.id
    frame_cnt = buffer & ((1 << 8) - 1)

    frames = [frame]
    for i in range(frame_cnt):
        frame = receive_frame(-1)
        frames.append(frame)
    return frames


if __name__ == '__main__':
    print('Setting up CANLib...')
    for dev in connected_devices():
        print(dev.probe_info())
    ch = setUpChannel()
    print('CanLib setup complete!')

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    app.exec()

    print('Closing CANLib...')
    tearDownChannel(ch)
