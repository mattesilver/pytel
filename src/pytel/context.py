import inspect
import logging
import typing

log = logging.getLogger(__name__)

T = typing.TypeVar('T')
FactoryType = typing.Union[T, typing.Callable[..., T]]
_K_RETURN = 'return'


class ObjectDescriptor(typing.Generic[T]):
    def __init__(self, factory: typing.Optional[FactoryType],
                 name: str,
                 _type: typing.Type[T],
                 deps: typing.Dict[str, typing.Type]
                 ):
        self._factory = factory
        self._name = name
        self._type = _type
        self._deps = deps
        self._instance: typing.Optional[T] = None

    @classmethod
    def from_(cls, name, obj) -> 'ObjectDescriptor':
        if obj is None:
            raise ValueError(None)
        elif isinstance(obj, type) or callable(obj):
            return ObjectDescriptor.from_callable(name, obj)
        else:
            return ObjectDescriptor.from_object(name, obj)

    @classmethod
    def from_callable(cls, name, factory: FactoryType) -> 'ObjectDescriptor':
        assert factory is not None
        spec = inspect.getfullargspec(factory)
        if isinstance(factory, type):
            t = factory
        else:
            if _K_RETURN in spec.annotations:
                t = spec.annotations[_K_RETURN]
                if t is None:
                    raise TypeError(name, 'Callable type hint is None', factory)
            else:
                raise TypeError(name, 'None type')

        deps = ObjectDescriptor._spec_to_deps(spec)

        log.debug("Dependencies for %s: %s", factory.__qualname__, deps)
        return ObjectDescriptor(factory, name, t, deps)

    @classmethod
    def from_object(cls, name, value: object) -> 'ObjectDescriptor':
        assert value is not None, f'{name} is None'
        result = ObjectDescriptor(None, name, type(value), {})
        result._instance = value
        return result

    @staticmethod
    def _spec_to_deps(spec: inspect.FullArgSpec) -> typing.Dict[str, typing.Type]:
        args = spec.args.copy()
        if len(args) > 0 and args[0] == 'self':
            args = args[1:]
        return {key: _assert_not_none(key, spec.annotations.get(key)) for key in args}

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self._name}: {self._type.__name__}'

    def __eq__(self, other):
        if isinstance(other, ObjectDescriptor):
            return self._factory == other._factory and \
                   self._type == other._type and \
                   self._deps == other._deps
        else:
            return NotImplemented

    @property
    def object_type(self):
        return self._type

    @property
    def dependencies(self):
        return self._deps


def _assert_not_none(name, obj):
    if obj is None:
        raise TypeError(name)
    else:
        return obj


class _DependencyChecker:
    def __init__(self, map: typing.Dict[str, ObjectDescriptor]):
        self._map = map
        self._clean = []

    def check(self):
        for name, descr in self._map.items():
            self.check_defs(name, descr)

        for name in self._map.keys():
            self.check_cycles(name, [])

    def check_defs(self, name: str, descr: ObjectDescriptor):
        for dep_name, dep_type in descr.dependencies.items():
            if dep_name not in self._map.keys():
                raise ValueError(f'Unresolved dependency of {name} => {dep_name}: {dep_type}')
            if dep_type is not self._map[dep_name].object_type:
                raise ValueError(
                    f'{descr._name}: {descr._type.__name__} has dependency {dep_name}: {dep_type.__name__}, but {dep_name} of type {self._map[dep_name].object_type.__name__}')

    def check_cycles(self, name: str, stack: typing.List[str]) -> None:
        """
        :param name:
        :param stack: reverse dependencies excluding the current one
        """
        if name in stack:
            raise ValueError(f'{name} depends on itself. Dependency path: {stack + [name]}')

        for dep_name in self._map[name].dependencies:
            self.check_cycles(dep_name, stack + [name])


class PytelContext:
    def __init__(self, d: typing.Dict[str, ObjectDescriptor]):
        self._objects = d

    def get(self, name: str):
        descr = self._objects[name]
        if descr._instance is None:
            descr._instance = self._resolve(name)
        return descr._instance

    def _resolve(self, name: str):
        descr = self._objects[name]
        assert descr._instance is None, "called resolve on resolved object"

        resolved_deps = {dep_name: self.get(dep_name) for dep_name in descr.dependencies.keys()}
        return descr._factory(**resolved_deps)

    def keys(self):
        return self._objects.keys()

    def items(self):
        return self._objects.items()
