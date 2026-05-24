import sys
import threading

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
)

from voice_live import VoiceAssistant


class UiSignals(QObject):
    log = Signal(str)
    status = Signal(str)


class HiMaxApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hi Max")
        self.setMinimumSize(600, 450)

        self.signals = UiSignals()
        self.signals.log.connect(self.write_log)
        self.signals.status.connect(self.set_status)

        self.assistant = None
        self.thread = None

        layout = QVBoxLayout()

        self.status_label = QLabel("Status: stopped")
        layout.addWidget(self.status_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_assistant)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_assistant)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def write_log(self, message):
        self.log_box.append(message)

    def set_status(self, message):
        self.status_label.setText(f"Status: {message}")

    def log_from_assistant(self, message):
        self.signals.log.emit(message)

    def start_assistant(self):
        if self.thread and self.thread.is_alive():
            return

        self.signals.status.emit("starting")
        self.signals.log.emit("Starting assistant...")

        self.assistant = VoiceAssistant(log_callback=self.log_from_assistant)

        self.thread = threading.Thread(
            target=self.assistant.run,
            daemon=True,
        )
        self.thread.start()

        self.signals.status.emit("listening")

    def stop_assistant(self):
        if self.assistant:
            self.assistant.stop()

        self.signals.status.emit("stopped")
        self.signals.log.emit("Assistant stopped")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = HiMaxApp()
    window.show()

    sys.exit(app.exec())