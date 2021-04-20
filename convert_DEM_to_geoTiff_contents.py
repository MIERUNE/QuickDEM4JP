# coding=utf-8

import re
import numpy as np
from osgeo import gdal
import os
from glob import glob
from math import floor
import sys
import time
from osgeo import osr

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *

from .convert_dem_to_geotiff_dialog import ConvertDEMtoGeoTiffDialog
from .convert_fgd_dem.converter import Converter


class ConvertDEMtoGeotiffContents:
    # ダイアログの初期表示等の処理はここに記載する
    def __init__(self, iface):
        self.iface = iface
        self.dlg = ConvertDEMtoGeoTiffDialog()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # ダイアログのobject_nameに対してメソッドを指定。デフォルトのパスをセット
        self.dlg.mQgsFileWidget_1.setFilePath(self.current_dir)
        self.dlg.mQgsFileWidget_2.setFilePath(self.current_dir)

        # ディレクトリの指定が出来るようにする
        self.dlg.mQgsFileWidget_1.setStorageMode(QgsFileWidget.GetDirectory)
        self.dlg.mQgsFileWidget_2.setStorageMode(QgsFileWidget.GetDirectory)

        # ダイアログのボタンボックスがaccepted（OK）されたらdlg_add()が作動
        self.dlg.button_box.accepted.connect(self.convert_DEM)
        # ダイアログのボタンボックスがrejected（キャンセル）されたらdlg_cancel()が作動
        self.dlg.button_box.rejected.connect(self.dlg_cancel)

    # 処理を一括で行い、選択されたディレクトリに入っているxmlをGeoTiffにコンバートして指定したディレクトリに吐き出す
    def convert_DEM(self):
        # 選択したフォルダのパスを取得
        self.import_path = self.dlg.mQgsFileWidget_1.filePath()
        self.geotiff_output_path = self.dlg.mQgsFileWidget_2.filePath()

        converter = Converter(
            import_path=self.import_path,
            output_path=self.geotiff_output_path
        )
        converter.dem_to_geotiff()

        output_layer = QgsRasterLayer(os.path.join(self.geotiff_output_path, 'output.tif'), 'output')
        QgsProject.instance().addMapLayer(output_layer)

        return True

    # キャンセルクリック
    def dlg_cancel(self):
        # ダイアログを非表示
        self.dlg.hide()
