import shutil
import xml.etree.ElementTree as et
import zipfile
from pathlib import Path

import numpy as np


class Dem:
    """DEMのxmlからメタデータを取り出すクラス"""

    def __init__(self, import_path):
        """イニシャライザ

        Args:
            import_path (Path): 取り込み対象のパスオブジェクト

        Notes:
            「meta_data」とはDEMを構成する「メッシュコード・左下と右上の緯度経度・グリッドサイズ・初期位置・ピクセルサイズ」のことを指す
            「content」とはメッシュコード・メタデータ・標高値のことを指す

        """
        self.import_path: Path = import_path
        self.xml_paths: list = self._get_xml_paths()

        self.all_content_list: list = []
        self.mesh_code_list: list = []
        self.meta_data_list: list = []
        self.elevation_list: list = []
        self._get_xml_content_list()

        self.np_array_list: list = []
        self._store_np_array_list()

        self.bounds_latlng: dict = {}
        self._store_bounds_latlng()

    def _get_xml_paths(self):
        """指定したパスからxmlのPathオブジェクトのリストを作成

        Returns:
            list: xmlのパスを格納したリスト

        """
        if self.import_path.is_dir():
            xml_paths = [
                xml_path for xml_path in self.import_path.glob("*.xml")]
            if xml_paths is None:
                raise Exception("指定ディレクトリに.xmlが存在しません")

        elif self.import_path.suffix == ".xml":
            xml_paths = [self.import_path]

        elif self.import_path.suffix == ".zip":
            with zipfile.ZipFile(self.import_path, "r") as zip_data:
                zip_data.extractall(
                    path=self.import_path.parent
                )
                extract_dir = self.import_path.parent / self.import_path.stem
                xml_paths = [
                    xml_path for xml_path in extract_dir.glob("*.xml")]
                if not xml_paths:
                    raise Exception("指定のパスにxmlファイルが存在しません")
            garbage_dir = self.import_path.parent / "__MACOSX"
            if garbage_dir.exists():
                shutil.rmtree(garbage_dir)
        else:
            raise Exception(
                "指定できる形式は「xml」「.xmlが格納されたディレクトリ」「.xmlが格納された.zip」のみです")
        return xml_paths

    @staticmethod
    def _format_metadata(raw_metadata):
        """取得した生のメタデータを整形する

        Args:
            raw_metadata (dict): xmlから取得した生のメタデータが格納された辞書

        Returns:
            dict: 加工したメタデータを格納した辞書

        """
        lowers = raw_metadata["lower_corner"].split(" ")
        lower_corner = {"lat": float(lowers[0]), "lon": float(lowers[1])}

        uppers = raw_metadata["upper_corner"].split(" ")
        upper_corner = {"lat": float(uppers[0]), "lon": float(uppers[1])}

        grids = raw_metadata["grid_length"].split(" ")
        grid_length = {"x": int(grids[0]) + 1, "y": int(grids[1]) + 1}

        start_points = raw_metadata["start_point"].split(" ")
        start_point = {"x": int(start_points[0]), "y": int(start_points[1])}

        pixel_size = {
            "x": (
                upper_corner["lon"] -
                lower_corner["lon"]) /
            grid_length["x"],
            "y": (
                lower_corner["lat"] -
                upper_corner["lat"]) /
            grid_length["y"],
        }

        meta_data = {
            "mesh_code": raw_metadata["mesh_code"],
            "lower_corner": lower_corner,
            "upper_corner": upper_corner,
            "grid_length": grid_length,
            "start_point": start_point,
            "pixel_size": pixel_size,
        }

        return meta_data

    def get_xml_content(self, xml_path):
        """xmlを読み込んでメッシュコード・メタデータ・標高値を取得する

        Args:
            xml_path (Path):　xmlのパスオブジェクト

        Returns:
            dict: メッシュコード・メタデータ・標高値を格納した辞書

        """
        if not xml_path.suffix == ".xml":
            raise Exception("指定できる形式は.xmlのみです")

        name_space = {
            "dataset": "http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema",
            "gml": "http://www.opengis.net/gml/3.2",
        }

        tree = et.parse(xml_path)
        root = tree.getroot()

        mesh_code = int(
            root.find(
                "dataset:DEM//dataset:mesh",
                name_space).text)

        raw_metadata = {
            "mesh_code": mesh_code,
            "lower_corner": root.find(
                "dataset:DEM//dataset:coverage//gml:boundedBy//gml:Envelope//gml:lowerCorner",
                name_space,
            ).text,
            "upper_corner": root.find(
                "dataset:DEM//dataset:coverage//gml:boundedBy//gml:Envelope//gml:upperCorner",
                name_space,
            ).text,
            "grid_length": root.find(
                "dataset:DEM//dataset:coverage//gml:gridDomain//gml:Grid//gml:high",
                name_space,
            ).text,
            "start_point": root.find(
                "dataset:DEM//dataset:coverage//gml:coverageFunction//gml:GridFunction//gml:startPoint",
                name_space,
            ).text,
        }

        meta_data = self._format_metadata(raw_metadata)

        tuple_list = root.find(
            "dataset:DEM//dataset:coverage//gml:rangeSet//gml:DataBlock//gml:tupleList",
            name_space,
        ).text

        # gml:tupleList先頭の改行を削除したのち、[[地表面,354.15]...]のようなlistのlistを作成
        if tuple_list.startswith("\n"):
            strip_tuple_list = tuple_list.strip()
            items = [item.split(",")[1]
                     for item in strip_tuple_list.split("\n")]
        else:
            items = [item.split(",")[1] for item in tuple_list.split("\n")]

        elevation = {"mesh_code": mesh_code, "items": items}

        return {
            "mesh_code": mesh_code,
            "meta_data": meta_data,
            "elevation": elevation,
        }

    def _check_mesh_codes(self):
        """2次メッシュと3次メッシュの重複をチェックする

        Raises:
            - メッシュコードが6桁 or 8桁以外の場合はエラー
            - 2次メッシュと3次メッシュが混合している場合にエラー

        """
        third_mesh_codes = []
        second_mesh_codes = []

        for mesh_code in self.mesh_code_list:
            str_mesh = str(mesh_code)
            if len(str_mesh) == 6:
                second_mesh_codes.append(mesh_code)
            elif len(str_mesh) == 8:
                third_mesh_codes.append(mesh_code)
            else:
                raise Exception(f"メッシュコードが不正です。mesh_code={mesh_code}")

        # どちらもTrue、つまり要素が存在しているときにraise
        if all((third_mesh_codes, second_mesh_codes)):
            raise Exception("2次メッシュと3次メッシュが混合しています。")

    def _get_xml_content_list(self):
        """xmlのリストを読み込んでメタデータと標高値のリストを作成する"""
        self.all_content_list = [
            self.get_xml_content(xml_path) for xml_path in self.xml_paths
        ]

        self.mesh_code_list = [item["mesh_code"]
                               for item in self.all_content_list]
        self._check_mesh_codes()

        self.meta_data_list = [item["meta_data"]
                               for item in self.all_content_list]
        self.elevation_list = [item["elevation"]
                               for item in self.all_content_list]

    def _store_bounds_latlng(self):
        """対象の全Demから緯度経度の最大・最小値を取得"""
        lower_left_lat = min([meta_data["lower_corner"]["lat"]
                              for meta_data in self.meta_data_list])
        lower_left_lon = min([meta_data["lower_corner"]["lon"]
                              for meta_data in self.meta_data_list])
        upper_right_lat = max([meta_data["upper_corner"]["lat"]
                               for meta_data in self.meta_data_list])
        upper_right_lon = max([meta_data["upper_corner"]["lon"]
                               for meta_data in self.meta_data_list])

        bounds_latlng = {
            "lower_left": {"lat": lower_left_lat, "lon": lower_left_lon},
            "upper_right": {"lat": upper_right_lat, "lon": upper_right_lon},
        }

        self.bounds_latlng = bounds_latlng

    @staticmethod
    def _get_np_array(content):
        """Demから標高値を取得し、メッシュコードと標高値（np.array）を格納した辞書を返す

        Args:
            content(dict): DEMの詳細情報が格納された辞書

        Returns:
            dict: メッシュコードと標高値（np.array）を格納した辞書

        """
        mesh_code = content["mesh_code"]
        meta_data = content["meta_data"]
        elevation = content["elevation"]["items"]

        x_length = meta_data["grid_length"]["x"]
        y_length = meta_data["grid_length"]["y"]

        # 標高地を保存するための二次元配列を作成
        array = np.empty((y_length, x_length), np.float32)
        array.fill(-9999)

        start_point_x = meta_data["start_point"]["x"]
        start_point_y = meta_data["start_point"]["y"]

        # 標高を格納
        # データの並びは北西端から南東端に向かっているので行毎に座標を配列に入れていく
        index = 0
        for y in range(start_point_y, y_length):
            for x in range(start_point_x, x_length):
                try:
                    insert_value = float(elevation[index])
                    array[y][x] = insert_value
                # データの行数とグリッドのサイズは必ずしもピッタリ合うわけではないのでインデックスのサイズをはみ出したらループを停止
                except IndexError:
                    break
                index += 1
            start_point_x = 0

        np_array = {"mesh_code": mesh_code, "np_array": array}

        return np_array

    def _store_np_array_list(self):
        """Demからメッシュコードと標高値のnp.arrayを格納した辞書のリストを作成する"""
        self.np_array_list = [
            self._get_np_array(content) for content in self.all_content_list
        ]
