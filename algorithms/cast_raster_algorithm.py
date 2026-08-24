from typing import Any, NoReturn

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
)


class CastRasterAlgorithm(QgsProcessingAlgorithm):
    """Skeleton algorithm — implementation pending."""

    INPUT = "INPUT"

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
                self.INPUT,
                "Input GeoPackage",
                extension="gpkg",
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> NoReturn:
        raise NotImplementedError
