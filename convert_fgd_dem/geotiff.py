from pathlib import Path

from osgeo import gdal, osr
from .helpers import warp


class Geotiff:
    """GeoTiffを生成するためのクラス"""

    def __init__(
            self,
            geo_transform,
            np_array,
            x_length,
            y_length,
            output_path):
        """イニシャライザ

        Args:
            geo_transform (list): GdalのDatasetクラスでSetGeoTransformするための情報
            np_array ():
            x_length (int):
            y_length (int):
            output_path (Path):

        Notes:
            geo_transformは以下のような情報
                geo_transform = [左上経度・東西解像度・回転（０で南北方向）・左上緯度・回転（０で南北方向）・南北解像度（北南方向であれば負）]
                                [lower_left_lon, pixel_size_x, 0, upper_right_lat, 0, pixel_size_y]

        """
        self.geo_transform = geo_transform
        self.np_array = np_array
        self.x_length = x_length
        self.y_length = y_length
        self.output_path: Path = output_path
        # TODO Noneよりディフォルトパス書いたほうがいいかな？
        self.created_tiff_path: Path = None

    def write_geotiff(self, file_name="output.tif", no_data_value=-9999):
        """標高と座標、ピクセルサイズ、グリッドサイズからGeoTiffを作成

        Args:
            file_name (str):
            no_data_value (int):

        """
        merge_tiff_file = file_name
        if not self.output_path.exists():
            self.output_path.mkdir()
        self.created_tiff_path = self.output_path / merge_tiff_file

        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.Create(
            str(self.created_tiff_path.resolve()),
            self.x_length,
            self.y_length,
            1,
            gdal.GDT_Float32,
        )
        dst_ds.SetGeoTransform(self.geo_transform)

        # 作成したラスターの第一バンドを取得し、numpyのarrayをセット
        r_band = dst_ds.GetRasterBand(1)
        r_band.WriteArray(self.np_array)
        r_band.SetNoDataValue(no_data_value)

        ref = osr.SpatialReference()
        ref.ImportFromEPSG(4326)
        dst_ds.SetProjection(ref.ExportToWkt())

        # ディスクへの書き出し
        dst_ds.FlushCache()

    def resampling(
            self,
            source_path=None,
            file_name="output.tif",
            epsg="EPSG:3857",
            no_data_value=0):
        """EPSG:4326のTiffから新たなGeoTiffを出力する

        Args:
            source_path (Path):
            file_name (str):
            epsg (str):
            no_data_value (int):

        """
        if source_path is None:
            source_path = self.created_tiff_path
        warp(
            source_path=source_path,
            file_name=file_name,
            epsg=epsg,
            output_path=self.output_path,
            no_data_value=no_data_value
        )
