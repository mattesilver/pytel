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

        ctx = ContextCreator(Configurer()).resolve()
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

        ctx = ContextCreator(Configurer()).resolve()
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

        ctx = ContextCreator(Configurer()).resolve()
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

        ctx = ContextCreator([Configurer(), m]).resolve()
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

        ctx = ContextCreator(Configurer()).resolve()
        self.assertEqual('A', ctx.a)
        self.assertIsInstance(ctx.b, TakingString)
        self.assertEqual('A', ctx.b.a)

    def test_missing_key(self):
        class Configurer:
            a = A

        ctx = ContextCreator(Configurer()).resolve()
        self.assertRaises(AttributeError, lambda: ctx.b)

    def test_len(self):
        class Configurer:
            a = A
            b = B
            c = C

        ctx = ContextCreator(Configurer()).resolve()
        self.assertEqual(3, len(ctx))

    def test_contains(self):
        class Configurer:
            a = A

        ctx = ContextCreator(Configurer()).resolve()
        self.assertTrue('a' in ctx)

    def test_duplicate_names(self):
        self.assertRaises(KeyError, lambda: ContextCreator([{
            'a': A
        }, {
            'a': B
        }]))

    def test_factory_returned_none(self):
        class Configurer:
            def a(self)->str:
                return None

        ctx= ContextCreator(Configurer()).resolve()
        self.assertRaises(ValueError, lambda:ctx.a)