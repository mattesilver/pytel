import unittest
from unittest import TestCase

from pytel import Pytel, auto, ResolveBy, ObjectResolver
from pytel.proxy import LazyLoadProxy
from pytel.pytel import AutoResolver


class A:
    pass


class B:
    def __init__(self, a: A):
        self.a = a


class test_Pytel(TestCase):
    def test_assignment_by_setattr(self):
        # given
        context = Pytel()
        a = object()

        # when
        context.a = a

        # then
        self.assertIs(a, context._objects['a'])

    def test_assignment_by_setattr_none_error(self):
        # given
        context = Pytel()

        # then
        with self.assertRaises(ValueError):
            context.a = None

    def test_assignment_setitem(self):
        # given
        ctx = Pytel()
        a = object()

        # when
        ctx['a'] = a

        # then
        self.assertIs(a, ctx._objects['a'])

    def test_assignment_setitem_none_error(self):
        # given
        ctx = Pytel()

        # then
        with self.assertRaises(ValueError):
            # when
            ctx['a'] = None

    def test_resolve_from_instance_method(self):
        # given
        a = object()

        class Context(Pytel):
            def a(self):
                return a

        # when
        ctx = Context()

        # then
        self.assertIs(a, ctx.a)

    def test_resolve_from_instance_method_none_error(self):
        # given
        class Context(Pytel):
            def a(self):
                return None

        # when
        ctx = Context()

        # then
        self.assertRaises(ValueError, lambda: ctx.a)

    @unittest.skip('@classmethod currently not supported')
    def test_resolve_from_class_method(self):
        a = object()

        # given
        class Context(Pytel):
            @classmethod
            def a(cls):
                return a

        # when
        ctx = Context()

        # given
        self.assertIs(a, ctx.a)

    @unittest.skip('@classmethod currently not supported')
    def test_resolve_from_class_method_none_error(self):
        class Context(Pytel):
            @classmethod
            def a(cls):
                return None

        ctx = Context()
        self.assertRaises(AttributeError, lambda: ctx.a)

    @unittest.skip('@staticmethod currently not supported')
    def test_resolve_from_static_method(self):
        a = object()

        # given
        class Context(Pytel):
            @staticmethod
            def a():
                return a

        # when
        ctx = Context()

        # givenó
        # self.assertIs(a, ctx.a)
        self.assertIsInstance(ctx._objects['a'], AutoResolver)

    @unittest.skip('@staticmethod currently not supported')
    def test_resolve_from_static_method_none_error(self):
        class Context(Pytel):
            @staticmethod
            def a():
                return None

        ctx = Context()
        self.assertRaises(AttributeError, lambda: ctx.a)

    def test_retrieval_by_getattr(self):
        # given
        context = Pytel()
        a = object()

        # when
        context.a = a

        # then
        self.assertIs(a, context.a)

    def test_retrieval_by_getitem(self):
        # given
        ctx = Pytel()
        a = A()

        # when
        ctx.a = a

        # then
        self.assertEqual(a, ctx['a'])

    def test_find_one_by_type(self):
        class A1:
            pass

        ctx = Pytel()
        ctx.a = A()
        ctx.b = A1()

        self.assertEqual(ctx.a, ctx.find_one_by_type(A))

    def test_find_one_by_type_fail_on_empty(self):
        ctx = Pytel()

        with self.assertRaises(ValueError):
            ctx.find_one_by_type(A)

    def test_find_one_by_type_fail_on_miss(self):
        ctx = Pytel()
        ctx.a = object()

        with self.assertRaises(ValueError):
            ctx.find_one_by_type(A)

    def test_find_one_by_type_fail_on_double(self):
        ctx = Pytel()
        ctx.a = A()
        ctx.b = A()

        with self.assertRaises(ValueError):
            ctx.find_one_by_type(A)

    def test_find_one_by_type_fail_on_double_inherit(self):
        class A1(A):
            pass

        ctx = Pytel()
        ctx.a = A()
        ctx.b = A1()

        with self.assertRaises(ValueError):
            ctx.find_one_by_type(A)

    def test_find_all_by_type(self):
        class F1:
            pass

        class F2:
            pass

        class F3(F2):
            pass

        ctx = Pytel()
        ctx.a = auto(F1)
        ctx.b = auto(F2)
        ctx.c = auto(F3)

        self.assertEqual([ctx.a], ctx.find_all_by_type(F1))
        self.assertEqual({ctx.b, ctx.c}, {*ctx.find_all_by_type(F2)})
        self.assertEqual([ctx.c], ctx.find_all_by_type(F3))
        self.assertEqual({ctx.a, ctx.b, ctx.c}, {*ctx.find_all_by_type(object)})
        self.assertEqual([], ctx.find_all_by_type(str))

    def test_len(self):
        # given
        ctx = Pytel()

        # then
        self.assertEqual(0, len(ctx))

        # given
        ctx.a = object()

        # then
        self.assertEqual(1, len(ctx))

    def test_keys(self):
        ctx = Pytel()
        ctx.a = object()

        self.assertEqual(['a'], list(ctx.keys()))

    def test_in(self):
        ctx = Pytel()
        ctx.a = object()

        self.assertIn('a', ctx)

    def test_items(self):
        a = object()
        ctx = Pytel()
        ctx.a = a

        self.assertEqual({'a': a}.items(), ctx.items())

    def test_delitem(self):
        # given
        ctx = Pytel()
        ctx.a = object()

        # when
        del ctx['a']

        # then
        self.assertNotIn('a', ctx._objects)

    def test_delattr(self):
        ctx = Pytel()
        ctx.a = object()
        del ctx.a
        self.assertNotIn('a', ctx._objects)

    def test_resolution_of_object_resolver(self):
        # given
        ctx = Pytel()
        a = object()

        class TestObjectResolver(ObjectResolver):
            def resolve(self, ctx):
                return a

        # when
        ctx.a = TestObjectResolver()

        # then
        self.assertEqual(a, ctx.a)

    def test_init_from_dict(self):
        a = object()
        ctx = Pytel({'a': a})
        self.assertEqual(a, ctx._objects['a'])

    def test_init_from_dict_none_error(self):
        with self.assertRaises(ValueError):
            ctx = Pytel({'a': None})

    def test_retrieve_missing_with_getattr(self):
        context = Pytel()

        self.assertRaises(AttributeError, lambda: context.a)

    def test_retrieve_missing_with_getitem(self):
        context = Pytel()

        self.assertRaises(KeyError, lambda: context['a'])

    def test_dependency_cycle(self):
        class Z:
            def __init__(self, context: Pytel):
                self.b = context.b

        class Y:
            def __init__(self, context: Pytel):
                self.a = context.a

        context = Pytel()
        context.a = auto(Z)
        context.b = auto(Y)

        self.assertIsInstance(context.a, Z)
        self.assertIsInstance(context.b, Y)

        self.assertIs(context.a.b, context.b)
        self.assertEqual(context.b.a, context.a)
        self.assertIsInstance(context.b.a, LazyLoadProxy)

    def test_subclass_with_inst_attr(self):
        a = object()

        class TestContext(Pytel):
            def __init__(self):
                super().__init__()
                self.a = a

        ctx = TestContext()
        self.assertEqual(a, ctx._objects['a'])

    def test_subclass_with_inst_attr_none_error(self):
        class TestContext(Pytel):
            def __init__(self):
                super().__init__()
                self.a = None

        self.assertRaises(ValueError, TestContext)

    def test_subclass_with_cls_attr(self):
        obj = object()

        class TestContext(Pytel):
            a = obj

        ctx = TestContext()

        self.assertEqual(obj, ctx._objects['a'])

    def test_subclass_with_cls_attr_none_errror(self):
        class TestContext(Pytel):
            a = None

        self.assertRaises(ValueError, TestContext)


