import contextlib
from unittest import TestCase
from unittest.mock import patch, Mock

from pytel import Pytel
from pytel.context import ObjectDescriptor


class A:
    pass


class B:
    def __init__(self):
        self.initialised = True


class C:
    def __init__(self, a: A):
        self.a = a


class test_Pytel(TestCase):
    # other tests

    def test_configure_from_map(self):
        cc = Pytel({'a': A})
        descr: ObjectDescriptor = cc._objects['a']
        self.assertEqual(A, descr.object_type)

    def test_configure_from_object_field(self):
        class Configurer:
            a = A

        cc = Pytel(Configurer())
        descr: ObjectDescriptor = cc._objects['a']
        self.assertEqual(A, descr.object_type)

    def test_missing_dependency(self):
        svc = {
            'c': C,
        }
        self.assertRaises(ValueError, lambda: Pytel(svc)._get('c'))

    def test_get_missing_name(self):
        ctx = Pytel([])
        self.assertRaises(KeyError, lambda: ctx._get('a'))

    def test_cyclic_dependency_raises(self):
        class Configurer:
            def a(self, b: B) -> A:
                pass

            def b(self, a: A) -> B:
                pass

        self.assertRaises(ValueError, lambda: Pytel(Configurer()))

    def test_cyclic_dependency_on_self_raises(self):
        class Configurer:
            def a(self, a: A) -> A:
                pass

        self.assertRaises(ValueError, lambda: Pytel(Configurer()))

    def test_dependency_wrong_type(self):
        class Configurer:
            def a(self, b: B) -> A:
                pass

            def b(self) -> A:
                pass

        self.assertRaises(ValueError, lambda: Pytel(Configurer()))

    def test_duplicate_names(self):
        self.assertRaises(KeyError, lambda: Pytel([{
            'a': A
        }, {
            'a': B
        }]))

    def test_factory_returned_none(self):
        class Configurer:
            def a(self) -> str:
                return None

        ctx = Pytel(Configurer())
        self.assertRaises(ValueError, lambda: ctx._get('a'))

    def test_keys(self):
        ctx = Pytel({'a': A})
        self.assertEqual(['a'], list(ctx.keys()))

    def test_items(self):
        ctx = Pytel({'a': A})
        self.assertEqual({'a': ObjectDescriptor.from_callable('a', A)}, dict(ctx.items()))

    def test_context_manager(self):
        m = Mock()

        @contextlib.contextmanager
        def factory() -> Mock:
            yield m

        with Pytel({'m': factory}) as ctx:
            self.assertEqual(m, ctx._get('m'))

    def test_close(self):
        with patch('contextlib.ExitStack') as exit_stack_mock:
            exit_stack_mock().close = Mock(return_value=False)
            Pytel([]).close()
            exit_stack_mock().close.assert_called_once_with()

    def test_object_not_truthy_is_valid(self):
        def factory() -> int:
            return 0

        self.assertFalse(factory())

        ctx = Pytel({'a': factory})
        self.assertEqual(0, ctx._get('a'))

    def test_object_not_truthy_is_valid_dependency(self):
        def factory() -> int:
            return 0

        def factory2(a: int) -> B:
            self.assertEqual(0, a)
            return B()

        ctx = Pytel({'a': factory, 'b': factory2})
        self.assertIsInstance(ctx._get('b'), B)

    def test_factory_returning_subclass(self):
        class D(A):
            pass

        def factory() -> A:
            return D()

        ctx = Pytel({'a': factory})
        self.assertIsInstance(ctx._get('a'), D)

    def test_factory_returning_subclass_as_dependency(self):
        class D(A):
            pass

        def factory() -> A:
            return D()

        ctx = Pytel({'a': factory, 'c': C})
        c = ctx._get('c')
        self.assertIsInstance(c, C)
        self.assertIsInstance(c.a, D)

    def test_len(self):
        p = Pytel({'a': A})
        self.assertEqual(1, len(p))

    def test_contains(self):
        p = Pytel({'a': A})
        self.assertTrue('a' in p)

    def test_init(self):
        ctx = {'a': A}
        p = Pytel(ctx)
        self.assertEqual({'a': ObjectDescriptor.from_callable('a', A)}, p._objects)
        self.assertIsInstance(p._exit_stack, contextlib.ExitStack)

    def test_init_with_none_raises(self):
        self.assertRaises(ValueError, lambda: Pytel(None))

    def test_init_with_empty_warns(self):
        with patch('pytel.pytel.log') as log_mock:
            Pytel([])

            log_mock.warning.assert_called_once_with('Empty context')

    def test_getattr(self):
        a = A()
        ctx = Pytel({'a': a})
        self.assertEqual(a, ctx.a)

    def test_getattr_with_attribute_error(self):
        p = Pytel([])
        self.assertRaises(AttributeError, lambda: p.a)
