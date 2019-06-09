import math

import numpy as np
from PIL import Image
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from pyqtgraph import opengl
from stl import mesh

import GLViewWidgetFix



class GPSDisplay(QWidget):

    def __init__(self, lat_key, lon_key, alt_key, sats_key, image_name="", lat_min=0, lat_max=0, lon_min=0, lon_max=0, max_points=250):
        super().__init__()

        self.image_name = image_name

        self.lat_key = lat_key
        self.lon_key = lon_key
        self.alt_key = alt_key
        self.sats_key = sats_key

        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max

        self.x_points = np.array([])
        self.y_points = np.array([])
        self.z_points = np.array([])

        self.max_points = max_points

        self.meters_per_lat = 111000
        self.meters_per_lon = math.cos((lat_min+lat_max)*math.pi/360) * 111321

        self.do3d = False

        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(250, 250)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        positions = np.vstack([self.x_points, self.y_points, self.z_points]).transpose()

        self.view = GLViewWidgetFix.GLViewWidgetFix()
        self.view.setBackgroundColor(119, 181, 254)
        self.view.setCameraPosition(distance=1950, elevation=90, azimuth=0)

        self.plot = opengl.GLLinePlotItem(pos=positions, color=[1,0,0,1], width=3)
        self.plot.setGLOptions("opaque")
        self.view.addItem(self.plot)

        # self.grid = opengl.GLGridItem(color="white")
        # self.grid.setSize(x=(self.lon_max-self.lon_min)*self.meters_per_lon,
        #                   y=(self.lat_max-self.lat_min)*self.meters_per_lat)
        # self.grid.setSpacing(x=100, y=100)
        # self.view.addItem(self.grid)

        self.image_file = Image.open(self.image_name)
        self.image = opengl.GLImageItem(np.asarray(self.image_file))
        self.view.addItem(self.image)
        self.image.scale((self.lat_max - self.lat_min) * self.meters_per_lat / self.image_file.size[1],
                         (self.lon_max - self.lon_min) * self.meters_per_lon / self.image_file.size[0],
                         1)
        self.image.translate(-(self.lat_max - self.lat_min) * self.meters_per_lat / 2,
                             -(self.lon_max - self.lon_min) * self.meters_per_lon / 2,
                             0)

        flat_earth = opengl.GLMeshItem(meshdata=opengl.MeshData.cylinder(1, 64, [6371000, 0], 0),
                                            color=[84/255, 89/255, 72/255, 1],
                                            smooth=True)
        flat_earth.translate(0, 0, -10000)
        flat_earth.setGLOptions("opaque")
        self.view.addItem(flat_earth)

        crosshair_mesh = mesh.Mesh.from_file("DisplayModels/Crosshairs.stl")
        crosshair_mesh_data = opengl.MeshData(vertexes=crosshair_mesh.vectors)
        self.crosshair = opengl.GLMeshItem(meshdata=crosshair_mesh_data, color=[1, 0, 0, 1])
        self.set_crosshair_pos(0, 0, 0)
        self.view.addItem(self.crosshair)

        self.view_btn = QPushButton("2D")
        self.view_btn.clicked.connect(self.switch_3d)
        self.view_btn.setMaximumWidth(30)

        self.coords_label = QLineEdit("0,0")
        self.coords_label.setAlignment(Qt.AlignCenter)
        self.coords_label.setReadOnly(True)

        self.clear_btn = QPushButton("CLR")
        self.clear_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clear_btn.setToolTip("Clear Data")
        self.clear_btn.setFixedWidth(35)
        self.clear_btn.setParent(self.view)
        self.clear_btn.clicked.connect(self.clear_plot)

        self.sats_label = QLineEdit("0")
        self.sats_label.setAlignment(Qt.AlignCenter);
        self.sats_label.setReadOnly(True)
        self.sats_label.setToolTip("Number of Satellites")
        self.sats_label.setMaximumWidth(50)

        layout.addWidget(self.view, 0, 0, 1, 4)
        layout.addWidget(self.clear_btn, 1, 3)
        layout.addWidget(self.view_btn, 1, 0)
        layout.addWidget(self.coords_label, 1, 1)
        layout.addWidget(self.sats_label, 1, 2)



    def update_plot(self, dictionary):
        self.coords_label.setText(f"{dictionary[self.lat_key]:.5f},{dictionary[self.lon_key]:.5f}")
        self.sats_label.setText(f"{dictionary[self.sats_key]:02.0f}")
        if dictionary[self.lat_key] != 0 and dictionary[self.lon_key] != 0:
            self.x_points = np.append(self.x_points, -(dictionary[self.lat_key]-(self.lat_min+self.lat_max)/2) * self.meters_per_lat)
            self.y_points = np.append(self.y_points, (dictionary[self.lon_key]-(self.lon_min+self.lon_max)/2) * self.meters_per_lon)
            self.z_points = np.append(self.z_points, dictionary[self.alt_key])

            if self.x_points.size > self.max_points:
                self.x_points = np.delete(self.x_points, 0)
            if self.y_points.size > self.max_points:
                self.y_points = np.delete(self.y_points, 0)
            if self.z_points.size > self.max_points:
                self.z_points = np.delete(self.z_points, 0)

            if self.do3d:
                positions = np.vstack([self.x_points, self.y_points, self.z_points]).transpose()
            else:
                positions = np.vstack([self.x_points, self.y_points, np.ones([1, self.x_points.size])]).transpose()

            self.set_crosshair_pos(self.x_points[-1], self.y_points[-1], 0)

            self.plot.setData(pos=positions)

    def switch_3d(self):
        if self.do3d:
            self.view_btn.setText("2D")
            self.do3d = False
            self.view.setCameraPosition(distance=1950, elevation=90, azimuth=0)
        else:
            self.view_btn.setText("3D")
            self.do3d = True
            self.view.setCameraPosition(distance=3000, elevation=45, azimuth=45)

    def set_crosshair_pos(self, x, y, z):
        self.crosshair.resetTransform()
        self.crosshair.scale(3, 3, 3)
        self.crosshair.translate(x, y, z)

    def clear_plot(self):
        self.x_points = np.array([])
        self.y_points = np.array([])
        self.z_points = np.array([])

        if self.do3d:
            positions = np.vstack([self.x_points, self.y_points, self.z_points]).transpose()
        else:
            positions = np.vstack([self.x_points, self.y_points, np.ones([1, self.x_points.size])]).transpose()

        self.set_crosshair_pos(0, 0, 0)

        self.plot.setData(pos=positions)



