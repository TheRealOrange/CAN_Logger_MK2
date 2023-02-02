from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget


class StateLabel(QLabel):
    def __init__(self, states=None, colours=None, curr=0, parent: QWidget=None):
        if states is None:
            states = ["No", "Yes"]
        if colours is None:
            colours = ["red", "green"]

        self.states = states
        self.colours = colours
        self._curr = curr
        if (self._curr >= len(self.states)):
            raise ValueError("Invalid current value", self._curr)

        super(StateLabel, self).__init__(parent=parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"background-color: {self.colours[self._curr]};margin:2px;")
        self.setText(self.states[self._curr])

    @property
    def curr(self):
        return self._curr

    @curr.setter
    def curr(self, a):
        if (a >= len(self.states)):
            raise ValueError("Invalid current value", self._curr)
        self._curr = a
        self.setStyleSheet(f"background-color: {self.colours[self._curr]};margin:2px;")
        self.setText(self.states[self._curr])

