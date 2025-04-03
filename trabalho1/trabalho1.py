import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math

from keyControl import KeyControl
from objectsControl import ObjectControl

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE);
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

objectsControl = ObjectControl('../trabalho1/objects')

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

# incrementos para translacao
x_inc = 0.0
y_inc = 0.0

# incrementos para rotacao
r_inc = 0.0

# coeficiente de escala
s_inc = 1.0

keyControl = KeyControl()

def key_event(window,key,scancode,action,mods):
    global x_inc, y_inc, r_inc, s_inc
    
    if key == 263: x_inc -= 0.0001 #esquerda
    if key == 262: x_inc += 0.0001 #direita

    if key == 265: y_inc += 0.0001 #cima
    if key == 264: y_inc -= 0.0001 #baixo
        
    if key == 65: r_inc += 0.1 #letra a
    if key == 83: r_inc -= 0.1 #letra s
        
    if key == 90: s_inc += 0.1 #letra z
    if key == 88: s_inc -= 0.1 #letra x

    keyControl.set_key_pressed(key, action)
        
           
glfw.set_key_callback(window,key_event)

glfw.show_window(window)

anguloRotacao = 0.0

glEnable(GL_DEPTH_TEST) ### importante para 3D

def multiplica_matriz(a,b):
    m_a = a.reshape(4,4)
    m_b = b.reshape(4,4)
    m_c = np.dot(m_a,m_b)
    c = m_c.reshape(1,16)
    return c

def draw_objects():
    for face_color in faces_color:
        r,g,b,a = face_color['rgb']
        vi, vt = face_color['first'], face_color['total']
        glUniform4f(loc_color, r, g, b, a)
        glDrawArrays(GL_TRIANGLE_STRIP, vi, vt)

t_x = 0
t_y = 0

while not glfw.window_should_close(window):

    t_x += x_inc
    t_y += y_inc

    keyControl.action(window=window)
    
    ### apenas para visualizarmos o cubo rotacionando
    anguloRotacao -= 0.001 # modifica o angulo de rotacao em cada iteracao
    cos_d = math.cos(anguloRotacao)
    sin_d = math.sin(anguloRotacao)
    
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    
    glClearColor(1.0, 1.0, 1.0, 1.0)
    
    mat_rotation_z = np.array([     cos_d, -sin_d, 0.0, 0.0, 
                                    sin_d,  cos_d, 0.0, 0.0, 
                                    0.0,      0.0, 1.0, 0.0, 
                                    0.0,      0.0, 0.0, 1.0], np.float32)
    
    mat_rotation_x = np.array([     1.0,   0.0,    0.0, 0.0, 
                                    0.0, cos_d, -sin_d, 0.0, 
                                    0.0, sin_d,  cos_d, 0.0, 
                                    0.0,   0.0,    0.0, 1.0], np.float32)
    
    mat_rotation_y = np.array([     cos_d,  0.0, sin_d, 0.0, 
                                    0.0,    1.0,   0.0, 0.0, 
                                    -sin_d, 0.0, cos_d, 0.0, 
                                    0.0,    0.0,   0.0, 1.0], np.float32)
    
    mat_translacao = np.array([     1.0,  0.0, 0.0,     t_x, 
                                    0.0,    1.0,   0.0, t_y, 
                                    0.0,    0.0,   1.0, 0.0, 
                                    0.0,    0.0,   0.0, 1.0], np.float32)


    # sequencia de transformações: rotação z, rotação y, rotação x, translação
    mat_transform = multiplica_matriz(mat_rotation_z,mat_rotation_y)
    mat_transform = multiplica_matriz(mat_rotation_x,mat_transform)
    mat_transform = multiplica_matriz(mat_translacao,mat_transform) #translacao ultima


    ########## Essa sequencia
    #
    #mat_transform = mat_rotation_x
    #mat_transform = multiplica_matriz(mat_translacao,mat_transform)
    #
    ############# tem o mesmo efeito que essa (ambas executam a rotação_x e depois a translação)
    #
    #mat_transform = mat_translacao
    #mat_transform = multiplica_matriz(mat_transform, mat_rotation_x)

    loc_transformation = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_transformation, 1, GL_TRUE, mat_transform) 

    draw_objects()
    
    # glUniform4f(loc_color, 0, 0, 1, 1.0) ### azul
    # glDrawArrays(GL_TRIANGLE_STRIP, 4, 4)
    
    # glUniform4f(loc_color, 0, 1, 0, 1.0) ### verde
    # glDrawArrays(GL_TRIANGLE_STRIP, 8, 4)
    
    # glUniform4f(loc_color, 1, 1, 0, 1.0) ### amarela
    # glDrawArrays(GL_TRIANGLE_STRIP, 12, 4)
    
    # glUniform4f(loc_color, 0.5, 0.5, 0.5, 1.0) ### cinza
    # glDrawArrays(GL_TRIANGLE_STRIP, 16, 4)
    
    # glUniform4f(loc_color, 0.5, 0, 0, 1.0) ### marrom
    # glDrawArrays(GL_TRIANGLE_STRIP, 20, 4)

    # glUniform4f(loc_color, 0.5, 0, 0, 1.0) ### marrom
    # glDrawArrays(GL_TRIANGLE_STRIP, 24, 3)

    # glUniform4f(loc_color, 1, 1, 0, 1.0) ### amarela
    # glDrawArrays(GL_TRIANGLE_STRIP, 27, 3)
    
    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()