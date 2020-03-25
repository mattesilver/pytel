import logging
import typing

from .context import PytelContext, ObjectDescriptor, _DependencyChecker

log = logging.getLogger(__name__)


class Pytel:
    def __init__(self, context: PytelContext):
        object.__setattr__(self, '_context', context)

    def __getattribute__(self, name: str):
        # __getattribute__ is required instead of __getattr__ to kidnap accessing the subclasses' methods
        if _is_special_name(name):
            return object.__getattribute__(self, name)

        try:
            return self._context.get(name)
        except KeyError as e:
            raise AttributeError(name) from e

    def __len__(self):
        return len(self._context.items())

    def __contains__(self, item):
        return item in self._context.keys()


def _is_special_name(name):
    return _is_dunder(name) or name in [
        '_context',
    ]


def _is_dunder(name):
    return name.startswith('__') and name.endswith('__')


class ContextCreator:
    def __init__(self, configurers: typing.Union[object, typing.Iterable[object]]):
        self._map = {}

        if isinstance(configurers, typing.Mapping):
            configurers = [configurers]
        elif not isinstance(configurers, typing.Iterable):
            configurers = [configurers]

        self.configure(*configurers)

    def configure(self, *configurers):
        for configurer in configurers:
            self._do_configure(configurer)
        return self

    def _do_configure(self, configurer):
        m = ContextCreator._to_factory_map(configurer)

        if not self._map.keys().isdisjoint(m.keys()):
            raise KeyError("Duplicate names", list(set(self._map.keys()).intersection(m.keys())))

        update = {name: ObjectDescriptor.from_(name, fact) for name, fact in m.items()}
        self._map.update(update)

    def resolve(self) -> Pytel:
        _DependencyChecker(self._map).check()
        return Pytel(context=PytelContext(self._map))

    @staticmethod
    def _to_factory_map(configurer) -> typing.Mapping[str, callable]:
        if isinstance(configurer, typing.Mapping):
            return configurer
        else:
            return ContextCreator._services_from_object(configurer)

    @staticmethod
    def _services_from_object(configurer):
        return {name: getattr(configurer, name)
                for name in dir(configurer)
                if not _is_dunder(name)
                }
