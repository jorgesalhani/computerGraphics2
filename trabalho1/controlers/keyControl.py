import glfw
from OpenGL.GL import *

class KeyControl:
  def __init__(self):
    self.key_pressed = ''
    self.key_action = None
    self.display_mash = False

  def set_key_pressed(self, key, action):
    self.key_pressed = key
    self.key_action = action

  def switch_mash(self):
    if self.display_mash:
      glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    else:
      glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

    if self.key_action == glfw.PRESS:
      if self.display_mash:
        self.display_mash = False
      else:
        self.display_mash = True


  def close_window(self, window):
    glfw.set_window_should_close(window, True)

  def action(self, window, key, action, objectsControl):
    self.set_key_pressed(key, action)
    
    if self.key_pressed == glfw.KEY_P:
      self.switch_mash()
    
    if self.key_pressed == glfw.KEY_ESCAPE:
      self.close_window(window=window)

    if self.key_pressed == glfw.KEY_A:
      objectsControl.update_position(objName='piramide', offset = (-0.01,0,0))

    if self.key_pressed == glfw.KEY_D:
      objectsControl.update_position(objName='piramide', offset = (0.01,0,0))

    if self.key_pressed == glfw.KEY_SPACE:
      objectsControl.update_position(objName='piramide', offset = (0,0.01,0))

    if self.key_pressed == glfw.KEY_L:
      objectsControl.update_position(objName='background', angle = (0.01,0,0))

    if self.key_pressed == glfw.KEY_K:
      objectsControl.update_position(objName='background', angle = (0,0.01,0))

    if self.key_pressed == glfw.KEY_M:
      objectsControl.update_position(objName='background', scale = (0,0.01,0))

    if self.key_pressed == glfw.KEY_N:
      objectsControl.update_position(objName='background', scale = (0,-0.01,0))
    

      






