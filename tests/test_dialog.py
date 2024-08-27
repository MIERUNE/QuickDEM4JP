from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from ..quick_dem_for_jp import QuickDEMforJP
from ..contents import Contents


def test_show_dialog(plugin: QuickDEMforJP):
    plugin.dialog_show()
    assert isinstance(plugin.contents, Contents)
