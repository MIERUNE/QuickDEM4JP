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

        # 選択したCSRの識別子を取得
        # import_crs = self.dlg.mQgsProjectionSelectionWidget_1.crs().authid()
        output_crs = self.dlg.mQgsProjectionSelectionWidget.crs().authid()

        file_name_list = self.file_name_list_from_dir_path()
        mesh_cord_list = self.get_mesh_cord(file_name_list)
        meta_data_list = self.get_metadata_list(file_name_list)
        contents_list = self.get_contents_list(file_name_list)
        lower_and_upper_latlon_list = self.find_lower_and_upper_latlon_from_all_xmls(meta_data_list)
        
        pixel_size_x = meta_data_list[0]['pixel_size']['x']
        pixel_size_y = meta_data_list[0]['pixel_size']['y']

        gridcell_size_list = self.cal_gridcell_size_of_xml(pixel_size_x,
                             pixel_size_y, lower_and_upper_latlon_list)

        large_mesh_contents_list = self.find_coordinates_in_the_large_mesh(
                                    gridcell_size_list,
                                    lower_and_upper_latlon_list,
                                    meta_data_list,
                                    contents_list
                                )
        
        # self.resampling('EPSG:4326', 'EPSG:2454')
        self.resampling('EPSG:4326', output_crs)

        merge_layer = QgsRasterLayer(os.path.join(self.geotiff_output_path, 'merge.tif'), 'merge')
        warp_layer = QgsRasterLayer(os.path.join(self.geotiff_output_path, 'warp.tif'), 'warp')

        QgsProject.instance().addMapLayer(merge_layer)
        QgsProject.instance().addMapLayer(warp_layer)

        return True

    # キャンセルクリック
    def dlg_cancel(self):
        # ダイアログを非表示
        self.dlg.hide()

    # file_name_listを作成
    def file_name_list_from_dir_path(self):
        file_name_list = []

        for x in glob(os.path.join(self.import_path, '*')):
            if not x.find('.xml') == -1:
                file_name_list.append(os.path.relpath(x, self.import_path))
            else:
                print('{}はXMLではありません。passします。\n'.format(x))
                continue

        return file_name_list

    # ディレクトリ内のxmlからメッシュコードやメタデータの辞書を取得し
    def get_metadata(self, file_name):
        xml_path = os.path.join(self.import_path, file_name)

        meta_data = {}
        
        with open(xml_path, 'r', encoding='utf8') as x:
            # メッシュコードを格納
            r = re.compile('<mesh>(.+)</mesh>')
            for x_line in x:
                m = r.search(x_line)
                if m is not None:
                    meta_data['mesh_cord'] = int(m.group(1))
                    break
            
            if meta_data == {}:
                raise Exception('{}はDEMではありません。処理を終了します。\n'.format(xml_path))

            # メッシュの左下の座標を格納
            r = re.compile('<gml:lowerCorner>(.+) (.+)</gml:lowerCorner>')
            for x_line in x:
                m = r.search(x_line)
                if m is not None:
                    lower_corner = {}

                    lower_corner['lat'] = float(m.group(1))
                    lower_corner['lon'] = float(m.group(2))

                    meta_data['lower_corner'] = lower_corner
                    break

            # メッシュの右上の座標を格納
            r = re.compile("<gml:upperCorner>(.+) (.+)</gml:upperCorner>")
            for x_line in x:
                m = r.search(x_line)
                if m is not None:
                    upper_corner = {}

                    upper_corner['lat']  = float(m.group(1))
                    upper_corner['lon'] = float(m.group(2))

                    meta_data['upper_corner'] = upper_corner
                    break

            # グリッド数を格納
            r = re.compile("<gml:high>(.+) (.+)</gml:high>")
            for x_line in x:
                m = r.search(x_line)
                if m is not None:
                    grid_length = {}

                    grid_length['x'] = int(m.group(1)) + 1
                    grid_length['y'] = int(m.group(2)) + 1

                    meta_data['grid_length'] = grid_length
                    break

            # スタートポジションを格納
            r = re.compile("<gml:startPoint>(.+) (.+)</gml:startPoint>")
            for x_line in x:
                m = r.search(x_line)
                if m is not None:
                    start_point = {}

                    start_point['x'] = int(m.group(1))
                    start_point['y']  = int(m.group(2))

                    meta_data['start_point'] = start_point
                    break

        upper_corner_lon = meta_data['upper_corner']['lon']
        lower_corner_lon = meta_data['lower_corner']['lon']
        xlen = meta_data['grid_length']['x']
        lower_corner_lat = meta_data['lower_corner']['lat']
        upper_corner_lat = meta_data['upper_corner']['lat']
        ylen = meta_data['grid_length']['y']

        # セルのサイズを算出
        # 右上から左下の緯度経度を引いてグリッドセルの配列数で割って1ピクセルのサイズを出す
        pixel_size = {}

        pixel_size['x'] = (upper_corner_lon - lower_corner_lon) / xlen
        pixel_size['y'] = (lower_corner_lat - upper_corner_lat) / ylen

        meta_data['pixel_size'] = pixel_size

        return meta_data

    # メタデータのリストを作成
    def get_metadata_list(self, file_name_list):
        mesh_metadata_list = []

        for file_name in file_name_list:
            metadata = self.get_metadata(file_name)
            mesh_metadata_list.append(metadata)
        
        return mesh_metadata_list
    
    # ディレクトリ内のxmlから標高値を取得し標高値のnarrayを返す
    def get_contents(self, file_name):
        contents = {}
        xml_path = os.path.join(self.import_path, file_name)

        meta_data = self.get_metadata(file_name)

        with open(xml_path, 'r', encoding='utf8') as x:
            # メッシュコードを取得
            for x_line in x:
                r = re.compile('<mesh>(.+)</mesh>')
                m = r.search(x_line)
                if m is not None:
                    mesh_cord = int(m.group(1))
                    break

            src_document = x.read()
            lines = src_document.split("\n")
            number_of_lines = len(lines)
            l1 = None
            l2 = None
            # 標高地のデータが出現するまでの行数を数える
            for n in range(number_of_lines):
                if lines[n].find("<gml:tupleList>") != -1:
                    l1 = n + 1
                    break
            # 標高地のデータが何行目で終わるか数える
            for n in range(number_of_lines - 1, -1, -1):
                if lines[n].find("</gml:tupleList>") != -1:
                    l2 = n - 1
                    break

        xlen = meta_data['grid_length']['x']
        ylen = meta_data['grid_length']['y']

        # 標高地を保存するための二次元配列を作成
        narray = np.empty((ylen, xlen), np.float32)
        # nodata(-9999)で初期化
        narray.fill(-9999)

        # 配列に入るデータ数を確認
        num_tuples = l2 - l1 + 1

        # スタートポジションを算出
        start_point_x = meta_data['start_point']['x']
        start_point_y = meta_data['start_point']['y']

        i = 0

        # 標高を格納
        # データの並びは北西端から南東端に向かっているので行毎に座標を配列に入れていく
        for y in range(start_point_y, ylen):
            for x in range(start_point_x, xlen):
                if i < num_tuples:
                    vals = lines[i + l1].split(",")
                    if len(vals) == 2:
                        narray[y][x] = float(vals[1])
                    i += 1
                else:
                    break

            if i == num_tuples:
                break
            # 次行の処理に移行する前にxtart_point_xは0で初期化
            start_point_x = 0

        contents['mesh_cord'] = mesh_cord
        contents['narray'] = narray
        
        return contents

    # 標高値のリストを作成
    def get_contents_list(self, file_name_list):
        mesh_contents_list = []

        for file_name in file_name_list:
            contents = self.get_contents(file_name)
            mesh_contents_list.append(contents)
        
        return mesh_contents_list

    # メタデータとコンテンツが与えられたらメッシュコードが同じなら結合
    def combine_data(self, meta_data_list, contents_list):
        mesh_data_list = []

        # 辞書のリストをメッシュコードをKeyにしてソート
        sort_metadata_list = sorted(meta_data_list, key=lambda x:x['mesh_cord'])
        sort_contents_list = sorted(contents_list, key=lambda x:x['mesh_cord'])
        # メタデータとコンテンツを結合
        for m, c in zip(sort_metadata_list, sort_contents_list):
            m.update(c)
            mesh_data_list.append(m)

        return mesh_data_list

    # メッシュコードをリスト化
    # 2次メッシュと3次メッシュが混合していたらエラーを吐く
    def get_mesh_cord(self, file_name_list):
        third_mesh_cord_list = []
        second_mesh_cord_list = []
        
        for file_name in file_name_list:
            mesh_cord = self.get_metadata(file_name)['mesh_cord']
            s_mesh = str(mesh_cord)
            if len(s_mesh) == 6:
                second_mesh_cord_list.append(mesh_cord)
            elif len(s_mesh) == 8:
                third_mesh_cord_list.append(mesh_cord)

        if third_mesh_cord_list != [] and second_mesh_cord_list != []:
            raise Exception('2次メッシュと3次メッシュが混合しています。')

        elif third_mesh_cord_list == []:
            second_mesh_cord_list.sort()
            return second_mesh_cord_list
        else:
            third_mesh_cord_list.sort()
            return third_mesh_cord_list

    # 複数のxmlを比較して左下と右上の緯度経度を見つける
    def find_lower_and_upper_latlon_from_all_xmls(self, meta_data_list):
        lower_left_lat_min = []
        lower_left_lon_min = []
        upper_right_lat_max = []
        upper_right_lon_max = []

        for meta_data in meta_data_list:
            lower_left_lat = meta_data['lower_corner']['lat']
            lower_left_lon = meta_data['lower_corner']['lon']
            upper_right_lat = meta_data['upper_corner']['lat']
            upper_right_lon = meta_data['upper_corner']['lon']

            lower_left_lat_min.append(lower_left_lat)
            lower_left_lon_min.append(lower_left_lon)
            upper_right_lat_max.append(upper_right_lat)
            upper_right_lon_max.append(upper_right_lon)
        
        return [min(lower_left_lat_min), min(lower_left_lon_min),\
                max(upper_right_lat_max), max(upper_right_lon_max)]

    # 全xmlの座標を参照して画像の大きさを算出する
    def cal_gridcell_size_of_xml(self, pixel_size_x, pixel_size_y, lower_and_upper_latlon_list):
        lower_left_lat = lower_and_upper_latlon_list[0]
        lower_left_lon = lower_and_upper_latlon_list[1]
        upper_right_lat = lower_and_upper_latlon_list[2]
        upper_right_lon = lower_and_upper_latlon_list[3]

        xlen = round(abs((upper_right_lon - lower_left_lon) / pixel_size_x))
        ylen = round(abs((upper_right_lat - lower_left_lat) / pixel_size_y))
        
        return xlen, ylen

    # アレイと座標、ピクセルサイズ、グリッドサイズからGeoTiffを作成
    def write_geotiff(self, narray, lower_left_lon, upper_right_lat, pixel_size_x, pixel_size_y, xlen, ylen):
        # 「左上経度・東西解像度・回転（０で南北方向）・左上緯度・回転（０で南北方向）・南北解像度（北南方向であれば負）」
        geotransform = [lower_left_lon,
                        pixel_size_x,
                        0,
                        upper_right_lat,
                        0,
                        pixel_size_y]

        merge_tiff_file = 'merge.tif'
        tiffFile = os.path.join(self.geotiff_output_path, merge_tiff_file)

        # ドライバーの作成
        driver = gdal.GetDriverByName("GTiff")
        # ドライバーに対して「保存するファイルのパス・グリットセル数・バンド数・ラスターの種類・ドライバー固有のオプション」を指定してファイルを作成
        dst_ds = driver.Create(tiffFile, xlen, ylen, 1, gdal.GDT_Float32)
        # geotransformをセット
        dst_ds.SetGeoTransform(geotransform)

        # 作成したラスターの第一バンドを取得
        rband = dst_ds.GetRasterBand(1)
        # 第一バンドにアレイをセット
        rband.WriteArray(narray)
        # nodataの設定
        rband.SetNoDataValue(-9999)

        # EPSGコードを引数にとる前処理？
        ref = osr.SpatialReference()
        # EPSGコードを引数にとる
        ref.ImportFromEPSG(4326)
        # ラスターに投影法の情報を入れる
        dst_ds.SetProjection(ref.ExportToWkt())

        # ディスクへの書き出し
        dst_ds.FlushCache()

    # 再投影
    # 元画像のEPSGとwarp先のEPSGを引数にとる
    def resampling(self, srcSRS, outputSRS):
        warp_path = os.path.join(self.geotiff_output_path, 'warp.tif')
        src_path = os.path.join(self.geotiff_output_path, 'merge.tif')
        resampledRas = gdal.Warp(warp_path, src_path, srcSRS=srcSRS, dstSRS=outputSRS, resampleAlg="near")

        resampledRas.FlushCache()
        resampledRas = None

    # 大きな配列を作って、そこに標高値をどんどん入れていく
    def find_coordinates_in_the_large_mesh(self, gridcell_size_list, lower_and_upper_latlon_list, metadata_list, contents_list):
        # 全xmlを包括するグリッドセル数
        large_mesh_xlen = gridcell_size_list[0]
        large_mesh_ylen = gridcell_size_list[1]

        # 全xmlを包括する配列を作成
        # グリッドセルサイズが10000以上なら処理を終了
        if large_mesh_xlen >= 10000 or large_mesh_ylen >= 10000:
            raise Exception('セルサイズが大きすぎます')

        large_mesh_narray = np.empty((large_mesh_ylen, large_mesh_xlen), np.float32)
        large_mesh_narray.fill(-9999)

        # マージ用配列の左下の座標を取得
        large_mesh_lower_left_lat = lower_and_upper_latlon_list[0]
        large_mesh_lower_left_lon = lower_and_upper_latlon_list[1]
        # マージ用配列の右上の座標を取得
        large_mesh_upper_right_lat = lower_and_upper_latlon_list[2]
        large_mesh_upper_right_lon = lower_and_upper_latlon_list[3]

        # マージ用配列のピクセルサイズ算出
        large_mesh_pixel_size_x = (large_mesh_upper_right_lon\
                                 - large_mesh_lower_left_lon) / large_mesh_xlen
        large_mesh_pixel_size_y = (large_mesh_lower_left_lat\
                                 - large_mesh_upper_right_lat) / large_mesh_ylen  

        # メタデータと標高値を結合
        mesh_data_list = self.combine_data(metadata_list, contents_list)

        # メッシュのメッシュコードを取り出す
        for mesh_data in mesh_data_list:
            # データから標高値の配列を取得
            narray = mesh_data['narray']
            # グリッドセルサイズ
            xlen = mesh_data['grid_length']['x']
            ylen = mesh_data['grid_length']['y']
            # 読み込んだarrayの左下の座標を取得
            lower_left_lat = mesh_data['lower_corner']['lat']
            lower_left_lon = mesh_data['lower_corner']['lon']
            # (0, 0)からの距離を算出
            lat_distans = lower_left_lat - large_mesh_lower_left_lat
            lon_distans = lower_left_lon - large_mesh_lower_left_lon
            # numpy上の座標を取得(ピクセルサイズが少数のため誤差が出るから四捨五入)
            x_coordinate = round(lon_distans / large_mesh_pixel_size_x)
            y_coordinate = round(lat_distans / (-large_mesh_pixel_size_y))
            # スライスで指定する範囲を算出
            row_start = int(large_mesh_ylen - (y_coordinate + ylen))
            row_end = int(row_start + ylen)
            column_start = int(x_coordinate)
            column_end = int(column_start + xlen)
            # スライスで大きい配列に代入
            large_mesh_narray[row_start:row_end, column_start:column_end] = narray

        # アレイからGeoTiffを作成
        self.write_geotiff(large_mesh_narray, large_mesh_lower_left_lon,
                           large_mesh_upper_right_lat, large_mesh_pixel_size_x,
                           large_mesh_pixel_size_y, large_mesh_xlen, large_mesh_ylen)

        return large_mesh_narray