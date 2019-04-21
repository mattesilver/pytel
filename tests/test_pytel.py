import logging
import sys
from unittest import TestCase

from pytel import __version__, Pytel, lazy, func
from pytel.pytel import FunctionWrapper

log = logging.getLogger(__name__)


class test_Pytel(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

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

    def test_lazy_dependency_creation_and_resolution(self):
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

    def test_method_as_func(self):
        class A:
            @classmethod
            def factory(cls, _):
                return cls()

        ctx = Pytel()
        ctx.a = func(A.factory)
        self.assertIsInstance(ctx.a, A)

    def test_lambda_func(self):
        class A:
            pass

        ctx = Pytel()
        ctx.a = func(lambda ctx: A())
        self.assertIsInstance(ctx.a, A)

    def test_subclassing_basic(self):
        class A:
            pass

        class Context(Pytel):
            def a(self):
                return A()

        ctx = Context()
        self.assertIsInstance(ctx._objects['a'], FunctionWrapper)
        self.assertIsInstance(ctx.a, A)

    def test_subclassing_with_dep(self):
        class A:
            pass

        class B:
            def __init__(self, a):
                self.a = a

        class Context(Pytel):
            def a(self):
                return A()

        ctx = Context()
        ctx.b = func(lambda ctx: B(ctx.a))
        self.assertIsInstance(ctx.b.a, A)

    def test_subclass_with_inst_attr(self):
        t = test_Pytel.T()

        class I(Pytel):
            def __init__(self):
                super().__init__()
                self.t = t

        ctx = I()
        self.assertEqual(t, ctx._objects['t'])

    def test_subclass_with_cls_attr(self):
        t = test_Pytel.T()

        class J(Pytel):
            a = t

        ctx = J()

        self.assertEqual(t, ctx.a)

    def test_init_from_dict(self):
        class A:
            pass

        a = A()
        ctx = Pytel({'a': a})
        self.assertEqual(a, ctx._objects['a'])

    class T:
        def __init__(self, *args):
            pass

    def test_len(self):
        ctx = Pytel({'a': self.T()})
        self.assertEqual(1, len(ctx))

    def test_get_item(self):
        ctx = Pytel()
        t = self.T()
        ctx.t = t
        self.assertEqual(t, ctx['t'])

    def test_set_item(self):
        ctx = Pytel()
        t = self.T()
        ctx['t'] = t
        self.assertEqual(t, ctx._objects['t'])

    def test_del_item(self):
        ctx = Pytel()
        t = self.T()
        ctx.t = t
        del ctx['t']
        self.assertNotIn('t', ctx._objects)

    def test_del(self):
        ctx = Pytel()
        t = self.T()
        ctx.t = t
        del ctx.t
        self.assertNotIn('t', ctx._objects)

    def test_contains(self):
        ctx = Pytel()
        t = self.T()
        ctx.t = t
        self.assertIn('t', ctx)

    def test_keys(self):
        ctx = Pytel()
        ctx.t = self.T()

        self.assertIn('t', ctx.keys())

    def test_keys_subclass(self):
        class Context(Pytel):
            def t(self):
                return test_Pytel.T()

        ctx = Context()

        self.assertIn('t', ctx.keys())

    def test_func_none(self):
        ctx = Pytel()
        ctx.a = func(lambda ctx: None)

        with self.assertRaises(ValueError):
            a = ctx.a
