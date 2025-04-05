import os
import json
from .transformControl import TransformControl
import numpy as np
import glfw
from OpenGL.GL import *

class ObjectControl(TransformControl) :
  def __init__(self, folder_path):
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

  def load_object(self, filename):
    fullpath = f'{self.folder_path}/{filename}'
    if not os.path.isfile(fullpath):
      raise FileNotFoundError(f'Object file not found: {filename}')
    
    first_vert = len(self.vertices_list['vertices'])
    
    vi = len(self.vertices_list['vertices'])
    
    objVertices = open(fullpath, 'r')
    faces = json.load(objVertices)['faces']

    objName = os.path.splitext(filename)[0]
    vf = vi

    for face in faces:
      total_vertices = len(face['vertices'])
      map_color_position = {
        'name': objName,
        'rgb': face['color'],
        'first': first_vert,
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
      
      vf += total_vertices

    self.object_list.append({
      'name': objName,
      'vertices': {
        'first': vi,
        'last': vf
      }
    })
    return self.vertices_list
  
  def draw(self, program):
    loc_color = glGetUniformLocation(program, "color")
    for face_color in self.current_object_faces:
      r,g,b,a = face_color['rgb']
      vi, vt = face_color['first'], face_color['total']
      glUniform4f(loc_color, r, g, b, a)
      glDrawArrays(GL_TRIANGLE_STRIP, vi, vt)
  
  def apply_transform(self, program, objName, angle = (0,0,0), offset = (0,0,0), scale = (3,1,1)):
    mat_rotation_x = TransformControl.rotation_x(angle[0])
    mat_rotation_y = TransformControl.rotation_y(angle[0])
    mat_rotation_z = TransformControl.rotation_z(angle[0])
    mat_translacao = TransformControl.translation(offset)

    mat_transform = TransformControl.multiplica_matriz(mat_rotation_z,mat_rotation_y)
    mat_transform = TransformControl.multiplica_matriz(mat_rotation_x,mat_transform)
    mat_transform = TransformControl.multiplica_matriz(mat_translacao,mat_transform)
    
    loc_transformation = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_transformation, 1, GL_TRUE, mat_transform) 
    
    self.current_object_faces = list(filter(lambda x : x['name'] == objName, self.faces_color))
    if not self.current_object_faces:
      raise NameError(f'Object named {objName} not loaded')
    
    self.draw(program)