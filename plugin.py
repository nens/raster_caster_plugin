from typing import Any

from qgis.PyQt.QtCore import QObject

from raster_caster_plugin.communication import UICommunication

PLUGIN_NAME = "Raster Caster"


class RasterCasterPlugin(QObject):
    """Main Plugin Class which register toolbar ad menu and add tools"""

    def __init__(self, iface: Any) -> None:
        QObject.__init__(self)
        self.iface = iface
        self.communication = UICommunication(PLUGIN_NAME)

        self.provider = None

    def initGui(self) -> None:
        """Create the UI. Called when the plugin is loaded."""
        # self.provider = RanaQgisPluginProvider()
        # QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self) -> None:
        """Remove UI. Called then the plugin is unloaded."""

        # QgsApplication.processingRegistry().removeProvider(self.provider)
        pass
