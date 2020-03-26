from unittest import TestCase

from pytel import PytelContext
from pytel.context import ObjectDescriptor


class A:
    pass


class B:
    def __init__(self):
        self.initialised = True


class C:
    def __init__(self, a: A):
        self.a = a


class TestPytelContext(TestCase):
    def test_resolve(self):
        ctx = PytelContext({'a': A})
        descr = ctx._objects['a']

        result_descr = ctx._objects['a']
        self.assertEqual(descr, result_descr)

    def test_configure_from_map(self):
        cc = PytelContext({'a': A})
        descr: ObjectDescriptor = cc._objects['a']
        self.assertEqual(A, descr.object_type)

    def test_configure_from_object_field(self):
        class Configurer:
            a = A

        cc = PytelContext(Configurer())
        descr: ObjectDescriptor = cc._objects['a']
        self.assertEqual(A, descr.object_type)

    def test_missing_dependency(self):
        svc = {
            'c': C,
        }
        self.assertRaises(ValueError, lambda: PytelContext(svc).get('c'))

    def test_missing_name(self):
        ctx = PytelContext([])
        self.assertRaises(KeyError, lambda: ctx.get('a'))

    def test_cyclic_dependency_raises(self):
        class Configurer:
            def a(self, b: B) -> A:
                pass

            def b(self, a: A) -> B:
                pass

        self.assertRaises(ValueError, lambda: PytelContext(Configurer()))

    def test_cyclic_dependency_on_self_raises(self):
        class Configurer:
            def a(self, a: A) -> A:
                pass

        self.assertRaises(ValueError, lambda: PytelContext(Configurer()))

    def test_dependency_wrong_type(self):
        class Configurer:
            def a(self, b: B) -> A:
                pass

            def b(self) -> A:
                pass

        self.assertRaises(ValueError, lambda: PytelContext(Configurer()))

    def test_duplicate_names(self):
        self.assertRaises(KeyError, lambda: PytelContext([{
            'a': A
        }, {
            'a': B
        }]))

    def test_factory_returned_none(self):
        class Configurer:
            def a(self) -> str:
                return None

        ctx = PytelContext(Configurer())
        self.assertRaises(ValueError, lambda: ctx.get('a'))

    def test_keys(self):
        ctx = PytelContext({'a': A})
        self.assertEqual(['a'], list(ctx.keys()))

    def test_items(self):
        ctx = PytelContext({'a': A})
        self.assertEqual({'a': ObjectDescriptor.from_callable('a', A)}, dict(ctx.items()))
