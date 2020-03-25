from unittest import TestCase, mock, SkipTest

from pytel.context import ObjectDescriptor


class TestObjectDescriptor(TestCase):
    def test_from_callable_none(self):
        self.assertRaises(AssertionError, lambda: ObjectDescriptor.from_callable(None))

    def test_from_callable_no_type(self):
        def a():
            pass

        self.assertRaises(TypeError, lambda: ObjectDescriptor.from_(a))

    def test_from_callable_type(self):
        def a() -> str:
            pass

        descr = ObjectDescriptor.from_(a)
        self.assertEqual(str, descr.object_type)

    def test_from_callable_params_no_type(self):
        def a(b) -> str:
            pass

        self.assertRaises(TypeError, lambda: ObjectDescriptor.from_(a))

    def test_from_callable_param_with_type(self):
        def a(b: str) -> str:
            pass

        descr = ObjectDescriptor.from_(a)
        self.assertEqual(str, descr.dependencies['b'])

    def test_from_with_none(self):
        self.assertRaises(ValueError, lambda: ObjectDescriptor.from_(None))

    def test_from_with_callable(self):
        with mock.patch('pytel.context.ObjectDescriptor.from_callable') as m:
            ObjectDescriptor.from_(''.capitalize)
            m.was_called_once_with(str.capitalize)

    def test_from_with_type(self):
        with mock.patch('pytel.context.ObjectDescriptor.from_callable') as m:
            ObjectDescriptor.from_(str)
            m.was_called_once_with(str)

    def test_from_with_object(self):
        with mock.patch('pytel.context.ObjectDescriptor.from_object') as m:
            ObjectDescriptor.from_("str")
            m.was_called_once_with("str")

    def test_from_object(self):
        descr = ObjectDescriptor.from_object("str")
        self.assertEqual(ObjectDescriptor(None, str, {}), descr)

    def test_from_object_none(self):
        self.assertRaises(AssertionError, lambda: ObjectDescriptor.from_object(None))

    @SkipTest
    def test_object_type(self):
        self.fail()

    @SkipTest
    def test_dependencies(self):
        self.fail()
