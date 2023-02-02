from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPalette, QColor

from config import Config


class PacketViewWindow(QWidget):

    def __init__(self, config: Config):
        super(PacketViewWindow, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('blue'))
        self.setPalette(palette)