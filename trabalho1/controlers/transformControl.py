import math
import numpy as np

class TransformControl:
  def __init__(self):
    pass

  @staticmethod
  def multiplica_matriz(a, b):
    m_a = a.reshape(4,4)
    m_b = b.reshape(4,4)
    m_c = np.dot(m_a,m_b)
    return m_c
  
  @staticmethod
  def rotation_z(theta):
    c = math.cos(theta)
    s = math.sin(theta)

    return np.array([ c, -s, 0.0, 0.0, 
                      s,  c, 0.0, 0.0, 
                      0.0, 0.0, 1.0, 0.0, 
                      0.0, 0.0, 0.0, 1.0], np.float32)
  
  @staticmethod
  def rotation_x(theta):    
    c = math.cos(theta)
    s = math.sin(theta)

    return np.array([ 1.0, 0.0, 0.0, 0.0, 
                      0.0, c, -s, 0.0, 
                      0.0, s,  c, 0.0, 
                      0.0, 0.0, 0.0, 1.0], np.float32)
  
  @staticmethod
  def rotation_y(theta):
    c = math.cos(theta)
    s = math.sin(theta)

    return np.array([ c, 0.0, s, 0.0, 
                      0.0, 1.0, 0.0, 0.0, 
                      -s, 0.0, c, 0.0, 
                      0.0, 0.0, 0.0, 1.0], np.float32)
  
  @staticmethod
  def translation(t = (0,0,0)):
    tx = t[0] 
    ty = t[1] 
    tz = t[2]

    return np.array([ 1.0, 0.0, 0.0, tx, 
                      0.0, 1.0, 0.0, ty, 
                      0.0, 0.0, 1.0, tz, 
                      0.0, 0.0, 0.0, 1.0], np.float32)
  
  @staticmethod
  def scale(s = (1,1,1)):
    sx = s[0] 
    sy = s[1] 
    sz = s[2]

    return np.array([ sx, 0.0, 0.0, 0.0, 
                      0.0, sy, 0.0, 0.0, 
                      0.0, 0.0, sz, 0.0, 
                      0.0, 0.0, 0.0, 1.0], np.float32)
  

    