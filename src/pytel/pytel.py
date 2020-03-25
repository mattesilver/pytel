import logging
from typing import Dict, Any

from .context import PytelContext, ObjectDescriptor, _DependencyChecker

log = logging.getLogger(__name__)


class Pytel:
    def __init__(self, context: PytelContext = None):
        object.__setattr__(self, '_context', context)

    def __setattr__(self, name, value):
        self._context.set(name, value)

    def __setitem__(self, key, value):
        self._context.set(key, value)

    def __delattr__(self, item):
        self._context.delete(item)

    def __getattribute__(self, name: str):
        # __getattribute__ is required instead of __getattr__ to kidnap accessing the subclasses' methods
        if _is_special_name(name):
            return object.__getattribute__(self, name)

        try:
            return self._context.get(name)
        except KeyError as e:
            raise AttributeError(name) from e

    def __getitem__(self, item):
        return self._context.get(item)

    def __len__(self):
        return len(self._context.items())

    def __contains__(self, item):
        return item in self._context.keys()

    def __delitem__(self, key):
        self._context.delete(key)


def _is_special_name(name):
    return _is_dunder(name) or name in [
        '_context',
    ]


def _is_dunder(name):
    return name.startswith('__') and name.endswith('__')


class ContextCreator:
    def __init__(self, d: Dict[str, Any] = None):
        services = {}

        if d:
            services.update(d)

        services_from_sub = self._services_from_subclasses()
        if not services.keys().isdisjoint(services_from_sub.keys()):
            raise KeyError("Duplicate names", list(set(services.keys()).intersection(services_from_sub.keys())))
        services.update(services_from_sub)

        self._map: Dict[str, ObjectDescriptor] = {name: ObjectDescriptor.from_(fact) for name, fact in services.items()}

    def set(self, name: str, descriptor: ObjectDescriptor) -> None:
        if name in self._map:
            raise KeyError('Duplicate name', name)
        self._map[name] = descriptor

    def resolve(self) -> Pytel():
        _DependencyChecker(self._map).check()
        return Pytel(context=PytelContext(self._map))

    def _services_from_subclasses(self):
        services = {}
        for t in reversed(list(self._list_superclasses())):
            _services = {}
            for name, item in t.__dict__.items():
                if not _is_dunder(name):
                    _services[name] = item
            services.update(_services)
            # services.update({name: item for name, item in t.__dict__.items() if not _is_dunder(name)})
        return services

    def _list_superclasses(self):
        for t in type(self).__mro__:
            if t is ContextCreator:
                break
            else:
                yield t

