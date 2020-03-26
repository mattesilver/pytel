import logging

from .context import PytelContext, _is_dunder

log = logging.getLogger(__name__)


class Pytel:
    def __init__(self, context: PytelContext):
        if context is None:
            raise ValueError('Context is None')
        if not context.items():
            log.warning('Empty context')

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
