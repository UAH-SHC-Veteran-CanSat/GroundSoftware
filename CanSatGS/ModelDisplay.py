import math
import time
from statistics import mean

import numpy as np
from PIL import Image
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from pyqtgraph import Transform3D
from pyqtgraph import opengl
from stl import mesh

import GLViewWidgetFix


def lerp_rot_signed(start_rot, end_rot, pct):
    return [lerp_rot_1axis_signed(start_rot[0], end_rot[0], pct),
            lerp_rot_1axis_signed(start_rot[1], end_rot[1], pct),
            lerp_rot_1axis_signed(start_rot[2], end_rot[2], pct)]


def lerp_rot_unsigned(start_rot, end_rot, pct):
    return [lerp_rot_1axis_unsigned(start_rot[0], end_rot[0], pct),
            lerp_rot_1axis_unsigned(start_rot[1], end_rot[1], pct),
            lerp_rot_1axis_unsigned(start_rot[2], end_rot[2], pct)]


def lerp_pos(start_pos, end_pos, pct):
    return [lerp(start_pos[0], end_pos[0], pct),
            lerp(start_pos[1], end_pos[1], pct),
            lerp(start_pos[2], end_pos[2], pct)]


def lerp(p1, p2, pct):
    return (1 - pct)*p1 + pct * p2


def lerp_rot_1axis_unsigned(p1, p2, pct):
    if abs(p1-p2) < 180:
        return (1 - pct) * p1 + pct * p2
    elif p2 > p1:
        p2 += 360
        return ((1 - pct) * p1 + pct * p2) % 360
    else:
        p2 -= 360
        return ((1 - pct) * p1 + pct * p2) % 360


def lerp_rot_1axis_signed(p1, p2, pct):
    if abs(p1 - p2) < 180:
        return (1 - pct) * p1 + pct * p2
    elif p2 < p1:
        p2 += 360
        return (((1 - pct) * p1 + pct * p2)+180) % 360 - 180
    else:
        p2 -= 360
        return (((1 - pct) * p1 + pct * p2)+180) % 360 - 180


def current_milli_time():
    return int(round(time.time() * 1000))


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])

def rotate_rpy(item, roll, pitch, yaw):

    roll = np.deg2rad(roll)
    pitch = np.deg2rad(pitch)
    yaw = np.deg2rad(yaw)

    matrix = [np.cos(roll) * np.cos(pitch),
              np.cos(roll) * np.sin(pitch) * np.sin(yaw) - np.sin(roll) * np.cos(yaw),
              np.cos(roll) * np.sin(pitch) * np.cos(yaw) + np.sin(roll) * np.sin(yaw),
              0,
              np.sin(roll) * np.cos(pitch),
              np.sin(roll) * np.sin(pitch) * np.sin(yaw) + np.cos(roll) * np.cos(yaw),
              np.sin(roll) * np.sin(pitch) * np.cos(yaw) - np.cos(roll) * np.sin(yaw),
              0,
              -np.sin(pitch),
              np.cos(pitch) * np.sin(yaw),
              np.cos(pitch) * np.cos(yaw),
              0,
              0, 0, 0, 1]

    transform = Transform3D(matrix)
    item.applyTransform(transform, True)

def rotate_inv_rpy(item, roll, pitch, yaw):

    roll = np.deg2rad(roll)
    pitch = np.deg2rad(pitch)
    yaw = np.deg2rad(yaw)

    matrix = np.array([[np.cos(roll)*np.cos(pitch),
              np.cos(roll)*np.sin(pitch)*np.sin(yaw)-np.sin(roll)*np.cos(yaw),
              np.cos(roll)*np.sin(pitch)*np.cos(yaw)+np.sin(roll)*np.sin(yaw),
              0],
              [np.sin(roll)*np.cos(pitch),
              np.sin(roll)*np.sin(pitch)*np.sin(yaw)+np.cos(roll)*np.cos(yaw),
              np.sin(roll)*np.sin(pitch)*np.cos(yaw)-np.cos(roll)*np.sin(yaw),
              0],
              [-np.sin(pitch),
              np.cos(pitch)*np.sin(yaw),
              np.cos(pitch)*np.cos(yaw),
              0],
              [0, 0, 0, 1]])

    inverse = np.linalg.inv(matrix)

    matrixList = inverse.flatten().tolist()

    transform = Transform3D(matrixList)
    item.applyTransform(transform, True)


