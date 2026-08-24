from typing import Any

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QObject

from raster_caster_plugin.communication import UICommunication
from raster_caster_plugin.provider import RasterCasterProvider

PLUGIN_NAME = "Raster Caster"


class RasterCasterPlugin(QObject):
    """Main Plugin Class which register toolbar ad menu and add tools"""

    def __init__(self, iface: Any) -> None:
        QObject.__init__(self)
        self.iface = iface
        self.communication = UICommunication(PLUGIN_NAME)

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
