import click

from convert_fgd_dem import Converter


@click.command()
@click.option(
    "--import_path",
    required=False,
    type=str,
    default="./DEM/FG-GML-6441-32-DEM5A.zip",
    help="変換対象のパスを指定（「xml」「.xmlが格納されたディレクトリ」「.xmlが格納された.zip」が対象です。） default=./DEM/FG-GML-6441-32-DEM5A.zip",
)
@click.option(
    "--output_path",
    required=False,
    type=str,
    default="./GeoTiff",
    help="GeoTiffを格納するディレクトリ default=./GeoTiff",
)
@click.option(
    "--output_epsg",
    required=False,
    type=str,
    default="EPSG:4326",
    help="書き出すGeoTiffのEPSGコード default=EPSG:4326",
)
@click.option(
    "--rgbify",
    required=False,
    type=bool,
    default=False,
    help="terrain rgbを作成するか選択 default=False",
)
def main(import_path, output_path, output_epsg, rgbify):
    converter = Converter(
        import_path=import_path,
        output_path=output_path,
        output_epsg=output_epsg,
        rgbify=rgbify,
    )
    converter.dem_to_geotiff()


if __name__ == "__main__":
    main()
