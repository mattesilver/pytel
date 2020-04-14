import collections
import contextlib
import logging
import typing

from .context import ObjectDescriptor, to_factory_map

log = logging.getLogger(__name__)


class Pytel:
    def __init__(
            self,
            configurers: typing.Union[object, typing.Iterable[object]],
            parent: typing.Optional['Pytel'] = None,
    ):

        if configurers is None:
            raise ValueError('configurers is None')

        self._parent = parent
        self._objects: typing.Dict[str, ObjectDescriptor] = {}
        self._exit_stack = contextlib.ExitStack()

        if isinstance(configurers, typing.Mapping):
            configurers = [configurers]
        elif configurers is not None and not isinstance(configurers, typing.Iterable):
            configurers = [configurers]

        for configurer in configurers:
            self._do_configure(configurer)

        if not self._objects.items():
            log.warning('Empty context')

        all_objects = self._get_all_objects()
        self._check(all_objects)
        self._resolve_all(all_objects)

    def _do_configure(self, configurer):
        m = to_factory_map(configurer)

        if not self._objects.keys().isdisjoint(m.keys()):
            raise KeyError("Duplicate names", list(set(self._objects.keys()).intersection(m.keys())))

        update = {name: ObjectDescriptor.from_(name, fact) for name, fact in m.items()}
        self._objects.update(update)

    def _get(self, name: str):
        if name in self._objects.keys():
            return self._objects[name].instance
        elif self._parent is not None:
            return self._parent._get(name)
        else:
            raise KeyError(name)

    def _resolve_all(self, all_objects) -> None:
        def resolver(name, typ):
            descriptor = all_objects[name]
            assert issubclass(descriptor.object_type, typ)
            return descriptor

        for value in self._objects.values():
            value.resolve_dependencies(resolver, self._exit_stack)

    def keys(self):
        return self._objects.keys()

    def items(self):
        return self._objects.items()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit_stack.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        return self._exit_stack.close()

    def __getattr__(self, name: str):
        try:
            return self._get(name)
        except KeyError as e:
            raise AttributeError(name) from e

    def __len__(self):
        return len(self._objects)

    def __contains__(self, item):
        return item in self._objects

    def _get_all_objects(self):
        p = self
        result = [self._objects]

        while p._parent is not None:
            p = p._parent
            result.append(p._objects)
        return collections.ChainMap(*result)

    def _check(self, all_objects):
        def check_defs(descr: ObjectDescriptor, all: typing.Mapping[str, ObjectDescriptor]):
            for dep_name, dep_type in descr.dependencies.items():
                if dep_name not in all.keys():
                    raise ValueError(f'Unresolved dependency of {descr.name} => {dep_name}: {dep_type}')
                if not issubclass(all[dep_name].object_type, dep_type):
                    raise ValueError(
                        f'{descr.name}: {descr.object_type.__name__} has dependency {dep_name}: {dep_type.__name__},'
                        f' but {dep_name} is type {all[dep_name].object_type.__name__}')

        for descr in self._objects.values():
            check_defs(descr, all_objects)

        for descr in self._objects.values():
            self._check_cycles(descr)

    def _check_cycles(
            self,
            descr: ObjectDescriptor,
            stack: typing.Optional[typing.List[str]] = None,
            clean: typing.Optional[typing.List[str]] = None,
    ) -> None:
        """
        :param descr:
        :param stack: reverse dependency path (excluding the current descriptor)
        :param clean:
        """

        if stack is None:
            stack = []
            clean = []

        if descr.name in stack:
            raise ValueError(f'{descr.name} depends on itself. Dependency path: {stack + [descr.name]}')

        for dep_name in descr.dependencies.keys():
            if dep_name not in clean and dep_name in self._objects.keys():
                self._check_cycles(self._objects[dep_name], stack + [descr.name], clean)

        clean.append(descr.name)
