from unittest import TestCase
from unittest.mock import Mock, patch, call

from pytel import Pytel, PytelContext


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

    def test_len(self):
        ctx = Mock()
        ctx.items = Mock(return_value={})

        len(Pytel(ctx))
        ctx.items.assert_has_calls([call(), call()])

    def test_contains(self):
        ctx = Mock()
        ctx.keys = Mock(return_value=[])

        p = Pytel(ctx)
        'a' in p
        ctx.keys.assert_called_once_with()

    def test_init(self):
        ctx = Mock()
        p = Pytel(ctx)
        self.assertEqual(ctx, p._context)

    def test_init_with_none_raises(self):
        self.assertRaises(ValueError, lambda: Pytel(None))

    def test_init_with_empty_warns(self):
        with patch('pytel.pytel.log') as log_mock:
            Pytel(PytelContext([]))

            log_mock.warning.assert_called_once_with('Empty context')

    def test_getattribute(self):
        ctx = Mock()
        p = Pytel(ctx)
        p.a
        ctx.get.assert_called_once_with('a')

    def test_getattribute_with_key_error(self):
        ctx = Mock()
        ctx.get = Mock(side_effect=KeyError())
        p = Pytel(ctx)
        self.assertRaises(AttributeError, lambda: p.a)
