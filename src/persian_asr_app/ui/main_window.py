"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QCheckBox,
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

from persian_asr_app.config import LONG_AUDIO_THRESHOLD_MINUTES
from persian_asr_app.core.asr_engine import ASREngine
from persian_asr_app.core.audio_utils import (
    estimate_audio_duration,
    format_duration,
    is_audio_longer_than_threshold,
    validate_audio_path,
)
from persian_asr_app.core.transcription_format import (
    format_display_text,
    format_export_text,
    format_processing_time,
)
from persian_asr_app.workers.model_load_worker import ModelLoadWorker
from persian_asr_app.workers.transcription_worker import TranscriptionWorker

AUDIO_FILTER = (
    "فایل‌های صوتی (*.wav *.mp3 *.m4a *.flac *.ogg *.aac);;"
    "همه فایل‌ها (*.*)"
)
TEXT_FILTER = "فایل متنی (*.txt);;همه فایل‌ها (*.*)"

NO_FILE_TEXT = "فایلی انتخاب نشده است"

MODEL_STATUS_NOT_LOADED = "مدل: بارگذاری نشده"
MODEL_STATUS_LOADING = "مدل: در حال بارگذاری..."
MODEL_STATUS_READY = "مدل: آماده"


class MainWindow(QMainWindow):
    """Persian ASR desktop window for file-based transcription."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = ASREngine()
        self._audio_path: str | None = None
        self._last_result: dict | None = None
        self._last_processing_time: float | None = None
        self._thread: QThread | None = None
        self._worker: TranscriptionWorker | None = None
        self._load_thread: QThread | None = None
        self._load_worker: ModelLoadWorker | None = None
        self._transcription_cancelled = False

        self._setup_ui()
        self._apply_styles()
        self._update_model_status()

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

        model_row = QHBoxLayout()
        self._model_status_label = QLabel(MODEL_STATUS_NOT_LOADED)
        self._model_status_label.setObjectName("modelStatusLabel")
        self._model_status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        model_row.addWidget(self._model_status_label)

        self._preload_btn = QPushButton("بارگذاری مدل")
        self._preload_btn.clicked.connect(self._start_model_preload)
        model_row.addWidget(self._preload_btn)
        model_row.addStretch()
        layout.addLayout(model_row)

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

        self._duration_label = QLabel("")
        self._duration_label.setObjectName("durationLabel")
        self._duration_label.setWordWrap(True)
        self._duration_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._duration_label)

        self._long_audio_warning = QLabel("")
        self._long_audio_warning.setObjectName("longAudioWarning")
        self._long_audio_warning.setWordWrap(True)
        self._long_audio_warning.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._long_audio_warning.hide()
        layout.addWidget(self._long_audio_warning)

        self._timestamps_checkbox = QCheckBox("نمایش زمان‌بندی تقریبی")
        self._timestamps_checkbox.setChecked(False)
        layout.addWidget(self._timestamps_checkbox)

        transcribe_row = QHBoxLayout()
        self._transcribe_btn = QPushButton("تبدیل به متن")
        self._transcribe_btn.setEnabled(False)
        self._transcribe_btn.clicked.connect(self._start_transcription)
        transcribe_row.addWidget(self._transcribe_btn)

        self._cancel_btn = QPushButton("لغو")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_transcription)
        transcribe_row.addWidget(self._cancel_btn)
        transcribe_row.addStretch()
        layout.addLayout(transcribe_row)

        self._result_edit = QTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setPlaceholderText("متن تبدیل‌شده اینجا نمایش داده می‌شود...")
        self._result_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self._result_edit, stretch=1)

        action_row = QHBoxLayout()
        self._copy_btn = QPushButton("کپی متن")
        self._copy_btn.clicked.connect(self._copy_result)
        self._save_btn = QPushButton("ذخیره متن")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_result)
        self._clear_btn = QPushButton("پاک کردن")
        self._clear_btn.clicked.connect(self._clear_all)
        action_row.addWidget(self._copy_btn)
        action_row.addWidget(self._save_btn)
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
            QLabel#durationLabel {
                font-size: 12px;
                color: #374151;
            }
            QLabel#longAudioWarning {
                font-size: 12px;
                color: #b45309;
                background-color: #fffbeb;
                border: 1px solid #fcd34d;
                border-radius: 4px;
                padding: 8px;
            }
            QLabel#modelStatusLabel {
                font-size: 12px;
                color: #374151;
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
            QPushButton#cancelButton {
                background-color: #dc2626;
            }
            QPushButton#cancelButton:hover:enabled {
                background-color: #b91c1c;
            }
            QCheckBox {
                font-size: 13px;
                color: #374151;
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
        self._cancel_btn.setObjectName("cancelButton")

    def _update_model_status(self) -> None:
        if self._engine.is_loaded:
            self._model_status_label.setText(MODEL_STATUS_READY)
            self._preload_btn.setEnabled(False)
        elif self._is_model_loading():
            self._model_status_label.setText(MODEL_STATUS_LOADING)
            self._preload_btn.setEnabled(False)
        else:
            self._model_status_label.setText(MODEL_STATUS_NOT_LOADED)
            self._preload_btn.setEnabled(not self._is_busy())

    def _is_model_loading(self) -> bool:
        return self._load_thread is not None and self._load_thread.isRunning()

    def _is_transcribing(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _is_busy(self) -> bool:
        return self._is_model_loading() or self._is_transcribing()

    def _start_model_preload(self) -> None:
        if self._engine.is_loaded or self._is_model_loading():
            return

        self._set_busy(True)
        self._update_model_status()

        self._load_thread = QThread()
        self._load_worker = ModelLoadWorker(self._engine)
        self._load_worker.moveToThread(self._load_thread)

        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.started.connect(self._on_model_load_started)
        self._load_worker.progress.connect(self._on_model_load_progress)
        self._load_worker.finished.connect(self._on_model_load_finished)
        self._load_worker.failed.connect(self._on_model_load_failed)
        self._load_worker.finished.connect(self._load_thread.quit)
        self._load_worker.failed.connect(self._load_thread.quit)
        self._load_worker.finished.connect(self._load_worker.deleteLater)
        self._load_worker.failed.connect(self._load_worker.deleteLater)
        self._load_thread.finished.connect(self._load_thread.deleteLater)
        self._load_thread.finished.connect(self._cleanup_load_thread)

        self._load_thread.start()

    def _on_model_load_started(self) -> None:
        self._model_status_label.setText(MODEL_STATUS_LOADING)

    def _on_model_load_progress(self, message: str) -> None:
        self._status_label.setText(message)

    def _on_model_load_finished(self) -> None:
        self._update_model_status()
        self._set_busy(False)
        self._status_label.setText("مدل با موفقیت بارگذاری شد")

    def _on_model_load_failed(self, message: str) -> None:
        self._update_model_status()
        self._set_busy(False)
        self._status_label.setText("خطا در بارگذاری مدل")
        QMessageBox.critical(self, "خطا", message)

    def _cleanup_load_thread(self) -> None:
        if self._load_thread is not None:
            self._load_thread.wait()
        self._load_thread = None
        self._load_worker = None

    def _select_audio_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "انتخاب فایل صوتی",
            "",
            AUDIO_FILTER,
        )
        if not path:
            return

        try:
            validate_audio_path(path)
        except (FileNotFoundError, ValueError) as exc:
            self._audio_path = None
            self._duration_label.clear()
            self._long_audio_warning.hide()
            self._transcribe_btn.setEnabled(False)
            self._file_label.setText(NO_FILE_TEXT)
            QMessageBox.warning(self, "فایل نامعتبر", str(exc))
            return

        self._audio_path = path
        self._file_label.setText(path)
        self._update_audio_metadata(path)
        self._transcribe_btn.setEnabled(True)
        self._status_label.setText("فایل انتخاب شد")

    def _update_audio_metadata(self, path: str) -> None:
        duration = estimate_audio_duration(path)
        threshold_minutes = LONG_AUDIO_THRESHOLD_MINUTES

        if duration is None:
            self._duration_label.setText("مدت زمان: نامشخص")
            self._long_audio_warning.setText(
                "مدت زمان فایل مشخص نشد. برای فایل‌های طولانی، تبدیل ممکن است "
                "زمان‌بر باشد یا با خطا مواجه شود. فعلاً تقسیم خودکار فایل "
                "پشتیبانی نمی‌شود."
            )
            self._long_audio_warning.show()
            return

        duration_text = format_duration(duration)
        self._duration_label.setText(f"مدت زمان: {duration_text}")

        if is_audio_longer_than_threshold(duration, threshold_minutes):
            threshold_text = format_duration(threshold_minutes * 60)
            self._long_audio_warning.setText(
                f"هشدار: این فایل ({duration_text}) از آستانه {threshold_text} "
                f"({int(threshold_minutes)} دقیقه) طولانی‌تر است. "
                "تبدیل روی CPU ممکن است بسیار زمان‌بر باشد، حافظه کافی نداشته باشد، "
                "یا با خطا متوقف شود. فعلاً تقسیم خودکار فایل (chunking) "
                "پیاده‌سازی نشده است."
            )
            self._long_audio_warning.show()
            QMessageBox.warning(
                self,
                "فایل صوتی طولانی",
                self._long_audio_warning.text(),
            )
        else:
            self._long_audio_warning.hide()

    def _start_transcription(self) -> None:
        if not self._audio_path or self._is_transcribing():
            return

        if self._long_audio_warning.isVisible():
            reply = QMessageBox.question(
                self,
                "ادامه تبدیل؟",
                (
                    f"{self._long_audio_warning.text()}\n\n"
                    "آیا می‌خواهید با وجود این محدودیت‌ها ادامه دهید؟"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._transcription_cancelled = False
        self._set_busy(True)
        self._update_model_status()
        self._status_label.setText("در حال تبدیل... (اولین بار ممکن است مدل دانلود شود)")
        self._result_edit.clear()
        self._last_result = None
        self._last_processing_time = None
        self._save_btn.setEnabled(False)

        return_timestamps = self._timestamps_checkbox.isChecked()

        self._thread = QThread()
        self._worker = TranscriptionWorker(
            self._audio_path,
            engine=self._engine,
            return_timestamps=return_timestamps,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.started.connect(self._on_transcription_started)
        self._worker.progress.connect(self._on_transcription_progress)
        self._worker.finished.connect(self._on_transcription_finished)
        self._worker.failed.connect(self._on_transcription_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _cancel_transcription(self) -> None:
        """UI-level cancellation: ignore the result when the worker finishes."""
        if not self._is_transcribing():
            return

        self._transcription_cancelled = True
        self._cancel_btn.setEnabled(False)
        self._status_label.setText(
            "لغو شد — پردازش در پس‌زمینه ادامه دارد و نتیجه نادیده گرفته می‌شود"
        )

    def _on_transcription_started(self) -> None:
        self._status_label.setText("تبدیل آغاز شد...")

    def _on_transcription_progress(self, message: str) -> None:
        self._status_label.setText(message)
        if not self._engine.is_loaded:
            self._model_status_label.setText(MODEL_STATUS_LOADING)

    def _on_transcription_finished(self, result: dict) -> None:
        self._update_model_status()
        if self._transcription_cancelled:
            self._status_label.setText("تبدیل لغو شد")
            return

        self._last_result = result
        self._last_processing_time = result.get("processing_time")
        self._result_edit.setPlainText(format_display_text(result))

        processing_time = self._last_processing_time
        if processing_time is not None:
            status = (
                f"تبدیل با موفقیت انجام شد "
                f"({format_processing_time(processing_time)})"
            )
        else:
            status = "تبدیل با موفقیت انجام شد"
        self._status_label.setText(status)
        self._save_btn.setEnabled(True)
        self._set_busy(False)

    def _on_transcription_failed(self, message: str) -> None:
        self._update_model_status()
        if self._transcription_cancelled:
            self._status_label.setText("تبدیل لغو شد")
            return

        self._status_label.setText("خطا در تبدیل")
        self._set_busy(False)
        QMessageBox.critical(self, "خطا", message)

    def _cleanup_thread(self) -> None:
        if self._thread is not None:
            self._thread.wait()
        self._thread = None
        self._worker = None
        if self._transcription_cancelled:
            self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self._select_btn.setEnabled(not busy)
        self._transcribe_btn.setEnabled(not busy and self._audio_path is not None)
        self._cancel_btn.setEnabled(busy and not self._transcription_cancelled)
        self._copy_btn.setEnabled(not busy)
        self._save_btn.setEnabled(not busy and self._last_result is not None)
        self._clear_btn.setEnabled(not busy)
        self._timestamps_checkbox.setEnabled(not busy)
        if not self._engine.is_loaded:
            self._preload_btn.setEnabled(not busy)

    def _copy_result(self) -> None:
        text = self._result_edit.toPlainText()
        if not text:
            self._status_label.setText("متنی برای کپی وجود ندارد")
            return

        QGuiApplication.clipboard().setText(text)
        self._status_label.setText("متن در حافظه کپی شد")

    def _save_result(self) -> None:
        if self._last_result is None:
            self._status_label.setText("متنی برای ذخیره وجود ندارد")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره متن",
            "",
            TEXT_FILTER,
        )
        if not path:
            return

        if not path.lower().endswith(".txt"):
            path = f"{path}.txt"

        content = format_export_text(self._last_result, self._last_processing_time)
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
        except OSError as exc:
            self._status_label.setText("خطا در ذخیره فایل")
            QMessageBox.critical(self, "خطا", str(exc))
            return

        self._status_label.setText(f"متن ذخیره شد: {path}")

    def _clear_all(self) -> None:
        self._audio_path = None
        self._last_result = None
        self._last_processing_time = None
        self._file_label.setText(NO_FILE_TEXT)
        self._duration_label.clear()
        self._long_audio_warning.hide()
        self._result_edit.clear()
        self._transcribe_btn.setEnabled(False)
        self._save_btn.setEnabled(False)
        self._status_label.setText("آماده")
