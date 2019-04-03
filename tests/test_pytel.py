from unittest import TestCase

from pytel import __version__, Pytel, lazy, func


class test_Pytel(TestCase):
    def test_version(self):
        assert __version__ == '0.1.0'

    def test_object_resolution(self):
        class A:
            def __init__(self, context: Pytel):
                self.b = context.b

        class B:
            pass

        context = Pytel()
        context.a = lazy(A)(context)
        context.b = B()

        self.assertIsInstance(context.a, A)
        self.assertIsInstance(context.b, B)
        self.assertIs(context.a.b, context.b)

    def test_lazy_dependency_creation_and_resulotion(self):
        class A:
            def __init__(self, context: Pytel):
                self.b = context.b

        class B:
            pass

        context = Pytel()
        context.a = lazy(A)(context)
        context.b = lazy(B)

        self.assertIsInstance(context.a, A)
        self.assertIsInstance(context.b, B)
        self.assertIs(context.a.b, context.b)

    def test_init_with_param(self):
        class A:
            def __init__(self, word):
                self.word = word

        context = Pytel()
        context.a = lazy(A)('hello')

        self.assertIsInstance(context.a, A)
        self.assertEqual(context.a.word, 'hello')

    def test_dependency_cycle(self):
        class A:
            def __init__(self, context: Pytel):
                self.b = context.b

        class B:
            def __init__(self, context: Pytel):
                self.a = context.a

        context = Pytel()
        context.a = lazy(A)(context)
        context.b = lazy(B)(context)

        self.assertIsInstance(context.a, A)
        self.assertIsInstance(context.b, B)

        self.assertIs(context.a.b, context.b)
        self.assertEqual(context.b.a, context.a)
        self.assertIsNot(context.b.a, context.a)

    def test_lazy_with_new(self):
        class A:
            def __new__(cls):
                inst = super().__new__(cls)
                inst.new_called = True
                return inst

        context = Pytel()
        context.a = lazy(A)

        self.assertTrue(context.a.new_called)

    def test_lazy_with_new_with_context_param(self):
        class A:
            def __new__(cls, context: Pytel):
                inst = super().__new__(cls)
                inst.context_from_new = context
                return inst

            def __init__(self, a):
                self.context_from_init = a

        context = Pytel()
        context.a = lazy(A)(context)

        self.assertIs(context.a.context_from_new, context)
        self.assertIs(context.a.context_from_init, context)

    def test_redefine(self):
        class A:
            pass

        class B:
            pass

        context = Pytel()
        context.a = lazy(A)
        self.assertIsInstance(context.a, A)

        context.a = lazy(B)
        self.assertIsInstance(context.a, B)

    def test_cycle_with_redefine(self):
        class A:
            def __init__(self, context):
                self.b = context.b

        class B:
            def __init__(self, context):
                self.a = context.a

        class C:
            pass

        context = Pytel()
        context.a = lazy(A)(context)
        context.b = lazy(B)(context)

        self.assertIsInstance(context.a, A)
        self.assertIsInstance(context.b, B)

        self.assertIs(context.a.b, context.b)
        self.assertEqual(context.b.a, context.a)
        self.assertIsNot(context.b.a, context.a)

        context.b = lazy(C)

        self.assertIsInstance(context.a.b, B)

    def test_undefined(self):
        context = Pytel()

        def get_a():
            context.a

        self.assertRaises(AttributeError, get_a)

    def test_func(self):
        a_created = [False]

        class A:
            def __init__(self, word, b):
                self.word = word,
                self.b = b

        class B:
            pass

        class C:
            def __init__(self, context):
                self.a = context.a

        def new_a(context):
            a_created[0] = True
            return A('hello', context.b)

        context = Pytel()
        context.a = func(new_a)
        context.b = B()
        context.c = lazy(C)(context)
        self.assertFalse(a_created[0])

        # getting c triggers new_a
        c = context.c
        self.assertTrue(a_created[0])

        self.assertIsInstance(context.a, A)

    def test_func_returning_none_raises_ValueError(self):
        class A:
            def __init__(self, context):
                self.b = context.b

        def new_b(_):
            return None

        context = Pytel()
        context.b = func(new_b)
        context.a = lazy(A)(context)

        def get_a():
            context.a

        self.assertRaises(ValueError, get_a)
