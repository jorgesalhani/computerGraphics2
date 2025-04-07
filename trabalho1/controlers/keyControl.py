import glfw
from OpenGL.GL import *
from .objectsControl import ObjectControl
import numpy as np


class KeyControl:
  """
  Classe dedicada a mapear cada tecla a sua ação
  """
  def __init__(self):
    self.key_pressed = ''
    self.key_action = None
    self.display_mash = False

  def set_key_pressed(self, key, action):
    """
    Definir tecla pressionada e qual a ação [PRESS, RELEASE]
    """
    self.key_pressed = key
    self.key_action = action

  def switch_mash(self):
    """
    Trocar exibição para malha de polígonos
    """
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
      # P: Exibir malha poligonal
      self.switch_mash()
    
    if self.key_pressed == glfw.KEY_ESCAPE:
      # ESC: Fechar janela
      self.close_window(window=window)

    if self.key_pressed == glfw.KEY_S:
      # S: ciclo lunar
      objectsControl.update_position(objName='moon', offset = [0,-0.01,0])

    if self.key_pressed == glfw.KEY_RIGHT:
      # KEY_RIGHT: mover cenário para direita
      objectsControl.update_position(objName='lighthouse_top', offset = [-0.001,0,0], angle= [0,0.001,0])
      objectsControl.update_position(objName='lighthouse', offset = [-0.001,0,0], angle= [0,0.001,0])
      objectsControl.update_position(objName='rocks', offset = [-0.01,0,0])
      objectsControl.update_position(objName='cloud', offset = [-0.0005,0,0])

      objectsControl.update_position('S0', offset=[-0.01,0,0])
      objectsControl.update_position('E0', offset=[-0.01,0,0])
      objectsControl.update_position('M0', offset=[-0.01,0,0])
      objectsControl.update_position('I0', offset=[-0.01,0,0])
      objectsControl.update_position('N0', offset=[-0.01,0,0])
      objectsControl.update_position('T0', offset=[-0.01,0,0])
      objectsControl.update_position('E1', offset=[-0.01,0,0])
      objectsControl.update_position('R0', offset=[-0.01,0,0])
      objectsControl.update_position('N1', offset=[-0.01,0,0])
      objectsControl.update_position('E2', offset=[-0.01,0,0])
      objectsControl.update_position('T1', offset=[-0.01,0,0])
    
    if self.key_pressed == glfw.KEY_L:
      # L: rotacionar feixes de luz
      objectsControl.update_position(objName='lighthouse_top', angle = [0,0.01,0])

    if self.key_pressed == glfw.KEY_G:
      # G: Escala (aumento) do dino
      objectsControl.update_position(objName='dino', scale = [0.01,0.01,0])
    
    if self.key_pressed == glfw.KEY_H:
      # H: Escala (redução) do dino
      objectsControl.update_position(objName='dino', scale = [-0.01,-0.01,0])

  
    

      






