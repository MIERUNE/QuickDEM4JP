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
        self.label.setText(message)

    def set_abortable(self, abortable=True):
        self.abortButton.setEnabled(abortable)

    def close_dialog(self):
        print("closing")
        self.ui.close()

    def translate(self, message):
        # translate in this QDialog class to be detected by QLinguist.
        if message == "Set the output file":
            translated_message = self.tr("Set the output file")
            # 保存ファイルを選択してください
        elif message == "Error":
            translated_message = self.tr("Error")
        elif message == "Finalizing...":
            translated_message = self.tr("Finalizing...")
        elif message == "Aborting":
            translated_message = self.tr("Aborting")
        elif message == "Are you sure to cancel process?":
            translated_message = self.tr("Are you sure to cancel process?")
        elif message == "Output format is not checked.":
            translated_message = self.tr("Output format is not checked.")
            # 出力形式にチェックを入れてください
        elif message == "Input DEM path is not defined.":
            translated_message = self.tr("Input DEM path is not defined.")
            # DEMの入力先パスを入力してください
        elif message == "GeoTIFF output path is not defined.":
            translated_message = self.tr("GeoTIFF output path is not defined.")
            # GeoTIFFの出力先パスを入力してください
        elif message == "Terrain RGB output path is not defined.":
            translated_message = self.tr("Terrain RGB output path is not defined.")
            # Terrain RGBの出力先パスを入力してください
        elif message == "CRS of output file is not defined.":
            translated_message = self.tr("CRS of output file is not defined.")
            # "DEMの出力CRSを入力してください"
        elif message == "Cannot find output folder.":
            translated_message = self.tr("Cannot find output folder.")
        elif message == "Completed":
            translated_message = self.tr("Completed")
            # 完了
        elif message == "Process completed.":
            translated_message = self.tr("Process completed.")
            # 処理が完了しました

        # Submodule errors
        elif message == "No XML file found in input folder.":
            translated_message = self.tr("No XML file found in input folder.")
            # 指定ディレクトリに.xmlが存在しません

        elif message == "Warning":
            translated_message = self.tr("Warning")
        elif message.split(":")[0] == "Image size is too large":
            translated_message = (
                self.tr("Image size is too large") + ": " + message.split(":")[1]
            )
            # セルサイズが大きすぎます。x={x_length}・y={y_length}
        else:
            # fallback origin message
            translated_message = message
        return translated_message
