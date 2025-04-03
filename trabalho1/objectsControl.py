import os
import json

class ObjectControl:
  def __init__(self, folder_path):
    if not os.path.isdir(folder_path):
      raise FileNotFoundError(f'Dir not found: {folder_path}')
    self.folder_path = folder_path
    self.vertices_list = {
      'vertices': [],
      'first_last_vertices': [],
    }
    self.faces_color = []

  def load_object(self, filename):
    fullpath = f'{self.folder_path}/{filename}'
    if not os.path.isfile(fullpath):
      raise FileNotFoundError(f'Object file not found: {filename}')
    
    first_vert = len(self.vertices_list['vertices'])
    
    vi = len(self.vertices_list['vertices'])
    
    objVertices = open(fullpath, 'r')
    faces = json.load(objVertices)['faces']

    for face in faces:
      total_vertices = len(face['vertices'])
      map_color_position = {
        'rgb': face['color'],
        'first': first_vert,
        'total': total_vertices
      }
      self.faces_color.append(map_color_position)
      
      for vert in face['vertices']:
        self.vertices_list['vertices'].append(vert)

      self.vertices_list['first_last_vertices'].append({
          'name': os.path.splitext(filename)[0],
          'first': vi,
          'last': vi + total_vertices
        })

    return self.vertices_list
  




