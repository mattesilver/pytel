import typing

__version__ = '0.1.0'

from .pytel import Pytel

T = typing.TypeVar('T')

lazy: typing.Callable[[T], T] = pytel.TypeWrapper

func = pytel.FunctionWrapper
