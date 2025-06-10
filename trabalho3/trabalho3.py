from OpenGL.GL import *
from glfw.GLFW import *

from glfw import _GLFWwindow as GLFWwindow
from PIL import Image

import glm

from shader_m import Shader
from camera import Camera, Camera_Movement

import platform, ctypes, os
import math
import numpy as np

def load_obj_model(filepath):
    positions = []
    texcoords = []
    normals = []
    vertices = []

    def parse_vertex(v_str):
        vals = v_str.split('/')
        v_idx = int(vals[0]) - 1
        vt_idx = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else 0
        vn_idx = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else 0
        return v_idx, vt_idx, vn_idx

    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("v "):  # Vertex position
                parts = line.strip().split()[1:]
                positions.append([float(p) for p in parts])
            elif line.startswith("vt "):  # Texture coordinate
                parts = line.strip().split()[1:]
                texcoords.append([float(p) for p in parts])
            elif line.startswith("vn "):  # Vertex normal
                parts = line.strip().split()[1:]
                normals.append([float(p) for p in parts])
            elif line.startswith("f "):  # Face
                face = line.strip().split()[1:]
                face_indices = [parse_vertex(v) for v in face]

                # Triangulate face using fan method: (0, i, i+1)
                for i in range(1, len(face_indices) - 1):
                    tri = [face_indices[0], face_indices[i], face_indices[i + 1]]
                    for v_idx, vt_idx, vn_idx in tri:
                        pos = positions[v_idx]
                        tex = texcoords[vt_idx] if texcoords else [0.0, 0.0]
                        norm = normals[vn_idx] if normals else [0.0, 0.0, 0.0]
                        vertices.extend(pos + norm + tex)

    return glm.array(glm.float32, *vertices)

def compute_model_matrix(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    angle = math.radians(angle)
    matrix_transform = glm.mat4(1.0)

    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))

    if angle != 0:
        matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(r_x, r_y, r_z))

    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))

    return matrix_transform

class LoadObject:
    def __init__(self, obj_path: str, diffuse_path: str, specular_path: str):
        self.vertices = load_obj_model(obj_path)
        self.diffuseMap = loadTexture(diffuse_path)
        self.specularMap = loadTexture(specular_path)

        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)

        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices.ptr, GL_STATIC_DRAW)

        stride = 8 * glm.sizeof(glm.float32)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * glm.sizeof(glm.float32)))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * glm.sizeof(glm.float32)))
        glEnableVertexAttribArray(2)

        glBindVertexArray(0)

        self.angle = 0.0
        self.position = glm.vec3(0.0, 0.0, 0.0)
        self.scale_factor = glm.vec3(1.0, 1.0, 1.0)
        self.rotate_coords = glm.vec3(0.0, 0.0, 0.0)
        self.model = glm.mat4(1.0)

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

    def draw(self, shader: Shader, model_matrix: glm.mat4):
        shader.setMat4("model", model_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.diffuseMap)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.specularMap)

        glBindVertexArray(self.VAO)
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 8)
        glBindVertexArray(0)


# the relative path where the textures are located
IMAGE_RESOURCE_PATH = "./texturas/"

# function that loads and automatically flips an image vertically
LOAD_IMAGE = lambda name: Image.open(name).transpose(Image.FLIP_TOP_BOTTOM)

# settings
SCR_WIDTH = 800
SCR_HEIGHT = 600

# camera
camera = Camera(glm.vec3(0.0, 5.0, 3.0))
lastX = SCR_WIDTH / 2.0
lastY = SCR_HEIGHT / 2.0
firstMouse = True

# timing
deltaTime = 0.0
lastFrame = 0.0

# lighting
lightPos = glm.vec3(1.2, 1.0, 2.0)

enable_ambient = True
enable_diffuse = True
enable_specular = True

rotation_angle = 0.0
light_radius = 10.0
light_height = 50.0 

