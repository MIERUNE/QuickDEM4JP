from pathlib import Path

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .quick_dem_for_jp_algorithm import QuickDEMforJPProcessingAlgorithm


class QuickDEMforJPProvider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(QuickDEMforJPProcessingAlgorithm())

    def id(self, *args, **kwargs):
        return "quickdemforjp"

    def name(self, *args, **kwargs):
        return self.tr("QuickDEM4JP")

    def icon(self):
        path = (Path(__file__).parent / "../icon.png").resolve()
        return QIcon(str(path))
