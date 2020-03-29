import contextlib
import logging
import typing

from .context import _DependencyChecker, ObjectDescriptor, to_factory_map

log = logging.getLogger(__name__)


class Pytel:
    def __init__(self, configurers: typing.Union[object, typing.Iterable[object]]):
        if configurers is None:
            raise ValueError('configurers is None')

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

        _DependencyChecker(self._objects).check()
        self._resolve_all()

    def _do_configure(self, configurer):
        m = to_factory_map(configurer)

        if not self._objects.keys().isdisjoint(m.keys()):
            raise KeyError("Duplicate names", list(set(self._objects.keys()).intersection(m.keys())))

        update = {name: ObjectDescriptor.from_(name, fact) for name, fact in m.items()}
        self._objects.update(update)

    def _get(self, name: str):
        return self._objects[name].instance

    def _resolve_all(self) -> None:
        def resolver(name, typ):
            descriptor = self._objects[name]
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
