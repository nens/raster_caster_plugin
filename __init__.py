from typing import Any

from .plugin import RasterCasterPlugin


def classFactory(iface: Any) -> RasterCasterPlugin:

    return RasterCasterPlugin(iface)
