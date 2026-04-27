from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from file_compressor.dependencies import GHOSTSCRIPT_DOWNLOAD_URL, detect_ghostscript
from file_compressor.discovery import discover_supported_files
from file_compressor.engine import compress_file
from file_compressor.models import CompressionJob, CompressionOptions
from file_compressor.planning import folder_batch_output_root, planned_batch_output_path
from file_compressor_app.view_model import FileJob, result_to_job


TRANSLATIONS = {
    "ko": {
        "window_title": "파일 압축기",
        "add_files": "파일 추가",
        "add_folder": "폴더 추가",
        "start_compression": "압축 시작",
        "settings": "고급 설정",
        "tools": "도구",
        "install_ghostscript": "Ghostscript 설치",
        "pdf_tool_available": "PDF 압축 도구: 사용 가능",
        "pdf_tool_missing": "PDF 압축 도구: 설치 필요",
        "ghostscript_install_button": "설치",
        "ghostscript_installed_button": "설치됨",
        "language": "언어",
        "image_size": "이미지 크기",
        "jpeg_quality": "JPEG 품질",
        "pdf_level": "PDF 수준",
        "headers": ["파일", "형식", "원본", "상태", "압축 후", "출력"],
        "initial_status": "파일을 추가하세요.",
        "ready_status": "{count}개 파일 준비됨.",
        "finished_status": "압축 완료.",
        "select_files": "파일 선택",
        "select_folder": "폴더 선택",
        "file_filter": "문서 (*.xlsx *.xlsm *.pptx *.pptm *.pdf *.hwpx *.hwp *.xls *.ppt);;모든 파일 (*.*)",
        "original": "원본",
        "screen": "화면용",
        "ebook": "전자책",
        "printer": "프린터",
        "prepress": "고품질",
        "pending": "대기",
        "processing": "처리 중",
        "completed": "완료",
        "skipped": "건너뜀",
        "failed": "실패",
    },
    "en": {
        "window_title": "File Compressor",
        "add_files": "Add files",
        "add_folder": "Add folder",
        "start_compression": "Start compression",
        "settings": "Advanced settings",
        "tools": "Tools",
        "install_ghostscript": "Install Ghostscript",
        "pdf_tool_available": "PDF compression tool: available",
        "pdf_tool_missing": "PDF compression tool: install required",
        "ghostscript_install_button": "Install",
        "ghostscript_installed_button": "Installed",
        "language": "Language",
        "image_size": "Image size",
        "jpeg_quality": "JPEG quality",
        "pdf_level": "PDF level",
        "headers": ["File", "Type", "Original", "Status", "Compressed", "Output"],
        "initial_status": "Add files to start.",
        "ready_status": "{count} file(s) ready.",
        "finished_status": "Compression finished.",
        "select_files": "Select files",
        "select_folder": "Select folder",
        "file_filter": "Documents (*.xlsx *.xlsm *.pptx *.pptm *.pdf *.hwpx *.hwp *.xls *.ppt);;All files (*.*)",
        "original": "Original",
        "screen": "Screen",
        "ebook": "Ebook",
        "printer": "Printer",
        "prepress": "High quality",
        "pending": "Pending",
        "processing": "Processing",
        "completed": "Completed",
        "skipped": "Skipped",
        "failed": "Failed",
    },
}


