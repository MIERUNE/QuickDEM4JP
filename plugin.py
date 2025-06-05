
import contextlib

from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QAction, QToolButton

from .processing_provider.quick_dem_for_jp_provider import QuickDEMforJPProvider

from processing import execAlgorithmDialog

class QuickDEMforJP:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
    
    def initProcessing(self):
        self.provider = QuickDEMforJPProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
	
    def initGui(self):
        self.initProcessing()
        self.setup_algorithms_tool_button()
	
    def unload(self):
        if hasattr(self, "toolButtonAction"):
            self.teardown_algorithms_tool_button()

        if hasattr(self, "provider"):
            QgsApplication.processingRegistry().removeProvider(self.provider)
            del self.provider
            
    def setup_algorithms_tool_button(self):
        if hasattr(self, "toolButtonAction"):
            return  # すでに追加済みなら何もしない

        tool_button = QToolButton()
        icon = self.provider.icon()
        default_action = QAction(icon, "Quick DEM for JP", self.iface.mainWindow())
        default_action.triggered.connect(
            lambda: execAlgorithmDialog("quickdemforjp:quickdemforjp", {})
        )
        tool_button.setDefaultAction(default_action)

        self.toolButtonAction = self.iface.addToolBarWidget(tool_button)

    def teardown_algorithms_tool_button(self):
        if hasattr(self, "toolButtonAction"):
            self.iface.removeToolBarIcon(self.toolButtonAction)
            del self.toolButtonAction

