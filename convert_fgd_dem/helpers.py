from osgeo import gdal


def warp(
        source_path=None,
        file_name="output.tif",
        output_path=None,
        epsg="EPSG:3857",
        no_data_value=0):
    """
    EPSG:4326のTiffから新たなGeoTiffを出力する

    Args:
        source_path (Path or None):
        file_name (str):
        output_path (Path or None):
        epsg (str):
        no_data_value (int):

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
