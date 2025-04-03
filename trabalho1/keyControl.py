import glfw
from OpenGL.GL import *

class KeyControl:
  def __init__(self):
    self.key_pressed = ''
    self.key_action = None
    self.key_count = {}
    self.display_mash = False

  def set_key_pressed(self, key, action):
    self.key_pressed = key
    self.key_action = action
    self.key_count[key] = self.key_count.setdefault(key,-1) + 1

  def switch_mash(self):
    if self.key_count[self.key_pressed] == 0:
      if self.display_mash:
        self.display_mash = False
      else:
        self.display_mash = True

    if self.display_mash:
      glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    else:
      glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    
    if self.key_action == glfw.RELEASE: 
      self.key_count[self.key_pressed] = 1
    if self.key_action == glfw.PRESS: 
      self.key_count[self.key_pressed] = 0


  def close_window(self, window):
    glfw.set_window_should_close(window, True)

  def action(self, window):
    if self.key_pressed == glfw.KEY_P:
      self.switch_mash()
    if self.key_pressed == 'esc':
      self.close_window(window=window)






