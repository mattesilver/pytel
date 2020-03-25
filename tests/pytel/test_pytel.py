from unittest import TestCase

from pytel import ContextCreator


class A:
    pass


class B:
    def __init__(self):
        self.initialised = True


class C:
    def __init__(self, a: A):
        self.a = a


class test_Pytel(TestCase):

    # intended use cases

    def test_create_from_dict(self):
        svc = {
            'a': A,
            'b': B,
            'c': C,
        }
        ctx = ContextCreator(svc).resolve()
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)
        self.assertTrue(ctx.b.initialised)

    def test_create_from_subclass_static_methods(self):
        class Subclass(ContextCreator):
            @staticmethod
            def a() -> A:
                return A()

            @staticmethod
            def b() -> B:
                return B()

            @staticmethod
            def c(a: A) -> C:
                return C(a)

        ctx = Subclass().resolve()
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)

    def test_create_from_subclass_fields(self):
        class Subclass(ContextCreator):
            a = A
            b = B
            c = C

        ctx = Subclass().resolve()
        self.assertIsInstance(ctx.a, A)
        self.assertIsInstance(ctx.b, B)
        self.assertTrue(ctx.b.initialised)
        self.assertIsInstance(ctx.c, C)
        self.assertEqual(ctx.c.a, ctx.a)
