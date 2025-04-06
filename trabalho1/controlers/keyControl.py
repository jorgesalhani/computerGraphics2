import glfw
from OpenGL.GL import *
from .objectsControl import ObjectControl
import numpy as np

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

  def action(self, window, key, action, objectsControl: ObjectControl):
    self.set_key_pressed(key, action)
    
    if self.key_pressed == glfw.KEY_P:
      self.switch_mash()
    
    if self.key_pressed == glfw.KEY_ESCAPE:
      self.close_window(window=window)

    if self.key_pressed == glfw.KEY_S:
      objectsControl.update_position(objName='moon', offset = [0,-0.01,0])

    if self.key_pressed == glfw.KEY_RIGHT:
      objectsControl.update_position(objName='lighthouse_top', offset = [-0.001,0,0])
      objectsControl.update_position(objName='lighthouse', offset = [-0.001,0,0])
      objectsControl.update_position(objName='rocks', offset = [-0.01,0,0])
      objectsControl.update_position(objName='cloud', offset = [-0.0005,0,0])
    
    if self.key_pressed == glfw.KEY_L:
      objectsControl.update_position(objName='lighthouse_top', angle = [0,-0.01,0])

    if self.key_pressed == glfw.KEY_G:
      objectsControl.update_position(objName='lighthouse_top', scale = [0,0.01,0])
    
    if self.key_pressed == glfw.KEY_H:
      objectsControl.update_position(objName='lighthouse_top', scale = [0,-0.01,0])

  
    

      






