import os
from pathlib import Path

import numpy as np
from osgeo import gdal

from .dem import Dem
from .geotiff import Geotiff


class Converter:

    def __init__(
            self,
            import_path,
            output_path,
            output_epsg="EPSG:4326",
            file_name='output.tif',
            rgbify=False):
        """Initializer

        Args:
            import_path (str): string of file import path
            output_path (str): string of file output path
            output_epsg (str): string of output epsg
            file_name (str): string of output filename
            rgbify (bool): whether to generate TerrainRGB or not

        Notes:
            "Meta_data" refers to mesh code, lonlat of the bottom left and top right, grid size, initial position, and pixel size of DEM.
            "Content" refers to mesh code, metadata, and elevation values.
        """
        self.import_path: Path = Path(import_path)
        self.output_path: Path = Path(output_path)
        if not output_epsg.startswith("EPSG:"):
            raise Exception("EPSGコードの指定が不正です。EPSG:〇〇の形式で入力してください")
        self.output_epsg: str = output_epsg
        self.file_name: str = file_name
        self.rgbify: bool = rgbify

        self.dem = Dem(self.import_path)

    def _calc_image_size(self):
        """Calculate the size of the output image from the lonlat of the Dem boundary and the pixel size.
        Returns:
            tuple: Image size in x / y direction
        """
        lower_left_lat = self.dem.bounds_latlng["lower_left"]["lat"]
        lower_left_lon = self.dem.bounds_latlng["lower_left"]["lon"]
        upper_right_lat = self.dem.bounds_latlng["upper_right"]["lat"]
        upper_right_lon = self.dem.bounds_latlng["upper_right"]["lon"]

        x_length = round(
            abs(
                (upper_right_lon - lower_left_lon)
                / self.dem.meta_data_list[0]["pixel_size"]["x"]
            )
        )
        y_length = round(
            abs(
                (upper_right_lat - lower_left_lat)
                / self.dem.meta_data_list[0]["pixel_size"]["y"]
            )
        )

        return x_length, y_length

    def _combine_meta_data_and_contents(self):
        """Combine metadata and elevation values ​​with the same mesh code

        Returns:
            list: Mesh data list
        """
        mesh_data_list = []

        sort_metadata_list = sorted(
            self.dem.meta_data_list, key=lambda x: x["mesh_code"]
        )
        sort_contents_list = sorted(
            self.dem.np_array_list, key=lambda x: x["mesh_code"]
        )
        for metadata, content in zip(sort_metadata_list, sort_contents_list):
            metadata.update(content)
            mesh_data_list.append(metadata)

        return mesh_data_list

    def make_data_for_geotiff(self):
        """Generate the data required to create GeoTiff from Dem information

        Returns:
            tuple: Geo transform list, dem numpy array, image size of x, y and output path
        """
        # Number of grid cells including all xml
        image_size = self._calc_image_size()
        x_length = image_size[0]
        y_length = image_size[1]

        if x_length >= 10000 or y_length >= 10000:
            raise Exception(f"セルサイズが大きすぎます。x={x_length}・y={y_length}")

        # Create an array that covers all xml
        dem_array = np.empty((y_length, x_length), np.float32)
        dem_array.fill(-9999)

        x_pixel_size = (
            self.dem.bounds_latlng["upper_right"]["lon"]
            - self.dem.bounds_latlng["lower_left"]["lon"]
        ) / x_length
        y_pixel_size = (
            self.dem.bounds_latlng["lower_left"]["lat"]
            - self.dem.bounds_latlng["upper_right"]["lat"]
        ) / y_length

        # Combine metadata and elevation values
        data_list = self._combine_meta_data_and_contents()

        for data in data_list:
            # Get the bottom left coordinates of the read array
            lower_left_lat = data["lower_corner"]["lat"]
            lower_left_lon = data["lower_corner"]["lon"]

            # Calculate the distance from (0, 0)
            lat_distance = lower_left_lat - \
                self.dem.bounds_latlng["lower_left"]["lat"]
            lon_distance = lower_left_lon - \
                self.dem.bounds_latlng["lower_left"]["lon"]

            # Get coordinates on numpy (Rounded off to eliminate errors)
            x_coordinate = round(lon_distance / x_pixel_size)
            y_coordinate = round(lat_distance / (-y_pixel_size))

            x_len = data["grid_length"]["x"]
            y_len = data["grid_length"]["y"]

            row_start = int(y_length - (y_coordinate + y_len))
            row_end = int(row_start + y_len)
            column_start = int(x_coordinate)
            column_end = int(column_start + x_len)

            # Get an array of elevation values ​​from the data
            np_array = data["np_array"]
            # Assign to a large array
            dem_array[row_start:row_end, column_start:column_end] = np_array

        geo_transform = [
            self.dem.bounds_latlng["lower_left"]["lon"],
            x_pixel_size,
            0,
            self.dem.bounds_latlng["upper_right"]["lat"],
            0,
            y_pixel_size,
        ]

        data_for_geotiff = (
            geo_transform,
            dem_array,
            x_length,
            y_length,
            self.output_path,
        )
        return data_for_geotiff

    def dem_to_geotiff(self):
        """
        Convert the xml(dem) in the selected directory to GeoTiff and store it in the specified directory
        If value of rgbify is True, also generate terrainRGB
        """
        data_for_geotiff = self.make_data_for_geotiff()

        geotiff = Geotiff(*data_for_geotiff)

        if self.rgbify:
            root, ext = os.path.splitext(self.file_name)
            geotiff.create(
                3,
                gdal.GDT_Byte,
                file_name=self.file_name,
                no_data_value=None,
                rgbify=self.rgbify
            )
            if not self.output_epsg == "EPSG:4326":
                geotiff.resampling(
                    file_name=self.file_name,
                    epsg=self.output_epsg,
                    no_data_value=None
                )
        else:
            geotiff.create(
                1,
                gdal.GDT_Float32,
                file_name=self.file_name
            )
            if not self.output_epsg == "EPSG:4326":
                geotiff.resampling(
                    file_name=self.file_name,
                    epsg=self.output_epsg,
                )
