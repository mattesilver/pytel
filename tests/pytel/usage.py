from unittest import TestCase

from pytel import Pytel, PytelContext
from .test_pytel import A, B, C


class TestUsage(TestCase):
    def test_create_from_dict(self):
        svc = {
            'a': A,
            'b': B,
            'c': C,
        }
        ctx = Pytel(PytelContext(svc))
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

        ctx = Pytel(PytelContext(Configurer()))
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

        ctx = Pytel(PytelContext(Configurer()))
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_create_from_object_fields(self):
        class Configurer:
            a = A
            b = B
            c = C

        ctx = Pytel(PytelContext(Configurer()))
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

        ctx = Pytel(PytelContext([Configurer(), m]))
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

        ctx = Pytel(PytelContext(Configurer()))
        self.assertEqual('A', ctx.a)
        self.assertIsInstance(ctx.b, TakingString)
        self.assertEqual('A', ctx.b.a)
