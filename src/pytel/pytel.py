import abc
import enum
import inspect
import logging
import types
import typing

from .proxy import LazyLoadProxy

log = logging.getLogger(__name__)


class ObjectResolver(abc.ABC):
    @abc.abstractmethod
    def resolve(self, context):
        pass  # pragma: no cover


class ResolveBy(enum.Enum):
    by_type = enum.auto()
    by_name = enum.auto()
    by_type_and_name = enum.auto()


T = typing.TypeVar('T')


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
                    if isinstance(value, types.FunctionType):
                        self._set(name, AutoResolver(types.MethodType(value, self)))
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
        obj = self._objects[name]
        return self._resolve(name, obj)

    def _set(self, name, value):
        if value is None:
            raise ValueError('None value', name)
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

    def find_one_by_type(self, cls: typing.Type[T]) -> T:
        candidates = list(self.find_all_by_type(cls))
        if len(candidates) != 1:
            raise ValueError('Could not find single instance of ', cls, len(candidates))
        else:
            return candidates[0]

    def find_all_by_type(self, cls: typing.Type[T]) -> typing.List[T]:
        result = []
        for key, value in self._objects.items():
            if isinstance(value, ObjectResolver):
                actual_value = self._resolve(key, value)
                if isinstance(actual_value, cls):
                    result.append(actual_value)
            elif isinstance(value, cls):
                result.append(value)

        return result

    def items(self):
        return self._objects.items()


def _is_special_name(name):
    return _is_dunder(name) or name in [
        '_get',
        '_objects',
        '_resolve',
        '_set',
        '_stack',
        'find_one_by_type',
        'find_all_by_type',
        'items',
        'keys',
    ]


def _is_dunder(name):
    return name.startswith('__') and name.endswith('__')


class AutoResolver(ObjectResolver):
    def __init__(self, factory: typing.Callable, resolve_by: ResolveBy = ResolveBy.by_name):
        if factory is None:
            raise ValueError('None for factory')
        self._factory = factory
        self._resolve_by = resolve_by
        self._xargs = {}

    def __call__(self, **kwargs) -> 'AutoResolver':
        self._xargs = kwargs.copy()
        return self

    def resolve(self, context):
        spec = inspect.getfullargspec(self._factory)

        args_list = spec.args if isinstance(self._factory, types.FunctionType) else spec.args[1:]
        if spec.varargs:
            args_list.append(spec.varargs)
        args = [self._resolve_argument(key, context, spec.annotations.get(key)) for key in args_list]

        kwargs = {key: self._resolve_argument(key, context, spec.annotations.get(key)) for key in spec.kwonlyargs}

        if spec.varkw and spec.varkw in self._xargs:
            kwargs.update(self._xargs.pop(spec.varkw))

        if self._xargs:
            raise TypeError(
                f"{self._factory.__name__}() got an unexpected keyword argument '{list(self._xargs.keys()).pop()}'")

        result = self._factory(*args, **kwargs)
        if result is not None:
            return result
        else:
            raise ValueError('Callable returned None', self._factory)

    def _resolve_argument(self, name, context, arg_type):
        if name in self._xargs:
            return self._xargs.pop(name)
        else:
            return self._resolve_dependency(context, name, arg_type)

    def _resolve_dependency(self, ctx: Pytel, name: str, arg_class: typing.Type[T]) -> T:
        if arg_class is Pytel:
            return ctx

        if (self._resolve_by is ResolveBy.by_type or self._resolve_by is ResolveBy.by_type_and_name) and \
                arg_class is None:
            raise ValueError('Unannotated argument', name, self._resolve_by)

        if self._resolve_by is ResolveBy.by_name or self._resolve_by is ResolveBy.by_type_and_name:
            resolved = ctx[name]
            if self._resolve_by is ResolveBy.by_type_and_name and not isinstance(resolved, arg_class):
                raise ValueError('Named dependency not of required type', name, arg_class, __class__)
            return resolved
        else:
            return ctx.find_one_by_type(arg_class)


FactoryType = typing.Callable[..., T]

auto: typing.Callable[[FactoryType, typing.Optional[ResolveBy]], T] = AutoResolver
