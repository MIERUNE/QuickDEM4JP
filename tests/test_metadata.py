import configparser
import os
import unittest
from urllib.parse import urlparse

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestInit(unittest.TestCase):
    """Test that the plugin init is usable for QGIS.
    reference: https://github.com/felt/qgis-plugin/blob/main/felt/test/test_init.py
    """

    def _read_metadata(self):
        file_path = os.path.join(PLUGIN_DIR, "metadata.txt")
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(file_path)
        message = 'Cannot find a section named "general" in %s' % file_path
        self.assertTrue(parser.has_section("general"), message)
        return dict(parser.items("general"))

    def test_read_init(self):
        """Test that the plugin __init__ will validate on plugins.qgis.org."""

        # You should update this list according to the latest in
        # https://github.com/qgis/QGIS-Django/blob/master/qgis-app/
        #        plugins/validator.py (PLUGIN_REQUIRED_METADATA)

        required_metadata = [
            "name",
            "description",
            "version",
            "qgisMinimumVersion",
            "author",
            "email",
            "about",
            "tracker",
            "repository",
        ]

        metadata = self._read_metadata()
        for expectation in required_metadata:
            message = 'Cannot find metadata "%s" in metadata.txt.' % expectation
            self.assertIn(expectation, metadata, message)

    def test_urls_are_valid(self):
        """plugins.qgis.org rejects an upload with an invalid tracker, repository or homepage."""
        metadata = self._read_metadata()
        for key in ("tracker", "repository", "homepage"):
            if key not in metadata:
                continue
            parsed = urlparse(metadata[key])
            message = 'Invalid url for "%s": %s' % (key, metadata[key])
            self.assertTrue(parsed.scheme and parsed.netloc, message)

    def test_license_exists(self):
        """plugins.qgis.org requires a LICENSE file in the package."""
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN_DIR, "LICENSE")))


if __name__ == "__main__":
    unittest.main()