def main() -> int:
    global deltaTime, lastFrame, rotation_angle, light_radius

    # glfw: initialize and configure
    # ------------------------------
    glfwInit()
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)

    if (platform.system() == "Darwin"): # APPLE
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE)

    # glfw window creation
    # --------------------
    window = glfwCreateWindow(SCR_WIDTH, SCR_HEIGHT, "LearnOpenGL", None, None)
    if (window == None):

        print("Failed to create GLFW window")
        glfwTerminate()
        return -1

    glfwMakeContextCurrent(window)
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)
    glfwSetCursorPosCallback(window, mouse_callback)
    glfwSetScrollCallback(window, scroll_callback)

    # tell GLFW to capture our mouse
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)

    # configure global opengl state
    # -----------------------------
    glEnable(GL_DEPTH_TEST)

    # build and compile our shader zprogram
    # ------------------------------------
    lightingShader = Shader("6.multiple_lights.vs", "6.multiple_lights.fs")
    lightCubeShader = Shader("6.light_cube.vs", "6.light_cube.fs")
    # set up vertex data (and buffer(s)) and configure vertex attributes
    # ------------------------------------------------------------------
    vertices = glm.array(glm.float32,
        # positions          # normals           # texture coords
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  0.0,  0.0,
         0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  1.0,  0.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  1.0,  1.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  1.0,  1.0,
        -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  0.0,  1.0,
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  0.0,  0.0,

        -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,  0.0,  0.0,
         0.5, -0.5,  0.5,  0.0,  0.0,  1.0,  1.0,  0.0,
         0.5,  0.5,  0.5,  0.0,  0.0,  1.0,  1.0,  1.0,
         0.5,  0.5,  0.5,  0.0,  0.0,  1.0,  1.0,  1.0,
        -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,  0.0,  1.0,
        -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,  0.0,  0.0,

        -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,  1.0,  0.0,
        -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,  1.0,  1.0,
        -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,  0.0,  1.0,
        -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,  0.0,  1.0,
        -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,  0.0,  0.0,
        -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,  1.0,  0.0,

         0.5,  0.5,  0.5,  1.0,  0.0,  0.0,  1.0,  0.0,
         0.5,  0.5, -0.5,  1.0,  0.0,  0.0,  1.0,  1.0,
         0.5, -0.5, -0.5,  1.0,  0.0,  0.0,  0.0,  1.0,
         0.5, -0.5, -0.5,  1.0,  0.0,  0.0,  0.0,  1.0,
         0.5, -0.5,  0.5,  1.0,  0.0,  0.0,  0.0,  0.0,
         0.5,  0.5,  0.5,  1.0,  0.0,  0.0,  1.0,  0.0,

        -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,  0.0,  1.0,
         0.5, -0.5, -0.5,  0.0, -1.0,  0.0,  1.0,  1.0,
         0.5, -0.5,  0.5,  0.0, -1.0,  0.0,  1.0,  0.0,
         0.5, -0.5,  0.5,  0.0, -1.0,  0.0,  1.0,  0.0,
        -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,  0.0,  0.0,
        -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,  0.0,  1.0,

        -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,  0.0,  1.0,
         0.5,  0.5, -0.5,  0.0,  1.0,  0.0,  1.0,  1.0,
         0.5,  0.5,  0.5,  0.0,  1.0,  0.0,  1.0,  0.0,
         0.5,  0.5,  0.5,  0.0,  1.0,  0.0,  1.0,  0.0,
        -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,  0.0,  0.0,
        -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,  0.0,  1.0
    )

    # positions of the point lights
    pointLightPositions = [
        # ambient
        glm.vec3( 140,  140, 140),
        glm.vec3( -140,  140,  140),
        glm.vec3( 140,  140,  -140),
        glm.vec3( -140,  140,  -140),

        # buddha
        glm.vec3( 65,  50.0,  65),

        # templo
        glm.vec3( 4.49172, 9, -24.85),
        glm.vec3( -4.49172, 9, -24.85),
        glm.vec3( 10.0,  8.0, -40.0),
        glm.vec3( -10.0,  8.0, -40.0),

        glm.vec3( 5, 19.3, -24.3),
        glm.vec3( -5, 19.3, -24.3),
        glm.vec3( 10.0,  8.0, -20.0),
        glm.vec3( -10.0,  8.0, -20.0),

        # entrada

        glm.vec3( -3.8,  4.2, -5.0),
        glm.vec3( 3.8,  4.2, -5.0),

        glm.vec3( -6.5,  17.2, 20.0),
        glm.vec3( 6.5,  17.2, 20.0),

        glm.vec3( -3.8,  4.2, 14),
        glm.vec3( 3.8,  4.2, 14),

        glm.vec3( -3.8,  4.2, 30.0),
        glm.vec3( 3.8,  4.2, 30.0),
    ]

    # first, configure the cube's VAO (and VBO)
    cubeVAO = glGenVertexArrays(1)
    VBO = glGenBuffers(1)

    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

    glBindVertexArray(cubeVAO)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * glm.sizeof(glm.float32), ctypes.c_void_p(3 * glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * glm.sizeof(glm.float32), ctypes.c_void_p(6 * glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(2)

    # second, configure the light's VAO (VBO stays the same the vertices are the same for the light object which is also a 3D cube)
    lightCubeVAO = glGenVertexArrays(1)
    glBindVertexArray(lightCubeVAO)

    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    # note that we update the lamp's position attribute's stride to reflect the updated buffer data
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # load textures (we now use a utility function to keep the code more organized)
    # -----------------------------------------------------------------------------

    # shader configuration
    # --------------------
    lightingShader.use()
    lightingShader.setInt("material.diffuse", 0)
    lightingShader.setInt("material.specular", 1)

    objects = {
        'boxSky': LoadObject("./objects/cube/cube.obj", "./objects/cube/Textures/sky.png", "./objects/cube/Textures/container2_specular.png"),
        'boxFloor': LoadObject("./objects/cube/cube.obj", "./objects/cube/Textures/container2.png", "./objects/cube/Textures/container2_specular.png"),
        'boxGround': LoadObject("./objects/cube/cube.obj", "./objects/cube/Textures/green_grass.jpg","./objects/cube/Textures/green_grass_specular.jpg"),
        'temple': LoadObject("./objects/temple/Japanese_Temple.obj", './objects/temple/Textures/Japanese_Temple_Paint2.png', './objects/temple/Textures/Japanese_Temple_Paint2_specular.png'),
        'gate': LoadObject("./objects/gate/Japanese_Torii_Gate.obj", "./objects/gate/Textures/Material.001_Base_color.png","./objects/gate/Textures/internal_ground_ao_texture.jpeg"),
        'buddha': LoadObject("./objects/buddha/SM_Buddha.obj", "./objects/buddha/Textures/Buddha_low_DefaultMaterial_BaseColor.png","./objects/buddha/Textures/Buddha_low_DefaultMaterial_Roughness.png"),
        'sconce': LoadObject("./objects/Wall_Sconce/Wall_Sconce.obj", "./objects/Wall_Sconce/Textures/Wall_Sconce_BaseColor_4k.png","./objects/Wall_Sconce/Textures/Wall_Sconce_Roughness_4k.png"),
        'sconce2': LoadObject("./objects/Wall_Sconce/Wall_Sconce.obj", "./objects/Wall_Sconce/Textures/Wall_Sconce_BaseColor_4k.png","./objects/Wall_Sconce/Textures/Wall_Sconce_Roughness_4k.png"),
        'sconce3': LoadObject("./objects/Wall_Sconce/Wall_Sconce.obj", "./objects/Wall_Sconce/Textures/Wall_Sconce_BaseColor_4k.png","./objects/Wall_Sconce/Textures/Wall_Sconce_Roughness_4k.png"),
        'sconce4': LoadObject("./objects/Wall_Sconce/Wall_Sconce.obj", "./objects/Wall_Sconce/Textures/Wall_Sconce_BaseColor_4k.png","./objects/Wall_Sconce/Textures/Wall_Sconce_Roughness_4k.png"),
        'table': LoadObject("./objects/table/simple-table.obj", "./objects/table/Textures/lambert1_Base_Color.png","./objects/table/Textures/lambert1_Roughness.png"),
        'pillow': LoadObject("./objects/pillow/Pillow1.obj", "./objects/pillow/Textures/FabricDenim001_COL_VAR1_1K.jpg","./objects/pillow/Textures/GraphicDesignWallpaperEclectic26_VAR2_1K.png"),
        'lantern': LoadObject("./objects/lantern/lantern.obj", "./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_BaseColor.png","./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_OcclusionRoughnessMetallic.png"),
        'lantern2': LoadObject("./objects/lantern/lantern.obj", "./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_BaseColor.png","./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_OcclusionRoughnessMetallic.png"),
        'lantern3': LoadObject("./objects/lantern/lantern.obj", "./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_BaseColor.png","./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_OcclusionRoughnessMetallic.png"),
        'lantern4': LoadObject("./objects/lantern/lantern.obj", "./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_BaseColor.png","./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_OcclusionRoughnessMetallic.png"),
        'lantern5': LoadObject("./objects/lantern/lantern.obj", "./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_BaseColor.png","./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_OcclusionRoughnessMetallic.png"),
        'lantern6': LoadObject("./objects/lantern/lantern.obj", "./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_BaseColor.png","./objects/lantern/Textures/Stone_Lantern_Stone_Lantern_OcclusionRoughnessMetallic.png"),
        }


    objects['table'].move(y=3.2,z=-31)
    objects['table'].scale(.02,.02,.02)
    objects['pillow'].move(y=3.8,z=-33)

    objects['lantern'].scale(5, 5, 5)
    objects['lantern'].move(x=-3.8, z=-5.0)
    objects['lantern2'].scale(5, 5, 5)
    objects['lantern2'].move(x=3.8, z=-5.0)
    objects['lantern3'].scale(5, 5, 5)
    objects['lantern3'].move(x=-3.8, z=14)
    objects['lantern4'].scale(5, 5, 5)
    objects['lantern4'].move(x=3.8, z=14)
    objects['lantern5'].scale(5, 5, 5)
    objects['lantern5'].move(x=-3.8, z=30)
    objects['lantern6'].scale(5, 5, 5)
    objects['lantern6'].move(x=3.8, z=30)

    objects['sconce'].scale(2,2,2)
    objects['sconce'].move(x=-4.49172, y=8,z=-24.85)
    objects['sconce'].rotate(90, axis='y')

    objects['sconce2'].scale(2,2,2)
    objects['sconce2'].move(x=4.49172, y=8,z=-24.85)
    objects['sconce2'].rotate(90, axis='y')

    objects['sconce3'].scale(2,2,2)
    objects['sconce3'].move(x=-5, y=18.3,z=-24.3)
    objects['sconce3'].rotate(-90, axis='y')

    objects['sconce4'].scale(2,2,2)
    objects['sconce4'].move(x=5, y=18.3,z=-24.3)
    objects['sconce4'].rotate(-90, axis='y')

    objects['boxFloor'].scale(20,.5,20)
    objects['boxFloor'].move(y=3.3,x=0.1,z=-30)
    objects['boxGround'].scale(149, 0.01, 149)
    objects['boxSky'].scale(150, 150, 150)

    objects['gate'].scale(15, 15, 15)
    objects['gate'].move(z=20)
    objects['temple'].scale(1.5, 1.5, 1.5)
    objects['temple'].move(z=-30)
    objects['buddha'].scale(20, 20, 20)
    objects['buddha'].rotate(180, axis='y')
    objects['buddha'].move(z=60)


    # render loop
    # -----------
    while (not glfwWindowShouldClose(window)):

        # per-frame time logic
        # --------------------
        currentFrame = glfwGetTime()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        buddha_center = 65
        rotation_angle += deltaTime * 0.5  
        x = light_radius * math.sin(rotation_angle)
        z = buddha_center + light_radius * math.cos(rotation_angle)

        pointLightPositions[0] = glm.vec3(x, light_height, z)
        #print(pointLightPositions[0])

        # input
        # -----
        processInput(window)
        glfwSetKeyCallback(window, key_callback)

        # render
        # ------
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # be sure to activate shader when setting uniforms/drawing objects
        lightingShader.use()
        lightingShader.setVec3("viewPos", camera.Position)
        lightingShader.setFloat("material.shininess", 32.0)

        
        #   Here we set all the uniforms for the 5/6 types of lights we have. We have to set them manually and index 
        #   the proper PointLight struct in the array to set each uniform variable. This can be done more code-friendly
        #   by defining light types as classes and set their values in there, or by using a more efficient uniform approach
        #   by using 'Uniform buffer objects', but that is something we'll discuss in the 'Advanced GLSL' tutorial.
           
        # # directional light
        # lightingShader.setVec3("dirLight.direction", -0.2, -1.0, -0.3)
        # lightingShader.setVec3("dirLight.ambient", 0.05, 0.05, 0.05)
        # lightingShader.setVec3("dirLight.diffuse", 0.4, 0.4, 0.4)
        # lightingShader.setVec3("dirLight.specular", 0.5, 0.5, 0.5)

        
        ambient_color = glm.vec3(0.0) 
        if enable_ambient:
            ambient_color = glm.vec3(0.05) 
        
        diffuse_color = glm.vec3(0.0)
        if enable_diffuse:
            diffuse_color = glm.vec3(0.7)
        
        specular_color = glm.vec3(0) 
        if enable_specular:
            specular_color = glm.vec3(1.0)

        # point light 1
        for i in range(len(pointLightPositions)):
            lightingShader.setVec3(f"pointLights[{i}].position", pointLightPositions[i])
            lightingShader.setVec3(f"pointLights[{i}].ambient", ambient_color)
            lightingShader.setVec3(f"pointLights[{i}].diffuse", diffuse_color)
            lightingShader.setVec3(f"pointLights[{i}].specular", specular_color)
            lightingShader.setFloat(f"pointLights[{i}].constant", 1.0)
            lightingShader.setFloat(f"pointLights[{i}].linear", 0.09)
            lightingShader.setFloat(f"pointLights[{i}].quadratic", 0.032)
        
        # spotLight
        # lightingShader.setVec3("spotLight.position", camera.Position)
        # lightingShader.setVec3("spotLight.direction", camera.Front)
        lightingShader.setVec3("spotLight.ambient", 0.0, 0.0, 0.0)
        lightingShader.setVec3("spotLight.diffuse", 1.0, 1.0, 1.0)
        lightingShader.setVec3("spotLight.specular", 1.0, 1.0, 1.0)
        lightingShader.setFloat("spotLight.constant", 1.0)
        lightingShader.setFloat("spotLight.linear", 0.09)
        lightingShader.setFloat("spotLight.quadratic", 0.032)
        lightingShader.setFloat("spotLight.cutOff", glm.cos(glm.radians(12.5)))
        lightingShader.setFloat("spotLight.outerCutOff", glm.cos(glm.radians(15.0)))     

        # view/projection transformations
        projection = glm.perspective(glm.radians(camera.Zoom), SCR_WIDTH / SCR_HEIGHT, 0.1, 100.0)
        view = camera.GetViewMatrix()
        lightingShader.setMat4("projection", projection)
        lightingShader.setMat4("view", view)

        # world transformation
        model = glm.mat4(1.0)
        lightingShader.setMat4("model", model)

        for obj in objects.values():
            model = obj.model
            lightingShader.setMat4("model", model)
            obj.draw(lightingShader, model)

        # also draw the lamp object(s)
        lightCubeShader.use()
        lightCubeShader.setMat4("projection", projection)
        lightCubeShader.setMat4("view", view)

        # we now draw as many light bulbs as we have point lights.
        glBindVertexArray(lightCubeVAO)
        for i in range(len(pointLightPositions)):
            model = glm.mat4(1.0)
            model = glm.translate(model, pointLightPositions[i])
            model = glm.scale(model, glm.vec3(0.2)) # Make it a smaller cube
            lightCubeShader.setMat4("model", model)
            glDrawArrays(GL_TRIANGLES, 0, 36)

        # glfw: swap buffers and poll IO events (keys pressed/released, mouse moved etc.)
        # -------------------------------------------------------------------------------
        glfwSwapBuffers(window)
        glfwPollEvents()

    # optional: de-allocate all resources once they've outlived their purpose:
    # ------------------------------------------------------------------------
    glDeleteVertexArrays(1, (cubeVAO,))
    glDeleteVertexArrays(1, (lightCubeVAO,))
    glDeleteBuffers(1, (VBO,))

    # glfw: terminate, clearing all previously allocated GLFW resources.
    # ------------------------------------------------------------------
    glfwTerminate()
    return 0

# process all input: query GLFW whether relevant keys are pressed/released this frame and react accordingly
# ---------------------------------------------------------------------------------------------------------
def processInput(window: GLFWwindow) -> None:

    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS):
        glfwSetWindowShouldClose(window, True)

    if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS):
        camera.ProcessKeyboard(Camera_Movement.FORWARD, deltaTime)
    if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS):
        camera.ProcessKeyboard(Camera_Movement.BACKWARD, deltaTime)
    if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS):
        camera.ProcessKeyboard(Camera_Movement.LEFT, deltaTime)
    if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS):
        camera.ProcessKeyboard(Camera_Movement.RIGHT, deltaTime)
    if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS):
        camera.ProcessKeyboard(Camera_Movement.UP, deltaTime)
    if (glfwGetKey(window, GLFW_KEY_LEFT_CONTROL) == GLFW_PRESS):
        camera.ProcessKeyboard(Camera_Movement.DOWN, deltaTime)

