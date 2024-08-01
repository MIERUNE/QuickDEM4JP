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
            self.set_abort_flag_callback()
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
        if message == "Processing...":
            translated_message = self.tr("Processing...")
        elif message == "Finalizing...":
            translated_message = self.tr("Finalizing...")
        elif message == "Aborting":
            translated_message = self.tr("Aborting")
        elif message == "Are you sure to cancel process?":
            translated_message = self.tr("Are you sure to cancel process?")
        elif message == "Error":
            translated_message = self.tr("Error")
        elif message == "Output file is not defined.":
            translated_message = self.tr("Output file is not defined.")
        elif message == "Cannot find output folder.":
            translated_message = self.tr("Cannot find output folder.")
        elif message == "CRS of output file is not defined.":
            translated_message = self.tr("CRS of output file is not defined.")
        elif (
            message
            == "Target extent must not cross the International Date Line meridian."
        ):
            translated_message = self.tr(
                "Target extent must not cross the International Date Line meridian."
            )
        elif message == "Too large amount of tiles ({})":
            translated_message = self.tr("Too large amount of tiles ({})")
        elif message == "Set a lower zoom level or extent to get less than {} tiles.":
            translated_message = self.tr(
                "Set a lower zoom level or extent to get less than {} tiles."
            )
        elif message == "Dowloading {} tiles may take a while. Process anyway?":
            translated_message = self.tr(
                "Dowloading {} tiles may take a while. Process anyway?"
            )
        elif message == "Warning":
            translated_message = self.tr("Warning")
        elif message == "DEM exported to Geotiff Format.":
            translated_message = self.tr("DEM exported to Geotiff Format.")
        else:
            # fallback origin message
            translated_message = message
        return translated_message
