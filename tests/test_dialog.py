from ..contents import Contents
from ..plugin import QuickDEMforJP


def test_show_dialog(plugin: QuickDEMforJP):
    plugin.dialog_show()
    assert isinstance(plugin.contents, Contents)
