"""
TRABALHO 1: código fonte

Integrantes:
-- Nome: Jorge Augusto Salgado Salhani
-- NUsp: 8927418
"""

import glfw
from OpenGL.GL import *
import numpy as np

from controlers.keyControl import KeyControl
from controlers.objectsControl import ObjectControl
from controlers.objectsBuildControl import ObjectsBuildControl

# Inicialização de janela e shaders
# =================================
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
window = glfw.create_window(700, 700, "Programa", None, None)

if (window == None):
    print("Failed to create GLFW window")
    glfw.terminate()
    
glfw.make_context_current(window)

vertex_code = """
        attribute vec3 position;
        uniform mat4 mat_transformation;
        void main(){
            gl_Position = mat_transformation * vec4(position,1.0);
        }
        """

fragment_code = """
        uniform vec4 color;
        void main(){
            gl_FragColor = color;
        }
        """

# Request a program and shader slots from GPU
program  = glCreateProgram()
vertex   = glCreateShader(GL_VERTEX_SHADER)
fragment = glCreateShader(GL_FRAGMENT_SHADER)

# Set shaders source
glShaderSource(vertex, vertex_code)
glShaderSource(fragment, fragment_code)

# Compile shaders
glCompileShader(vertex)
if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
    error = glGetShaderInfoLog(vertex).decode()
    print(error)
    raise RuntimeError("Erro de compilacao do Vertex Shader")

glCompileShader(fragment)
if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
    error = glGetShaderInfoLog(fragment).decode()
    print(error)
    raise RuntimeError("Erro de compilacao do Fragment Shader")

# Attach shader objects to the program
glAttachShader(program, vertex)
glAttachShader(program, fragment)

# Build program
glLinkProgram(program)
if not glGetProgramiv(program, GL_LINK_STATUS):
    print(glGetProgramInfoLog(program))
    raise RuntimeError('Linking error')
    
# Make program the default program
glUseProgram(program)

objectsControl = ObjectControl('./trabalho1/objects')
objectsBuildControl = ObjectsBuildControl('./trabalho1/objects')

# Carregando objetos
# ==================
objectsControl.load_object('rocks.json')
objectsControl.load_object('floor.json')
objectsControl.load_object('lighthouse.json')

# Normalizando objetos 
# construídos fora do cubo unitário
# =================================
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 3, 'dino')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'S', 5, 'S0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'E', 5, 'E0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'M', 5, 'M0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'I', 5, 'I0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'N', 5, 'N0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'T', 5, 'T0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'E', 5, 'E1')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'R', 5, 'R0')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'N', 5, 'N1')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'E', 5, 'E2')
# objectsBuildControl.normalize_sketch('./trabalho1/sketches', 'T', 5, 'T1')

# Construindo objetos via código
# ==============================
global_offset_moon = objectsBuildControl.build_moon()
global_offset_lighhouse_top = objectsBuildControl.build_lighthouse_top()
global_offset_cloud = objectsBuildControl.build_cloud()

# Carregando vértices dos objetos
# ===============================
objectsControl.load_object('moon.json', global_offset_moon)
objectsControl.load_object('dino.json', [-0.5,-0.5,-0.5])
objectsControl.load_object('S0.json', [6,0,0.8])
objectsControl.load_object('E0.json', [6.3,0,0.8])
objectsControl.load_object('M0.json', [6.6,0,0.8])
objectsControl.load_object('I0.json', [7,0,0.8])
objectsControl.load_object('N0.json', [7.3,0,0.8])
objectsControl.load_object('T0.json', [7.6,0,0.8])
objectsControl.load_object('E1.json', [7.9,0,0.8])
objectsControl.load_object('R0.json', [8.2,0,0.8])
objectsControl.load_object('N1.json', [8.5,0,0.8])
objectsControl.load_object('E2.json', [8.8,0,0.8])
objectsControl.load_object('T1.json', [9.1,0,0.8])

objectsControl.load_object('lighthouse_top.json', global_offset_lighhouse_top)
objectsControl.load_object('cloud.json', global_offset_cloud)

vertices_list = objectsControl.vertices_list['vertices']
faces_color = objectsControl.faces_color

total_vertices = len(vertices_list)
vertices = np.zeros(total_vertices, [("position", np.float32, 3)])
vertices['position'] = vertices_list

# Request a buffer slot from GPU
buffer_VBO = glGenBuffers(1)
# Make this buffer the default one
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO)

# Upload data
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO)

# Bind the position attribute
# --------------------------------------
stride = vertices.strides[0]
offset = ctypes.c_void_p(0)

loc = glGetAttribLocation(program, "position")
glEnableVertexAttribArray(loc)

glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

loc_color = glGetUniformLocation(program, "color")

keyControl = KeyControl()

def key_event(window,key,scancode,action,mods):
    keyControl.action(window=window, key=key, action=action, objectsControl=objectsControl)
                   
glfw.set_key_callback(window, key_event)
glfw.show_window(window)

glEnable(GL_DEPTH_TEST) ### importante para 3D
while not glfw.window_should_close(window):
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    
    glClearColor(1.0, 1.0, 1.0, 1.0)

    # Aplicando transformações por objeto
    # ===================================
    objectsControl.apply_transform(program, 'cloud')    
    objectsControl.apply_transform(program, 'moon')
    objectsControl.apply_transform(program, 'rocks')
    objectsControl.apply_transform(program, 'floor')
    objectsControl.apply_transform(program, 'dino')
    objectsControl.apply_transform(program, 'lighthouse')
    objectsControl.apply_transform(program, 'lighthouse_top')

    objectsControl.apply_transform(program, 'S0')
    objectsControl.apply_transform(program, 'E0')
    objectsControl.apply_transform(program, 'M0')
    objectsControl.apply_transform(program, 'I0')
    objectsControl.apply_transform(program, 'N0')
    objectsControl.apply_transform(program, 'T0')
    objectsControl.apply_transform(program, 'E1')
    objectsControl.apply_transform(program, 'R0')
    objectsControl.apply_transform(program, 'N1')
    objectsControl.apply_transform(program, 'E2')
    objectsControl.apply_transform(program, 'T1')
    
    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()