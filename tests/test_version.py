from unittest import TestCase

from pytel import __version__


class ModuleTest(TestCase):
    def test_version(self):
        assert __version__ == '0.1.0'