class AutoResolverTest(TestCase):
    def test_with_none_as_callable(self):
        with self.assertRaises(ValueError):
            AutoResolver(None)

    def test_no_arg_function(self):
        a = object()

        def factory():
            return a

        result = AutoResolver(factory).resolve(None)
        self.assertEqual(a, result)

    def test_no_arg_function_none_error(self):
        def factory():
            return None

        with self.assertRaises(ValueError):
            AutoResolver(factory).resolve(None)

    def test_no_arg_ctor(self):
        result = AutoResolver(A).resolve(None)

        self.assertIsInstance(result, A)

    def test_no_arg_inst_method(self):
        a = object()

        class Factory:
            def a(self):
                return a

        result = AutoResolver(Factory().a).resolve(None)

        self.assertIs(a, result)

    def test_classmethod_factory(self):
        a = object()

        class Factory:
            @classmethod
            def factory(cls):
                return a

        result = auto(Factory.factory).resolve(None)
        self.assertIs(a, result)

    def test_staticmethod_factory(self):
        a = object()

        class Factory:
            @staticmethod
            def factory():
                return a

        self.assertEqual(a, auto(Factory.factory).resolve(None))

    def test_function_with_named_depedency(self):
        a = A()

        def factory(a):
            return B(a)

        ctx = Pytel({'a': a})
        b = AutoResolver(factory).resolve(ctx)
        self.assertIsInstance(b, B)
        self.assertIs(a, b.a)

    def test_ctor_with_named_dependency(self):
        a = A()
        ctx = Pytel({'a': a})
        b = AutoResolver(B).resolve(ctx)

        self.assertIsInstance(b, B)
        self.assertIs(a, b.a)

    def test_function_with_dependency_missing_from_context(self):
        def factory(a):
            return B(a)

        with self.assertRaises(KeyError):
            AutoResolver(factory).resolve(Pytel())

    def test_function_with_dependency_resolved_by_type(self):
        a = A()
        ctx = Pytel({'b': a})

        def factory(a: A):
            return B(a)

        b = AutoResolver(B, ResolveBy.by_type).resolve(ctx)

        self.assertIsInstance(b, B)
        self.assertIs(a, b.a)

    def test_function_with_dependency_resolved_by_name_and_type(self):
        a = A()
        a2 = A()
        ctx = Pytel({'a': a, 'a2': a2})

        def factory(a: A):
            return B(a)

        b = AutoResolver(B, ResolveBy.by_type_and_name).resolve(ctx)

        self.assertIsInstance(b, B)
        self.assertIs(a, b.a)

    def test_function_with_resolved_parameter(self):
        val = 'hello'

        def factory(a):
            return B(a)

        b = AutoResolver(factory)(a=val).resolve(None)
        self.assertIsInstance(b, B)
        self.assertIs(val, b.a)

    def test_function_with_parameter_resolved_to_none(self):
        def factory(a):
            return B(a)

        b = AutoResolver(factory)(a=None).resolve(None)
        self.assertIsInstance(b, B)
        self.assertIs(None, b.a)
