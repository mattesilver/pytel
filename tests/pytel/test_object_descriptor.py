from unittest import TestCase, mock

from pytel.context import ObjectDescriptor


class TestObjectDescriptor(TestCase):
    def test_from_callable_none(self):
        self.assertRaises(AssertionError, lambda: ObjectDescriptor.from_callable('a', None))

    def test_from_callable_no_type(self):
        def a():
            pass

        self.assertRaises(TypeError, lambda: ObjectDescriptor.from_('a', a))

    def test_from_callable_type_none(self):
        def factory() -> None:
            pass

        self.assertRaises(TypeError, lambda: ObjectDescriptor.from_('a', factory))

    def test_from_callable_type(self):
        def a() -> str:
            pass

        descr = ObjectDescriptor.from_('a', a)
        self.assertEqual(str, descr.object_type)

    def test_from_callable_params_no_type(self):
        def a(b) -> str:
            pass

        self.assertRaises(TypeError, lambda: ObjectDescriptor.from_('a', a))

    def test_from_callable_param_with_type(self):
        def a(b: str) -> str:
            pass

        descr = ObjectDescriptor.from_('b', a)
        self.assertEqual(str, descr.dependencies['b'])

    def test_from_with_none(self):
        self.assertRaises(ValueError, lambda: ObjectDescriptor.from_('a', None))

    def test_from_with_callable(self):
        with mock.patch('pytel.context.ObjectDescriptor.from_callable') as m:
            ObjectDescriptor.from_('a', ''.capitalize)
            m.was_called_once_with(str.capitalize)

    def test_from_with_type(self):
        with mock.patch('pytel.context.ObjectDescriptor.from_callable') as m:
            ObjectDescriptor.from_('a', str)
            m.was_called_once_with(str)

    def test_from_with_object(self):
        with mock.patch('pytel.context.ObjectDescriptor.from_object') as m:
            ObjectDescriptor.from_('a', "str")
            m.was_called_once_with("str")

    def test_from_object(self):
        descr = ObjectDescriptor.from_object('a', "str")
        self.assertEqual(ObjectDescriptor(None, 'a', str, {}), descr)

    def test_from_object_none(self):
        self.assertRaises(AssertionError, lambda: ObjectDescriptor.from_object('a', None))

    def test_repr(self):
        descr = ObjectDescriptor.from_object('a', "value")
        self.assertEqual(str(descr), '<ObjectDescriptor> a: str')

    def test_neq(self):
        descr = ObjectDescriptor.from_object('a', "str")
        self.assertFalse(descr == 1)
