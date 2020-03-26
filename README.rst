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
        def __init__(self, b: B):
            self.b = b

    class B:
        pass

    svc = {
        'a': A,
        'b': B,
    }
    context = Pytel(PytelContext(svc))
    assert context.a.b == context.b

See .. _usage: https://github.com/mattesilver/pytel/blob/master/tests/pytel/test_usage.py for more cases
