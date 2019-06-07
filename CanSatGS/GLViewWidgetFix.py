import numpy as np
from PyQt5 import QtGui
from PyQt5.QtCore import *
from pyqtgraph import opengl


class GLViewWidgetFix(opengl.GLViewWidget):

    double_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

    def width(self):
        return super().width() * self.devicePixelRatio()

    def height(self):
        return super().height() * self.devicePixelRatio()

    def projectionMatrix(self, region=None):
        # Xw = (Xnd + 1) * width/2 + X
        if region is None:
            region = (0, 0, self.width(), self.height())

        x0, y0, w, h = self.getViewport()
        dist = self.opts['distance']
        fov = self.opts['fov']
        nearClip = dist * 0.1
        farClip = dist * 10000000.

        r = nearClip * np.tan(fov * 0.5 * np.pi / 180.)
        t = r * h / w

        # convert screen coordinates (region) to normalized device coordinates
        # Xnd = (Xw - X0) * 2/width - 1
        ## Note that X0 and width in these equations must be the values used in viewport
        left  = r * ((region[0]-x0) * (2.0/w) - 1)
        right = r * ((region[0]+region[2]-x0) * (2.0/w) - 1)
        bottom = t * ((region[1]-y0) * (2.0/h) - 1)
        top    = t * ((region[1]+region[3]-y0) * (2.0/h) - 1)

        tr = QtGui.QMatrix4x4()
        tr.frustum(left, right, bottom, top, nearClip, farClip)
        return tr

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        return super().mouseDoubleClickEvent(event)
