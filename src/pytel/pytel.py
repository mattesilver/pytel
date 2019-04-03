import abc
import typing

from .proxy import LazyLoadProxy


class ObjectResolver(abc.ABC):
    @abc.abstractmethod
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

    def __init__(self):
        object.__setattr__(self, '_objects', {})
        object.__setattr__(self, '_stack', [])

    def __setattr__(self, name, value):
        self._objects[name] = value

    def __getattr__(self, name):
        try:
            obj = self._objects[name]
        except KeyError:
            raise AttributeError(name)

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
                self._objects[name] = inst
                return inst
            finally:
                self._stack.pop()


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
        return self._fn(context)
