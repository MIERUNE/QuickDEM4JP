# QuickDEM4JP

## Overview
![](./docs/img/1.gif)

This is QGIS plugin to convert DEM XML files, provided by Geospatial Information Authority of Japan(GSI) to GeoTiff and Terrain RGB format.

You can find the DEM data in XML format for any location from the following site. https://fgd.gsi.go.jp/download

## Usage

- The plugin will be added Plugin --> QuickDEM4JP.
- Or you will find this icon on QGIS toolbar.

![](./icon.png)

- Choose input type('xml'または'xml'を含む'zip' / 'xml'を含むフォルダ), input DEM path, output type(GeoTiff / Terrain RGB), output path and CRS of outputfile, then click OK.
- The outputfile will be added to the map canvas when the checkbox (アルゴリズムの終了後、QGIS上で出力ファイルを開く) is checked.

![](./docs/img/1.png)
