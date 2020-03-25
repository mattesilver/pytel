import inspect
import logging
from typing import Optional, Type, TypeVar, Union, Callable, Generic, List, Dict, Iterable

log = logging.getLogger(__name__)

T = TypeVar('T')
FactoryType = Union[T, Callable[..., T]]
_K_RETURN = 'return'


class ObjectDescriptor(Generic[T]):
    def __init__(self, factory: Optional[FactoryType],
                 _type: Type[T],
                 deps: Dict[str, Type]
                 ):
        self._factory = factory
        self._type = _type
        self._deps = deps
        self._instance: Optional[T] = None

    @classmethod
    def from_(cls, obj) -> 'ObjectDescriptor':
        if obj is None:
            raise ValueError(None)
        elif isinstance(obj, staticmethod):
            return ObjectDescriptor.from_callable(obj.__func__)
        elif isinstance(obj, type) or callable(obj):
            return ObjectDescriptor.from_callable(obj)
        else:
            return ObjectDescriptor.from_object(obj)

    @classmethod
    def from_callable(cls, factory: FactoryType) -> 'ObjectDescriptor':
        assert factory is not None
        spec = inspect.getfullargspec(factory)
        if isinstance(factory, type):
            t = factory
        else:
            if _K_RETURN in spec.annotations:
                t = spec.annotations[_K_RETURN]
                if t is None:
                    raise TypeError('Callable type hint is None', factory)
            else:
                raise TypeError('None type')

        try:
            deps = ObjectDescriptor._spec_to_deps(spec)
        except ValueError as e:
            raise ValueError(str(factory)) from e

        log.debug("Dependencies for %s: %s", factory.__qualname__, deps)
        return ObjectDescriptor(factory, t, deps)

    @classmethod
    def from_staticmethod(cls, creator, value: staticmethod) -> 'ObjectDescriptor':
        pass

    @classmethod
    def from_object(cls, value: object) -> 'ObjectDescriptor':
        assert value is not None
        result = ObjectDescriptor(None, type(value), {})
        result._instance = value
        return result

    @staticmethod
    def _spec_to_deps(spec: inspect.FullArgSpec) -> Dict[str, Type]:
        args = spec.args.copy()
        if len(args) > 0 and args[0] == 'self':
            args = args[1:]
        return {key: _assert_not_none(key, spec.annotations.get(key)) for key in args}

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def __eq__(self, other):
        if isinstance(other, ObjectDescriptor):
            return self._factory == other._factory and \
                   self._type == other._type and \
                   self._deps == other._deps
        else:
            raise NotImplemented

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
    def __init__(self, map: Dict[str, ObjectDescriptor]):
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
                raise ValueError(f'Undefined dependency of {name}: {dep_name}')
            if dep_type is not self._map[dep_name].object_type:
                raise ValueError(
                    f'Expectied {dep_name}:{dep_type}, but found {self._map[dep_name].object_type}')

    def check_cycles(self, name: str, stack: List[str]) -> None:
        """
        :param name:
        :param stack: reverse dependencies excluding the current one
        """
        if name in stack:
            raise ValueError(f'{name} depends on itself. Dependency path: {stack + [name]}')

        for dep_name in self._map[name].dependencies:
            self.check_cycles(dep_name, stack + [name])


class ObjectWrapper:
    def __init__(self, descr: ObjectDescriptor, value=None):
        self.descr: ObjectDescriptor = descr
        self.value = value


class PytelContext:
    def __init__(self, d: Dict[str, ObjectDescriptor]):
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

    def find_one_by_type(self, cls: Type[T]) -> T:
        candidates = list(self.find_all_by_type(cls))
        if len(candidates) != 1:
            raise ValueError('Could not find single instance of ', cls, len(candidates))
        else:
            return candidates[0]

    def find_all_by_type(self, cls: Type[T]) -> Iterable[T]:
        return (self.get(name) for name, descr in self._objects.items() if isinstance(descr.object_type, cls))

    def keys(self):
        return self._objects.keys()

    def items(self):
        return self._objects.items()
