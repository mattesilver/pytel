from unittest import TestCase

import toml

from pytel import __version__


class ModuleTest(TestCase):
    def get_project_version(self):
        return toml.load('pyproject.toml')['tool']['poetry']['version']

    def test_version_matches(self):
        self.assertEqual(self.get_project_version(), __version__)
