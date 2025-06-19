
from pathlib import Path

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .quick_dem_for_jp_algorithm import QuickDEMforJPProcessingAlgorithm


class MieruneProvider(QgsProcessingProvider):
    def __init__(self):
        QgsProcessingProvider.__init__(self)

        # Deactivate provider by default
        self.activate = False
        self.alglist = []
    
    def alg_list(self, algs):
        self.alglist = algs

    def loadAlgorithms(self, *args, **kwargs):
        # self.addAlgorithm(QuickDEMforJPProcessingAlgorithm())
        for alg in self.alglist:
            self.addAlgorithm(alg)

    def id(self, *args, **kwargs):
        return 'mierune'

    def name(self, *args, **kwargs):
        return self.tr('MIERUNE')

    def icon(self):
        path = (Path(__file__).parent / "../imgs/mierune_icon.png").resolve()
        return QIcon(str(path))
    
    def load(self):
        self.refreshAlgorithms()
        return True
    