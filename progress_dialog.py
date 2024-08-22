import os

# QGIS-API
from qgis.PyQt import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QDialog


class ProgressDialog(QDialog):
    def __init__(self, set_abort_flag_callback):
        """_summary_

        Args:
            set_abort_flag_callback (optional, method()): called when abort clicked
        """
        super().__init__()
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.ui = uic.loadUi(
            os.path.join(os.path.dirname(__file__), "progress_dialog.ui"), self
        )

        self.set_abort_flag_callback = set_abort_flag_callback
        self.init_ui()

    def init_ui(self):
        self.label.setText(self.tr("Initializing process..."))
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(0)
        self.abortButton.setEnabled(True)
        self.abortButton.setText(self.tr("Cancel"))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            return
        super().keyPressEvent(event)

    def abort_dialog(self):
        if self.abortButton.isEnabled():  # abort if possible
            self.abortButton.setEnabled(False)
            self.abortButton.setText(self.tr("Cancelling..."))
            self.close()

    def set_maximum(self, value: int):
        self.progressBar.setMaximum(value)

    def add_progress(self, value: int):
        self.progressBar.setValue(self.progressBar.value() + value)

    def set_message(self, message: str):
        self.label.setText(self.translate(message))

    def set_abortable(self, abortable=True):
        self.abortButton.setEnabled(abortable)

    def close_dialog(self):
        print("closing")
        self.ui.close()

    def translate(self, message):
        # translate in this QDialog class to be detected by QLinguist.
        message_dic = {
            "Set the output file": self.tr("Set the output file"),
            "Error": self.tr("Error"),
            "Aborting": self.tr("Aborting"),
            "Are you sure to cancel process?": self.tr(
                "Are you sure to cancel process?"
            ),
            "Output format is not checked.": self.tr("Output format is not checked."),
            "Input DEM path is not defined.": self.tr("Input DEM path is not defined."),
            "GeoTIFF output path is not defined.": self.tr(
                "GeoTIFF output path is not defined."
            ),
            "Terrain RGB output path is not defined.": self.tr(
                "Terrain RGB output path is not defined."
            ),
            "CRS of output file is not defined.": self.tr(
                "CRS of output file is not defined."
            ),
            "Cannot find output folder.": self.tr("Cannot find output folder."),
            "Completed": self.tr("Completed"),
            "Process completed.": self.tr("Process completed."),
            # Submodule errors
            "Converting XML files to Terrain RGB...": self.tr(
                "Converting XML files to Terrain RGB..."
            ),
            "Converting XML files to GeoTIFF DEM...": self.tr(
                "Converting XML files to GeoTIFF DEM..."
            ),
            "Creating TIFF file...": self.tr("Creating TIFF file..."),
            "No XML file found in input folder.": self.tr(
                "No XML file found in input folder."
            ),
            "No XML file found in input zip file.": self.tr(
                "No XML file found in input zip file."
            ),
            "Only ZIP file, XML file, or folder conatining XML files are allowed.": self.tr(
                "Only ZIP file, XML file, or folder conatining XML files are allowed."
            ),
            "Only XML file format is allowed.": self.tr(
                "Only XML file format is allowed."
            ),
            "Incorrect XML file.": self.tr("Incorrect XML file."),
            "Mixed mesh format (2nd mesh and 3rd mesh)": self.tr(
                "Mixed mesh format (2nd mesh and 3rd mesh)"
            ),
            "Output DEM has no elevation data.": self.tr(
                "Output DEM has no elevation data."
            ),
            "Warning": self.tr("Warning"),
        }
        translated_message = message_dic.get(
            message, message
        )  # fallback is self message

        # Handle messages with variables
        if translated_message.split(":")[0] == "Incorrect Mesh code":
            translated_message = (
                self.tr("Incorrect Mesh code") + ": " + message.split(":")[1]
            )
            # メッシュコードが不正です: mesh_code={mesh_code}
        elif translated_message.split(":")[0] == "Image size is too large":
            translated_message = (
                self.tr("Image size is too large") + ": " + message.split(":")[1]
            )
            # セルサイズが大きすぎます。x={x_length}・y={y_length}

        return translated_message
