from osgeo import gdal


def warp(
        source_path=None,
        file_name="output.tif",
        output_path=None,
        epsg="EPSG:3857",
        no_data_value="None"):
    """
    Create new GeoTiff from EPSG: 4326 Tiff

    Args:
        source_path (Path or None): Path object of source file
        file_name (str): string of file name
        output_path (Path or None): Path object of file output path
        epsg (str): string of epsg
        no_data_value (int): integer of no data value
    """

    if not output_path.exists():
        output_path.mkdir()
    if source_path is None:
        source_path = output_path / file_name

    if file_name is None:
        file_name = "".join(f"dem_{epsg.lower()}.tif".split(":"))

    warp_path = str((output_path / file_name).resolve())
    src_path = str(source_path.resolve())

    resampled_ras = gdal.Warp(
        warp_path,
        src_path,
        srcSRS="EPSG:4326",
        dstSRS=epsg,
        dstNodata=no_data_value,
        resampleAlg="near"
    )
    resampled_ras.FlushCache()


def convert_height_to_R(height, no_data_value=-9999):
    """
    Convert height to R value of RGB

    Args:
        height (int): integer of height
    """
    if height == no_data_value:
        # Calculate with nodata as elevation value 0
        return 1
    r_min_height = 65536
    offset_height = int(height * 10) + 100000
    return offset_height // r_min_height


def convert_height_to_G(height, r_value, no_data_value=-9999):
    """
    Convert height to G value of RGB

    Args:
        height (int): integer of height
    """
    if height == no_data_value:
        # Calculate with nodata as elevation value 0
        return 134
    r_min_height = 65536
    g_min_height = 256
    offset_height = int(height * 10) + 100000
    return (offset_height - r_value * r_min_height) // g_min_height


def convert_height_to_B(height, r_value, g_value, no_data_value=-9999):
    """
    Convert height to B value of RGB

    Args:
        height (int): integer of height
    """
    if height == no_data_value:
        # Calculate with nodata as elevation value 0
        return 160
    r_min_height = 65536
    g_min_height = 256
    offset_height = int(height * 10) + 100000
    return offset_height - r_value * r_min_height - g_value * g_min_height
