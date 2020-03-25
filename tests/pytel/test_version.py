from pathlib import Path
from unittest import TestCase

import toml

from pytel import __version__


def get_project_version():
    return toml.load(Path(__file__).parent / '../../pyproject.toml')['tool']['poetry']['version']


class ModuleTest(TestCase):
    def test_version_matches(self):
        self.assertEqual(get_project_version(), __version__)
