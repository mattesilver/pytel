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
    context = Pytel(svc)
    assert context.a.b == context.b

See `usage <https://github.com/mattesilver/pytel/blob/master/tests/pytel/test_usage.py>`_ for more cases

Features
========

- Build a graph of objects based on init methods or factory functions
- Initialize from
    - a dictionary of string to any of:
        - callable
        - type
        - value
    - Object containing any of:
        - object fields with objects or types (or callables)
        - class fields with objects or types (or callables)
        - methods
        - static methods
    - An Iterable of the above
- Verify integrity of the dependency graph using type annotations
- Recurrently resolve all dependencies at the first reference
- Works as a Context Manager, on __exit__ close all objects that are Context Managers

Because of strict type checking this package is probably quite unpythonic.
