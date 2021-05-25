from pathlib import Path

from osgeo import gdal, osr
import numpy as np

from .helpers import (
    convert_height_to_R,
    convert_height_to_G,
    convert_height_to_B,
    warp
)


class Geotiff:
    """Generate GeoTiff"""

    def __init__(
            self,
            geo_transform,
            np_array,
            x_length,
            y_length,
            output_path):
        """Initializer

        Args:
            geo_transform (list): Data for SetGeoTransform in Gdal's Dataset class
            np_array (numpy.ndarray): dem numpy array
            x_length (int): image size of x
            y_length (int): iamge size of y
            output_path (Path): Path object of output path

        Notes:
            The contents of geo_transform list are as follows
            geo_transform = [Top left longitude, east-west resolution, rotation, top left latitude, rotation, north-south resolution]
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
        no_data_value=-9999
    ):
        """Make raster band

        Args:
            rgbify (bool): whether to generate TerrainRGB or not
            band_count (int): number of bands
            dst_ds (gdal.Dataset): gdal Dataset object
            no_data_value (int): integer of no data value
        """
        if rgbify:
            func_R = np.frompyfunc(convert_height_to_R, 1, 1)
            func_G = np.frompyfunc(convert_height_to_G, 2, 1)
            func_B = np.frompyfunc(convert_height_to_B, 3, 1)

            r_arr = func_R(self.np_array)
            g_arr = func_G(self.np_array, r_arr)
            b_arr = func_B(self.np_array, r_arr, g_arr)

            self.np_array = np.array([r_arr, g_arr, b_arr])

            # 3バンドにnumpyのarrayをセット
            for band in range(1, band_count + 1):
                raster_band = dst_ds.GetRasterBand(band)
                raster_band.WriteArray(self.np_array[band - 1])

        else:
            # 作成したラスターの第一バンドを取得し、numpyのarrayをセット
            raster_band = dst_ds.GetRasterBand(1)
            raster_band.WriteArray(self.np_array)
            raster_band.SetNoDataValue(no_data_value)

    def generate(
        self,
        band_count,
        dtype,
        file_name="output.tif",
        no_data_value=-9999,
        rgbify=False
    ):
        """Create GeoTiff from elevation and coordinates, pixel size, grid size

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
        print(type(dst_ds))
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
