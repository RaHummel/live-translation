import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.version import _load_pyproject, get_app_version


class TestVersion(unittest.TestCase):
    def test_load_pyproject_returns_none_when_missing(self):
        result = _load_pyproject(Path('/tmp/does-not-exist-pyproject.toml'))
        self.assertIsNone(result)

    def test_load_pyproject_returns_none_on_invalid_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pyproject.toml'
            path.write_text('not = valid = toml = [', encoding='utf-8')

            result = _load_pyproject(path)

            self.assertIsNone(result)

    def test_load_pyproject_parses_valid_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pyproject.toml'
            path.write_text('[project]\nversion = "1.2.3"\n', encoding='utf-8')

            result = _load_pyproject(path)

            self.assertEqual(result['project']['version'], '1.2.3')

    def test_get_app_version_returns_actual_version(self):
        # Uses the real pyproject.toml of the project.
        version = get_app_version()
        self.assertNotEqual(version, 'unknown')
        self.assertRegex(version, r'^\d+\.\d+\.\d+')

    @patch('utils.version._load_pyproject', return_value=None)
    def test_get_app_version_returns_unknown_when_no_data(self, _mock_load):
        self.assertEqual(get_app_version(), 'unknown')

    @patch('utils.version._load_pyproject', return_value={'project': {}})
    def test_get_app_version_returns_unknown_when_no_version_key(self, _mock_load):
        self.assertEqual(get_app_version(), 'unknown')

    @patch('utils.version._load_pyproject', return_value={'other': {}})
    def test_get_app_version_returns_unknown_when_no_project_section(self, _mock_load):
        self.assertEqual(get_app_version(), 'unknown')

    @patch('utils.version.Path.resolve', side_effect=RuntimeError('boom'))
    def test_get_app_version_returns_unknown_on_error(self, _mock_resolve):
        self.assertEqual(get_app_version(), 'unknown')
