from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class QTabWidgetResize(QTabWidget):

    resized = QtCore.pyqtSignal(QResizeEvent)

    def __init__(self):
        super().__init__()

    def resizeEvent(self, event):
        self.resized.emit(event)
        return super().resizeEvent(event)