from typing import Iterable

import pytest
from qgis.gui import QgisInterface

from ..__init__ import classFactory


@pytest.fixture()
def plugin(qgis_iface: QgisInterface) -> Iterable[None]:
    _plugin = classFactory(qgis_iface)
    _plugin.initGui()

    yield _plugin

    # _plugin.unload() QgisInterface.removePluginMenu()がpytest-qgisで未実装
