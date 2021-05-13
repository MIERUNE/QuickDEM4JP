from pathlib import Path

from osgeo import gdal, osr
import numpy as np

from .helpers import warp, convert_height_to_rgb


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

    def make_raster_bands(
        self,
        rgbify,
        band_count,
        dst_ds,
        no_data_value=-9999):
        """条件に応じてラスターのバンドを作成

        Args:
            rgbify (bool):
            band_count (int):
            dst_ds (gdalのドライバ):
            no_data_value (int):
        """
        if rgbify:
            r_arr, g_arr, b_arr = [], [], []
            for i in self.np_array:
                for j in i:
                    r_value, g_value, b_value = convert_height_to_rgb(j)
                    r_arr.append(r_value)
                    g_arr.append(g_value)
                    b_arr.append(b_value)
            r_arr = np.array(r_arr).reshape(self.y_length, self.x_length)
            g_arr = np.array(g_arr).reshape(self.y_length, self.x_length)
            b_arr = np.array(b_arr).reshape(self.y_length, self.x_length)
            self.np_array = np.stack([r_arr, g_arr, b_arr]).astype(np.uint8)

            # 3バンドにnumpyのarrayをセット
            for band in range(1, band_count + 1):
                raster_band = dst_ds.GetRasterBand(band)
                raster_band.WriteArray(self.np_array[band - 1])

        else:
            # 作成したラスターの第一バンドを取得し、numpyのarrayをセット
            raster_band = dst_ds.GetRasterBand(1)
            raster_band.WriteArray(self.np_array)
            raster_band.SetNoDataValue(no_data_value)

    def write(
        self,
        band_count,
        dtype,
        file_name="output.tif",
        no_data_value=-9099,
        rgbify=False
    ):
        """標高と座標、ピクセルサイズ、グリッドサイズからGeoTiffを作成

        Args:
            band_count (int):
            dtype (gdalのピクセルデータタイプ):
            file_name (str):
            no_data_value (int):
            rgbify (bool):
        """
        if not self.output_path.exists():
            self.output_path.mkdir()
        created_tiff_path = self.output_path / file_name

        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.Create(
            str(created_tiff_path.resolve()),
            self.x_length,
            self.y_length,
            band_count,
            dtype
        )
        dst_ds.SetGeoTransform(self.geo_transform)

        self.make_raster_bands(
            rgbify,
            band_count,
            dst_ds,
            no_data_value
        )

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
            no_data_value=-9999):
        """EPSG:4326のTiffから新たなGeoTiffを出力する

        Args:
            source_path (Path):
            file_name (str):
            epsg (str):
            no_data_value (int):

        """
        if source_path is None:
            source_path = self.output_path / file_name
        warp(
            source_path=source_path,
            file_name=file_name,
            epsg=epsg,
            output_path=self.output_path,
            no_data_value=no_data_value
        )
