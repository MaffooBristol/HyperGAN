#From https://gist.github.com/EndingCredits/b5f35e84df10d46cfa716178d9c862a3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import state_ops
from tensorflow.python.framework import ops
from tensorflow.python.training import optimizer
import tensorflow as tf
import inspect

class GANOptimizer(optimizer.Optimizer):
  """
    Splits optimization targets between g_optimizer and g_optimizer
  """

  def __init__(self, _, gan=None, config=None, g_optimizer=None, d_optimizer=None, name="GANOptimizer"):
    super().__init__(config.learn_rate, name=name)
    self.gan = gan
    self.config = config
    def create_optimizer(klass, _learn_rate):
        config['gan']=self.gan
        config['config']=config
        defn = {k: v for k, v in config.items() if k in inspect.getargspec(klass).args}
        return klass(_learn_rate, **defn)


    self.d_optimizer = create_optimizer(d_optimizer, config.d_learn_rate or config.learn_rate)
    self.g_optimizer = create_optimizer(g_optimizer, config.g_learn_rate or config.learn_rate)

  def _prepare(self):
    super()._prepare()
    self.d_optimizer._prepare()
    self.g_optimizer._prepare()

  def variables(self):
    return self.d_optimizer.variables() + self.g_optimizer.variables()

  def _create_slots(self, var_list):
    super()._create_slots(var_list)
    d_vars = [v for v in var_list if v in self.gan.d_vars()]
    g_vars = [v for v in var_list if v in self.gan.g_vars()]
    print("GV", g_vars)
    print("--", var_list)
    self.d_optimizer._create_slots(d_vars)
    self.g_optimizer._create_slots(g_vars)
    missing_vars = [v for v in var_list if v not in self.gan.g_vars() + self.gan.d_vars()]
    if len(missing_vars) > 0:
        print("Error, GANOptimizer does not know how to handle missing variables (not in d_vars or g_vars)", missing_vars)
        raise("Error, GANOptimizer does not know how to handle missing variables (not in d_vars or g_vars)")

  def _apply_dense(self, grad, var):
    if var in self.gan.d_vars():
        return self.d_optimizer._apply_dense(grad, var)
    elif var in self.gan.g_vars():
        return self.g_optimizer._apply_dense(grad, var)
    raise("Unable to handle", var)

  def _apply_sparse(self, grad, var):
    raise NotImplementedError("Sparse gradient updates are not supported.")
