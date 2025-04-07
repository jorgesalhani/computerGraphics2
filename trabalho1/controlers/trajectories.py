import numpy as np

class Trajectories:
  """
  Classe auxiliar para desenho das trajetórios
  """
  @staticmethod
  def linear(g_pos, offset):
    """
    Calculo de trajetória linear
    """
    xp = offset[0] + g_pos[0]
    yp = offset[1] + g_pos[1]
    zp = offset[2] + g_pos[2]

    return xp, yp, zp

  @staticmethod
  def circle(g_pos, dt):
    """
    Calculo de trajetória circular
    """
    xp = np.cos(dt)
    yp = np.sin(dt)

    return xp, yp, g_pos[2]