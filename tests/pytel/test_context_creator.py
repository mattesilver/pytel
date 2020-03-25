from unittest import TestCase

from pytel import ContextCreator
from pytel.context import ObjectDescriptor


class A:
    pass


class B:
    def __init__(self):
        self.initialised = True


class C:
    def __init__(self, a: A):
        self.a = a


class TestContextCreator(TestCase):
    def test_resolve(self):
        cc = ContextCreator({'a': A})
        descr = cc._map['a']

        ctx = cc.resolve()
        result_descr = ctx._context._objects['a']
        self.assertEqual(descr, result_descr)

    def test_configure_from_map(self):
        cc = ContextCreator({'a': A})
        descr: ObjectDescriptor = cc._map['a']
        self.assertEqual(A, descr.object_type)

    def test_configure_from_object_field(self):
        class Configurer:
            a = A

        cc = ContextCreator(Configurer())
        descr: ObjectDescriptor = cc._map['a']
        self.assertEqual(A, descr.object_type)

    def test_missing_dependency(self):
        svc = {
            'c': C,
        }
        self.assertRaises(ValueError, ContextCreator(svc).resolve)

    def test_cyclic_dependency_raises(self):
        class Configurer:
            def a(self, b: B) -> A:
                pass

            def b(self, a: A) -> B:
                pass

        cc = ContextCreator(Configurer())
        self.assertRaises(ValueError, cc.resolve)

    def test_cyclic_dependency_on_self_raises(self):
        class Configurer:
            def a(self, a: A) -> A:
                pass

        cc = ContextCreator(Configurer())
        self.assertRaises(ValueError, cc.resolve)

    def test_dependency_wrong_type(self):
        class Configurer:
            def a(self, b: B) -> A:
                pass

            def b(self) -> A:
                pass

        cc = ContextCreator(Configurer())
        self.assertRaises(ValueError, cc.resolve)
