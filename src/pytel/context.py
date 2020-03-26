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
        self._resolved_deps = None
        self._instance: typing.Optional[T] = None

    def _resolve(self) -> T:
        assert self._instance is None, 'Called factory on resolved object'

        deps = {name: descr.instance for name, descr in self._resolved_deps.items()}
        self._instance = self._factory(**deps)
        if self._instance is None:
            raise ValueError(self._name, 'Factory returned None')
        return self._instance

    def resolve_dependencies(self, resolver: typing.Callable[[str, typing.Type], 'ObjectDescriptor']):
        self._resolved_deps = {name: resolver(name, typ) for name, typ in self._deps.items()}

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

        deps = spec_to_types(spec)

        log.debug("Dependencies for %s: %s", factory.__qualname__, deps)
        return ObjectDescriptor(factory, name, t, deps)

    @classmethod
    def from_object(cls, name, value: object) -> 'ObjectDescriptor':
        assert value is not None, f'{name} is None'
        result = ObjectDescriptor(None, name, type(value), {})
        result._instance = value
        return result

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
    def object_type(self) -> typing.Type[T]:
        return self._type

    @property
    def dependencies(self):
        return self._deps

    @property
    def instance(self) -> T:
        return self._instance \
            if self._instance \
            else self._resolve()


def spec_to_types(spec: inspect.FullArgSpec) -> typing.Dict[str, typing.Type]:
    args = spec.args.copy()
    if len(args) > 0 and args[0] == 'self':
        args = args[1:]
    return {key: _assert_not_none(key, spec.annotations.get(key)) for key in args}


def _assert_not_none(name, obj):
    if obj is None:
        raise TypeError(name, None)
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
                    f'{descr._name}: {descr._type.__name__} has dependency {dep_name}: {dep_type.__name__},'
                    f' but {dep_name} is type {self._map[dep_name].object_type.__name__}')

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
    def __init__(self, configurers: typing.Union[object, typing.Iterable[object]]):
        self._objects = {}

        if isinstance(configurers, typing.Mapping):
            configurers = [configurers]
        elif not isinstance(configurers, typing.Iterable):
            configurers = [configurers]

        for configurer in configurers:
            self._do_configure(configurer)

        _DependencyChecker(self._objects).check()
        self._resolve_all()

    def _do_configure(self, configurer):
        m = to_factory_map(configurer)

        if not self._objects.keys().isdisjoint(m.keys()):
            raise KeyError("Duplicate names", list(set(self._objects.keys()).intersection(m.keys())))

        update = {name: ObjectDescriptor.from_(name, fact) for name, fact in m.items()}
        self._objects.update(update)

    def get(self, name: str):
        descriptor = self._objects[name]
        return descriptor.instance

    def _resolve_all(self) -> None:
        def resolver(name, typ):
            descriptor = self._objects[name]
            assert issubclass(descriptor.object_type, typ)
            return descriptor

        for value in self._objects.values():
            value.resolve_dependencies(resolver)

    def keys(self):
        return self._objects.keys()

    def items(self):
        return self._objects.items()


def _is_dunder(name):
    return name.startswith('__') and name.endswith('__')


def to_factory_map(configurer) -> typing.Mapping[str, object]:
    if isinstance(configurer, typing.Mapping):
        return configurer
    else:
        return services_from_object(configurer)


def services_from_object(configurer: object) -> typing.Dict[str, object]:
    return {name: getattr(configurer, name)
            for name in dir(configurer)
            if not _is_dunder(name)
            }
