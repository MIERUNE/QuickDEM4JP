from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QIcon


def test_registered(qgis_app: QgsApplication, provider: str):
    registory = QgsApplication.processingRegistry()
    provider = registory.providerById("quickdemforjp")
    assert provider is not None
    assert len(provider.name()) > 0
    assert isinstance(provider.icon(), QIcon)

    alg = registory.algorithmById("quickdemforjp:quickdemforjp")
    assert alg is not None
    assert alg.group() is None
    assert alg.groupId() is None
    assert isinstance(alg.displayName(), str)
    assert isinstance(alg.shortHelpString(), str)