# glfw: whenever the window size changed (by OS or user resize) this callback function executes
# ---------------------------------------------------------------------------------------------
def framebuffer_size_callback(window: GLFWwindow, width: int, height: int) -> None:

    # make sure the viewport matches the new window dimensions note that width and 
    # height will be significantly larger than specified on retina displays.
    glViewport(0, 0, width, height)

# glfw: whenever the mouse moves, this callback is called
# -------------------------------------------------------
def mouse_callback(window: GLFWwindow, xpos: float, ypos: float) -> None:
    global lastX, lastY, firstMouse

    if (firstMouse):

        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos # reversed since y-coordinates go from bottom to top

    lastX = xpos
    lastY = ypos

    camera.ProcessMouseMovement(xoffset, yoffset)

# glfw: whenever the mouse scroll wheel scrolls, this callback is called
# ----------------------------------------------------------------------
def scroll_callback(window: GLFWwindow, xoffset: float, yoffset: float) -> None:

    camera.ProcessMouseScroll(yoffset)

# utility function for loading a 2D texture from file
# ---------------------------------------------------
def loadTexture(path: str) -> int:

    textureID = glGenTextures(1)
    
    try:
        img = LOAD_IMAGE(path)

        nrComponents = len(img.getbands())

        format = GL_RED if nrComponents == 1 else \
                 GL_RGB if nrComponents == 3 else \
                 GL_RGBA 

        glBindTexture(GL_TEXTURE_2D, textureID)
        glTexImage2D(GL_TEXTURE_2D, 0, format, img.width, img.height, 0, format, GL_UNSIGNED_BYTE, img.tobytes())
        glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        img.close()

    except:

        print("Texture failed to load at path: " + path)

    return textureID

def key_callback(window, key, scancode, action, mods):
    global enable_ambient, enable_diffuse, enable_specular

    if action == GLFW_PRESS:
        if key == GLFW_KEY_1:
            enable_ambient = not enable_ambient
        elif key == GLFW_KEY_2:
            enable_diffuse = not enable_diffuse
        elif key == GLFW_KEY_3:
            enable_specular = not enable_specular


main()
