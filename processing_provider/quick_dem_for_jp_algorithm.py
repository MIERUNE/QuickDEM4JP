"""
/***************************************************************************
 QuickDEMforJPDialog
                                 A QGIS plugin
 The plugin to convert DEM to GeoTiff and Terrain RGB (Tiff).
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-05-31
        git sha              : $Format:%H$
        copyright            : (C) 2021 by MIERUNE Inc.
        email                : info@mierune.co.jp
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.core import (
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFile,
    QgsProcessingParameterCrs,
    QgsProcessingParameterBoolean,
)
from qgis.PyQt.QtCore import QCoreApplication

from ..convert_fgd_dem.src.convert_fgd_dem.converter import Converter


class QuickDEMforJPProcessingAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT_GEOTIFF = "OUTPUT_GEOTIFF"
    OUTPUT_TERRAINRGB = "OUTPUT_TERRAINRGB"
    CRS = "CRS"
    SEA_AT_ZERO = "SEA_AT_ZERO"

    def tr(self, string):
        return QCoreApplication.translate("QuickDEMforJPProcessingAlgorithm", string)

    def createInstance(self):
        return QuickDEMforJPProcessingAlgorithm()

    def name(self):
        return "quickdemforjp"

    def group(self):
        return None

    def groupId(self):
        return None

    def displayName(self):
        return self.tr("Load Japan DEM from XML file")

    def shortHelpString(self):
        return (
            self.tr(
                "Geospatial Information Authority of Japan(GSI) provides 1m, 5m and 10m DEM XML files of Japan <a href='https://service.gsi.go.jp/kiban/'>on the web</a>. This plugin imports XML files or XML included zip files and converts them to DEM GeoTiff and/or Terrain RGB format GeoTiff."
            )
            + "\nTracker: <a href='https://github.com/MIERUNE/QuickDEM4JP/issues'>https://github.com/MIERUNE/QuickDEM4JP/issues</a>"
            + "\nRepository: <a href='https://github.com/MIERUNE/QuickDEM4JP'>https://github.com/MIERUNE/QuickDEM4JP</a>"
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr("DEM file (.xml or .zip containing .xml)"),
                fileFilter=self.tr("DEM (*.xml *.zip)"),
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_GEOTIFF, self.tr("Output DEM Geotiff"), optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_TERRAINRGB,
                self.tr("Output Terrain RGB"),
                optional=True,
                createByDefault=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS, self.tr("CRS"), defaultValue="EPSG:4326"
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SEA_AT_ZERO,
                self.tr("Set 0m to sea area"),
                defaultValue=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        import_path = self.parameterAsFile(parameters, self.INPUT, context)

        output_epsg = self.parameterAsCrs(parameters, self.CRS, context)
        output_path = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_GEOTIFF, context
        )
        output_path_terrain = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_TERRAINRGB, context
        )
        sea_at_zero = self.parameterAsBool(parameters, self.SEA_AT_ZERO, context)

        if not output_path and not output_path_terrain:
            feedback.reportError(
                self.tr("DEM Geotiff and/or Terrain RGB output are not defined.")
            )
            return {}

        results = {}

        try:
            if output_path:
                filename = os.path.basename(output_path)
                if not filename.lower().endswith(".tif"):
                    filename += ".tif"

                Converter(
                    import_path=import_path,
                    output_path=os.path.dirname(output_path),
                    output_epsg=output_epsg.authid(),
                    file_name=filename,
                    rgbify=False,
                    sea_at_zero=sea_at_zero,
                    feedback=feedback,
                ).run()
                results[self.OUTPUT_GEOTIFF] = output_path

            if output_path_terrain:
                filename = os.path.basename(output_path_terrain)
                if not filename.lower().endswith(".tif"):
                    filename += ".tif"

                Converter(
                    import_path=import_path,
                    output_path=os.path.dirname(output_path_terrain),
                    output_epsg=output_epsg.authid(),
                    file_name=filename,
                    rgbify=True,
                    sea_at_zero=sea_at_zero,
                    feedback=feedback,
                ).run()
                results[self.OUTPUT_TERRAINRGB] = output_path_terrain

            feedback.pushInfo(self.tr("Conversion completed."))

        except Exception as e:
            raise QgsProcessingException(self.tr("An error occured: {}").format(str(e)))

        return results
