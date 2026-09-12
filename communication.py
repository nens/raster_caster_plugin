from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import QMessageBox


class UICommunication:
    def __init__(self, context: str):
        self.context = context

    def show_warn(self, msg: str) -> None:
        """Show the message in a modal warning dialog."""
        QMessageBox.warning(None, self.context, msg)

    def log_msg(self, msg: str, level: Qgis.MessageLevel) -> None:
        """Log the message to QGIS log with a given level."""
        QgsMessageLog.logMessage(msg, self.context, level)

    def log_err(self, msg: str) -> None:
        self.log_msg(msg, level=Qgis.MessageLevel.Critical)

    def log_warn(self, msg: str) -> None:
        self.log_msg(msg, level=Qgis.MessageLevel.Warning)

    def log_info(self, msg: str) -> None:
        self.log_msg(msg, level=Qgis.MessageLevel.Info)
