from qgis.core import QgsProcessingProvider

from raster_caster_plugin.algorithms.cast_raster_algorithm import CastRasterAlgorithm
from raster_caster_plugin.algorithms.generate_geopackage_algorithm import (
    GenerateGeopackageAlgorithm,
)


class RasterCasterProvider(QgsProcessingProvider):

    def id(self) -> str:
        return "raster_caster"

    def name(self) -> str:
        return "Raster Caster"

    def longName(self) -> str:
        return "Raster Caster"

    def loadAlgorithms(self) -> None:
        self.addAlgorithm(GenerateGeopackageAlgorithm())
        self.addAlgorithm(CastRasterAlgorithm())
