import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class GSGraph(QWidget):

    def __init__(self, x_key, y_key, max_points=600, title="", x_units="", y_units=""):
        super().__init__()

        self.x_data = np.array([])
        self.y_data = np.array([])

        self.x_key = x_key
        self.y_key = y_key

        self.max_points = max_points

        self.init_ui(title, x_units, y_units)

    def init_ui(self, title, x_units, y_units):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(250)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.plot_w = pg.PlotWidget()
        self.plot = self.plot_w.plot(self.x_data, self.y_data)

        self.clear_btn = QPushButton("CLR")
        f = QFont()
        f.setPointSize(8)
        self.clear_btn.setFont(f)
        self.clear_btn.setFixedSize(22, 22)
        self.clear_btn.setAttribute(Qt.WA_TranslucentBackground, True)
        self.clear_btn.setAttribute(Qt.WA_NoSystemBackground, True)
        self.clear_btn.setStyleSheet("QPushButton{background: transparent;}")
        self.clear_btn.setToolTip("Clear Data")
        self.clear_btn.setParent(self.plot_w)
        self.clear_btn.clicked.connect(self.clear_plot)

        if title:
            self.plot_w.setTitle(title)
        if x_units:
            self.plot_w.setLabels(bottom=x_units)
        if y_units:
            self.plot_w.setLabels(left=y_units)

        layout.addWidget(self.plot_w)


    def update_plot(self, dictionary):
        self.x_data = np.append(self.x_data, dictionary[self.x_key])
        self.y_data = np.append(self.y_data, dictionary[self.y_key])
        if self.x_data.size > self.max_points:
            self.x_data = np.delete(self.x_data, 0)
        if self.y_data.size > self.max_points:
            self.y_data = np.delete(self.y_data, 0)
        self.plot.setData(self.x_data, self.y_data)

    def clear_plot(self):
        self.x_data = np.array([])
        self.y_data = np.array([])
        self.plot.setData(self.x_data, self.y_data)
