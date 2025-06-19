
import contextlib

from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QAction, QToolButton

from .processing_provider.quick_dem_for_jp_provider import MieruneProvider
from .processing_provider.quick_dem_for_jp_algorithm import QuickDEMforJPProcessingAlgorithm

from processing import execAlgorithmDialog

class QuickDEMforJP:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
    
    def initProcessing(self):
        processing_registry = QgsApplication.processingRegistry()
        self.provider = processing_registry.providerById("mierune")
        if not self.provider:
            self.provider = MieruneProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

        self.algorithm = QuickDEMforJPProcessingAlgorithm()
        if not self.provider.algorithm("quickdemforjp"):
            self.provider.addAlgorithm(self.algorithm)

    def initGui(self):
        self.initProcessing()
        self.setup_algorithms_tool_button()
	
    def unload(self):
        if hasattr(self, "toolButtonAction"):
            self.teardown_algorithms_tool_button()

        if hasattr(self, "provider"):
            self.provider.refreshAlgorithms()
            QgsApplication.processingRegistry().removeProvider(self.provider)
            del self.provider
            
    def setup_algorithms_tool_button(self):
        if hasattr(self, "toolButtonAction"):
            return  # すでに追加済みなら何もしない

        tool_button = QToolButton()
        icon = self.algorithm.icon()
        default_action = QAction(icon, "Quick DEM for JP", self.iface.mainWindow())
        default_action.triggered.connect(
            lambda: execAlgorithmDialog("mierune:quickdemforjp", {})
        )
        tool_button.setDefaultAction(default_action)

        self.toolButtonAction = self.iface.addToolBarWidget(tool_button)

    def teardown_algorithms_tool_button(self):
        if hasattr(self, "toolButtonAction"):
            self.iface.removeToolBarIcon(self.toolButtonAction)
            del self.toolButtonAction

