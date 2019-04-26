import logging
import typing

from .proxy import LazyLoadProxy

log = logging.getLogger(__name__)


class ObjectResolver:
    def resolve(self, context):
        pass


class TypeWrapper(ObjectResolver):
    """Allow adding lazily loaded instance to the context. The resulting object is a functor, call it to pass arguments
     to the constructor

     >>> context = Pytel()
     >>> class A:
     >>>   ...
     Normal use:
     >>> a=A()
     Pytel use:
     >>> context.a=A()
     >>> a = context.a
     Lazy loading
     >>> context.a=lazy(A)
     >>> a = context.a
     Lazy loading with parameters:
     >>> context.a = lazy(A)(...)
     >>> a = context.a
     """

    def __init__(self, klass):
        self._klass = klass
        self._args = []
        self._kwargs = {}

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def resolve(self, context):
        new_args = []
        for i in range(len(self._args)):
            arg = self._args[i]
            while isinstance(arg, ObjectResolver):
                arg = arg.resolve(context)
            else:
                new_args.append(arg)

        new_kwargs = {}
        for name, value in self._kwargs:
            while isinstance(value, ObjectResolver):
                value = value.resolve(context)
            else:
                new_kwargs[name] = value
        return self._klass(*new_args, **self._kwargs)


class Pytel:
    """
    Provide a dependency-injection-like mechanism for loose coupling

    To add object to the context simply assing it as an attribute:

    >>> context = Pytel()
    >>> context.a = A()

    To retrieve that object simple by accessing that attribute:

    >>> a = context.a

    That's maybe useful when you have too many dependencies in your class and you don't like too many __init__
    arguments or self attributes:

    >>> class TooManyDeps:
    >>>     def __init__(self, context):
    >>>         self.a = context.a
    >>>         self.context = context
    >>>         ...
    >>>
    >>>     def do_sth(self):
    >>>         self.context.a.call_method()

    See also :py:func:`~pytel.Pytel.lazy` and :py:func:`~Pytel.ref`

    """

    def __init__(self, init: dict = None):
        objects = {}
        object.__setattr__(self, '_objects', objects)
        object.__setattr__(self, '_stack', [])

        if init:
            for k, v in init.items():
                self._set(k, v)

        # init subclass
        for t in [type(self)] + list(type(self).__bases__):
            if t is Pytel:
                break
            for name, value in t.__dict__.items():
                if not _is_dunder(name):
                    if callable(value) and not isinstance(value, type):
                        self._set(name, FunctionWrapper(value))
                    else:
                        self._set(name, value)

    def __setattr__(self, name, value):
        self._set(name, value)

    def __delattr__(self, item):
        if item not in self._objects:
            raise AttributeError(item)
        else:
            del self._objects[item]

    def __getattribute__(self, name: str):
        # __getattribute__ is required instead of __getattr__ to kidnap accessing the subclasses' methods
        if _is_special_name(name):
            return object.__getattribute__(self, name)

        try:
            return self._get(name)
        except KeyError:
            raise AttributeError(name) from None

    def _get(self, name):
        _objects = self._objects
        if name in _objects:
            return self._resolve(name, _objects[name])
        else:
            raise KeyError(name)

    def _set(self, name, value):
        log.debug('Registering %s := %s', name, value)
        self._objects[name] = value

    def _resolve(self, name, obj):
        if not isinstance(obj, ObjectResolver):
            return obj
        else:
            if name in self._stack:
                def _break_cycle():
                    return self._objects[name]

                return LazyLoadProxy(_break_cycle)
            try:
                self._stack.append(name)
                inst = obj.resolve(self)
                if inst is None:
                    raise ValueError('None', name)
                self._set(name, inst)
                return inst
            finally:
                self._stack.pop()

    def __len__(self):
        return len(self._objects)

    def __getitem__(self, item):
        return self._get(item)

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        del self._objects[key]

    def __contains__(self, item):
        return item in self._objects

    def keys(self):
        return self._objects.keys()


def _is_special_name(name):
    return _is_dunder(name) or name in ['_objects', '_stack', '_get', '_set', '_resolve', 'keys']


def _is_dunder(name):
    return name.startswith('__') and name.endswith('__')


class FunctionWrapper(ObjectResolver):
    """
    Allow to use arbitrary function to lazily create the object.

    >>> context = Pytel()
    >>> def mk_str(context):
    >>>     return 'hello'
    >>> context.a = func(mk_str)

    Now accessing context.a will call mk_str:

    >>> word = context.a
    """

    def __init__(self, fn: typing.Callable[[Pytel], object]):
        self._fn = fn

    def resolve(self, context):
        result = self._fn(context)
        if result is None:
            raise ValueError
        return result
