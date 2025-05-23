import numpy as np
import json

class ObjectsBuildControl:
  """
  Construção de objetos via script
  """
  def __init__(self, objFilesPath):
    self.objFilesPath = objFilesPath
    self.PI = 3.141592
    self.num_sectors = 32 # qtd de sectors (longitude)
    self.num_stacks = 32 # qtd de stacks (latitude)
    self.sector_step=(self.PI*2) / self.num_sectors # variar de 0 até 2π
    self.stack_step=(self.PI) / self.num_stacks # variar de 0 até π

  def normalize_sketch(self, sketchFolderPath, objName, scale, fname = None):
    """
    Normalizar desenhos construídos vertice a vertice, 
    considerando (0,0,0) como canto inferior esquerdo
    dos vértices desenhados, sem normalização

    @params:
      sketchFolderPath: caminho origem dos desenhos
      objName: nome do objeto buscado na pasta de desenhos
      scale: fator de escala aplicado a todos os vertices do desenho
      fname: nome do objeto destino, criado de modo normalizado
    """
    fskecth = open(f'{sketchFolderPath}/{objName}.json', 'r')

    verts = json.load(fskecth)
    xs, ys, zs = zip(*verts)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    def normalize(v, min_val, max_val):
        return (v - min_val) / ((max_val - min_val)*scale) if max_val != min_val else 0.0

    normalized_verts = [
        (
            normalize(x, min_x, max_x),
            normalize(y, min_y, max_y),
            normalize(z, min_z, max_z)
        )
        for x, y, z in verts
    ]
    if not fname:
      fjson = open(f'{self.objFilesPath}/{objName}.json', 'w')
    else:
      fjson = open(f'{self.objFilesPath}/{fname}.json', 'w')

    moonObj = {
      "faces": [{
        "vertices": normalized_verts,
        "color": [0,0,0,1]
      }]
    }
    fjson.writelines(json.dumps(moonObj))
    return normalized_verts


  def build_sphere(self, vertices, x0, y0, r, sphere_func = None):
    """
    Construir esfera

    @param
      vertices: listagem de vertices que será atualizada
      x0: origem x da esfera
      y0: origem y da esfera
      r: raio da esfera
      sphere_func: funcao de recorte da esfera
    """
    if not sphere_func:
      sphere_func = self.default_sphere

    # vamos gerar um conjunto de vertices representantes poligonos
    # para a superficie da esfera.
    # cada poligono eh representado por dois triangulos
    for i in range(0,self.num_sectors): # para cada sector (longitude)
      for j in range(0,self.num_stacks): # para cada stack (latitude)
        u = i * self.sector_step # angulo setor
        v = j * self.stack_step # angulo stack
        
        un = 0 # angulo do proximo sector
        if i+1==self.num_sectors:
            un = self.PI*2
        else: un = (i+1)*self.sector_step
            
        vn = 0 # angulo do proximo stack
        if j+1==self.num_stacks:
            vn = self.PI
        else: vn = (j+1)*self.stack_step
        
        # vertices do poligono
        p0=sphere_func(x0,y0,u, v, r)
        p1=sphere_func(x0,y0,u, vn, r)
        p2=sphere_func(x0,y0,un, v, r)
        p3=sphere_func(x0,y0,un, vn, r)
        
        # triangulo 1 (primeira parte do poligono)
        vertices.append(p0)
        vertices.append(p2)
        vertices.append(p1)
        
        # triangulo 2 (segunda e ultima parte do poligono)
        vertices.append(p3)
        vertices.append(p1)
        vertices.append(p2)

  def default_sphere(self,x0,y0,u,v,r):
    x = x0 + r*np.sin(v)*np.cos(u)
    y = y0 + r*np.sin(v)*np.sin(u)
    z = r*np.cos(v)
    return (x,y,z)
  
  def moon_sphere(self,x0,y0,u,v,r):
    if u < self.PI/4:
      x = x0
      y = y0
      z = 0
      return (x,y,z)

    x = x0 + r*np.sin(v)*np.cos(u)
    y = y0 + r*np.sin(v)*np.sin(u)
    z = r*np.cos(v)

    return (x,y,z)
  
  def lighthouse_sphere(self,x0,y0,u,v,r):
    if self.PI/4 < v < 3*self.PI/4:
      x = x0
      y = y0
      z = 0
      return (x,y,z)

    x = x0 + r*np.sin(v)*np.cos(u)
    y = y0 + r*np.sin(v)*np.sin(u)
    z = r*np.cos(v)

    return (x,y,z)

  def build_cloud(self):
    verts = []
    r = 0.2
    y_shift0 = 0.1
    x_shift0 = 0.5
    z_shift0 = 0

    self.build_sphere(verts, x_shift0, y_shift0, r)
    self.build_sphere(verts, x_shift0 + 0.15, y_shift0+0.1, 0.1)
    self.build_sphere(verts, x_shift0 + 0.2, y_shift0-0.2, 0.15)
    fjson = open(f'{self.objFilesPath}/cloud.json', 'w')
    moonObj = {
      "faces": [{
        "vertices": verts,
        "color": [0.254,0.823,0.858,1]
      }]
    }
    fjson.writelines(json.dumps(moonObj))
    
    return y_shift0, x_shift0, z_shift0


  def build_moon(self):
    verts = []
    r = 0.2
    y_shift = 0
    x_shift = 1.2
    z_shift = 0.8

    self.build_sphere(verts, x_shift, y_shift, r, sphere_func=self.moon_sphere)
    fjson = open(f'{self.objFilesPath}/moon.json', 'w')
    moonObj = {
      "faces": [{
        "vertices": verts,
        "color": [1,0,0,1]
      }]
    }
    fjson.writelines(json.dumps(moonObj))
    return y_shift, x_shift, z_shift

  def build_lighthouse_top(self):
    verts = []
    r = 0.2
    y_shift = 0
    x_shift = 0
    z_shift = 0

    self.sector_step=(self.PI*2)/self.num_sectors # variar de 0 até 2π
    self.stack_step=(self.PI)/self.num_stacks # variar de 0 até π

    self.build_sphere(verts, x_shift, y_shift, r, sphere_func=self.lighthouse_sphere)
    fjson = open(f'{self.objFilesPath}/lighthouse_top.json', 'w')
    moonObj = {
      "faces": [{
        "vertices": verts,
        "color": [0.941,0.933,0.6117,1]
      }]
    }
    fjson.writelines(json.dumps(moonObj))
    return y_shift, x_shift, z_shift