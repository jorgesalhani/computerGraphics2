import os
import json
from .transformControl import TransformControl
import numpy as np
import glfw
from OpenGL.GL import *
from .trajectories import Trajectories

class ObjectControl(TransformControl) :
  """
  Classe de controle de objetos
  - carregamento
  - aplicação de transformação
  """
  def __init__(self, folder_path):
    """
    Inicialização da classe

    @param
      folder_path: caminho da pasta com os arquivos dos objetos
    """
    if not os.path.isdir(folder_path):
      raise FileNotFoundError(f'Dir not found: {folder_path}')
    self.folder_path = folder_path
    self.vertices_list = {
      'vertices': [],
      'first_last_vertices': [],
    }
    self.faces_color = []
    self.object_list = []
    self.current_object_faces = {}


  def load_object(self, filename, global_offset = [0,0,0]):
    """
    Carregar objetos

    @param
      filename: nome do arquivo
      global_offset: posições iniciais do objeto carregados na cena
    """
    fullpath = f'{self.folder_path}/{filename}'
    if not os.path.isfile(fullpath):
      raise FileNotFoundError(f'Object file not found: {filename}')
    
    vi = len(self.vertices_list['vertices'])
    
    objVertices = open(fullpath, 'r')
    faces = json.load(objVertices)['faces']

    objName = os.path.splitext(filename)[0]
    vf = vi

    # Nesse loop, atualizamos a listagem de faces
    # para cada objeto, anotando qual o vertice inicial e o total de vertices
    # assim como suas cores
    """
    self.faces_color =  [{
      'name': objName,
      'rgb': face['color'],
      'first': vi,
      'total': total_vertices
    }]
    """

    # Atualizamos também a listagem de vertices 
    # de cada face a ser carregada nos shaders

    """
    self.vertices_list = [{
      'vertices': [
        [0.6, -0.3, 0.2],
        ...
      ],
      'first_last_vertices': {
        'name': objName,
        'first': vi,
        'last': vi + total_vertices
      }
    }]
    """
    for face in faces:
      total_vertices = len(face['vertices'])
      map_color_position = {
        'name': objName,
        'rgb': face['color'],
        'first': vi,
        'total': total_vertices
      }
      self.faces_color.append(map_color_position)
      
      for vert in face['vertices']:
        self.vertices_list['vertices'].append(vert)

      self.vertices_list['first_last_vertices'].append({
          'name': objName,
          'first': vi,
          'last': vi + total_vertices
        })
      
      vf = vi + total_vertices
      vi += total_vertices

    # Também construimos uma listagem de objetos 
    # com suas principais caracteristicas e posicoes
    # globais
    """
    self.object_list = [{
      'name': objName,
      'vertices': {
        'first': vi,
        'last': vf
      },
      'global_offset': global_offset,
      'global_angle': [0,0,0],
      'global_scale': [1,1,1],
      'global_dt': 0
    }]
    """
    
    self.object_list.append({
      'name': objName,
      'vertices': {
        'first': vi,
        'last': vf
      },
      'global_offset': global_offset,
      'global_angle': [0,0,0],
      'global_scale': [1,1,1],
      'global_dt': 0
    })
    self.dt = 0.01
    return self.vertices_list
  
  def get_trajectory(self, offset):
    """
    Função auxiliar para calculo de trajetórias

    @param
      offset: deslocamento incrementado
    """
    g_offset = self.current_object['global_offset']

    if self.current_object['name'] == 'moon':
      res = Trajectories.circle(g_offset, self.current_object['global_dt'])
      self.current_object['global_dt'] += self.dt
      return res
    
    return Trajectories.linear(g_offset, offset)
  
  def update_position(self, objName, angle = None, offset = None, scale = None):
    """
    Atualização da posição global de um dado objeto por seu nome

    @param
      objName: Nome do objeto a ser atualizado
      angle: angulo a ser rotacionado
      offset: deslocamento para translado
      scale: fato de escala
    """
    curObj = list(filter(lambda x : x['name'] == objName, self.object_list))
    if not curObj:
      raise NameError(f'Object named {objName} not loaded')
    self.current_object = curObj[0]
    
    if offset:
      self.current_object['global_offset'] = self.get_trajectory(offset)

    if angle:
      g_angle = self.current_object['global_angle']
      self.current_object['global_angle'] = [angle[0] + g_angle[0], angle[1] + g_angle[1], angle[2] + g_angle[2]]
    
    if scale:
      g_scale = self.current_object['global_scale']
      self.current_object['global_scale'] = [scale[0] + g_scale[0], scale[1] + g_scale[1], scale[2] + g_scale[2]]
    
  def draw(self, program):
    """
    Exibir em tela o objeto corrente com seus vértices
    e cor de face
    """
    loc_color = glGetUniformLocation(program, "color")
    for face_color in self.current_object_faces:
      r,g,b,a = face_color['rgb']
      vi, vt = face_color['first'], face_color['total']
      glUniform4f(loc_color, r, g, b, a)
      glDrawArrays(GL_TRIANGLE_STRIP, vi, vt)
  
  def apply_transform(self, program, objName):
    """
    Aplicação de matriz de tranformação para deslocamento do 
    objeto no cenário

    @param
      objName: nome do objeto a ser transformado
    """
    cur_Obj = list(filter(lambda x : x['name'] == objName, self.object_list))
    if not cur_Obj:
      raise NameError(f'Object named {objName} not loaded')
    self.current_object = cur_Obj[0]
    
    offset = self.current_object['global_offset']
    angle = self.current_object['global_angle']
    scale = self.current_object['global_scale']

    mat_rotation_x = TransformControl.rotation_x(angle[0])
    mat_rotation_y = TransformControl.rotation_y(angle[1])
    mat_rotation_z = TransformControl.rotation_z(angle[2])

    mat_scale = TransformControl.scale(scale)

    mat_translacao = TransformControl.translation(offset)

    mat_transform = TransformControl.multiplica_matriz(mat_rotation_z,mat_rotation_y)
    mat_transform = TransformControl.multiplica_matriz(mat_rotation_x,mat_transform)
    mat_transform = TransformControl.multiplica_matriz(mat_scale,mat_transform)
    
    mat_transform = TransformControl.multiplica_matriz(mat_translacao,mat_transform)
    
    loc_transformation = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_transformation, 1, GL_TRUE, mat_transform) 
    
    self.current_object_faces = list(filter(lambda x : x['name'] == objName, self.faces_color))
    if not self.current_object_faces:
      raise NameError(f'Object named {objName} without faces')
    
    self.draw(program)