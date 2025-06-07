from OpenGL.GL import *
from glfw.GLFW import *

from glfw import _GLFWwindow as GLFWwindow
from PIL import Image

import glm

from shader_m import Shader
from camera import Camera, Camera_Movement

import platform, ctypes, os

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

import math

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
SCR_WIDTH = 1100
SCR_HEIGHT = 900

# camera
camera = Camera(glm.vec3(0.0, 0.0, 3.0))
lastX = SCR_WIDTH / 2.0
lastY = SCR_HEIGHT / 2.0
firstMouse = True

# timing
deltaTime = 0.0
lastFrame = 0.0

# lighting
lightPos = glm.vec3(1.2, 1.0, 2.0)

def main() -> int:
    global deltaTime, lastFrame

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
    model_path = "./objects/cube/cube.obj"  # <- your .obj file
    vertices = load_obj_model(model_path)

    # positions of the point lights
    pointLightPositions = [
        glm.vec3( 0.7,  0.2,  2.0),
        glm.vec3( 2.3, -3.3, -4.0),
        glm.vec3(-4.0,  2.0, -12.0),
        glm.vec3( 0.0,  0.0, -3.0)
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

    # shader configuration
    # --------------------
    lightingShader.use()
    lightingShader.setInt("material.diffuse", 0)
    lightingShader.setInt("material.specular", 1)

    objects = {
        'boxGround': LoadObject("./objects/cube/cube.obj", "./objects/cube/Textures/green_grass.jpg", "./objects/cube/Textures/green_grass_specular.jpg"),
        'box1': LoadObject("./objects/cube/cube.obj", "./objects/cube/Textures/container2.png","./objects/cube/Textures/container2_specular.png"),
        'box2': LoadObject("./objects/cube/cube.obj", "./objects/cube/Textures/container2.png","./objects/cube/Textures/container2_specular.png"),
        'house': LoadObject("./objects/house/Cottage_FREE.obj", './objects/house/Textures/Cottage_Clean_Base_Color.png', './objects/house/Textures/Cottage_Clean_Base_Color.png'),
        'gate': LoadObject("./objects/gate/Japanese_Torii_Gate.obj", "./objects/gate/Textures/Material.001_Base_color.png","./objects/gate/Textures/internal_ground_ao_texture.jpeg"),
    }

    objects['box1'].scale(2,2,2)
    objects['box2'].scale(0.5,0.5,2)
    objects['box2'].move(2)
    objects['boxGround'].scale(149, 1, 149)
    objects['boxGround'].move(y=-2)
    objects['gate'].scale(15, 15, 15)
    objects['gate'].move(z=20)


    # render loop
    # -----------
    while (not glfwWindowShouldClose(window)):

        # per-frame time logic
        # --------------------
        currentFrame = glfwGetTime()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        # input
        # -----
        processInput(window)

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
           
        # directional light
        lightingShader.setVec3("dirLight.direction", -0.2, -1.0, -0.3)
        lightingShader.setVec3("dirLight.ambient", 0.05, 0.05, 0.05)
        lightingShader.setVec3("dirLight.diffuse", 0.4, 0.4, 0.4)
        lightingShader.setVec3("dirLight.specular", 0.5, 0.5, 0.5)
        # point light 1
        lightingShader.setVec3("pointLights[0].position", pointLightPositions[0])
        lightingShader.setVec3("pointLights[0].ambient", 0.05, 0.05, 0.05)
        lightingShader.setVec3("pointLights[0].diffuse", 0.8, 0.8, 0.8)
        lightingShader.setVec3("pointLights[0].specular", 1.0, 1.0, 1.0)
        lightingShader.setFloat("pointLights[0].constant", 1.0)
        lightingShader.setFloat("pointLights[0].linear", 0.09)
        lightingShader.setFloat("pointLights[0].quadratic", 0.032)
        # point light 2
        lightingShader.setVec3("pointLights[1].position", pointLightPositions[1])
        lightingShader.setVec3("pointLights[1].ambient", 0.05, 0.05, 0.05)
        lightingShader.setVec3("pointLights[1].diffuse", 0.8, 0.8, 0.8)
        lightingShader.setVec3("pointLights[1].specular", 1.0, 1.0, 1.0)
        lightingShader.setFloat("pointLights[1].constant", 1.0)
        lightingShader.setFloat("pointLights[1].linear", 0.09)
        lightingShader.setFloat("pointLights[1].quadratic", 0.032)
        # point light 3
        lightingShader.setVec3("pointLights[2].position", pointLightPositions[2])
        lightingShader.setVec3("pointLights[2].ambient", 0.05, 0.05, 0.05)
        lightingShader.setVec3("pointLights[2].diffuse", 0.8, 0.8, 0.8)
        lightingShader.setVec3("pointLights[2].specular", 1.0, 1.0, 1.0)
        lightingShader.setFloat("pointLights[2].constant", 1.0)
        lightingShader.setFloat("pointLights[2].linear", 0.09)
        lightingShader.setFloat("pointLights[2].quadratic", 0.032)
        # point light 4
        lightingShader.setVec3("pointLights[3].position", pointLightPositions[3])
        lightingShader.setVec3("pointLights[3].ambient", 0.05, 0.05, 0.05)
        lightingShader.setVec3("pointLights[3].diffuse", 0.8, 0.8, 0.8)
        lightingShader.setVec3("pointLights[3].specular", 1.0, 1.0, 1.0)
        lightingShader.setFloat("pointLights[3].constant", 1.0)
        lightingShader.setFloat("pointLights[3].linear", 0.09)
        lightingShader.setFloat("pointLights[3].quadratic", 0.032)
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
        for i in range(4):

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

main()
