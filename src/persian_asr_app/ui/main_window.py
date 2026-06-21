"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from persian_asr_app.core.asr_engine import ASREngine
from persian_asr_app.workers.transcription_worker import TranscriptionWorker

AUDIO_FILTER = (
    "فایل‌های صوتی (*.wav *.mp3 *.m4a *.flac *.ogg *.aac);;"
    "همه فایل‌ها (*.*)"
)

NO_FILE_TEXT = "فایلی انتخاب نشده است"


class MainWindow(QMainWindow):
    """Persian ASR desktop window for file-based transcription."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = ASREngine()
        self._audio_path: str | None = None
        self._thread: QThread | None = None
        self._worker: TranscriptionWorker | None = None

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        self.setWindowTitle("تبدیل گفتار فارسی به متن")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumSize(640, 480)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("تبدیل گفتار فارسی به متن")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        file_row = QHBoxLayout()
        self._select_btn = QPushButton("انتخاب فایل صوتی")
        self._select_btn.clicked.connect(self._select_audio_file)
        file_row.addWidget(self._select_btn)
        file_row.addStretch()
        layout.addLayout(file_row)

        self._file_label = QLabel(NO_FILE_TEXT)
        self._file_label.setObjectName("filePathLabel")
        self._file_label.setWordWrap(True)
        self._file_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._file_label)

        self._transcribe_btn = QPushButton("تبدیل به متن")
        self._transcribe_btn.setEnabled(False)
        self._transcribe_btn.clicked.connect(self._start_transcription)
        layout.addWidget(self._transcribe_btn)

        self._result_edit = QTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setPlaceholderText("متن تبدیل‌شده اینجا نمایش داده می‌شود...")
        self._result_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self._result_edit, stretch=1)

        action_row = QHBoxLayout()
        self._copy_btn = QPushButton("کپی متن")
        self._copy_btn.clicked.connect(self._copy_result)
        self._clear_btn = QPushButton("پاک کردن")
        self._clear_btn.clicked.connect(self._clear_all)
        action_row.addWidget(self._copy_btn)
        action_row.addWidget(self._clear_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        self._status_label = QLabel("آماده")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._status_label)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel#headerLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1a1a1a;
                padding: 4px 0;
            }
            QLabel#filePathLabel {
                font-size: 12px;
                color: #555555;
            }
            QLabel#statusLabel {
                font-size: 12px;
                color: #666666;
            }
            QPushButton {
                font-size: 13px;
                padding: 8px 16px;
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover:enabled {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
            QTextEdit {
                font-size: 14px;
                padding: 8px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            """
        )

    def _select_audio_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "انتخاب فایل صوتی",
            "",
            AUDIO_FILTER,
        )
        if not path:
            return

        self._audio_path = path
        self._file_label.setText(path)
        self._transcribe_btn.setEnabled(True)
        self._status_label.setText("فایل انتخاب شد")

    def _start_transcription(self) -> None:
        if not self._audio_path:
            return

        self._set_busy(True)
        self._status_label.setText("در حال تبدیل... (اولین بار ممکن است مدل دانلود شود)")
        self._result_edit.clear()

        self._thread = QThread()
        self._worker = TranscriptionWorker(self._engine, self._audio_path)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_transcription_finished)
        self._worker.error.connect(self._on_transcription_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.error.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _on_transcription_finished(self, text: str) -> None:
        self._result_edit.setPlainText(text)
        self._status_label.setText("تبدیل با موفقیت انجام شد")
        self._set_busy(False)

    def _on_transcription_error(self, message: str) -> None:
        self._status_label.setText("خطا در تبدیل")
        self._set_busy(False)
        QMessageBox.critical(self, "خطا", message)

    def _cleanup_thread(self) -> None:
        self._thread = None
        self._worker = None

    def _set_busy(self, busy: bool) -> None:
        self._select_btn.setEnabled(not busy)
        self._transcribe_btn.setEnabled(not busy and self._audio_path is not None)
        self._copy_btn.setEnabled(not busy)
        self._clear_btn.setEnabled(not busy)

    def _copy_result(self) -> None:
        text = self._result_edit.toPlainText()
        if not text:
            self._status_label.setText("متنی برای کپی وجود ندارد")
            return

        QGuiApplication.clipboard().setText(text)
        self._status_label.setText("متن در حافظه کپی شد")

    def _clear_all(self) -> None:
        self._audio_path = None
        self._file_label.setText(NO_FILE_TEXT)
        self._result_edit.clear()
        self._transcribe_btn.setEnabled(False)
        self._status_label.setText("آماده")
