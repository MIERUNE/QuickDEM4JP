"""
Test Suite.
"""

import os
import sys
import unittest

from osgeo import gdal
from qgis.core import Qgis

__author__ = "Alessandro Pasotti"
__revision__ = "$Format:%H$"
__date__ = "30/04/2018"
__copyright__ = "Copyright 2018, North Road"


def _run_tests(test_suite, package_name):
    """Core function to test a test suite."""
    count = test_suite.countTestCases()
    print("########")
    print("%s tests has been discovered in %s" % (count, package_name))
    print("Python GDAL : %s" % gdal.VersionInfo("VERSION_NUM"))
    print("QGIS version : {}".format(Qgis.version()))
    print("########")
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(test_suite)


def test_package(package="plugin_dir"):
    """Test package.
    This function is called by travis without arguments.

    :param package: The package to test.
    :type package: str
    """
    test_loader = unittest.defaultTestLoader
    try:
        test_suite = test_loader.discover(package)
    except ImportError:
        test_suite = unittest.TestSuite()
    _run_tests(test_suite, package)


def test_environment():
    """Test package with an environment variable."""
    package = os.environ.get("TESTING_PACKAGE", "plugin_dir")
    test_loader = unittest.defaultTestLoader
    try:
        test_suite = test_loader.discover(package)
    except ImportError:
        test_suite = unittest.TestSuite()
    _run_tests(test_suite, package)


if __name__ == "__main__":
    test_package()
