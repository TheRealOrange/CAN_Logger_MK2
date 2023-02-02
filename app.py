import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QWidget,
)

from config import Config
from layout_operation_widget import OperationWindow
from layout_operation_config_widget import OperationConfigWindow
from layout_logging_config_widget import LoggingConfigWindow
from layout_packet_view_widget import PacketViewWindow

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.config = Config()

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.West)
        tabs.setMovable(True)

        tabs.addTab(OperationWindow(self.config), "Operation")
        tabs.addTab(OperationConfigWindow(self.config), "Parameters")
        tabs.addTab(LoggingConfigWindow(self.config), "Logging")
        tabs.addTab(PacketViewWindow(self.config), "Bus")

        self.setCentralWidget(tabs)

        self.setWindowTitle("ELITE ECU Operations")


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()