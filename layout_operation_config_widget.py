from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QPushButton, QScrollArea, QLabel, QSpinBox, \
    QSizePolicy, QInputDialog, QMessageBox, QAbstractItemView
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
        self.rename_button = QPushButton("Rename", parent=self)

        self.list_controls.addWidget(self.add_button)
        self.list_controls.addWidget(self.remove_button)
        self.list_controls.addWidget(self.rename_button)

        self.left_col.addWidget(self.list_view)
        self.left_col.addLayout(self.list_controls)

        #   Container Widget
        self.scroll_container_widget = QWidget()
        #   Layout of Container Widget
        self.scroll_container_layout = QVBoxLayout(self)
        # self.scroll_container_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_container_widget.setLayout(self.scroll_container_layout)

        self.scroll_area = QScrollArea(parent=self)
        self.scroll_area.setWidget(self.scroll_container_widget)
        self.scroll_area.setWidgetResizable(True)

        self.reset_default_button = QPushButton("Reset to Defaults", parent=self)
        self.reload_fromfile_button = QPushButton("Reload from File", parent=self)
        self.save_button = QPushButton("Save Preset", parent=self)

        self.param_edit = dict()
        for p in self.config.sent_parameters:
            param_name = p.name
            l = QHBoxLayout()
            s = QSpinBox(self.scroll_container_widget)

            s.setMinimum(p.min)
            s.setMaximum(p.max)
            s.setValue(p.default)
            s.setFixedWidth(150)
            s.setMinimumHeight(25)
            s.valueChanged.connect((lambda i: lambda x: self.set_parameter(i, x))(param_name))

            name = QLabel(p.name, parent=self.scroll_container_widget)
            name.setAlignment(Qt.AlignmentFlag.AlignRight)
            l.addWidget(name)
            l.addWidget(s)

            units = QLabel(p.units, parent=self.scroll_container_widget)
            units.setAlignment(Qt.AlignmentFlag.AlignLeft)
            units.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            units.setFixedWidth(50)
            l.addWidget(units)

            self.param_edit[param_name] = s
            self.scroll_container_layout.addLayout(l)

        self.right_col.addWidget(self.scroll_area)
        self.right_col.addWidget(self.save_button)
        self.right_col.addWidget(self.reload_fromfile_button)
        self.right_col.addWidget(self.reset_default_button)

        self.hlayout.addLayout(self.left_col)
        self.hlayout.addLayout(self.right_col)

        self.setLayout(self.hlayout)

        self.add_button.clicked.connect(self.on_add_preset)
        self.remove_button.clicked.connect(self.on_remove_preset)

        self.save_button.clicked.connect(self.save_preset_to_file)
        self.reset_default_button.clicked.connect(self.reset_default)
        self.reload_fromfile_button.clicked.connect(self.reload_preset)

        self.load_presets()

        self.list_view.clicked.connect(self.select_item)
        self.list_view.itemSelectionChanged.connect(self.selection_changed)
        self.sel_preset = 'default'

        self.populate_parameters()

    def populate_parameters(self):
        for k, v in self.config.presets[self.sel_preset].values.items():
            self.param_edit[k].setValue(v)
            self.config.sent_parameters[k] = v
        if (not self.sel_preset == 'default'):
            self.save_button.setDisabled(not self.config.presets[self.sel_preset].diff())

    def sel_default(self):
        self.list_view.setCurrentIndex(self.list_view.model().index(0, 0))
        self.sel_preset = 'default'
        self.save_button.setDisabled(True)
        self.reload_fromfile_button.setDisabled(True)

    def load_presets(self):
        self.list_view.clear()
        self.list_view.addItem('default')
        self.list_view.addItems([p.name for p in self.config.presets if p.name != 'default'])
        self.sel_default()
        self.populate_parameters()

    def select_item(self, ind):
        self.sel_preset = ind.data()
        if (self.sel_preset == 'default'):
            self.sel_default()
        else:
            self.reload_fromfile_button.setDisabled(False)
        self.populate_parameters()

    def selection_changed(self):
        if (len(self.list_view.selectedItems()) == 0):
            self.sel_default()

    def set_parameter(self, param, val):
        self.config.sent_parameters[param] = val
        self.config.presets[self.sel_preset].values[param] = val
        if (not self.sel_preset == 'default'):
            self.save_button.setDisabled(not self.config.presets[self.sel_preset].diff())
        # print(self.config.sent_parameters[param])

    def save_preset_to_file(self):
        self.config.presets[self.sel_preset].save_to_file()
        if (not self.sel_preset == 'default'):
            self.save_button.setDisabled(not self.config.presets[self.sel_preset].diff())

    def reload_preset(self):
        self.config.presets[self.sel_preset].load_from_file()
        if (not self.sel_preset == 'default'):
            self.save_button.setDisabled(not self.config.presets[self.sel_preset].diff())

    def reset_default(self):
        self.config.presets[self.sel_preset].load_defaults()
        self.populate_parameters()

    def on_add_preset(self):
        ok = True
        while (ok):
            name, ok = QInputDialog.getText(self, 'Add Preset', 'Enter preset name:')
            if (ok):
                if (not name):
                    QMessageBox.warning(self, 'Error', f"Please specify a name!")
                elif (not name in self.config.presets):
                    try:
                        print("adding preset")
                        self.config.presets.add_preset(parameters=self.config.sent_parameters, name=name)
                    except Exception as e:
                        QMessageBox.warning(self, 'Error', f"Could not add preset:\n{e.message}\n{e.args}")
                        return
                    QMessageBox.information(self, 'Success', f"Preset [{name}] successfully saved")
                    self.load_presets()
                    return
                else:
                    QMessageBox.warning(self, 'Error', f"Preset with name: [{name}] already exists!")

    def on_remove_preset(self):
        if (self.sel_preset == 'default'):
            QMessageBox.warning(self, 'Error', "Cannot delete default preset!")
            return
        ok = QMessageBox.question(self, 'Delete', f"Are you sure you want to delete preset: {self.sel_preset}?")
        if (ok):
            if (self.sel_preset in self.config.presets):
                self.config.presets.remove_preset(self.sel_preset)
                QMessageBox.information(self, 'Success', f"Preset [{self.sel_preset}] successfully removed")
                self.load_presets()
            else:
                QMessageBox.warning(self, 'Error', f"Preset with name: [{self.sel_preset}] doesn't exist!")

    def on_rename_preset(self):
        if (self.sel_preset == 'default'):
            QMessageBox.warning(self, 'Error', "Cannot rename default preset!")
            return
        ok = True
        while (ok):
            name, ok = QInputDialog.getText(self, 'Rename Preset', 'Enter preset name:')
            if (ok):
                if (not name):
                    QMessageBox.warning(self, 'Error', f"Please specify a name!")
                elif (not name in self.config.presets):
                    try:
                        self.config.presets.rename_preset(self.sel_preset, name)
                    except Exception as e:
                        QMessageBox.warning(self, 'Error', f"Could not rename preset:\n{e.message}\n{e.args}")
                        return
                    QMessageBox.information(self, 'Success', f"Preset [{self.sel_preset}] successfully renamed to [{name}")
                    self.load_presets()
                    return
                else:
                    QMessageBox.warning(self, 'Error', f"Preset with name: [{name}] already exists!")