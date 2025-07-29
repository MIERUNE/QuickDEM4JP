import contextlib
import os

from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QAction, QToolButton
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator

from .processing_provider.quick_dem_for_jp_provider import QuickDEMforJPProvider

from processing import execAlgorithmDialog


class QuickDEMforJP:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.translator = None
        self.initTranslator()

    def initTranslator(self):
        locale = QSettings().value("locale/userLocale")

        if locale:
            locale = locale[0:2]
        else:
            locale = "en"

        locale_path = os.path.join(
            os.path.dirname(__file__), "i18n", f"QuickDEMforJP_{locale}.qm"
        )
        print(locale_path)
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            if self.translator.load(locale_path):
                QCoreApplication.installTranslator(self.translator)

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

    def tr(self, string):
        return QgsApplication.translate("QuickDEMforJPProcessingAlgorithm", string)
