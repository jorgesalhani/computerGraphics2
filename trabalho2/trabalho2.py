import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
from PIL import Image
import glm
import os

# Camera state
camera_pos = glm.vec3(0.0, 1.0, 5.0)
camera_front = glm.vec3(0.0, 0.0, -1.0)
camera_up = glm.vec3(0.0, 1.0, 0.0)

first_mouse = True
last_x, last_y = 400, 300
yaw = -90.0
pitch = 0.0
sensitivity = 0.1

import math

def compute_model_matrix(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    angle = math.radians(angle)
    matrix_transform = glm.mat4(1.0)

    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))

    if angle != 0:
        matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(r_x, r_y, r_z))

    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))

    return matrix_transform

class ObjectLoad:
    def __init__(self, obj_path, texture_file = None):
        self.vertices = self.load_obj(obj_path, texture_file)
        self.model = glm.mat4(1.0)
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.setup_buffers()

        # Transformation state
        self.angle = 0.0
        self.position = glm.vec3(0.0, 0.0, 0.0)
        self.scale_factor = glm.vec3(1.0, 1.0, 1.0)
        self.rotate_coords = glm.vec3(0.0, 0.0, 0.0)

    def update_model_matrix(self):
        self.model = compute_model_matrix(
            self.angle,
            self.rotate_coords.x, self.rotate_coords.y, self.rotate_coords.z,
            self.position.x, self.position.y, self.position.z,
            self.scale_factor.x, self.scale_factor.y, self.scale_factor.z
        )

    def move(self, x=0, y=0, z=0):
        self.position.x += x 
        self.position.y += y
        self.position.z += z
        self.update_model_matrix()

    def scale(self, x=1, y=1, z=1):
        self.scale_factor.x *= x
        self.scale_factor.y *= y
        self.scale_factor.z *= z
        self.update_model_matrix()

    def rotate(self, degrees=0.1, axis='x'):
        self.angle += degrees
        if axis == 'x': self.rotate_coords.x = 1
        if axis == 'y': self.rotate_coords.y = 1
        if axis == 'z': self.rotate_coords.z = 1
        self.update_model_matrix()
        self.update_model_matrix()

    def load_texture(self, path):
        img = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGBA").tobytes()
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)
        return texture

    def load_obj(self, path, texture_file):
        positions = []
        texcoords = []
        faces = []
        mtl_path = None

        base_dir = os.path.dirname(path)

        with open(path, 'r') as file:
            for line in file:
                if line.startswith('mtllib'):
                    mtl_name = ''.join(line.strip().split(' ', 1)[1:])
                    mtl_path = os.path.join(base_dir, mtl_name)
                elif line.startswith('v '):
                    parts = line.strip().split()[1:]
                    positions.append([float(p) for p in parts])
                elif line.startswith('vt '):
                    parts = line.strip().split()[1:]
                    texcoords.append([float(p) for p in parts])
                elif line.startswith('f '):
                    parts = line.strip().split()[1:]
                    face = []
                    for part in parts:
                        v_idx, vt_idx = (part.split('/') + [0, 0])[:2]
                        face.append((int(v_idx) - 1, int(vt_idx) - 1))
                    if len(face) == 3:
                        faces.append(face)
                    elif len(face) == 4:
                        faces.append([face[0], face[1], face[2]])
                        faces.append([face[0], face[2], face[3]])

        # parse the mtl file (if any)
        if mtl_path and os.path.exists(mtl_path):
            with open(mtl_path, 'r') as mtl_file:
                for line in mtl_file:
                    if line.startswith("map_Kd"):
                        texture_file = os.path.join(base_dir, ''.join(line.strip().split(' ', 1)[1:]))
                        break

        self.texture = self.load_texture(texture_file) if texture_file else None

        vertex_data = []
        for face in faces:
            for v_idx, vt_idx in face:
                if abs(v_idx) > len(positions) - 1: 
                    break
                vertex = positions[v_idx]
                tex = texcoords[vt_idx]
                vertex_data.extend(vertex[:3] + tex[:2])

        return np.array(vertex_data, dtype=np.float32)


    def setup_buffers(self):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

    def draw(self, shader):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBindVertexArray(self.vao)
        glUniformMatrix4fv(glGetUniformLocation(shader, "model"), 1, GL_FALSE, glm.value_ptr(self.model))
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 5)

# Callbacks
def scroll_callback(window, xoffset, yoffset):
    global camera_pos, camera_front
    camera_pos += camera_front * float(yoffset)

def mouse_callback(window, xpos, ypos):
    global first_mouse, last_x, last_y, yaw, pitch, camera_front

    if first_mouse:
        last_x = xpos
        last_y = ypos
        first_mouse = False

    xoffset = xpos - last_x
    yoffset = last_y - ypos  # reversed: y ranges bottom to top
    last_x = xpos
    last_y = ypos

    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # Constrain pitch
    pitch = max(-89.0, min(89.0, pitch))

    # Convert spherical to cartesian coords
    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    camera_front = glm.normalize(front)


