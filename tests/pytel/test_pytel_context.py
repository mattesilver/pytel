from unittest import TestCase
from unittest.mock import Mock, patch

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

    def test_context_manager(self):
        import contextlib

        m = Mock()

        @contextlib.contextmanager
        def factory() -> Mock:
            yield m

        with PytelContext({'m': factory}) as ctx:
            self.assertEquals(m, ctx.get('m'))

    def test_close(self):
        with patch('contextlib.ExitStack') as exit_stack_mock:
            exit_stack_mock().close = Mock(return_value=False)
            PytelContext(None).close()
            exit_stack_mock().close.assert_called_once_with()

    def test_object_not_truthy_is_valid(self):
        def factory() -> int:
            return 0

        self.assertFalse(factory())

        ctx = PytelContext({'a': factory})
        self.assertEqual(0, ctx.get('a'))

    def test_object_not_truthy_is_valid_dependency(self):
        def factory() -> int:
            return 0

        def factory2(a: int) -> B:
            self.assertEqual(0, a)
            return B()

        ctx = PytelContext({'a': factory, 'b': factory2})
        self.assertIsInstance(ctx.get('b'), B)

    def test_factory_returning_subclass(self):
        class D(A):
            pass

        def factory() -> A:
            return D()

        ctx = PytelContext({'a': factory})
        self.assertIsInstance(ctx.get('a'), D)

    def test_factory_returning_subclass_as_dependency(self):
        class D(A):
            pass

        def factory() -> A:
            return D()

        ctx = PytelContext({'a': factory, 'c': C})
        c = ctx.get('c')
        self.assertIsInstance(c, C)
        self.assertIsInstance(c.a, D)
