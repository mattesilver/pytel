A bag of objects for Python
===========================

.. image:: https://img.shields.io/pypi/v/pytel-inject.svg?style=flat
    :target: https://pypi.org/project/pytel-inject/

.. image:: https://travis-ci.com/mattesilver/pytel.svg
  :target: https://travis-ci.com/mattesilver/pytel

.. image:: https://codecov.io/gh/mattesilver/pytel/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/mattesilver/pytel

For when your object graph is too big

.. code-block:: python

  class A:
    def __init__(self, context: Pytel):
        self.b = context.b

  class B:
      pass

  context = Pytel()
  context.a = lazy(A)(context)
  context.b = lazy(B)

  assert context.a.b == context.b

Works with dependency cycles (through a proxy object):

.. code-block:: python

  class A:
    def __init__(self, context: Pytel):
      self.b = context.b

  class B:
    def __init__(self, context: Pytel):
      self.a = context.a

  context = Pytel()
  context.a = lazy(A)(context)
  context.b = lazy(B)(context)
  
  assert context.a.b == context.b
  assert context.b.a == context.a
  
