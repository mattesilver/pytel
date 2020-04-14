import contextlib
from unittest import TestCase
from unittest.mock import Mock

from pytel import Pytel
from .test_pytel import A, B, C


class TestUsage(TestCase):
    def test_create_from_dict(self):
        svc = {
            'a': A,
            'b': B,
            'c': C,
        }
        ctx = Pytel(svc)
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)
        self.assertTrue(ctx.b.initialised)

    def test_create_from_object_static_methods(self):
        class Configurer:
            @staticmethod
            def a() -> A:
                return A()

            @staticmethod
            def b() -> B:
                return B()

            @staticmethod
            def c(a: A) -> C:
                return C(a)

        ctx = Pytel(Configurer())
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_create_from_object_methods(self):
        class Configurer:
            def a(self) -> A:
                return A()

            def b(self) -> B:
                return B()

            def c(self, a: A) -> C:
                return C(a)

        ctx = Pytel(Configurer())
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_create_from_class_fields(self):
        class Configurer:
            a = A
            b = B
            c = C

        ctx = Pytel(Configurer())
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_create_from_object_fields(self):
        class Configurer:
            def __init__(self):
                self.a = A()
                self.b = B
                self.c = C

        ctx = Pytel(Configurer())
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_create_from_many_configurers(self):
        class Configurer:
            a = A
            b = B

        m = {
            'c': C
        }

        ctx = Pytel([Configurer(), m])
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_inject_simple_variable(self):
        class TakingString:
            def __init__(self, a: str):
                self.a = a

        class Configurer:
            a = 'A'
            b = TakingString

        ctx = Pytel(Configurer())
        self.assertEqual('A', ctx.a)
        self.assertIsInstance(ctx.b, TakingString)
        self.assertEqual('A', ctx.b.a)

    def test_context_manager(self):
        class D:
            def __init__(self):
                self.initialised = True
                self.entered = False

            def __enter__(self):
                self.entered = True
                return self

            def __exit__(self, *exc_details):
                self.exited = True
                return False

        with Pytel({'m': D}) as ctx:
            m = ctx.m
            self.assertTrue(m.initialised)
            self.assertTrue(m.entered)
        self.assertTrue(m.exited)

    def test_context_manager_annotation(self):
        obj = Mock()

        @contextlib.contextmanager
        def factory() -> Mock:
            obj.opened = True
            yield obj
            obj.closed = True

        with Pytel({'m': factory}) as ctx:
            m = ctx.m
            self.assertTrue(m.opened)

        self.assertTrue(m.closed)

    def test_resolve_from_parent(self):
        parent = Pytel({'a': A})
        child = Pytel({}, parent=parent)

        self.assertIsInstance(child.a, A)

    def test_resolve_dependency_from_parent(self):
        parent = Pytel({'a': A})
        child = Pytel({'c': C}, parent=parent)

        self.assertIsInstance(child.c.a, A)