class DropTable(QTableWidget):
    def __init__(self, on_files):
        super().__init__(0, 6)
        self.on_files = on_files
        self.setAcceptDrops(True)
        self.setHorizontalHeaderLabels(["File", "Type", "Original", "Status", "Compressed", "Output"])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.on_files(paths)
        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = "ko"
        self._status_key = "initial_status"
        self._status_context: dict[str, int] = {}
        self.setWindowTitle(self.tr("window_title"))
        self.resize(980, 560)
        self.jobs: list[FileJob] = []
        self.ghostscript_status = detect_ghostscript()

        self.table = DropTable(self.add_paths)
        self.status_label = QLabel()
        self.add_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.start_button = QPushButton()
        self.pdf_tool_status_label = QLabel()
        self.ghostscript_install_button = QPushButton()
        self.language_label = QLabel()
        self.image_size_label = QLabel()
        self.jpeg_quality_label = QLabel()
        self.pdf_level_label = QLabel()
        self.language_combo = QComboBox()
        self.image_dimension_combo = QComboBox()
        self.jpeg_quality_combo = QComboBox()
        self.pdf_preset_combo = QComboBox()

        self._setup_language_control()
        self._setup_option_controls()
        self._setup_menu()

        self.add_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.start_button.clicked.connect(self.compress_jobs)
        self.ghostscript_install_button.clicked.connect(self.open_ghostscript_download)
        self.language_combo.currentIndexChanged.connect(self.change_language)

        actions = QHBoxLayout()
        actions.addWidget(self.add_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.start_button)
        actions.addStretch()

        self.settings_group = QGroupBox()
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.language_label)
        settings_layout.addWidget(self.language_combo)
        settings_layout.addWidget(self.image_size_label)
        settings_layout.addWidget(self.image_dimension_combo)
        settings_layout.addWidget(self.jpeg_quality_label)
        settings_layout.addWidget(self.jpeg_quality_combo)
        settings_layout.addWidget(self.pdf_level_label)
        settings_layout.addWidget(self.pdf_preset_combo)
        settings_layout.addWidget(self.pdf_tool_status_label)
        settings_layout.addWidget(self.ghostscript_install_button)
        settings_layout.addStretch()
        self.settings_group.setLayout(settings_layout)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.settings_group)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)
        self.apply_language()

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def _setup_language_control(self):
        self.language_combo.addItem("한국어", "ko")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex(self.language_combo.findData("ko"))

    def _setup_option_controls(self):
        self._set_image_dimension_items(1600)
        self._set_jpeg_quality_items(78)
        self._set_pdf_preset_items("screen")

    def _setup_menu(self):
        self.tools_menu = self.menuBar().addMenu("")
        self.ghostscript_install_action = QAction(self)
        self.ghostscript_install_action.triggered.connect(self.open_ghostscript_download)
        self.tools_menu.addAction(self.ghostscript_install_action)

    def _set_image_dimension_items(self, selected):
        self.image_dimension_combo.blockSignals(True)
        self.image_dimension_combo.clear()
        self.image_dimension_combo.addItem("800 px", 800)
        self.image_dimension_combo.addItem("1200 px", 1200)
        self.image_dimension_combo.addItem("1600 px", 1600)
        self.image_dimension_combo.addItem(str(self.tr("original")), None)
        self.image_dimension_combo.blockSignals(False)
        self.image_dimension_combo.setCurrentIndex(self.image_dimension_combo.findData(selected))

    def _set_jpeg_quality_items(self, selected):
        self.jpeg_quality_combo.blockSignals(True)
        self.jpeg_quality_combo.clear()
        for quality in (50, 65, 78, 90):
            self.jpeg_quality_combo.addItem(str(quality), quality)
        self.jpeg_quality_combo.blockSignals(False)
        self.jpeg_quality_combo.setCurrentIndex(self.jpeg_quality_combo.findData(selected))

    def _set_pdf_preset_items(self, selected):
        self.pdf_preset_combo.blockSignals(True)
        self.pdf_preset_combo.clear()
        self.pdf_preset_combo.addItem(str(self.tr("screen")), "screen")
        self.pdf_preset_combo.addItem(str(self.tr("ebook")), "ebook")
        self.pdf_preset_combo.addItem(str(self.tr("printer")), "printer")
        self.pdf_preset_combo.addItem(str(self.tr("prepress")), "prepress")
        self.pdf_preset_combo.blockSignals(False)
        self.pdf_preset_combo.setCurrentIndex(self.pdf_preset_combo.findData(selected))

    def change_language(self):
        self.language = self.language_combo.currentData()
        self.apply_language()

    def apply_language(self):
        selected_dimension = self.image_dimension_combo.currentData()
        selected_quality = self.jpeg_quality_combo.currentData()
        selected_pdf_preset = self.pdf_preset_combo.currentData()

        self.setWindowTitle(str(self.tr("window_title")))
        self.add_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.start_button.setText(str(self.tr("start_compression")))
        self.tools_menu.setTitle(str(self.tr("tools")))
        self.ghostscript_install_action.setText(str(self.tr("install_ghostscript")))
        self.settings_group.setTitle(str(self.tr("settings")))
        self.language_label.setText(str(self.tr("language")))
        self.image_size_label.setText(str(self.tr("image_size")))
        self.jpeg_quality_label.setText(str(self.tr("jpeg_quality")))
        self.pdf_level_label.setText(str(self.tr("pdf_level")))
        self.table.setHorizontalHeaderLabels(self.tr("headers"))

        self._set_image_dimension_items(selected_dimension)
        self._set_jpeg_quality_items(selected_quality)
        self._set_pdf_preset_items(selected_pdf_preset)
        self._refresh_pdf_tool_status()
        self._refresh_status_label()
        self.refresh_table()

    def _refresh_pdf_tool_status(self):
        if self.ghostscript_status.available:
            self.pdf_tool_status_label.setText(str(self.tr("pdf_tool_available")))
            self.ghostscript_install_button.setText(str(self.tr("ghostscript_installed_button")))
            self.ghostscript_install_button.setEnabled(False)
            return

        self.pdf_tool_status_label.setText(str(self.tr("pdf_tool_missing")))
        self.ghostscript_install_button.setText(str(self.tr("ghostscript_install_button")))
        self.ghostscript_install_button.setEnabled(True)

    def open_ghostscript_download(self):
        QDesktopServices.openUrl(QUrl(GHOSTSCRIPT_DOWNLOAD_URL))

    def _set_status(self, key: str, **context: int):
        self._status_key = key
        self._status_context = context
        self._refresh_status_label()

    def _refresh_status_label(self):
        self.status_label.setText(str(self.tr(self._status_key)).format(**self._status_context))

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def current_options(self) -> CompressionOptions:
        return CompressionOptions(
            max_image_dimension=self.image_dimension_combo.currentData(),
            jpeg_quality=self.jpeg_quality_combo.currentData(),
            pdf_preset=self.pdf_preset_combo.currentData(),
        )

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("file_filter")),
        )
        self.add_files([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            str(self.tr("select_folder")),
            "",
        )
        if folder:
            self.add_folder(Path(folder))

    def add_files(self, paths: list[Path]):
        for path in paths:
            if path.is_file():
                self._append_job(path)
        self.refresh_table()
        self._set_status("ready_status", count=len(self.jobs))

    def add_folder(self, folder: Path):
        if not folder.is_dir():
            return

        self._append_folder_jobs(folder)
        self.refresh_table()
        self._set_status("ready_status", count=len(self.jobs))

    def add_paths(self, paths: list[Path]):
        for path in paths:
            if path.is_dir():
                self._append_folder_jobs(path)
            elif path.is_file():
                self._append_job(path)
        self.refresh_table()
        self._set_status("ready_status", count=len(self.jobs))

    def _append_folder_jobs(self, folder: Path):
        batch_root = folder_batch_output_root(folder)
        for source in discover_supported_files(folder):
            output = planned_batch_output_path(source, folder, batch_root=batch_root)
            compression_job = CompressionJob(source=source, output=output, batch_root=batch_root)
            self._append_job(source, compression_job=compression_job)

    def _append_job(self, path: Path, compression_job: CompressionJob | None = None):
        size = path.stat().st_size
        output_path = compression_job.output if compression_job else None
        self.jobs.append(
            FileJob(
                path=path,
                original_size=size,
                output_path=output_path,
                compression_job=compression_job,
            )
        )

    def compress_jobs(self):
        options = self.current_options()
        for index, job in enumerate(list(self.jobs)):
            self.jobs[index].status = "processing"
            self.refresh_table()
            QApplication.processEvents()

            target = job.compression_job or job.path
            result = compress_file(target, options)
            self.jobs[index] = result_to_job(result, compression_job=job.compression_job)
            self.refresh_table()
            QApplication.processEvents()
        self._set_status("finished_status")

    def refresh_table(self):
        self.table.setRowCount(len(self.jobs))
        for row, job in enumerate(self.jobs):
            values = [
                job.name,
                job.kind,
                job.original_size_text,
                self.status_text(job.status),
                job.compressed_size_text,
                job.output_text,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(job.message if column == 3 else value)
                if column == 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()
