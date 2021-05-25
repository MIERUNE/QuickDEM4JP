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
            output_path (Path): Path object of file output path

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

    def write_raster_bands(
        self,
        rgbify,
        band_count,
        dst_ds,
        no_data_value=-9999
    ):
        """Write numpy array on raster bands 

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

            for band in range(1, band_count + 1):
                raster_band = dst_ds.GetRasterBand(band)
                raster_band.WriteArray(self.np_array[band - 1])

        else:
            raster_band = dst_ds.GetRasterBand(1)
            raster_band.WriteArray(self.np_array)
            raster_band.SetNoDataValue(no_data_value)

    def create(
        self,
        band_count,
        dtype,
        file_name="output.tif",
        no_data_value=-9999,
        rgbify=False
    ):
        """Create GeoTiff from elevation and coordinates, pixel size, grid size

        Args:
            band_count (int): number of bands
            dtype (int): integer of gdal data type
            file_name (str): output file name
            no_data_value (int): integer of no data value
            rgbify (bool): whether to generate TerrainRGB or not
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

        self.write_raster_bands(
            rgbify,
            band_count,
            dst_ds,
            no_data_value
        )

        ref = osr.SpatialReference()
        ref.ImportFromEPSG(4326)
        dst_ds.SetProjection(ref.ExportToWkt())

        dst_ds.FlushCache()

    def resampling(
            self,
            source_path=None,
            file_name="output.tif",
            epsg="EPSG:3857",
            no_data_value=-9999):
        """Create new GeoTiff from EPSG: 4326 Tiff

        Args:
            source_path (Path): Path object of source file
            file_name (str): string of file name
            epsg (str): string of epsg
            no_data_value (int): integer of no data value
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