def key_callback(window, key, scancode, action, mods):
    global camera_pos, camera_front, camera_up

    objects = glfw.get_window_user_pointer(window)
    # obj1 : ObjectLoad = objects["obj1"]
    # obj2 : ObjectLoad = objects["obj2"]

    speed = 0.1
    translate_step = 0.1
    scale_step = 0.1
    rotate_step = 10

    if action == glfw.PRESS and key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)

    if action == glfw.PRESS or action == glfw.REPEAT:
        right = glm.normalize(glm.cross(camera_front, camera_up))

        # Camera controls
        if key == glfw.KEY_LEFT:
            camera_pos -= right * speed
        elif key == glfw.KEY_RIGHT:
            camera_pos += right * speed
        elif key == glfw.KEY_UP:
            if camera_pos.y + speed >= 0:
                camera_pos += camera_up * speed
        elif key == glfw.KEY_DOWN:
            if camera_pos.y - speed >= 0:
                camera_pos -= camera_up * speed

        # # Object controls
        # elif key == glfw.KEY_A:
        #     obj1.move(x=-translate_step)
        # elif key == glfw.KEY_D:
        #     obj2.move(x=translate_step)

# Shader
vertex_src = """
#version 330 core
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_texcoord;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
out vec2 texcoord;
void main() {
    gl_Position = projection * view * model * vec4(a_position, 1.0);
    texcoord = a_texcoord;
}
"""

fragment_src = """
#version 330 core
in vec2 texcoord;
out vec4 out_color;
uniform sampler2D tex;
void main() {
    out_color = texture(tex, texcoord);
}
"""

# Main
def main():
    if not glfw.init():
        return

    window = glfw.create_window(800, 600, "ObjectLoad Class Demo", None, None)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.make_context_current(window)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)

    shader = compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER)
    )

    glUseProgram(shader)
    glEnable(GL_DEPTH_TEST)

    objects = {
        # 'objSky': ObjectLoad("objects/caixa/caixa.obj", "objects/caixa/matrix.jpg"),
        # 'objBox': ObjectLoad("objects/caixa/caixa.obj", "objects/caixa/caixa.jpg"),
        'obj1': ObjectLoad("objects/desk/Stylized_Desk.obj"),
        'obj2': ObjectLoad("objects/miniDesk/japanschooldesk.obj"),
        'obj3': ObjectLoad("objects/tableOut/Outdoor Furniture_02_obj.obj"),
        'obj4': ObjectLoad("objects/plant1/eb_house_plant_01.obj"),
        'obj5': ObjectLoad("objects/plant2/eb_house_plant_02.obj"),
        'obj6': ObjectLoad("objects/plant3/eb_house_plant_03.obj"),
        'obj7': ObjectLoad("objects/cat/Cat_v1_l3.obj"),
        'obj8': ObjectLoad("objects/tree/Tree2.obj"),
    }
    # objects['objSky'].scale(10, 10, 10)
    # objects['objSky'].move(y=9.9)
    # objects['objBox'].scale(5, 5, 5)
    # objects['objBox'].move(y=5)
    objects['obj1'].scale(0.01, 0.01, 0.01)
    objects['obj1'].move(x=3)
    objects['obj2'].move(z=4)
    objects['obj3'].move(x=4,z=-4)
    objects['obj3'].scale(0.02, 0.02, 0.02)
    objects['obj4'].scale(0.04, 0.04, 0.04)
    objects['obj4'].move(z=-5)
    objects['obj5'].scale(0.04, 0.04, 0.04)
    objects['obj5'].move(z=-3.4)
    objects['obj6'].scale(0.04, 0.04, 0.04)
    objects['obj6'].move(x=-3,z=-3.4)
    objects['obj7'].scale(0.02, 0.02, 0.02)
    objects['obj7'].rotate(90, axis='z')
    objects['obj7'].rotate(90, axis='y')
    objects['obj7'].move(z=-2)
    objects['obj8'].scale(0.5, 0.5, 0.5)


    
    glfw.set_window_user_pointer(window, objects)

    projection = glm.perspective(glm.radians(45.0), 800/600, 0.1, 100.0)

    while not glfw.window_should_close(window):
        glfw.poll_events()

        view = glm.lookAt(camera_pos, camera_pos + camera_front, camera_up)

        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glUseProgram(shader)
        glUniformMatrix4fv(glGetUniformLocation(shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(glGetUniformLocation(shader, "projection"), 1, GL_FALSE, glm.value_ptr(projection))

        for obj in objects.values():
            model_loc = glGetUniformLocation(shader, "model")
            glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(obj.model))

            if obj.texture:  # Ensure texture is bound only if one was loaded
                glBindTexture(GL_TEXTURE_2D, obj.texture)

            glBindVertexArray(obj.vao)
            glDrawArrays(GL_TRIANGLES, 0, len(obj.vertices) // 5)
        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()
