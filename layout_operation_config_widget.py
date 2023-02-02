from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QPushButton, QScrollArea, QLabel, QSpinBox, \
    QSizePolicy, QInputDialog, QMessageBox
from PyQt6.QtGui import QPalette, QColor

from config import Config


class OperationConfigWindow(QWidget):

    def __init__(self, config: Config):
        super(OperationConfigWindow, self).__init__()
        self.config = config

        self.hlayout = QHBoxLayout()

        self.left_col = QVBoxLayout()
        self.right_col = QVBoxLayout()

        self.list_controls = QHBoxLayout()

        self.list_view = QListWidget(parent=self)
        self.add_button = QPushButton("Add Preset", parent=self)
        self.remove_button = QPushButton("Delete", parent=self)

        self.list_controls.addWidget(self.add_button)
        self.list_controls.addWidget(self.remove_button)

        self.left_col.addWidget(self.list_view)
        self.left_col.addLayout(self.list_controls)

        #   Container Widget
        self.scroll_container_widget = QWidget()
        #   Layout of Container Widget
        self.scroll_container_layout = QVBoxLayout(self)
        #self.scroll_container_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_container_widget.setLayout(self.scroll_container_layout)

        self.scroll_area = QScrollArea(parent=self)
        self.scroll_area.setWidget(self.scroll_container_widget)
        self.scroll_area.setWidgetResizable(True)

        self.reset_default_button = QPushButton("Reset to Defaults", parent=self)

        self.param_edit = dict()
        for p in self.config.sent_parameters.params.values():
            l = QHBoxLayout()
            s = QSpinBox(self.scroll_container_widget)

            s.setMinimum(p.min)
            s.setMaximum(p.max)
            s.setValue(p.default)
            s.setFixedWidth(150)
            s.setMinimumHeight(25)

            name = QLabel(p.name, parent=self.scroll_container_widget)
            name.setAlignment(Qt.AlignmentFlag.AlignRight)
            l.addWidget(name)
            l.addWidget(s)

            units = QLabel(p.units, parent=self.scroll_container_widget)
            units.setAlignment(Qt.AlignmentFlag.AlignLeft)
            units.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            units.setFixedWidth(50)
            l.addWidget(units)

            self.param_edit[p.name] = l
            self.scroll_container_layout.addLayout(l)

        self.right_col.addWidget(self.scroll_area)
        self.right_col.addWidget(self.reset_default_button)

        self.hlayout.addLayout(self.left_col)
        self.hlayout.addLayout(self.right_col)

        self.setLayout(self.hlayout)

        self.add_button.clicked.connect(self.onAddPreset)

    def onAddPreset(self):
        name, ok = QInputDialog.getText(self, 'Add Preset', 'Enter preset name:')
        if (ok):
            QMessageBox.information(self, 'Success', f"Preset {name} successfully saved")
