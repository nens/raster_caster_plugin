from typing import Any

from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtCore import QObject

from raster_caster_plugin.communication import UICommunication
from raster_caster_plugin.provider import RasterCasterProvider

PLUGIN_NAME = "Raster Caster"
UNSUPPORTED_QGIS_VERSION_INT = 40200


class RasterCasterPlugin(QObject):
    """Main Plugin Class which register toolbar ad menu and add tools"""

    def __init__(self, iface: Any) -> None:
        QObject.__init__(self)
        self.iface = iface
        self.communication = UICommunication(PLUGIN_NAME)

        if Qgis.versionInt() == UNSUPPORTED_QGIS_VERSION_INT:
            self.communication.show_warn(
                "QGIS 4.2.0 is not supported by this plugin because of a bug in "
                "OGR/GDAL 3.13.1. Please use a different QGIS version."
            )

        self.provider: RasterCasterProvider | None = None

    def initGui(self) -> None:
        """Create the UI. Called when the plugin is loaded."""
        self.provider = RasterCasterProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self) -> None:
        """Remove UI. Called then the plugin is unloaded."""
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
