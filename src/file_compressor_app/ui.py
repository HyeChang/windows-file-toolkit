from pathlib import Path

from PySide6.QtCore import Qt
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

from file_compressor.engine import compress_file
from file_compressor.models import CompressionOptions
from file_compressor_app.view_model import FileJob, result_to_job


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
        self.setWindowTitle("File Compressor")
        self.resize(980, 560)
        self.jobs: list[FileJob] = []

        self.table = DropTable(self.add_files)
        self.status_label = QLabel("Add files to start.")
        self.add_button = QPushButton("Add files")
        self.start_button = QPushButton("Start compression")
        self.image_dimension_combo = QComboBox()
        self.jpeg_quality_combo = QComboBox()
        self.pdf_preset_combo = QComboBox()

        self._setup_option_controls()

        self.add_button.clicked.connect(self.pick_files)
        self.start_button.clicked.connect(self.compress_jobs)

        actions = QHBoxLayout()
        actions.addWidget(self.add_button)
        actions.addWidget(self.start_button)
        actions.addStretch()

        settings = QGroupBox("Advanced settings")
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Image size"))
        settings_layout.addWidget(self.image_dimension_combo)
        settings_layout.addWidget(QLabel("JPEG quality"))
        settings_layout.addWidget(self.jpeg_quality_combo)
        settings_layout.addWidget(QLabel("PDF level"))
        settings_layout.addWidget(self.pdf_preset_combo)
        settings_layout.addStretch()
        settings.setLayout(settings_layout)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(settings)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def _setup_option_controls(self):
        self.image_dimension_combo.addItem("800 px", 800)
        self.image_dimension_combo.addItem("1200 px", 1200)
        self.image_dimension_combo.addItem("1600 px", 1600)
        self.image_dimension_combo.addItem("Original", None)
        self.image_dimension_combo.setCurrentIndex(self.image_dimension_combo.findData(1600))

        for quality in (50, 65, 78, 90):
            self.jpeg_quality_combo.addItem(str(quality), quality)
        self.jpeg_quality_combo.setCurrentIndex(self.jpeg_quality_combo.findData(78))

        self.pdf_preset_combo.addItem("Screen", "screen")
        self.pdf_preset_combo.addItem("Ebook", "ebook")
        self.pdf_preset_combo.addItem("Printer", "printer")
        self.pdf_preset_combo.addItem("High quality", "prepress")
        self.pdf_preset_combo.setCurrentIndex(self.pdf_preset_combo.findData("screen"))

    def current_options(self) -> CompressionOptions:
        return CompressionOptions(
            max_image_dimension=self.image_dimension_combo.currentData(),
            jpeg_quality=self.jpeg_quality_combo.currentData(),
            pdf_preset=self.pdf_preset_combo.currentData(),
        )

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            "",
            "Documents (*.xlsx *.xlsm *.pptx *.pptm *.pdf *.hwpx *.hwp *.xls *.ppt);;All files (*.*)",
        )
        self.add_files([Path(file) for file in files])

    def add_files(self, paths: list[Path]):
        for path in paths:
            if path.is_file():
                size = path.stat().st_size
                self.jobs.append(FileJob(path=path, original_size=size))
        self.refresh_table()
        self.status_label.setText(f"{len(self.jobs)} file(s) ready.")

    def compress_jobs(self):
        options = self.current_options()
        for index, job in enumerate(list(self.jobs)):
            self.jobs[index].status = "processing"
            self.refresh_table()
            QApplication.processEvents()

            result = compress_file(job.path, options)
            self.jobs[index] = result_to_job(result)
            self.refresh_table()
            QApplication.processEvents()
        self.status_label.setText("Compression finished.")

    def refresh_table(self):
        self.table.setRowCount(len(self.jobs))
        for row, job in enumerate(self.jobs):
            values = [
                job.name,
                job.kind,
                job.original_size_text,
                job.status,
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
