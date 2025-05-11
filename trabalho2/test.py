import glfw
from OpenGL.GL import *
from PIL import Image
import numpy as np
import glm

class OBJLoader:
    def __init__(self, filename):
        self.vertices = []
        self.texcoords = []
        self.normals = []
        self.faces = []
        self.materials = {}
        self.textures = {}

        self.current_material = None
        self.load_model(filename)

    def load_model(self, filename):
        material_lib = None
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('mtllib'):
                    material_lib = line.strip().split()[1]
                    self.load_mtl(material_lib)
                elif line.startswith('usemtl'):
                    self.current_material = line.strip().split()[1]
                elif line.startswith('v '):
                    self.vertices.append(list(map(float, line.strip().split()[1:])))
                elif line.startswith('vt '):
                    self.texcoords.append(list(map(float, line.strip().split()[1:])))
                elif line.startswith('vn '):
                    self.normals.append(list(map(float, line.strip().split()[1:])))
                elif line.startswith('f '):
                    face = []
                    for vert in line.strip().split()[1:]:
                        vals = vert.split('/')
                        v_idx = int(vals[0]) - 1
                        vt_idx = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else 0
                        vn_idx = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else 0
                        face.append((v_idx, vt_idx, vn_idx, self.current_material))
                    self.faces.append(face)

    def load_mtl(self, filename):
        current_mtl = None
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('newmtl'):
                    current_mtl = line.strip().split()[1]
                    self.materials[current_mtl] = {}
                elif line.startswith('map_Kd') and current_mtl:
                    texture_file = line.strip().split()[1]
                    self.materials[current_mtl]['map_Kd'] = texture_file
                    self.textures[current_mtl] = self.load_texture(texture_file)

    def load_texture(self, filename):
        img = Image.open(filename).convert('RGBA')
        img_data = np.array(list(img.getdata()), np.uint8)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        return tex_id

    def render(self):
        current_tex = None
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for v_idx, vt_idx, vn_idx, material in face:
                if material in self.textures and self.textures[material] != current_tex:
                    glEnd()
                    glBindTexture(GL_TEXTURE_2D, self.textures[material])
                    glBegin(GL_TRIANGLES)
                    current_tex = self.textures[material]

                if vt_idx < len(self.texcoords):
                    glTexCoord2fv(self.texcoords[vt_idx])
                if vn_idx < len(self.normals):
                    glNormal3fv(self.normals[vn_idx])
                glVertex3fv(self.vertices[v_idx])
        glEnd()
        glDisable(GL_TEXTURE_2D)

# ===================== GLFW & OpenGL Setup ========================

def main():
    if not glfw.init():
        return

    window = glfw.create_window(800, 600, "OBJ Loader with MTL", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glm.perspective(45, 800/600, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    obj = OBJLoader("Campfire_OBJ.obj")

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glm.lookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

        obj.render()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