class ModelDisplay(QWidget):

    def __init__(self, lat_key, lon_key, alt_key, blade_rate_key, state_key, roll_key, pitch_key, yaw_key, image_name="", lat_min=0, lat_max=0, lon_min=0, lon_max=0, max_points=50):
        super().__init__()

        self.image_name = image_name

        self.lat_key = lat_key
        self.lon_key = lon_key
        self.alt_key = alt_key
        self.blade_rate_key = blade_rate_key
        self.state_key = state_key
        self.roll_key = roll_key
        self.pitch_key = pitch_key
        self.yaw_key = yaw_key

        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max

        self.x_points = np.array([])
        self.y_points = np.array([])
        self.z_points = np.array([])

        self.roc_detach = False
        self.can_detach = False

        self.roc_pos = [0, 0, 0]
        self.can_pos = [0, 0, 0]
        self.sat_pos = [0, 0, 0]
        self.view_pos = [0, 0, 0]

        self.last_roc_pos = [0, 0, 0]
        self.last_can_pos = [0, 0, 0]
        self.last_sat_pos = [0, 0, 0]
        self.last_view_pos = [0, 0, 0]

        self.curr_roc_pos = [0, 0, 0]
        self.curr_can_pos = [0, 0, 0]
        self.curr_sat_pos = [0, 0, 0]
        self.curr_view_pos = [0, 0, 0]

        self.roc_rot = [0, 0, 0]
        self.can_rot = [0, 0, 0]
        self.sat_rot = [0, 0, 0]

        self.last_roc_rot = [0, 0, 0]
        self.last_can_rot = [0, 0, 0]
        self.last_sat_rot = [0, 0, 0]

        self.curr_roc_rot = [0, 0, 0]
        self.curr_can_rot = [0, 0, 0]
        self.curr_sat_rot = [0, 0, 0]

        self.blade_rate = 0
        self.deploy_angle = 0
        self.last_deploy_angle = 0
        self.blades_deployed = False

        self.chute_deployed = False

        self.update_dt = 1000
        self.update_old_dts = [1000]
        self.update_last_time = 0

        self.max_points = max_points

        self.meters_per_lat = 111000
        self.meters_per_lon = math.cos((lat_min+lat_max)*math.pi/360) * 111321

        self.shader = opengl.shaders.ShaderProgram('lighted', [
            opengl.shaders.VertexShader("""
                varying vec4 diffuse,ambient;
                varying vec3 normal;
                 
                void main()
                {
                    /* first transform the normal into eye space and
                    normalize the result */
                    normal = normalize(gl_NormalMatrix * gl_Normal);
                 
                    /* Compute the diffuse, ambient and globalAmbient terms */
                    diffuse = gl_Color * vec4(0.7, 0.7, 0.6, 1);
                    ambient = gl_Color * vec4(0.3, 0.3, 0.4, 1);
                    gl_Position = ftransform();
                }
            """),
            opengl.shaders.FragmentShader("""

                varying vec4 diffuse,ambient;
                varying vec3 normal;
                 
                void main()
                {
                    vec3 n,lightDir;
                    float NdotL;
                    
                    lightDir = normalize(vec3(1,-1,5));
                 
                    /* The ambient term will always be present */
                    vec4 color = ambient;
                    /* a fragment shader can't write a varying variable, hence we need
                    a new variable to store the normalized interpolated normal */
                    n = normalize(normal);
                    /* compute the dot product between normal and ldir */
                 
                    NdotL = max(dot(n,lightDir),0.0);
                    
                    if (NdotL > 0.0) {
                        color += diffuse * NdotL;
                    }
                    
                    if(gl_FrontFacing)
                    {
                        gl_FragColor = color;
                    }
                    else
                    {
                        gl_FragColor = vec4(1,1,1,0);
                    }
                }
            """)
        ])

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)


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
        self.view.setCameraPosition(distance=2, elevation=45, azimuth=45)
        self.view.pan(0, 0, 0.73)

        self.plot = opengl.GLLinePlotItem(pos=positions)
        self.plot.setGLOptions("opaque")
        self.view.addItem(self.plot)

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
        flat_earth.translate(0, 0, -1000)
        flat_earth.setGLOptions("opaque")
        self.view.addItem(flat_earth)

        rocket_mesh = mesh.Mesh.from_file("DisplayModels/Rocket.stl")
        rocket_mesh_data = opengl.MeshData(vertexes=rocket_mesh.vectors)
        self.rocket = opengl.GLMeshItem(meshdata=rocket_mesh_data, color=[235 / 255, 193 / 255, 153 / 255, 1], smooth=True)
        self.rocket.scale(1/1000, 1/1000, 1/1000)
        self.rocket.setShader(self.shader)
        self.view.addItem(self.rocket)

        payload_mesh = mesh.Mesh.from_file("DisplayModels/PayloadSection.stl")
        payload_mesh_data = opengl.MeshData(vertexes=payload_mesh.vectors)
        self.payload = opengl.GLMeshItem(meshdata=payload_mesh_data, color=[235 / 255, 193 / 255, 153 / 255, 50 / 255])
        self.payload.setParentItem(self.rocket)
        self.payload.setShader(self.shader)
        self.payload.setGLOptions("additive")
        self.view.addItem(self.payload)

        nose_mesh = mesh.Mesh.from_file("DisplayModels/Nosecone.stl")
        nose_mesh_data = opengl.MeshData(vertexes=nose_mesh.vectors)
        self.nose = opengl.GLMeshItem(meshdata=nose_mesh_data, color=[240 / 255, 240 / 255, 240 / 255, 1], smooth=True)
        self.nose.setParentItem(self.rocket)
        self.nose.setShader(self.shader)
        self.view.addItem(self.nose)

        body_mesh = mesh.Mesh.from_file("DisplayModels/Body.stl")
        body_mesh_data = opengl.MeshData(vertexes=body_mesh.vectors)
        self.body = opengl.GLMeshItem(meshdata=body_mesh_data, color=[240 / 255, 20 / 255, 20 / 255, 1], smooth=False)
        self.body.scale(1 / 1000, 1 / 1000, 1 / 1000)
        self.body.setShader(self.shader)
        self.view.addItem(self.body)
        self.body.translate(0, 0, 0.6)

        rotor_mesh = mesh.Mesh.from_file("DisplayModels/Rotor.stl")
        rotor_mesh_data = opengl.MeshData(vertexes=rotor_mesh.vectors)
        self.rotor = opengl.GLMeshItem(meshdata=rotor_mesh_data, color=[200 / 255, 200 / 255, 200 / 255, 1], smooth=False)
        self.rotor.setParentItem(self.body)
        self.rotor.setShader(self.shader)
        self.view.addItem(self.rotor)
        self.rotor.translate(0, 0, 0.6)

        blade_mesh = mesh.Mesh.from_file("DisplayModels/Blade.stl")
        blade_mesh_data = opengl.MeshData(vertexes=blade_mesh.vectors)
        self.blades = [0]*4
        for n in range(0, 4):
            self.blades[n] = opengl.GLMeshItem(meshdata=blade_mesh_data, color=[200 / 255, 200 / 255, 200 / 255, 1], smooth=False)
            self.blades[n].setParentItem(self.rotor)
            self.blades[n].setShader(self.shader)
            self.view.addItem(self.blades[n])
            self.blades[n].rotate(n*90, 0, 0, 1)
            self.blades[n].translate(0, 0, 0.6)
            self.blades[n].translate(45, 0, 255, local=True)
            self.blades[n].rotate(90, 0, 1, 0, local=True)
            self.blades[n].translate(-45, 0, -255, local=True)

        self.blades[-1].setColor([50 / 255, 50 / 255, 50 / 255, 1])

        fin_holder_mesh = mesh.Mesh.from_file("DisplayModels/FinHolder.stl")
        fin_holder_mesh_data = opengl.MeshData(vertexes=fin_holder_mesh.vectors)

        fin_mesh = mesh.Mesh.from_file("DisplayModels/Fin.stl")
        fin_mesh_data = opengl.MeshData(vertexes=fin_mesh.vectors)

        self.fins = [0] * 2
        self.fin_holders = [0] * 2
        for n in range(0, 2):
            self.fin_holders[n] = opengl.GLMeshItem(meshdata=fin_holder_mesh_data,
                                                    color=[200 / 255, 200 / 255, 200 / 255, 1],
                                                    smooth=False)
            self.fin_holders[n].setParentItem(self.body)
            self.fin_holders[n].setShader(self.shader)
            self.view.addItem(self.fin_holders[n])
            self.fin_holders[n].rotate(n * 180, 0, 0, 1)

            self.fins[n] = opengl.GLMeshItem(meshdata=fin_mesh_data, color=[200 / 255, 200 / 255, 200 / 255, 1],
                                               smooth=False)
            self.fins[n].setParentItem(self.fin_holders[n])
            self.fins[n].setShader(self.shader)
            self.view.addItem(self.fins[n])
            self.fins[n].translate(0, 0, 0.6)
            self.fins[n].translate(41.3, 0, 126.5, local=True)
            self.fins[n].rotate(-90, 0, 1, 0, local=True)
            self.fins[n].translate(-41.3, 0, -126.5, local=True)

        can_mesh = mesh.Mesh.from_file("DisplayModels/Container.stl")
        can_mesh_data = opengl.MeshData(vertexes=can_mesh.vectors)
        self.can = opengl.GLMeshItem(meshdata=can_mesh_data, color=[255 / 255, 20 / 255, 147 / 255, 50 / 255],
                                       smooth=True)
        self.can.setShader(self.shader)
        self.can.setGLOptions("additive")
        self.view.addItem(self.can)
        self.can.scale(1 / 1000, 1 / 1000, 1 / 1000)
        self.can.translate(0, 0, 0.6)

        can_roof_mesh = mesh.Mesh.from_file("DisplayModels/ContainerRoof.stl")
        can_roof_mesh_data = opengl.MeshData(vertexes=can_roof_mesh.vectors)
        self.can_roof = opengl.GLMeshItem(meshdata=can_roof_mesh_data, color=[240 / 255, 20 / 255, 20 / 255, 1],
                                     smooth=False)
        self.can_roof.setParentItem(self.can)
        self.can_roof.setShader(self.shader)
        self.view.addItem(self.can_roof)
        self.can_roof.translate(0, 0, 0.6)

        chute_mesh = mesh.Mesh.from_file("DisplayModels/Chute.stl")
        chute_mesh_data = opengl.MeshData(vertexes=chute_mesh.vectors)
        self.chute = opengl.GLMeshItem(meshdata=chute_mesh_data, color=[255 / 255, 20 / 255, 147 / 255, 50 / 255],
                                          smooth=False)
        self.chute.setParentItem(self.can)
        self.chute.setShader(self.shader)
        self.view.addItem(self.chute)
        self.chute.translate(0, 0, 0.6)
        self.chute.hide()

        layout.addWidget(self.view)
        self.view.double_clicked.connect(self.change_speed)

        self.timer.start(16)

    def change_speed(self):
        if self.timer.interval() == 1000:
            self.timer.setInterval(100)
        elif self.timer.interval() == 100:
            self.timer.setInterval(16)
        else:
            self.timer.setInterval(1000)


    def update_plot(self, dictionary):

        dt = current_milli_time() - self.update_last_time
        self.update_old_dts.append(dt if dt < 2000 else 1000)
        self.update_last_time = current_milli_time()
        if len(self.update_old_dts) > 10:
            self.update_old_dts.pop(0)
        self.update_dt = mean(self.update_old_dts)

        if dictionary[self.state_key] == "UNARMED":
            self.rocket.hide()
            self.roc_detach = False
            self.can_detach = False
            self.blades_deployed = False
            self.chute_deployed = False
            self.blade_rate = 0
        elif dictionary[self.state_key] == "PRELAUNCH":
            self.nose.show()
            self.rocket.show()
            self.roc_detach = False
            self.can_detach = False
            self.blades_deployed = False
            self.chute_deployed = False
            self.blade_rate = 0
        elif dictionary[self.state_key] == "ASCENT":
            self.nose.show()
            self.rocket.show()
            self.roc_detach = False
            self.can_detach = False
            self.blades_deployed = False
            self.chute_deployed = False
            self.blade_rate = 0
        elif dictionary[self.state_key] == "DESCENT":
            self.nose.hide()
            self.rocket.show()
            self.roc_detach = True
            self.can_detach = False
            self.blades_deployed = False
            self.chute_deployed = True
            self.blade_rate = 0
        elif dictionary[self.state_key] == "ACTIVE":
            self.nose.hide()
            self.rocket.show()
            self.roc_detach = True
            self.can_detach = True
            self.blades_deployed = True
            self.chute_deployed = True
            self.blade_rate = dictionary[self.blade_rate_key] * 6
        else:
            self.nose.hide()
            self.rocket.show()
            self.roc_detach = True
            self.can_detach = True
            self.blades_deployed = True
            self.chute_deployed = False
            self.blade_rate = 0

        if self.chute_deployed and self.can_pos[2] > 1:
            self.chute.show()
        else:
            self.chute.hide()

        self.last_sat_rot = self.sat_rot
        self.sat_rot = [dictionary[self.yaw_key], dictionary[self.pitch_key], dictionary[self.roll_key]]

        self.last_roc_rot = self.roc_rot
        if not self.roc_detach:
            self.roc_rot = [dictionary[self.yaw_key], dictionary[self.pitch_key], dictionary[self.roll_key]]
        else:
            self.roc_rot[:] = [x - (x * 0.25) for x in self.roc_rot]

        self.last_can_rot = self.can_rot
        if not self.can_detach:
            self.can_rot = [dictionary[self.yaw_key], dictionary[self.pitch_key], dictionary[self.roll_key]]
        else:
            self.can_rot[:] = [x - (x * 0.25) for x in self.can_rot]

        if dictionary[self.lat_key] != 0 and dictionary[self.lon_key] != 0:
            self.x_points = np.append(self.x_points, -(dictionary[self.lat_key]-(self.lat_min+self.lat_max)/2) * self.meters_per_lat)
            self.y_points = np.append(self.y_points, (dictionary[self.lon_key]-(self.lon_min+self.lon_max)/2) * self.meters_per_lon)
            self.z_points = np.append(self.z_points, dictionary[self.alt_key])

        else:
            self.x_points = np.append(self.x_points, 0)
            self.y_points = np.append(self.y_points, 0)
            self.z_points = np.append(self.z_points, dictionary[self.alt_key])

        positions = np.vstack([self.x_points, self.y_points, self.z_points + 0.73]).transpose()
        self.plot.setData(pos=positions)

        self.last_view_pos = self.view_pos
        self.view_pos = [self.x_points[-1], self.y_points[-1], max(self.z_points[-1], 0)]

        self.last_roc_pos = self.roc_pos
        if not self.roc_detach:
            self.roc_pos = [self.x_points[-1], self.y_points[-1], self.z_points[-1]]
        else:
            self.roc_pos = [self.roc_pos[0], self.roc_pos[1], max(self.roc_pos[2] - 5, 0)]

        self.last_can_pos = self.can_pos
        if not self.can_detach:
            self.can_pos = [self.x_points[-1], self.y_points[-1], self.z_points[-1]]
        else:
            self.can_pos = [self.can_pos[0], self.can_pos[1], max(self.can_pos[2] - 5, 0)]

        self.last_sat_pos = self.sat_pos
        self.sat_pos = [self.x_points[-1], self.y_points[-1], max(self.z_points[-1], 0)]

        if self.x_points.size > self.max_points:
            self.x_points = np.delete(self.x_points, 0)
        if self.y_points.size > self.max_points:
            self.y_points = np.delete(self.y_points, 0)
        if self.z_points.size > self.max_points:
            self.z_points = np.delete(self.z_points, 0)



    def refresh(self):
        lerp_pct = min((current_milli_time()-self.update_last_time)/self.update_dt, 1)
        self.rotor.rotate(self.blade_rate*100/1000, 0, 0, 1)
        if self.blades_deployed:
            self.last_deploy_angle = self.deploy_angle
            self.deploy_angle = min(self.deploy_angle + 5, 90)
        else:
            self.last_deploy_angle = self.deploy_angle
            self.deploy_angle = max(self.deploy_angle - 5, 0)
        for blade in self.blades:
            blade.translate(45, 0, 255, local=True)
            blade.rotate(-(self.deploy_angle-self.last_deploy_angle), 0, 1, 0, local=True)
            blade.translate(-45, 0, -255, local=True)
        for fin in self.fins:
            fin.translate(41.3, 0, 126.5, local=True)
            fin.rotate((self.deploy_angle-self.last_deploy_angle), 0, 1, 0, local=True)
            fin.translate(-41.3, 0, -126.5, local=True)
        self.set_view(lerp_pos(self.last_view_pos, self.view_pos, lerp_pct))
        self.set_roc(lerp_pos(self.last_roc_pos, self.roc_pos, lerp_pct),
                     lerp_rot_signed(self.last_roc_rot, self.roc_rot, lerp_pct),
                     [0,0,730])
        self.set_sat(lerp_pos(self.last_sat_pos, self.sat_pos, lerp_pct),
                     lerp_rot_signed(self.last_sat_rot, self.sat_rot, lerp_pct),
                     [0,0,130])
        self.set_can(lerp_pos(self.last_can_pos, self.can_pos, lerp_pct),
                     lerp_rot_signed(self.last_can_rot, self.can_rot, lerp_pct),
                     [0,0,130])

    def set_view(self, pos):
        self.view.pan(pos[0]-self.curr_view_pos[0], pos[1]-self.curr_view_pos[1], pos[2]-self.curr_view_pos[2])
        self.curr_view_pos = pos

    def set_roc(self, pos, rot, rot_ctr):
        self.rocket.translate(pos[0]-self.curr_roc_pos[0], pos[1]-self.curr_roc_pos[1], pos[2]-self.curr_roc_pos[2])
        self.curr_roc_pos = pos
        self.rocket.translate(rot_ctr[0], rot_ctr[1], rot_ctr[2], local=True)
        rotate_inv_rpy(self.rocket, self.curr_roc_rot[0], self.curr_roc_rot[1], self.curr_roc_rot[2])
        rotate_rpy(self.rocket, rot[0], rot[1], rot[2])
        self.rocket.translate(-rot_ctr[0], -rot_ctr[1], -rot_ctr[2], local=True)
        self.curr_roc_rot = rot

    def set_sat(self, pos, rot, rot_ctr):
        self.body.translate(pos[0] - self.curr_sat_pos[0], pos[1] - self.curr_sat_pos[1],
                              pos[2] - self.curr_sat_pos[2])
        self.curr_sat_pos = pos
        self.body.translate(rot_ctr[0], rot_ctr[1], rot_ctr[2], local=True)
        rotate_inv_rpy(self.body, self.curr_sat_rot[0], self.curr_sat_rot[1], self.curr_sat_rot[2])
        rotate_rpy(self.body, rot[0], rot[1], rot[2])
        self.body.translate(-rot_ctr[0], -rot_ctr[1], -rot_ctr[2], local=True)
        self.curr_sat_rot = rot

    def set_can(self, pos, rot, rot_ctr):
        self.can.translate(pos[0] - self.curr_can_pos[0], pos[1] - self.curr_can_pos[1],
                           pos[2] - self.curr_can_pos[2])
        self.curr_can_pos = pos
        self.can.translate(rot_ctr[0], rot_ctr[1], rot_ctr[2], local=True)
        rotate_inv_rpy(self.can, self.curr_can_rot[0], self.curr_can_rot[1], self.curr_can_rot[2])
        rotate_rpy(self.can, rot[0], rot[1], rot[2])
        self.can.translate(-rot_ctr[0], -rot_ctr[1], -rot_ctr[2], local=True)

        self.chute.translate(0, 0, 303.13, local=True)
        rotate_rpy(self.chute, self.curr_can_rot[0], self.curr_can_rot[1], self.curr_can_rot[2])
        rotate_inv_rpy(self.chute, rot[0], rot[1], rot[2])
        self.chute.translate(0, 0, -303.13, local=True)

        self.curr_can_rot = rot

    def clear_plot(self):
        self.x_points = np.array([])
        self.y_points = np.array([])
        self.z_points = np.array([])

        positions = np.vstack([self.x_points, self.y_points, self.z_points]).transpose()

        self.plot.setData(pos=positions)






