import glfw
from OpenGL.GL import *
import numpy as np

from controlers.keyControl import KeyControl
from controlers.objectsControl import ObjectControl
from controlers.transformControl import TransformControl

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

# preenchendo as coordenadas de cada vértice
objectsControl.load_object('background.json')
objectsControl.load_object('piramide.json')

vertices_list = objectsControl.vertices_list['vertices']
faces_color = objectsControl.faces_color
# print(faces_color)

total_vertices = len(vertices_list)
vertices = np.zeros(total_vertices, [("position", np.float32, 3)])
vertices['position'] = vertices_list
# print(vertices['position'])

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

    objectsControl.apply_transform(program, 'background')
    objectsControl.apply_transform(program, 'piramide')
    
    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()