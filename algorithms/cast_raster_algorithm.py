import math
from typing import Any

import numpy as np
from osgeo import gdal, ogr
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
)


class CastRasterAlgorithm(QgsProcessingAlgorithm):
    """Skeleton algorithm — implementation pending."""

    INPUT_GPKG = "INPUT_GPKG"
    INPUT_RASTER = "INPUT_RASTER"
    PIXEL_SIZE = "PIXEL_SIZE"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "cast_raster"

    def displayName(self) -> str:
        return "Cast Raster"

    def group(self) -> str:
        return "Analysis"

    def groupId(self) -> str:
        return "analysis"

    def shortHelpString(self) -> str:
        return "Cast a raster from a Raster Caster GeoPackage."

    def createInstance(self) -> "CastRasterAlgorithm":
        return CastRasterAlgorithm()

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_GPKG,
                "Input GeoPackage",
                extension="gpkg",
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER,
                "Input Raster",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PIXEL_SIZE,
                "Pixel Size",
                type=QgsProcessingParameterNumber.Type.Double,
                optional=True,
                minValue=0.0,
                defaultValue=0.5,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                "Output Raster",
                fileFilter="GeoTIFF files (*.tif)",
            )
        )

    def checkParameterValues(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
    ) -> Any:
        raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        pixel_size = self.parameterAsDouble(parameters, self.PIXEL_SIZE, context)
        if raster is None and (self.PIXEL_SIZE not in parameters or pixel_size <= 0):
            return False, "Pixel Size is required when no Input Raster is provided."
        return super().checkParameterValues(parameters, context)

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, str]:
        gpkg_path = self.parameterAsString(parameters, self.INPUT_GPKG, context)
        raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        output_path = self.parameterAsString(parameters, self.OUTPUT, context)

        if raster is not None:
            pixel_size = raster.rasterUnitsPerPixelX()
        else:
            pixel_size = self.parameterAsDouble(parameters, self.PIXEL_SIZE, context)

        ds = ogr.Open(gpkg_path)
        layer = ds.GetLayerByName("surface")
        extent = layer.GetExtent()  # (minX, maxX, minY, maxY)
        srs = layer.GetSpatialRef()
        ds = None

        min_x, max_x, min_y, max_y = extent
        cols = math.ceil((max_x - min_x) / pixel_size)
        rows = math.ceil((max_y - min_y) / pixel_size)

        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(output_path, cols, rows, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform((min_x, pixel_size, 0, max_y, 0, -pixel_size))
        out_ds.SetProjection(srs.ExportToWkt())

        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999.0)

        band.WriteArray(np.ones((rows, cols), dtype=np.float32))

        gdal.Rasterize(
            out_ds,
            gpkg_path,
            layers=["surface"],
            attribute="param_1",
            where="definition_type = 'constant'",
        )

        out_ds = None

        return {self.OUTPUT: output_path}
