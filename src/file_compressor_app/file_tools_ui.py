from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDateTime, QTimer, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QTransform
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from file_compressor.dependencies import detect_jpegtran
from file_compressor.file_tools import (
    ClassificationPlan,
    DateChangePlan,
    RenameOptions,
    RenamePlan,
    apply_classification_plan,
    apply_date_change_plan,
    apply_rename_plan,
    build_classification_plan,
    build_date_change_plan,
    build_rename_plan,
    get_file_timestamps,
    undo_classification_results,
    undo_date_change_results,
    undo_rename_results,
)
from file_compressor.image_rotation import (
    ImageRotationPlan,
    apply_image_rotation_plan,
    build_image_rotation_plan,
)
from file_compressor.image_ratio_classification import (
    SUPPORTED_IMAGE_SUFFIXES as RATIO_SUPPORTED_IMAGE_SUFFIXES,
    ImageRatioOptions,
    ImageRatioPlan,
    apply_image_ratio_classification_plan,
    build_image_ratio_classification_plan,
    effective_threshold_ratio,
    image_dimensions,
)


TRANSLATIONS = {
    "ko": {
        "add_files": "파일 추가",
        "add_folder": "폴더 추가",
        "remove_selected": "선택 삭제",
        "clear_list": "목록 비우기",
        "preview": "미리보기",
        "apply": "적용",
        "undo": "되돌리기",
        "select_files": "파일 선택",
        "select_folder": "폴더 선택",
        "all_files_filter": "모든 파일 (*.*)",
        "rename_options": "이름 변경 옵션",
        "prefix": "앞에 추가",
        "suffix": "뒤에 추가",
        "find": "찾기",
        "replace": "바꾸기",
        "clean_spaces": "공백 정리",
        "clean_special": "특수문자 제거",
        "number_files": "번호 붙이기",
        "number_start": "시작 번호",
        "date_format": "날짜 형식",
        "date_fallback": "날짜 없을 때",
        "date_fallback_none": "사용 안 함",
        "date_fallback_created": "등록일 사용",
        "date_fallback_modified": "수정일 사용",
        "date_change_options": "날짜 변경 옵션",
        "date_source": "날짜 기준",
        "manual": "직접 입력",
        "filename": "파일명 날짜",
        "now": "현재 시간",
        "change_created": "생성일 변경",
        "change_modified": "수정일 변경",
        "created_input": "생성일",
        "modified_input": "수정일",
        "preserve_modified_time": "수정일 유지",
        "rename_headers": ["원본", "변경 후", "상태", "위치"],
        "classify_headers": ["파일", "크기", "분류", "대상 폴더", "상태"],
        "date_headers": ["파일", "생성일", "수정일", "상태", "위치"],
        "image_rotate_headers": ["파일", "회전", "출력", "상태"],
        "image_ratio_headers": ["파일", "크기", "이미지 크기", "비율", "분류", "상태", "출력"],
        "classify_operation": "작업",
        "classify_move": "이동",
        "classify_copy": "복사",
        "classify_strategy": "분류 기준",
        "classify_by_extension": "확장자 기준",
        "classify_by_name_similarity": "파일명 유사도 기준",
        "classify_sensitivity": "민감도",
        "sensitivity_strict": "엄격",
        "sensitivity_medium_strict": "약간 엄격",
        "sensitivity_normal": "보통",
        "sensitivity_medium_loose": "약간 느슨",
        "sensitivity_loose": "느슨",
        "duplicate_action": "중복 파일",
        "duplicate_keep": "미삭제",
        "duplicate_delete": "삭제",
        "duplicate_detail_keep": "중복 발생\n원본: {source}\n기존 파일: {target}\n처리: 미삭제(기존 파일 유지)",
        "duplicate_detail_delete": "중복 처리\n원본: {source}\n기존 파일: {target}\n처리: 삭제(원본 중복 파일 삭제)",
        "prefer_existing_folders": "기존 유사 폴더 우선 사용",
        "skip_single_file_folder": "단일 파일은 폴더 생성 안 함",
        "folder_candidate_group": "후보 폴더 선택",
        "folder_candidate_label": "선택 그룹: {category}",
        "folder_candidate_headers": ["후보 폴더", "일치 단어", "전체 경로"],
        "folder_candidate_file_headers": ["적용", "파일", "위치"],
        "folder_candidate_files": "적용할 파일",
        "folder_candidate_terms": "일치: {terms}",
        "folder_candidate_new": "새 폴더 생성: {folder}",
        "folder_candidate_apply": "선택 적용",
        "folder_candidate_none": "일치 단어 없음",
        "show_size": "크기 보기",
        "classify_options": "분류 설정",
        "classify_summary": "분류 요약",
        "expand_summary": "크게 보기",
        "classify_summary_headers": ["폴더", "파일 수"],
        "classify_summary_file_headers": ["파일", "예정 위치"],
        "classify_summary_text": "생성 폴더 {folders}개 / 배치 파일 {files}개",
        "classify_summary_files_text": "{folder} 파일 {files}개",
        "classify_summary_files_empty": "폴더를 선택하면 파일 목록이 표시됩니다.",
        "selected_target_folder": "선택 대상 폴더: {path}",
        "selected_target_folder_empty": "선택 대상 폴더: -",
        "folder_selection_title": "폴더 포함 선택",
        "folder_selection_message": "추가할 폴더를 체크하세요. 체크 해제한 폴더의 파일은 제외됩니다.",
        "folder_selection_headers": ["폴더", "파일 수"],
        "select_all": "전체 선택",
        "deselect_all": "전체 해제",
        "confirm": "확인",
        "cancel": "취소",
        "select_output_folder_button": "출력 폴더 선택",
        "select_output_folder": "출력 폴더 선택",
        "output_folder_default": "출력 폴더: 원본 위치",
        "output_folder_missing": "출력 폴더: 원본 폴더에 정리 폴더 자동 생성",
        "output_folder_selected": "출력 폴더: {path}",
        "image_rotate_options": "이미지 회전 옵션",
        "image_ratio_options": "이미지 비율 분류 옵션",
        "image_ratio_direction": "방향",
        "image_ratio_wide": "가로가 더 긴 이미지",
        "image_ratio_tall": "세로가 더 긴 이미지",
        "image_ratio_min": "최소 비율",
        "image_ratio_reference_multiplier": "기준 배율",
        "select_reference_image": "기준 이미지 선택",
        "clear_reference_image": "기준 이미지 해제",
        "image_ratio_reference_empty": "기준 이미지: 없음 - 이미지 파일을 여기나 기준 이미지 선택 버튼에 드롭",
        "image_ratio_reference_drop_hint": "이미지 파일을 드롭하면 기준 이미지로 설정됩니다.",
        "image_ratio_reference_info": "기준 이미지: {width} x {height} / 비율 {ratio}",
        "image_ratio_reference_condition": "기준 이미지: {width} x {height} / 기준 비율 {base_ratio} / 현재 조건 {threshold_ratio} 이상",
        "image_ratio_condition_wide": "선택 조건: 가로 / 세로 >= {ratio}. 예: 세로 1000px이면 가로 {width}px 이상인 이미지가 선택됩니다.",
        "image_ratio_condition_tall": "선택 조건: 세로 / 가로 >= {ratio}. 예: 가로 1000px이면 세로 {height}px 이상인 이미지가 선택됩니다.",
        "image_ratio_reference_condition_wide": "기준 {width} x {height}에서 시작해 배율 {multiplier} 적용. 선택 조건: 가로 / 세로 >= {ratio}. 예: 세로 1000px이면 가로 {target}px 이상.",
        "image_ratio_reference_condition_tall": "기준 {width} x {height}에서 시작해 배율 {multiplier} 적용. 선택 조건: 세로 / 가로 >= {ratio}. 예: 가로 1000px이면 세로 {target}px 이상.",
        "image_ratio_output_default": "출력 폴더: 원본 폴더에 이미지 비율 분류 폴더 자동 생성",
        "image_ratio_idle": "이미지를 추가하세요.",
        "image_ratio_processing": "분류 중...",
        "image_ratio_preview_summary": "미리보기: 조건 일치 {matched}, 조건 미달 {missed}, 기타 {other}, 실패 {failed}",
        "image_ratio_result_summary": "처리 결과: 완료 {completed}, 건너뜀 {skipped}, 실패 {failed}",
        "image_ratio_match": "조건 일치",
        "image_ratio_miss": "조건 미달",
        "image_ratio_read_failed": "읽기 실패",
        "image_ratio_non_image": "이미지 아님",
        "rotation": "회전",
        "right_90": "오른쪽 90도",
        "left_90": "왼쪽 90도",
        "rotate_180": "180도",
        "allow_lossy_jpeg": "손실 회전 허용",
        "image_files_filter": "이미지 (*.jpg *.jpeg *.png *.bmp);;모든 파일 (*.*)",
        "image_rotate_idle": "이미지를 추가하세요.",
        "image_rotate_processing": "처리 중...",
        "image_rotate_preview_summary": "미리보기: 준비 {ready}, 건너뜀 {skipped}, 실패 {failed}",
        "image_rotate_result_summary": "처리 결과: 완료 {completed}, 건너뜀 {skipped}, 실패 {failed}",
        "image_preview": "이미지 미리보기",
        "preview_unavailable": "미리보기 불가",
        "ready": "준비",
        "completed": "완료",
        "unchanged": "변경 없음",
        "skipped": "건너뜀",
        "duplicate": "중복 파일",
        "duplicate_deleted": "중복 삭제",
        "needs_choice": "선택 필요",
        "failed": "실패",
        "undone": "되돌림",
        "details": "파일 상세 정보",
        "no_selection": "선택 없음",
        "file_name": "파일명",
        "full_path": "전체 경로",
        "extension": "확장자",
        "size": "크기",
        "created": "생성일",
        "modified": "수정일",
        "planned_path": "예정 위치",
        "status": "상태",
        "none": "날짜 변경 안 함",
        "prefix_dash": "YYYY-MM-DD_파일명",
        "prefix_underscore": "YYYY_MM_DD_파일명",
        "prefix_compact": "YYYYMMDD_파일명",
        "prefix_short_compact": "YYMMDD_파일명",
        "suffix_dash": "파일명_YYYY-MM-DD",
        "suffix_underscore": "파일명_YYYY_MM_DD",
        "suffix_compact": "파일명_YYYYMMDD",
        "suffix_short_compact": "파일명_YYMMDD",
    },
    "en": {
        "add_files": "Add files",
        "add_folder": "Add folder",
        "remove_selected": "Remove selected",
        "clear_list": "Clear list",
        "preview": "Preview",
        "apply": "Apply",
        "undo": "Undo",
        "select_files": "Select files",
        "select_folder": "Select folder",
        "all_files_filter": "All files (*.*)",
        "rename_options": "Rename options",
        "prefix": "Prefix",
        "suffix": "Suffix",
        "find": "Find",
        "replace": "Replace",
        "clean_spaces": "Clean spaces",
        "clean_special": "Remove special characters",
        "number_files": "Number files",
        "number_start": "Start number",
        "date_format": "Date format",
        "date_fallback": "When no date",
        "date_fallback_none": "Do not add",
        "date_fallback_created": "Use created date",
        "date_fallback_modified": "Use modified date",
        "date_change_options": "Date change options",
        "date_source": "Date source",
        "manual": "Manual",
        "filename": "File name date",
        "now": "Current time",
        "change_created": "Change created",
        "change_modified": "Change modified",
        "created_input": "Created",
        "modified_input": "Modified",
        "preserve_modified_time": "Preserve modified date",
        "rename_headers": ["Original", "New name", "Status", "Location"],
        "classify_headers": ["File", "Size", "Category", "Target folder", "Status"],
        "date_headers": ["File", "Created", "Modified", "Status", "Location"],
        "image_rotate_headers": ["File", "Rotation", "Output", "Status"],
        "image_ratio_headers": ["File", "Size", "Image size", "Ratio", "Class", "Status", "Output"],
        "classify_operation": "Operation",
        "classify_move": "Move",
        "classify_copy": "Copy",
        "classify_strategy": "Classify by",
        "classify_by_extension": "Extension",
        "classify_by_name_similarity": "Similar file names",
        "classify_sensitivity": "Sensitivity",
        "sensitivity_strict": "Strict",
        "sensitivity_medium_strict": "Slightly strict",
        "sensitivity_normal": "Normal",
        "sensitivity_medium_loose": "Slightly loose",
        "sensitivity_loose": "Loose",
        "duplicate_action": "Duplicates",
        "duplicate_keep": "Keep",
        "duplicate_delete": "Delete",
        "duplicate_detail_keep": "Duplicate found\nSource: {source}\nExisting file: {target}\nAction: kept source and existing file",
        "duplicate_detail_delete": "Duplicate handled\nSource: {source}\nExisting file: {target}\nAction: deleted duplicate source",
        "prefer_existing_folders": "Use similar existing folders",
        "skip_single_file_folder": "Do not create folder for a single file",
        "folder_candidate_group": "Candidate folders",
        "folder_candidate_label": "Group: {category}",
        "folder_candidate_headers": ["Candidate folder", "Matched terms", "Full path"],
        "folder_candidate_file_headers": ["Apply", "File", "Location"],
        "folder_candidate_files": "Files to apply",
        "folder_candidate_terms": "Matched: {terms}",
        "folder_candidate_new": "Create new folder: {folder}",
        "folder_candidate_apply": "Apply choice",
        "folder_candidate_none": "No matched terms",
        "show_size": "Show size",
        "classify_options": "Classify settings",
        "classify_summary": "Summary",
        "expand_summary": "Expand",
        "classify_summary_headers": ["Folder", "Files"],
        "classify_summary_file_headers": ["File", "Planned path"],
        "classify_summary_text": "{folders} folder(s) / {files} file(s)",
        "classify_summary_files_text": "{folder}: {files} file(s)",
        "classify_summary_files_empty": "Select a folder to show its files.",
        "selected_target_folder": "Selected target folder: {path}",
        "selected_target_folder_empty": "Selected target folder: -",
        "folder_selection_title": "Choose folders to include",
        "folder_selection_message": "Check the folders to add. Unchecked folders are excluded.",
        "folder_selection_headers": ["Folder", "Files"],
        "select_all": "Select all",
        "deselect_all": "Clear all",
        "confirm": "OK",
        "cancel": "Cancel",
        "select_output_folder_button": "Select output folder",
        "select_output_folder": "Select output folder",
        "output_folder_default": "Output folder: original location",
        "output_folder_missing": "Output folder: auto-create Organized folder beside source files",
        "output_folder_selected": "Output folder: {path}",
        "image_rotate_options": "Image rotation options",
        "image_ratio_options": "Image ratio classification",
        "image_ratio_direction": "Direction",
        "image_ratio_wide": "Wider than tall",
        "image_ratio_tall": "Taller than wide",
        "image_ratio_min": "Minimum ratio",
        "image_ratio_reference_multiplier": "Reference multiplier",
        "select_reference_image": "Select reference image",
        "clear_reference_image": "Clear reference",
        "image_ratio_reference_empty": "Reference image: none - drop an image here or on Select reference image",
        "image_ratio_reference_drop_hint": "Drop an image file to use it as the reference image.",
        "image_ratio_reference_info": "Reference image: {width} x {height} / ratio {ratio}",
        "image_ratio_reference_condition": "Reference image: {width} x {height} / base ratio {base_ratio} / current threshold {threshold_ratio}+",
        "image_ratio_condition_wide": "Condition: width / height >= {ratio}. Example: if height is 1000px, width must be {width}px or more.",
        "image_ratio_condition_tall": "Condition: height / width >= {ratio}. Example: if width is 1000px, height must be {height}px or more.",
        "image_ratio_reference_condition_wide": "Starts from {width} x {height}, multiplier {multiplier}. Condition: width / height >= {ratio}. Example: if height is 1000px, width must be {target}px or more.",
        "image_ratio_reference_condition_tall": "Starts from {width} x {height}, multiplier {multiplier}. Condition: height / width >= {ratio}. Example: if width is 1000px, height must be {target}px or more.",
        "image_ratio_output_default": "Output folder: auto-create Image Ratio Classification beside source files",
        "image_ratio_idle": "Add images to start.",
        "image_ratio_processing": "Classifying...",
        "image_ratio_preview_summary": "Preview: matched {matched}, missed {missed}, other {other}, failed {failed}",
        "image_ratio_result_summary": "Result: completed {completed}, skipped {skipped}, failed {failed}",
        "image_ratio_match": "Matched",
        "image_ratio_miss": "Missed",
        "image_ratio_read_failed": "Read failed",
        "image_ratio_non_image": "Not an image",
        "rotation": "Rotation",
        "right_90": "Right 90 degrees",
        "left_90": "Left 90 degrees",
        "rotate_180": "180 degrees",
        "allow_lossy_jpeg": "Allow lossy rotation",
        "image_files_filter": "Images (*.jpg *.jpeg *.png *.bmp);;All files (*.*)",
        "image_rotate_idle": "Add images to start.",
        "image_rotate_processing": "Processing...",
        "image_rotate_preview_summary": "Preview: ready {ready}, skipped {skipped}, failed {failed}",
        "image_rotate_result_summary": "Result: completed {completed}, skipped {skipped}, failed {failed}",
        "image_preview": "Image preview",
        "preview_unavailable": "Preview unavailable",
        "ready": "Ready",
        "completed": "Completed",
        "unchanged": "Unchanged",
        "skipped": "Skipped",
        "duplicate": "Duplicate",
        "duplicate_deleted": "Duplicate deleted",
        "needs_choice": "Needs choice",
        "failed": "Failed",
        "undone": "Undone",
        "details": "File details",
        "no_selection": "No selection",
        "file_name": "File name",
        "full_path": "Full path",
        "extension": "Extension",
        "size": "Size",
        "created": "Created",
        "modified": "Modified",
        "planned_path": "Planned path",
        "status": "Status",
        "none": "Do not change dates",
        "prefix_dash": "YYYY-MM-DD_filename",
        "prefix_underscore": "YYYY_MM_DD_filename",
        "prefix_compact": "YYYYMMDD_filename",
        "prefix_short_compact": "YYMMDD_filename",
        "suffix_dash": "filename_YYYY-MM-DD",
        "suffix_underscore": "filename_YYYY_MM_DD",
        "suffix_compact": "filename_YYYYMMDD",
        "suffix_short_compact": "filename_YYMMDD",
    },
}


def _local_drop_paths(event) -> list[Path]:
    mime_data = event.mimeData()
    paths: list[Path] = []
    if mime_data.hasUrls():
        for url in mime_data.urls():
            if url.isLocalFile():
                local_file = url.toLocalFile()
                if local_file:
                    paths.append(Path(local_file))
    if not paths and mime_data.hasText():
        for line in mime_data.text().splitlines():
            text = line.strip()
            if not text:
                continue
            if text.startswith("file:///"):
                text = text.removeprefix("file:///")
            paths.append(Path(text))
    if not paths:
        for mime_format in mime_data.formats():
            if "FileNameW" in mime_format:
                raw = bytes(mime_data.data(mime_format))
                for text in raw.decode("utf-16le", errors="ignore").split("\x00"):
                    text = text.strip()
                    if text:
                        paths.append(Path(text))
            elif 'FileName"' in mime_format or mime_format.endswith("FileName"):
                raw = bytes(mime_data.data(mime_format))
                for text in raw.decode("mbcs", errors="ignore").split("\x00"):
                    text = text.strip()
                    if text:
                        paths.append(Path(text))
    return paths


class FileToolTable(QTableWidget):
    def __init__(self, columns: int, on_files=None):
        super().__init__(0, columns)
        self.on_files = on_files
        self.setAcceptDrops(on_files is not None)
        self.viewport().setAcceptDrops(on_files is not None)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setWordWrap(False)

    def dragEnterEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dragMoveEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dropEvent(self, event):
        paths = _local_drop_paths(event)
        if self.on_files is None or not paths:
            return

        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        QTimer.singleShot(0, lambda paths=paths: self.on_files(paths))


class FileDropLabel(QLabel):
    def __init__(self, on_files, parent: QWidget | None = None):
        super().__init__(parent)
        self.on_files = on_files
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self.setStyleSheet("border: 1px dashed #666; border-radius: 4px; padding: 4px 6px;")

    def dragEnterEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dragMoveEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dropEvent(self, event):
        paths = _local_drop_paths(event)
        if not paths:
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        QTimer.singleShot(0, lambda paths=paths: self.on_files(paths))


class FileDropButton(QPushButton):
    def __init__(self, on_files, parent: QWidget | None = None):
        super().__init__(parent)
        self.on_files = on_files
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dragMoveEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dropEvent(self, event):
        paths = _local_drop_paths(event)
        if not paths:
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        QTimer.singleShot(0, lambda paths=paths: self.on_files(paths))


class FolderSelectionDialog(QDialog):
    def __init__(self, folder: Path, language: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.folder = Path(folder)
        self.language = language
        self._updating_checks = False

        self.message_label = QLabel(str(self.tr("folder_selection_message")))
        self.message_label.setWordWrap(True)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(self.tr("folder_selection_headers"))
        self.tree.setTextElideMode(Qt.TextElideMode.ElideMiddle)

        root_item = self._build_folder_item(self.folder)
        self.tree.addTopLevelItem(root_item)
        self.tree.itemExpanded.connect(self._ensure_children_loaded)
        self.tree.itemChanged.connect(self._item_changed)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.select_all_button = QPushButton(str(self.tr("select_all")))
        self.deselect_all_button = QPushButton(str(self.tr("deselect_all")))
        self.confirm_button = QPushButton(str(self.tr("confirm")))
        self.cancel_button = QPushButton(str(self.tr("cancel")))
        self.select_all_button.clicked.connect(lambda: self._set_all_checked(Qt.CheckState.Checked))
        self.deselect_all_button.clicked.connect(lambda: self._set_all_checked(Qt.CheckState.Unchecked))
        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.select_all_button)
        action_layout.addWidget(self.deselect_all_button)
        action_layout.addStretch()
        action_layout.addWidget(self.confirm_button)
        action_layout.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self.message_label)
        layout.addWidget(self.tree, 1)
        layout.addLayout(action_layout)
        self.setLayout(layout)
        self.setWindowTitle(str(self.tr("folder_selection_title")))
        self.resize(560, 420)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def selected_files(self) -> list[Path]:
        return list(_files_from_scan_roots(self.selected_scan_roots()))

    def selected_paths(self) -> list[Path]:
        paths: list[Path] = []
        for scan_root in self.selected_scan_roots():
            if isinstance(scan_root, tuple):
                paths.append(Path(scan_root[0]))
            else:
                paths.append(Path(scan_root))
        return paths

    def selected_scan_roots(self) -> list[Path | tuple[Path, tuple[Path, ...]]]:
        root = self.tree.topLevelItem(0)
        if root is None:
            return []
        selections, _, _ = self._collect_selected_scan_roots(root)
        return selections

    def _build_folder_item(self, folder: Path, *, populate_children: bool = False) -> QTreeWidgetItem:
        item = QTreeWidgetItem([folder.name or str(folder), "-"])
        item.setToolTip(0, str(folder))
        item.setData(0, Qt.ItemDataRole.UserRole, str(folder))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked)
        if populate_children:
            for child in _child_folders(folder):
                item.addChild(self._build_folder_item(child))
        else:
            self._add_placeholder(item)
        return item

    def _add_placeholder(self, item: QTreeWidgetItem):
        placeholder = QTreeWidgetItem(["...", ""])
        placeholder.setData(0, Qt.ItemDataRole.UserRole, None)
        item.addChild(placeholder)

    def _is_placeholder(self, item: QTreeWidgetItem) -> bool:
        return item.data(0, Qt.ItemDataRole.UserRole) is None

    def _ensure_children_loaded(self, item: QTreeWidgetItem):
        if item.childCount() != 1 or not self._is_placeholder(item.child(0)):
            return
        item.takeChild(0)
        folder = Path(item.data(0, Qt.ItemDataRole.UserRole))
        state = item.checkState(0)
        for child in _child_folders(folder):
            child_item = self._build_folder_item(child)
            child_item.setCheckState(0, state)
            item.addChild(child_item)

    def _item_changed(self, item: QTreeWidgetItem, column: int):
        if self._updating_checks or column != 0:
            return
        self._updating_checks = True
        try:
            state = item.checkState(0)
            if state != Qt.CheckState.PartiallyChecked:
                self._set_children_check_state(item, state)
            if state == Qt.CheckState.Checked:
                self._set_ancestor_check_state(item.parent(), Qt.CheckState.Checked)
        finally:
            self._updating_checks = False

    def _set_all_checked(self, state: Qt.CheckState):
        root = self.tree.topLevelItem(0)
        if root is None:
            return
        self._updating_checks = True
        try:
            root.setCheckState(0, state)
            self._set_children_check_state(root, state)
        finally:
            self._updating_checks = False

    def _set_children_check_state(self, item: QTreeWidgetItem, state: Qt.CheckState):
        for index in range(item.childCount()):
            child = item.child(index)
            if self._is_placeholder(child):
                continue
            child.setCheckState(0, state)
            self._set_children_check_state(child, state)

    def _set_ancestor_check_state(self, item: QTreeWidgetItem | None, state: Qt.CheckState):
        while item is not None:
            item.setCheckState(0, state)
            item = item.parent()

    def _folder_paths_with_state(self, state: Qt.CheckState) -> set[Path]:
        paths: set[Path] = set()
        root = self.tree.topLevelItem(0)
        if root is None:
            return paths
        self._collect_folder_paths(root, state, paths)
        return paths

    def _collect_folder_paths(self, item: QTreeWidgetItem, state: Qt.CheckState, paths: set[Path]):
        if self._is_placeholder(item):
            return
        if item.checkState(0) == state:
            paths.add(Path(item.data(0, Qt.ItemDataRole.UserRole)))
        for index in range(item.childCount()):
            self._collect_folder_paths(item.child(index), state, paths)

    def _collect_selected_paths(self, item: QTreeWidgetItem) -> tuple[list[Path], bool]:
        if self._is_placeholder(item):
            return [], False
        if item.checkState(0) == Qt.CheckState.Unchecked:
            return [], True

        selected: list[Path] = []
        has_exclusion = False
        for index in range(item.childCount()):
            child_paths, child_excluded = self._collect_selected_paths(item.child(index))
            selected.extend(child_paths)
            has_exclusion = has_exclusion or child_excluded

        if has_exclusion:
            return selected, True
        return [Path(item.data(0, Qt.ItemDataRole.UserRole))], False

    def _collect_selected_scan_roots(
        self,
        item: QTreeWidgetItem,
    ) -> tuple[list[Path | tuple[Path, tuple[Path, ...]]], list[Path], bool]:
        if self._is_placeholder(item):
            return [], [], False

        item_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if item.checkState(0) == Qt.CheckState.Unchecked:
            return [], [item_path], True

        child_selections: list[Path | tuple[Path, tuple[Path, ...]]] = []
        excluded: list[Path] = []
        constrained = False
        for index in range(item.childCount()):
            selections, child_excluded, child_constrained = self._collect_selected_scan_roots(item.child(index))
            child_selections.extend(selections)
            excluded.extend(child_excluded)
            constrained = constrained or child_constrained

        if item.checkState(0) == Qt.CheckState.Checked:
            if constrained:
                return [(item_path, tuple(excluded))], excluded, True
            return [item_path], [], False

        return child_selections, excluded, constrained


class FolderSummaryDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        summary_text: str,
        headers: list[str],
        file_headers: list[str],
        summary: dict[Path, int],
        files_by_folder: dict[Path, list[ClassificationPlan]],
        files_text_template: str,
        files_empty_text: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.summary_rows = _folder_summary_display_rows(summary)
        self.files_by_folder = files_by_folder
        self.files_text_template = files_text_template
        self.files_empty_text = files_empty_text
        self.summary_label = QLabel(summary_text)
        self.summary_label.setWordWrap(True)
        self.table = QTableWidget(len(summary), 2)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setHorizontalHeaderLabels(headers)
        for row, (folder, display_name, count) in enumerate(self.summary_rows):
            item = _set_table_text(self.table, row, 0, display_name, tooltip=str(folder))
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            _set_table_text(self.table, row, 1, str(count))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files_label = QLabel(files_empty_text)
        self.files_label.setWordWrap(True)
        self.files_table = QTableWidget(0, 2)
        self.files_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.files_table.setHorizontalHeaderLabels(file_headers)
        files_header = self.files_table.horizontalHeader()
        files_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        files_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.refresh_selected_folder_files)

        layout = QVBoxLayout()
        layout.addWidget(self.summary_label)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.files_label)
        layout.addWidget(self.files_table, 1)
        self.setLayout(layout)
        self.setWindowTitle(title)
        self.setMinimumSize(760, 560)

    def refresh_selected_folder_files(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.files_label.setText(self.files_empty_text)
            self.files_table.setRowCount(0)
            return
        row = selected_rows[0].row()
        if not (0 <= row < len(self.summary_rows)):
            self.files_label.setText(self.files_empty_text)
            self.files_table.setRowCount(0)
            return
        folder, display_name, _ = self.summary_rows[row]
        plans = self.files_by_folder.get(folder, [])
        self.files_label.setText(self.files_text_template.format(folder=display_name, files=len(plans)))
        _populate_folder_summary_files(self.files_table, plans)


class CandidateChoiceDialog(QDialog):
    def __init__(
        self,
        *,
        language: str,
        current_index: int,
        plan_indices: list[int],
        plans: list[ClassificationPlan],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.language = language
        self.current_index = current_index
        self.plan_indices = plan_indices
        self.plans_by_index = {index: plans[index] for index in plan_indices}
        current_plan = plans[current_index]

        self.group_label = QLabel(str(self.tr("folder_candidate_label")).format(category=current_plan.category))
        self.group_label.setWordWrap(True)
        self.candidate_table = QTableWidget(0, 3)
        self.candidate_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.candidate_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.candidate_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.candidate_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.candidate_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.candidate_table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.candidate_table.setHorizontalHeaderLabels(list(self.tr("folder_candidate_headers")))

        self.files_label = QLabel(str(self.tr("folder_candidate_files")))
        self.file_table = QTableWidget(0, 3)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.file_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.file_table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.file_table.setHorizontalHeaderLabels(list(self.tr("folder_candidate_file_headers")))

        self.apply_button = QPushButton(str(self.tr("folder_candidate_apply")))
        self.cancel_button = QPushButton(str(self.tr("cancel")))
        self.apply_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        for candidate in current_plan.folder_candidates:
            self._add_candidate_row(
                candidate.path.name,
                self._candidate_terms_text(candidate.matched_terms),
                str(candidate.path),
            )
        self._add_candidate_row(
            str(self.tr("folder_candidate_new")).format(folder=current_plan.target.parent.name),
            "-",
            "__new__",
            tooltip=str(current_plan.target.parent),
            full_path=str(current_plan.target.parent),
        )
        for index in plan_indices:
            self._add_file_row(index, plans[index], checked=index == current_index)

        self.candidate_table.resizeRowsToContents()
        self.file_table.resizeRowsToContents()
        self.candidate_table.setColumnWidth(0, 360)
        self.candidate_table.setColumnWidth(1, 170)
        self.candidate_table.setColumnWidth(2, 520)
        self.file_table.setColumnWidth(0, 70)
        self.file_table.setColumnWidth(1, 300)
        self.file_table.setColumnWidth(2, 520)
        if self.candidate_table.rowCount() > 0:
            self.candidate_table.selectRow(0)

        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(self.apply_button)
        action_layout.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self.group_label)
        layout.addWidget(self.candidate_table, 2)
        layout.addWidget(self.files_label)
        layout.addWidget(self.file_table, 1)
        layout.addLayout(action_layout)
        self.setLayout(layout)
        self.setWindowTitle(str(self.tr("folder_candidate_group")))
        self.resize(900, 560)
        self.setMinimumSize(640, 420)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def selected_folder_value(self) -> str | None:
        selected_rows = self.candidate_table.selectionModel().selectedRows()
        row = selected_rows[0].row() if selected_rows else 0
        item = self.candidate_table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def selected_plan_indices(self) -> list[int]:
        indices: list[int] = []
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item is None or item.checkState() != Qt.CheckState.Checked:
                continue
            value = item.data(Qt.ItemDataRole.UserRole)
            if value is not None:
                indices.append(int(value))
        return indices

    def _add_candidate_row(
        self,
        folder_text: str,
        terms_text: str,
        value: str,
        *,
        tooltip: str | None = None,
        full_path: str | None = None,
    ):
        row = self.candidate_table.rowCount()
        self.candidate_table.insertRow(row)
        folder_item = QTableWidgetItem(folder_text)
        folder_item.setToolTip(tooltip or value)
        folder_item.setData(Qt.ItemDataRole.UserRole, value)
        terms_item = QTableWidgetItem(terms_text)
        terms_item.setToolTip(terms_text)
        path_item = QTableWidgetItem(full_path or value)
        path_item.setToolTip(full_path or value)
        self.candidate_table.setItem(row, 0, folder_item)
        self.candidate_table.setItem(row, 1, terms_item)
        self.candidate_table.setItem(row, 2, path_item)
        header = self.candidate_table.horizontalHeader()
        for column in range(3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)

    def _add_file_row(self, index: int, plan: ClassificationPlan, *, checked: bool):
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        check_item = QTableWidgetItem("")
        check_item.setFlags(check_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        check_item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        check_item.setData(Qt.ItemDataRole.UserRole, index)
        file_item = QTableWidgetItem(plan.source.name)
        file_item.setToolTip(str(plan.source))
        location_item = QTableWidgetItem(str(plan.source.parent))
        location_item.setToolTip(str(plan.source.parent))
        self.file_table.setItem(row, 0, check_item)
        self.file_table.setItem(row, 1, file_item)
        self.file_table.setItem(row, 2, location_item)
        header = self.file_table.horizontalHeader()
        for column in range(3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)

    def _candidate_terms_text(self, terms: tuple[str, ...]) -> str:
        return ", ".join(terms) if terms else str(self.tr("folder_candidate_none"))


class FileDetailPanel(QGroupBox):
    FIELD_KEYS = (
        "file_name",
        "full_path",
        "extension",
        "size",
        "created",
        "modified",
        "planned_path",
        "status",
    )

    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.field_labels: dict[str, QLabel] = {}
        self.value_labels: dict[str, QLabel] = {}
        layout = QFormLayout()
        for key in self.FIELD_KEYS:
            field_label = QLabel()
            value_label = QLabel()
            value_label.setWordWrap(True)
            self.field_labels[key] = field_label
            self.value_labels[key] = value_label
            layout.addRow(field_label, value_label)
        self.setLayout(layout)
        self.set_language(language)
        self.clear()

    def tr(self, key: str) -> str:
        return str(TRANSLATIONS[self.language][key])

    def set_language(self, language: str):
        self.language = language
        self.setTitle(self.tr("details"))
        for key, label in self.field_labels.items():
            label.setText(self.tr(key))

    def clear(self):
        for key in self.FIELD_KEYS:
            self.value_labels[key].setText("-")
        self.value_labels["status"].setText(self.tr("no_selection"))

    def set_file(self, path: Path, *, planned_path: Path | None = None, status: str = ""):
        path = Path(path)
        stat_path = path if path.exists() else planned_path
        self.value_labels["file_name"].setText(path.name)
        self.value_labels["full_path"].setText(str(path))
        self.value_labels["extension"].setText(path.suffix or "-")
        self.value_labels["planned_path"].setText(str(planned_path) if planned_path else "-")
        self.value_labels["status"].setText(status or "-")

        if stat_path and Path(stat_path).exists():
            stat_path = Path(stat_path)
            timestamps = get_file_timestamps(stat_path)
            self.value_labels["size"].setText(_format_size(stat_path.stat().st_size))
            self.value_labels["created"].setText(_format_timestamp(timestamps.created))
            self.value_labels["modified"].setText(_format_timestamp(timestamps.modified))
        else:
            self.value_labels["size"].setText("-")
            self.value_labels["created"].setText("-")
            self.value_labels["modified"].setText("-")

    def value_text(self, key: str) -> str:
        return self.value_labels[key].text()


class ImagePreviewPanel(QGroupBox):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.image_label = QLabel()
        self.caption_label = QLabel()

        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(260, 220)
        self.image_label.setStyleSheet("border: 1px solid #555; background-color: #1f1f1f;")
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label, 1)
        layout.addWidget(self.caption_label)
        self.setLayout(layout)
        self.set_language(language)
        self.clear()

    def tr(self, key: str) -> str:
        return str(TRANSLATIONS[self.language][key])

    def set_language(self, language: str):
        self.language = language
        self.setTitle(self.tr("image_preview"))

    def clear(self):
        self.image_label.clear()
        self.image_label.setText("-")
        self.caption_label.setText("-")

    def set_image(self, path: Path, *, angle: int, rotation_text: str):
        path = Path(path)
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.image_label.clear()
            self.image_label.setText(self.tr("preview_unavailable"))
            self.caption_label.setText(path.name)
            return

        transformed = pixmap.transformed(QTransform().rotate(angle), Qt.TransformationMode.SmoothTransformation)
        scaled = transformed.scaled(
            360,
            280,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.caption_label.setText(f"{path.name} | {rotation_text}")


class RatioExampleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.direction = "wide"
        self.threshold_ratio = 2.0
        self.reference_ratio: float | None = None
        self.multiplied_ratio: float | None = None
        self.setMinimumSize(280, 190)

    def set_values(
        self,
        *,
        direction: str,
        threshold_ratio: float,
        reference_ratio: float | None = None,
        multiplied_ratio: float | None = None,
    ):
        self.direction = direction
        self.threshold_ratio = max(0.01, threshold_ratio)
        self.reference_ratio = reference_ratio if reference_ratio and reference_ratio > 0 else None
        self.multiplied_ratio = multiplied_ratio if multiplied_ratio and multiplied_ratio > 0 else None
        self.update()

    def sizeHint(self):
        return QSize(320, 220)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(39, 39, 39))

        margin = 28
        available_width = max(10, self.width() - margin * 2)
        available_height = max(10, self.height() - margin * 2 - 24)
        ratios = [max(1.0, self.threshold_ratio)]
        if self.reference_ratio and self.multiplied_ratio and abs(self.multiplied_ratio - self.threshold_ratio) > 0.005:
            text = f"배율 {self.multiplied_ratio:.2f}:1  ->  실제 {self.threshold_ratio:.2f}:1"
        elif self.reference_ratio:
            ratios.append(max(1.0, self.reference_ratio))
        if self.multiplied_ratio:
            ratios.append(max(1.0, self.multiplied_ratio))
        max_ratio = max(ratios)
        base_long = min(available_width, available_height, 170)
        if self.direction == "tall":
            long_side = min(available_height, base_long)
            scale = long_side / max_ratio
            threshold_width = max(10, scale)
            threshold_height = max(10, scale * self.threshold_ratio)
            reference_width = max(10, scale)
            reference_height = max(10, scale * self.reference_ratio) if self.reference_ratio else 0
            multiplied_width = max(8, scale)
            multiplied_height = max(8, scale * self.multiplied_ratio) if self.multiplied_ratio else 0
        else:
            long_side = min(available_width, base_long)
            scale = long_side / max_ratio
            threshold_width = max(10, scale * self.threshold_ratio)
            threshold_height = max(10, scale)
            reference_width = max(10, scale * self.reference_ratio) if self.reference_ratio else 0
            reference_height = max(10, scale)
            multiplied_width = max(8, scale * self.multiplied_ratio) if self.multiplied_ratio else 0
            multiplied_height = max(8, scale)

        if self.reference_ratio:
            reference_x = int((self.width() - reference_width) / 2)
            reference_y = int((self.height() - reference_height) / 2 - 4)
            painter.setPen(QPen(QColor(160, 160, 160), 2))
            painter.setBrush(QColor(80, 80, 80, 60))
            painter.drawRect(reference_x, reference_y, int(reference_width), int(reference_height))

        if self.multiplied_ratio and abs(self.multiplied_ratio - self.threshold_ratio) > 0.005:
            multiplied_x = int((self.width() - multiplied_width) / 2)
            multiplied_y = int((self.height() - multiplied_height) / 2 - 4)
            multiplied_pen = QPen(QColor(255, 190, 70), 2)
            multiplied_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(multiplied_pen)
            painter.setBrush(QColor(140, 92, 20, 45))
            painter.drawRect(multiplied_x, multiplied_y, int(multiplied_width), int(multiplied_height))

        x = int((self.width() - threshold_width) / 2)
        y = int((self.height() - threshold_height) / 2 - 4)
        painter.setPen(QPen(QColor(80, 190, 240), 3))
        painter.setBrush(QColor(54, 94, 112, 90))
        painter.drawRect(x, y, int(threshold_width), int(threshold_height))
        painter.setPen(QColor(235, 235, 235))
        if self.reference_ratio:
            text = f"기준 {self.reference_ratio:.2f}:1  ->  조건 {self.threshold_ratio:.2f}:1"
        else:
            text = f"조건 {self.threshold_ratio:.2f}:1"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, text)


class RenameToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.plans: list[RenamePlan] = []
        self.last_results: list[RenamePlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.options_group = QGroupBox()
        self.prefix_label = QLabel()
        self.prefix_edit = QLineEdit()
        self.suffix_label = QLabel()
        self.suffix_edit = QLineEdit()
        self.find_label = QLabel()
        self.find_edit = QLineEdit()
        self.replace_label = QLabel()
        self.replace_edit = QLineEdit()
        self.clean_spaces_checkbox = QCheckBox()
        self.clean_special_checkbox = QCheckBox()
        self.number_files_checkbox = QCheckBox()
        self.number_start_label = QLabel()
        self.number_start_spin = QSpinBox()
        self.date_format_label = QLabel()
        self.date_format_combo = QComboBox()
        self.date_fallback_label = QLabel()
        self.date_fallback_combo = QComboBox()
        self.preserve_modified_time_checkbox = QCheckBox()
        self.table = FileToolTable(4, self.add_paths)
        self.detail_panel = FileDetailPanel(language)

        self.number_start_spin.setRange(1, 999999)
        self.number_start_spin.setValue(1)
        self.preserve_modified_time_checkbox.setChecked(True)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_changes)
        self.apply_button.clicked.connect(self.apply_changes)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.undo_button)

        options_layout = QGridLayout()
        options_layout.addWidget(self.prefix_label, 0, 0)
        options_layout.addWidget(self.prefix_edit, 0, 1)
        options_layout.addWidget(self.suffix_label, 0, 2)
        options_layout.addWidget(self.suffix_edit, 0, 3)
        options_layout.addWidget(self.find_label, 1, 0)
        options_layout.addWidget(self.find_edit, 1, 1)
        options_layout.addWidget(self.replace_label, 1, 2)
        options_layout.addWidget(self.replace_edit, 1, 3)
        options_layout.addWidget(self.clean_spaces_checkbox, 2, 0)
        options_layout.addWidget(self.clean_special_checkbox, 2, 1)
        options_layout.addWidget(self.number_files_checkbox, 2, 2)
        options_layout.addWidget(self.number_start_label, 2, 3)
        options_layout.addWidget(self.number_start_spin, 2, 4)
        options_layout.addWidget(self.date_format_label, 3, 0)
        options_layout.addWidget(self.date_format_combo, 3, 1)
        options_layout.addWidget(self.date_fallback_label, 3, 2)
        options_layout.addWidget(self.date_fallback_combo, 3, 3)
        options_layout.addWidget(self.preserve_modified_time_checkbox, 3, 4)
        self.options_group.setLayout(options_layout)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        content_layout.addWidget(self.detail_panel, 1)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_date_format = self.date_format_combo.currentData() or "none"
        selected_date_fallback = self.date_fallback_combo.currentData() or "none"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.options_group.setTitle(str(self.tr("rename_options")))
        self.prefix_label.setText(str(self.tr("prefix")))
        self.suffix_label.setText(str(self.tr("suffix")))
        self.find_label.setText(str(self.tr("find")))
        self.replace_label.setText(str(self.tr("replace")))
        self.clean_spaces_checkbox.setText(str(self.tr("clean_spaces")))
        self.clean_special_checkbox.setText(str(self.tr("clean_special")))
        self.number_files_checkbox.setText(str(self.tr("number_files")))
        self.number_start_label.setText(str(self.tr("number_start")))
        self.date_format_label.setText(str(self.tr("date_format")))
        self.date_fallback_label.setText(str(self.tr("date_fallback")))
        self.preserve_modified_time_checkbox.setText(str(self.tr("preserve_modified_time")))
        self.table.setHorizontalHeaderLabels(self.tr("rename_headers"))
        self.detail_panel.set_language(language)
        self._set_date_format_items(selected_date_format)
        self._set_date_fallback_items(selected_date_fallback)
        self.refresh_table()
        self.refresh_detail_panel()

    def _set_date_format_items(self, selected: str):
        self.date_format_combo.blockSignals(True)
        self.date_format_combo.clear()
        for key in (
            "none",
            "prefix_dash",
            "prefix_underscore",
            "prefix_compact",
            "prefix_short_compact",
            "suffix_dash",
            "suffix_underscore",
            "suffix_compact",
            "suffix_short_compact",
        ):
            self.date_format_combo.addItem(str(self.tr(key)), key)
        self.date_format_combo.blockSignals(False)
        index = self.date_format_combo.findData(selected)
        self.date_format_combo.setCurrentIndex(index if index >= 0 else 0)

    def _set_date_fallback_items(self, selected: str):
        self.date_fallback_combo.blockSignals(True)
        self.date_fallback_combo.clear()
        for key, value in (
            ("date_fallback_none", "none"),
            ("date_fallback_created", "created"),
            ("date_fallback_modified", "modified"),
        ):
            self.date_fallback_combo.addItem(str(self.tr(key)), value)
        self.date_fallback_combo.blockSignals(False)
        index = self.date_fallback_combo.findData(selected)
        self.date_fallback_combo.setCurrentIndex(index if index >= 0 else 0)

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("all_files_filter")),
        )
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if not folder:
            return
        folder_path = Path(folder)
        if _child_folders(folder_path):
            dialog = FolderSelectionDialog(folder_path, self.language, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            self.add_paths(dialog.selected_files())
            return
        self.add_paths([folder_path])

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()
        self.refresh_detail_panel()

    def current_options(self) -> RenameOptions:
        return RenameOptions(
            prefix=self.prefix_edit.text(),
            suffix=self.suffix_edit.text(),
            find_text=self.find_edit.text(),
            replace_text=self.replace_edit.text(),
            clean_spaces=self.clean_spaces_checkbox.isChecked(),
            clean_special=self.clean_special_checkbox.isChecked(),
            number_files=self.number_files_checkbox.isChecked(),
            number_start=self.number_start_spin.value(),
            date_format=self.date_format_combo.currentData() or "none",
            date_fallback_source=self.date_fallback_combo.currentData() or "none",
            preserve_modified_time=self.preserve_modified_time_checkbox.isChecked(),
        )

    def preview_changes(self):
        self.plans = build_rename_plan(self.paths, self.current_options())
        self.refresh_table()
        self.refresh_detail_panel()

    def apply_changes(self):
        if not self.plans:
            self.preview_changes()
        self.plans = apply_rename_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self.paths = [plan.target if plan.status == "completed" else plan.source for plan in self.plans]
        self.refresh_table()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_rename_results(self.last_results)
        self.paths = [plan.source if plan.status == "undone" else plan.target for plan in self.plans]
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self.refresh_detail_panel()

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                values = [
                    plan.source.name,
                    plan.target.name,
                    self.status_text(plan.status),
                    str(plan.target.parent),
                ]
                self._set_row(row, values)
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, "", str(path.parent), ""])
        _configure_preview_table_columns(self.table, preferred_widths={0: 280, 1: 280, 2: 96, 3: 560})
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            _set_table_text(self.table, row, column, value)

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.target,
                status=self.status_text(plan.status),
            )
            return
        self.detail_panel.set_file(self.paths[row])

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if not selected:
            return 0 if row_count > 0 else None
        row = selected[0].row()
        if 0 <= row < row_count:
            return row
        return None


class ClassifyToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.auto_output_source_roots: dict[Path, Path] = {}
        self.output_folder: Path | None = None
        self.plans: list[ClassificationPlan] = []
        self.last_results: list[ClassificationPlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.output_folder_button = QPushButton()
        self.output_folder_label = QLabel()
        self.output_folder_label.setWordWrap(True)
        self.operation_label = QLabel()
        self.operation_combo = QComboBox()
        self.strategy_label = QLabel()
        self.strategy_combo = QComboBox()
        self.sensitivity_label = QLabel()
        self.sensitivity_combo = QComboBox()
        self.duplicate_action_label = QLabel()
        self.duplicate_action_combo = QComboBox()
        self.prefer_existing_folders_checkbox = QCheckBox()
        self.skip_single_file_folder_checkbox = QCheckBox()
        self.show_size_checkbox = QCheckBox()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.table = FileToolTable(5, self.add_paths)
        self.detail_panel = FileDetailPanel(language)
        self.controls_group = QGroupBox()
        self.selected_target_folder_label = QLabel()
        self.selected_target_folder_label.setWordWrap(True)
        self.folder_summary_group = QGroupBox()
        self.folder_summary_label = QLabel()
        self.folder_summary_expand_button = QPushButton()
        self.folder_summary_table = QTableWidget(0, 2)
        self.folder_summary_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.folder_summary_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.folder_summary_files_label = QLabel()
        self.folder_summary_files_label.setWordWrap(True)
        self.folder_summary_files_table = QTableWidget(0, 2)
        self.folder_summary_files_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.folder_summary_files_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.folder_summary_files_table.setMaximumHeight(160)
        self.folder_summary_rows: list[tuple[Path, str, int]] = []
        self.folder_summary_files_by_folder: dict[Path, list[ClassificationPlan]] = {}
        self.prefer_existing_folders_checkbox.setChecked(True)
        self.skip_single_file_folder_checkbox.setChecked(True)
        self.show_size_checkbox.setChecked(True)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.output_folder_button.clicked.connect(self.pick_output_folder)
        self.operation_combo.currentIndexChanged.connect(self.classification_operation_changed)
        self.strategy_combo.currentIndexChanged.connect(self.classification_operation_changed)
        self.sensitivity_combo.currentIndexChanged.connect(self.classification_operation_changed)
        self.duplicate_action_combo.currentIndexChanged.connect(self.classification_operation_changed)
        self.prefer_existing_folders_checkbox.stateChanged.connect(self.classification_operation_changed)
        self.skip_single_file_folder_checkbox.stateChanged.connect(self.classification_operation_changed)
        self.show_size_checkbox.stateChanged.connect(self._refresh_size_column_visibility)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_moves)
        self.apply_button.clicked.connect(self.apply_moves)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.folder_summary_expand_button.clicked.connect(self.show_folder_summary_dialog)
        self.folder_summary_table.itemSelectionChanged.connect(self.refresh_folder_summary_files)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)
        self.table.itemClicked.connect(self.open_candidate_dialog_for_item)

        controls_layout = QGridLayout()
        controls_layout.addWidget(self.add_files_button, 0, 0)
        controls_layout.addWidget(self.add_folder_button, 0, 1)
        controls_layout.addWidget(self.output_folder_button, 0, 2)
        controls_layout.addWidget(self.output_folder_label, 0, 3, 1, 5)
        controls_layout.addWidget(self.operation_label, 1, 0)
        controls_layout.addWidget(self.operation_combo, 1, 1)
        controls_layout.addWidget(self.strategy_label, 1, 2)
        controls_layout.addWidget(self.strategy_combo, 1, 3)
        controls_layout.addWidget(self.sensitivity_label, 1, 4)
        controls_layout.addWidget(self.sensitivity_combo, 1, 5)
        controls_layout.addWidget(self.show_size_checkbox, 1, 6)
        controls_layout.addWidget(self.duplicate_action_label, 2, 0)
        controls_layout.addWidget(self.duplicate_action_combo, 2, 1)
        controls_layout.addWidget(self.prefer_existing_folders_checkbox, 2, 2, 1, 3)
        controls_layout.addWidget(self.skip_single_file_folder_checkbox, 2, 5, 1, 2)
        controls_layout.addWidget(self.remove_selected_button, 3, 0)
        controls_layout.addWidget(self.clear_list_button, 3, 1)
        controls_layout.addWidget(self.preview_button, 3, 3)
        controls_layout.addWidget(self.apply_button, 3, 4)
        controls_layout.addWidget(self.undo_button, 3, 5)
        controls_layout.setColumnStretch(3, 1)
        self.controls_group.setLayout(controls_layout)

        summary_header_layout = QHBoxLayout()
        summary_header_layout.addWidget(self.folder_summary_label, 1)
        summary_header_layout.addWidget(self.folder_summary_expand_button)
        summary_layout = QVBoxLayout()
        summary_layout.addLayout(summary_header_layout)
        summary_layout.addWidget(self.folder_summary_table, 2)
        summary_layout.addWidget(self.folder_summary_files_label)
        summary_layout.addWidget(self.folder_summary_files_table, 1)
        self.folder_summary_group.setLayout(summary_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.controls_group)
        content_layout = QHBoxLayout()
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.selected_target_folder_label)
        side_layout.addWidget(self.folder_summary_group, 1)
        side_layout.addWidget(self.detail_panel, 2)
        content_layout.addWidget(self.table, 3)
        content_layout.addLayout(side_layout, 1)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_operation = self.operation_combo.currentData() or "move"
        selected_strategy = self.strategy_combo.currentData() or "extension"
        selected_sensitivity = self.sensitivity_combo.currentData() or "normal"
        selected_duplicate_action = self.duplicate_action_combo.currentData() or "keep"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.output_folder_button.setText(str(self.tr("select_output_folder_button")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.controls_group.setTitle(str(self.tr("classify_options")))
        self.operation_label.setText(str(self.tr("classify_operation")))
        self._set_operation_items(selected_operation)
        self.strategy_label.setText(str(self.tr("classify_strategy")))
        self._set_strategy_items(selected_strategy)
        self.sensitivity_label.setText(str(self.tr("classify_sensitivity")))
        self._set_sensitivity_items(selected_sensitivity)
        self.duplicate_action_label.setText(str(self.tr("duplicate_action")))
        self._set_duplicate_action_items(selected_duplicate_action)
        self.prefer_existing_folders_checkbox.setText(str(self.tr("prefer_existing_folders")))
        self.skip_single_file_folder_checkbox.setText(str(self.tr("skip_single_file_folder")))
        self.show_size_checkbox.setText(str(self.tr("show_size")))
        self.table.setHorizontalHeaderLabels(self.tr("classify_headers"))
        self.folder_summary_group.setTitle(str(self.tr("classify_summary")))
        self.folder_summary_expand_button.setText(str(self.tr("expand_summary")))
        self.folder_summary_table.setHorizontalHeaderLabels(self.tr("classify_summary_headers"))
        self.folder_summary_files_table.setHorizontalHeaderLabels(self.tr("classify_summary_file_headers"))
        self.detail_panel.set_language(language)
        self._refresh_output_folder_label()
        self.refresh_table()
        self.refresh_detail_panel()

    def _set_operation_items(self, selected: str):
        self.operation_combo.blockSignals(True)
        self.operation_combo.clear()
        self.operation_combo.addItem(str(self.tr("classify_move")), "move")
        self.operation_combo.addItem(str(self.tr("classify_copy")), "copy")
        self.operation_combo.blockSignals(False)
        self.operation_combo.setCurrentIndex(self.operation_combo.findData(selected))

    def _set_strategy_items(self, selected: str):
        self.strategy_combo.blockSignals(True)
        self.strategy_combo.clear()
        self.strategy_combo.addItem(str(self.tr("classify_by_extension")), "extension")
        self.strategy_combo.addItem(str(self.tr("classify_by_name_similarity")), "name_similarity")
        self.strategy_combo.blockSignals(False)
        self.strategy_combo.setCurrentIndex(self.strategy_combo.findData(selected))

    def _set_sensitivity_items(self, selected: str):
        self.sensitivity_combo.blockSignals(True)
        self.sensitivity_combo.clear()
        self.sensitivity_combo.addItem(str(self.tr("sensitivity_loose")), "loose")
        self.sensitivity_combo.addItem(str(self.tr("sensitivity_medium_loose")), "medium_loose")
        self.sensitivity_combo.addItem(str(self.tr("sensitivity_normal")), "normal")
        self.sensitivity_combo.addItem(str(self.tr("sensitivity_medium_strict")), "medium_strict")
        self.sensitivity_combo.addItem(str(self.tr("sensitivity_strict")), "strict")
        self.sensitivity_combo.blockSignals(False)
        self.sensitivity_combo.setCurrentIndex(self.sensitivity_combo.findData(selected))

    def _set_duplicate_action_items(self, selected: str):
        self.duplicate_action_combo.blockSignals(True)
        self.duplicate_action_combo.clear()
        self.duplicate_action_combo.addItem(str(self.tr("duplicate_keep")), "keep")
        self.duplicate_action_combo.addItem(str(self.tr("duplicate_delete")), "delete")
        self.duplicate_action_combo.blockSignals(False)
        self.duplicate_action_combo.setCurrentIndex(self.duplicate_action_combo.findData(selected))

    def classification_operation_changed(self):
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def current_operation(self) -> str:
        return self.operation_combo.currentData() or "move"

    def current_strategy(self) -> str:
        return self.strategy_combo.currentData() or "extension"

    def current_sensitivity(self) -> str:
        return self.sensitivity_combo.currentData() or "normal"

    def current_duplicate_action(self) -> str:
        return self.duplicate_action_combo.currentData() or "keep"

    def should_prefer_existing_folders(self) -> bool:
        return self.prefer_existing_folders_checkbox.isChecked()

    def should_skip_single_file_folder(self) -> bool:
        return self.skip_single_file_folder_checkbox.isChecked()

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("all_files_filter")),
        )
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if folder:
            self.add_paths([Path(folder)])

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_output_folder")), "")
        if folder:
            self.set_output_folder(Path(folder))

    def set_output_folder(self, folder: Path):
        self.output_folder = Path(folder)
        self.plans = []
        self._refresh_output_folder_label()
        self.refresh_table()
        self.refresh_detail_panel()

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        files: list[tuple[Path, Path]] = []
        for path in paths:
            path = Path(path)
            if path.is_dir():
                selected_files = self._select_folder_files(path)
                if selected_files is None:
                    continue
                files.extend((selected_file, path) for selected_file in selected_files)
            elif path.is_file():
                files.append((path, path.parent))

        for path, source_root in files:
            if path not in known:
                self.paths.append(path)
                self.auto_output_source_roots[path] = source_root
                known.add(path)
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def _select_folder_files(self, folder: Path) -> list[Path] | None:
        dialog = FolderSelectionDialog(folder, self.language, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.selected_files()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                self.auto_output_source_roots.pop(self.paths[row], None)
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.auto_output_source_roots.clear()
        self.plans.clear()
        self.refresh_table()
        self.refresh_detail_panel()

    def preview_moves(self):
        self.plans = build_classification_plan(
            self.paths,
            self.output_folder,
            operation=self.current_operation(),
            strategy=self.current_strategy(),
            sensitivity=self.current_sensitivity(),
            auto_output_roots=self._auto_output_roots() if self.output_folder is None else None,
            duplicate_action=self.current_duplicate_action(),
            prefer_existing_similar_folders=self.should_prefer_existing_folders(),
            skip_single_file_category_folder=self.should_skip_single_file_folder(),
        )
        self.refresh_table()
        self.refresh_detail_panel()

    def apply_moves(self):
        if not self.plans:
            self.preview_moves()
        if any(plan.status == "needs_choice" for plan in self.plans):
            self.refresh_table()
            self.refresh_detail_panel()
            return
        self.plans = apply_classification_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self._sync_paths_after_apply()
        self.refresh_table()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_classification_results(self.last_results)
        self._sync_paths_after_undo()
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self.refresh_detail_panel()

    def _auto_output_roots(self) -> dict[Path, Path]:
        selected_root_outputs: dict[Path, Path] = {}
        occupied_outputs: set[Path] = set()
        output_roots: dict[Path, Path] = {}
        for source in self.paths:
            source_root = self.auto_output_source_roots.get(source, source.parent)
            if source_root not in selected_root_outputs:
                selected_root_outputs[source_root] = _unique_organized_folder(source_root, occupied_outputs)
                occupied_outputs.add(selected_root_outputs[source_root])
            output_roots[source] = selected_root_outputs[source_root]
        return output_roots

    def _sync_paths_after_apply(self):
        next_paths: list[Path] = []
        next_roots: dict[Path, Path] = {}
        for plan in self.plans:
            if plan.status == "completed" and plan.operation == "move":
                path = plan.target
            elif plan.status == "duplicate_deleted":
                path = plan.target
            else:
                path = plan.source
            next_paths.append(path)
            next_roots[path] = self.auto_output_source_roots.get(plan.source, plan.source.parent)
        self.paths = next_paths
        self.auto_output_source_roots = next_roots

    def _sync_paths_after_undo(self):
        next_paths: list[Path] = []
        next_roots: dict[Path, Path] = {}
        for plan in self.plans:
            path = plan.source if plan.status == "undone" else plan.target
            next_paths.append(path)
            next_roots[path] = plan.source.parent if plan.status == "undone" else path.parent
        self.paths = next_paths
        self.auto_output_source_roots = next_roots

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                self._set_row(
                    row,
                    [
                        plan.source.name,
                        _path_size_text(plan.source),
                        plan.category,
                        self.plan_target_folder_text(plan),
                        self.plan_status_text(plan),
                    ],
                    [
                        str(plan.source),
                        _path_size_text(plan.source),
                        plan.category,
                        self.plan_target_folder_detail(plan),
                        self.plan_status_detail(plan),
                    ],
                )
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, _path_size_text(path), "", "", ""])
        _configure_preview_table_columns(
            self.table,
            preferred_widths={0: 260, 1: 88, 2: 150, 3: 160, 4: 96},
        )
        self._refresh_size_column_visibility()
        self._refresh_folder_summary()
        self._refresh_apply_button_state()
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def plan_target_folder_text(self, plan: ClassificationPlan) -> str:
        if plan.status == "needs_choice":
            return self.status_text(plan.status)
        return plan.target.parent.name

    def plan_target_folder_detail(self, plan: ClassificationPlan) -> str:
        if plan.status == "needs_choice":
            return self.plan_status_detail(plan)
        return str(plan.target)

    def plan_status_text(self, plan: ClassificationPlan) -> str:
        return self.status_text(plan.status)

    def plan_status_detail(self, plan: ClassificationPlan) -> str:
        if plan.status == "needs_choice":
            candidate_lines = [
                f"{candidate.path} ({self._candidate_terms_text(candidate.matched_terms)})"
                for candidate in plan.folder_candidates
            ]
            return "\n".join([self.status_text(plan.status), *candidate_lines])
        if plan.status == "duplicate":
            return str(self.tr("duplicate_detail_keep")).format(
                source=plan.source,
                target=plan.target,
            )
        if plan.status == "duplicate_deleted":
            return str(self.tr("duplicate_detail_delete")).format(
                source=plan.source,
                target=plan.target,
            )
        return self.status_text(plan.status)

    def _refresh_output_folder_label(self):
        if self.output_folder is None:
            self.output_folder_label.setText(str(self.tr("output_folder_missing")))
            return
        self.output_folder_label.setText(str(self.tr("output_folder_selected")).format(path=self.output_folder))

    def _set_row(self, row: int, values: list[str], tooltips: list[str] | None = None):
        for column, value in enumerate(values):
            tooltip = tooltips[column] if tooltips and column < len(tooltips) else value
            _set_table_text(self.table, row, column, value, tooltip=tooltip)

    def _refresh_size_column_visibility(self):
        self.table.setColumnHidden(1, not self.show_size_checkbox.isChecked())

    def _refresh_apply_button_state(self):
        has_unresolved_choices = any(plan.status == "needs_choice" for plan in self.plans)
        self.apply_button.setEnabled(bool(self.paths) and not has_unresolved_choices)

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self._refresh_selected_target_folder(None)
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self._refresh_selected_target_folder(None if plan.status == "needs_choice" else plan.target.parent)
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.target,
                status=self.plan_status_detail(plan),
            )
            return
        self._refresh_selected_target_folder(None)
        self.detail_panel.set_file(self.paths[row])

    def _candidate_terms_text(self, terms: tuple[str, ...]) -> str:
        return ", ".join(terms) if terms else str(self.tr("folder_candidate_none"))

    def open_candidate_dialog_for_item(self, item: QTableWidgetItem):
        if item.column() not in {3, 4}:
            return
        self.open_candidate_dialog_for_row(item.row())

    def open_candidate_dialog_for_row(self, row: int):
        if not self.plans or not (0 <= row < len(self.plans)):
            return
        if self.plans[row].status != "needs_choice":
            return
        dialog = self.create_candidate_dialog(row)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_candidate_dialog_choice(dialog)

    def create_candidate_dialog(self, row: int) -> CandidateChoiceDialog:
        if not self.plans or not (0 <= row < len(self.plans)):
            raise IndexError(row)
        plan = self.plans[row]
        group_indices = [
            index
            for index, candidate_plan in enumerate(self.plans)
            if candidate_plan.status == "needs_choice" and candidate_plan.category == plan.category
        ]
        return CandidateChoiceDialog(
            language=self.language,
            current_index=row,
            plan_indices=group_indices,
            plans=self.plans,
            parent=self,
        )

    def apply_candidate_dialog_choice(self, dialog: CandidateChoiceDialog):
        if not self.plans:
            return
        selected_value = dialog.selected_folder_value()
        if not selected_value:
            return
        selected_indices = set(dialog.selected_plan_indices())
        if not selected_indices:
            return

        occupied = {
            plan.target
            for index, plan in enumerate(self.plans)
            if index not in selected_indices and plan.status == "ready"
        }
        resolved_plans: list[ClassificationPlan] = []
        for index, plan in enumerate(self.plans):
            if index in selected_indices and plan.status == "needs_choice":
                folder = plan.target.parent if selected_value == "__new__" else Path(str(selected_value))
                resolved_plans.append(self._resolve_candidate_plan(plan, folder, occupied))
            else:
                resolved_plans.append(plan)
        self.plans = resolved_plans
        self.refresh_table()
        self.refresh_detail_panel()

    def _resolve_candidate_plan(
        self,
        plan: ClassificationPlan,
        folder: Path,
        occupied: set[Path],
    ) -> ClassificationPlan:
        target = Path(folder) / plan.source.name
        if target == plan.source:
            return replace(
                plan,
                target=target,
                category=Path(folder).name,
                status="unchanged",
                folder_candidates=(),
            )
        if target.exists() and _files_have_same_content(plan.source, target):
            return replace(
                plan,
                target=target,
                category=Path(folder).name,
                status="duplicate",
                folder_candidates=(),
            )
        target = _unique_preview_path(target, occupied)
        occupied.add(target)
        return replace(
            plan,
            target=target,
            category=Path(folder).name,
            status="ready",
            folder_candidates=(),
        )

    def _refresh_folder_summary(self):
        summary = self._folder_summary()
        self.folder_summary_rows = _folder_summary_display_rows(summary)
        self.folder_summary_files_by_folder = self._folder_summary_files()
        self.folder_summary_label.setText(
            self._folder_summary_text(summary)
        )
        self.folder_summary_table.setRowCount(len(summary))
        for row, (folder, display_name, count) in enumerate(self.folder_summary_rows):
            item = _set_table_text(self.folder_summary_table, row, 0, display_name, tooltip=str(folder))
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            _set_table_text(self.folder_summary_table, row, 1, str(count))
        header = self.folder_summary_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        files_header = self.folder_summary_files_table.horizontalHeader()
        files_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        files_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.refresh_folder_summary_files()

    def _folder_summary(self) -> dict[Path, int]:
        summary: dict[Path, int] = {}
        for plan in self.plans:
            if plan.status not in {"ready", "completed"}:
                continue
            folder = plan.target.parent
            summary[folder] = summary.get(folder, 0) + 1
        return dict(sorted(summary.items(), key=lambda item: str(item[0]).lower()))

    def _folder_summary_files(self) -> dict[Path, list[ClassificationPlan]]:
        files: dict[Path, list[ClassificationPlan]] = {}
        for plan in self.plans:
            if plan.status not in {"ready", "completed"}:
                continue
            files.setdefault(plan.target.parent, []).append(plan)
        return {
            folder: sorted(plans, key=lambda plan: plan.source.name.lower())
            for folder, plans in files.items()
        }

    def _folder_summary_text(self, summary: dict[Path, int]) -> str:
        return str(self.tr("classify_summary_text")).format(
            folders=len(summary),
            files=sum(summary.values()),
        )

    def create_folder_summary_dialog(self) -> FolderSummaryDialog:
        summary = self._folder_summary()
        return FolderSummaryDialog(
            title=str(self.tr("classify_summary")),
            summary_text=self._folder_summary_text(summary),
            headers=list(self.tr("classify_summary_headers")),
            file_headers=list(self.tr("classify_summary_file_headers")),
            summary=summary,
            files_by_folder=self._folder_summary_files(),
            files_text_template=str(self.tr("classify_summary_files_text")),
            files_empty_text=str(self.tr("classify_summary_files_empty")),
            parent=self,
        )

    def show_folder_summary_dialog(self):
        self.create_folder_summary_dialog().exec()

    def refresh_folder_summary_files(self):
        selected_rows = self.folder_summary_table.selectionModel().selectedRows()
        if not selected_rows:
            self.folder_summary_files_label.setText(str(self.tr("classify_summary_files_empty")))
            self.folder_summary_files_table.setRowCount(0)
            return
        row = selected_rows[0].row()
        if not (0 <= row < len(self.folder_summary_rows)):
            self.folder_summary_files_label.setText(str(self.tr("classify_summary_files_empty")))
            self.folder_summary_files_table.setRowCount(0)
            return
        folder, display_name, _ = self.folder_summary_rows[row]
        plans = self.folder_summary_files_by_folder.get(folder, [])
        self.folder_summary_files_label.setText(
            str(self.tr("classify_summary_files_text")).format(folder=display_name, files=len(plans))
        )
        _populate_folder_summary_files(self.folder_summary_files_table, plans)

    def _refresh_selected_target_folder(self, folder: Path | None):
        if folder is None:
            self.selected_target_folder_label.setText(str(self.tr("selected_target_folder_empty")))
            return
        self.selected_target_folder_label.setText(
            str(self.tr("selected_target_folder")).format(path=folder)
        )

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if not selected:
            return 0 if row_count > 0 else None
        row = selected[0].row()
        if 0 <= row < row_count:
            return row
        return None


class DateChangeToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.plans: list[DateChangePlan] = []
        self.last_results: list[DateChangePlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.options_group = QGroupBox()
        self.source_mode_label = QLabel()
        self.source_mode_combo = QComboBox()
        self.change_created_checkbox = QCheckBox()
        self.change_modified_checkbox = QCheckBox()
        self.created_input_label = QLabel()
        self.modified_input_label = QLabel()
        self.created_datetime_edit = QDateTimeEdit()
        self.modified_datetime_edit = QDateTimeEdit()
        self.table = FileToolTable(5, self.add_paths)
        self.detail_panel = FileDetailPanel(language)

        for editor in (self.created_datetime_edit, self.modified_datetime_edit):
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            editor.setCalendarPopup(True)
            editor.setDateTime(QDateTime.currentDateTime())
        self.change_created_checkbox.setChecked(True)
        self.change_modified_checkbox.setChecked(True)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_changes)
        self.apply_button.clicked.connect(self.apply_changes)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.undo_button)

        options_layout = QGridLayout()
        options_layout.addWidget(self.source_mode_label, 0, 0)
        options_layout.addWidget(self.source_mode_combo, 0, 1)
        options_layout.addWidget(self.change_created_checkbox, 0, 2)
        options_layout.addWidget(self.change_modified_checkbox, 0, 3)
        options_layout.addWidget(self.created_input_label, 1, 0)
        options_layout.addWidget(self.created_datetime_edit, 1, 1)
        options_layout.addWidget(self.modified_input_label, 1, 2)
        options_layout.addWidget(self.modified_datetime_edit, 1, 3)
        self.options_group.setLayout(options_layout)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        content_layout.addWidget(self.detail_panel, 1)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_mode = self.source_mode_combo.currentData() or "manual"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.options_group.setTitle(str(self.tr("date_change_options")))
        self.source_mode_label.setText(str(self.tr("date_source")))
        self.change_created_checkbox.setText(str(self.tr("change_created")))
        self.change_modified_checkbox.setText(str(self.tr("change_modified")))
        self.created_input_label.setText(str(self.tr("created_input")))
        self.modified_input_label.setText(str(self.tr("modified_input")))
        self.table.setHorizontalHeaderLabels(self.tr("date_headers"))
        self.detail_panel.set_language(language)
        self._set_source_mode_items(selected_mode)
        self.refresh_table()
        self.refresh_detail_panel()

    def _set_source_mode_items(self, selected: str):
        self.source_mode_combo.blockSignals(True)
        self.source_mode_combo.clear()
        for key in ("manual", "filename", "now"):
            self.source_mode_combo.addItem(str(self.tr(key)), key)
        self.source_mode_combo.blockSignals(False)
        self.source_mode_combo.setCurrentIndex(self.source_mode_combo.findData(selected))

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("all_files_filter")),
        )
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if folder:
            folder_path = Path(folder)
            dialog = FolderSelectionDialog(folder_path, self.language, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            self.add_paths(dialog.selected_paths())

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()
        self.refresh_detail_panel()

    def set_manual_timestamps(self, created: float, modified: float):
        self.source_mode_combo.setCurrentIndex(self.source_mode_combo.findData("manual"))
        self.created_datetime_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(created)))
        self.modified_datetime_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(modified)))

    def preview_changes(self):
        mode = self.source_mode_combo.currentData() or "manual"
        self.plans = build_date_change_plan(
            self.paths,
            created_timestamp=self.created_datetime_edit.dateTime().toSecsSinceEpoch(),
            modified_timestamp=self.modified_datetime_edit.dateTime().toSecsSinceEpoch(),
            from_filename=mode == "filename",
            use_now=mode == "now",
            change_created=self.change_created_checkbox.isChecked(),
            change_modified=self.change_modified_checkbox.isChecked(),
        )
        self.refresh_table()
        self.refresh_detail_panel()

    def apply_changes(self):
        if not self.plans:
            self.preview_changes()
        self.plans = apply_date_change_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self.refresh_table()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_date_change_results(self.last_results)
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self.refresh_detail_panel()

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                self._set_row(
                    row,
                    [
                        plan.source.name,
                        _format_timestamp(plan.target_timestamps.created),
                        _format_timestamp(plan.target_timestamps.modified),
                        self.status_text(plan.status),
                        str(plan.source.parent),
                    ],
                )
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, "", "", "", str(path.parent)])
        _configure_preview_table_columns(self.table, preferred_widths={0: 280, 1: 172, 2: 172, 3: 96, 4: 560})
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            _set_table_text(self.table, row, column, value)

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.source,
                status=self.status_text(plan.status),
            )
            return
        self.detail_panel.set_file(self.paths[row])

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if 0 <= row < row_count:
            return row
        return None


class ImageRatioClassifyToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.setAcceptDrops(True)
        self.paths: list[Path] = []
        self.output_folder: Path | None = None
        self.reference_image: Path | None = None
        self.plans: list[ImageRatioPlan] = []
        self.last_results: list[ImageRatioPlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.output_folder_button = QPushButton()
        self.output_folder_label = QLabel()
        self.output_folder_label.setWordWrap(True)
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.options_group = QGroupBox()
        self.operation_label = QLabel()
        self.operation_combo = QComboBox()
        self.direction_label = QLabel()
        self.direction_combo = QComboBox()
        self.min_ratio_label = QLabel()
        self.min_ratio_spin = QDoubleSpinBox()
        self.reference_multiplier_label = QLabel()
        self.reference_multiplier_spin = QDoubleSpinBox()
        self.reference_button = FileDropButton(self.set_reference_image_from_drop)
        self.clear_reference_button = QPushButton()
        self.reference_info_label = FileDropLabel(self.set_reference_image_from_drop)
        self.example_description_label = QLabel()
        self.example_description_label.setWordWrap(True)
        self.status_label = QLabel()
        self.table = FileToolTable(7, self.add_paths)
        self.example_widget = RatioExampleWidget()
        self.reference_base_ratio: float | None = None
        self.threshold_ratio = 2.0
        self.detail_panel = FileDetailPanel(language)

        self.min_ratio_spin.setRange(1.0, 20.0)
        self.min_ratio_spin.setDecimals(2)
        self.min_ratio_spin.setSingleStep(0.1)
        self.min_ratio_spin.setValue(2.0)
        self.reference_multiplier_spin.setRange(0.1, 10.0)
        self.reference_multiplier_spin.setDecimals(2)
        self.reference_multiplier_spin.setSingleStep(0.1)
        self.reference_multiplier_spin.setValue(1.0)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.output_folder_button.clicked.connect(self.pick_output_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_classification)
        self.apply_button.clicked.connect(self.apply_classification)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.reference_button.clicked.connect(self.pick_reference_image)
        self.clear_reference_button.clicked.connect(self.clear_reference_image)
        self.operation_combo.currentIndexChanged.connect(self.clear_preview_plan)
        self.direction_combo.currentIndexChanged.connect(self.options_changed)
        self.min_ratio_spin.valueChanged.connect(self.options_changed)
        self.reference_multiplier_spin.valueChanged.connect(self.options_changed)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.output_folder_button)
        actions.addWidget(self.output_folder_label, 1)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.undo_button)

        options_layout = QGridLayout()
        options_layout.addWidget(self.operation_label, 0, 0)
        options_layout.addWidget(self.operation_combo, 0, 1)
        options_layout.addWidget(self.direction_label, 0, 2)
        options_layout.addWidget(self.direction_combo, 0, 3)
        options_layout.addWidget(self.min_ratio_label, 1, 0)
        options_layout.addWidget(self.min_ratio_spin, 1, 1)
        options_layout.addWidget(self.reference_multiplier_label, 1, 2)
        options_layout.addWidget(self.reference_multiplier_spin, 1, 3)
        options_layout.addWidget(self.reference_button, 2, 0)
        options_layout.addWidget(self.clear_reference_button, 2, 1)
        options_layout.addWidget(self.reference_info_label, 2, 2, 1, 2)
        options_layout.setColumnStretch(3, 1)
        self.options_group.setLayout(options_layout)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.example_widget, 1)
        side_layout.addWidget(self.example_description_label)
        side_layout.addWidget(self.detail_panel, 2)
        content_layout.addLayout(side_layout, 1)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        layout.addWidget(self.status_label)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_operation = self.operation_combo.currentData() or "move"
        selected_direction = self.direction_combo.currentData() or "wide"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.output_folder_button.setText(str(self.tr("select_output_folder_button")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.options_group.setTitle(str(self.tr("image_ratio_options")))
        self.operation_label.setText(str(self.tr("classify_operation")))
        self.direction_label.setText(str(self.tr("image_ratio_direction")))
        self.min_ratio_label.setText(str(self.tr("image_ratio_min")))
        self.reference_multiplier_label.setText(str(self.tr("image_ratio_reference_multiplier")))
        self.reference_button.setText(str(self.tr("select_reference_image")))
        self.reference_button.setToolTip(str(self.tr("image_ratio_reference_drop_hint")))
        self.clear_reference_button.setText(str(self.tr("clear_reference_image")))
        self.reference_info_label.setToolTip(str(self.tr("image_ratio_reference_drop_hint")))
        self.table.setHorizontalHeaderLabels(self.tr("image_ratio_headers"))
        self.detail_panel.set_language(language)
        self._set_operation_items(selected_operation)
        self._set_direction_items(selected_direction)
        self._refresh_output_folder_label()
        self._refresh_reference_state()
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def _set_operation_items(self, selected: str):
        self.operation_combo.blockSignals(True)
        self.operation_combo.clear()
        self.operation_combo.addItem(str(self.tr("classify_move")), "move")
        self.operation_combo.addItem(str(self.tr("classify_copy")), "copy")
        self.operation_combo.blockSignals(False)
        index = self.operation_combo.findData(selected)
        self.operation_combo.setCurrentIndex(index if index >= 0 else 0)

    def _set_direction_items(self, selected: str):
        self.direction_combo.blockSignals(True)
        self.direction_combo.clear()
        self.direction_combo.addItem(str(self.tr("image_ratio_wide")), "wide")
        self.direction_combo.addItem(str(self.tr("image_ratio_tall")), "tall")
        self.direction_combo.blockSignals(False)
        index = self.direction_combo.findData(selected)
        self.direction_combo.setCurrentIndex(index if index >= 0 else 0)

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("image_files_filter")),
        )
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if folder:
            folder_path = Path(folder)
            dialog = FolderSelectionDialog(folder_path, self.language, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            self.add_paths(dialog.selected_paths())

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_output_folder")), "")
        if folder:
            self.set_output_folder(Path(folder))

    def pick_reference_image(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            str(self.tr("select_reference_image")),
            "",
            str(self.tr("image_files_filter")),
        )
        if file:
            self.set_reference_image(Path(file))

    def set_output_folder(self, folder: Path):
        self.output_folder = Path(folder)
        self.clear_preview_plan()
        self._refresh_output_folder_label()

    def set_reference_image(self, path: Path):
        self.reference_image = Path(path)
        self.options_changed()

    def set_reference_image_from_drop(self, paths: list[Path]):
        image_path = next(iter(_image_ratio_files(paths)), None)
        if image_path is not None:
            self.set_reference_image(image_path)

    def clear_reference_image(self):
        self.reference_image = None
        self.options_changed()

    def add_paths(self, paths: list[Path]):
        import threading
        from PySide6.QtCore import QTimer

        if getattr(self, "_image_ratio_add_paths_running", False):
            return

        known = set(self.paths)
        selected_paths: list[Path] = []
        for path in paths:
            path = Path(path)
            if path.is_dir():
                dialog = FolderSelectionDialog(path, self.language, self)
                if dialog.exec() != QDialog.DialogCode.Accepted:
                    continue
                selected_paths.extend(dialog.selected_scan_roots())
            else:
                selected_paths.append(path)
        if not selected_paths:
            return

        token = object()
        self._image_ratio_add_paths_token = token
        self._image_ratio_add_paths_running = True
        self.status_label.setText(str(self.tr("image_ratio_processing")))
        self._refresh_apply_button_state()
        QApplication.processEvents()

        def worker():
            try:
                seen = set(known)
                result: list[Path] = []
                for image_path in _image_ratio_files(selected_paths):
                    if image_path in seen:
                        continue
                    result.append(image_path)
                    seen.add(image_path)
            except BaseException as exc:
                result = exc
            self._image_ratio_add_paths_result = (token, result)

        def poll():
            result_pair = getattr(self, "_image_ratio_add_paths_result", None)
            if result_pair is None or result_pair[0] is not token:
                QTimer.singleShot(100, poll)
                return

            try:
                del self._image_ratio_add_paths_result
            except AttributeError:
                pass
            self._image_ratio_add_paths_running = False

            result = result_pair[1]
            if isinstance(result, BaseException):
                self.status_label.setText(f"Load failed: {result}")
                self._refresh_apply_button_state()
                return

            self.paths.extend(result)
            self.clear_preview_plan()

        threading.Thread(target=worker, daemon=True).start()
        QTimer.singleShot(100, poll)

    def dragEnterEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dragMoveEvent(self, event):
        if _local_drop_paths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dropEvent(self, event):
        paths = _local_drop_paths(event)
        if not paths:
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        QTimer.singleShot(0, lambda paths=paths: self.add_paths(paths))

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.clear_preview_plan()

    def clear_paths(self):
        self.paths.clear()
        self.clear_preview_plan()

    def current_operation(self) -> str:
        return self.operation_combo.currentData() or "move"

    def current_direction(self) -> str:
        return self.direction_combo.currentData() or "wide"

    def current_options(self) -> ImageRatioOptions:
        return ImageRatioOptions(
            direction=self.current_direction(),
            threshold_ratio=self.min_ratio_spin.value(),
            reference_path=self.reference_image,
            reference_multiplier=self.reference_multiplier_spin.value(),
            operation=self.current_operation(),
        )

    def options_changed(self, *_):
        self.plans = []
        self._refresh_reference_state()
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def clear_preview_plan(self, *_):
        self.plans = []
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def preview_classification(self):
        self.plans = build_image_ratio_classification_plan(
            self.paths,
            self.output_folder,
            self.current_options(),
        )
        self.refresh_table()
        self._refresh_preview_status_label()
        self.refresh_detail_panel()

    def apply_classification(self):
        if not self.plans:
            self.preview_classification()
        self.status_label.setText(str(self.tr("image_ratio_processing")))
        QApplication.processEvents()
        self.plans = apply_image_ratio_classification_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self._sync_paths_after_apply()
        self.refresh_table()
        self._refresh_result_status_label()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_image_ratio_classification_results(self.last_results)
        self._sync_paths_after_undo()
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self._refresh_result_status_label()
        self.refresh_detail_panel()

    def _sync_paths_after_apply(self):
        next_paths: list[Path] = []
        for plan in self.plans:
            if plan.status == "completed" and plan.operation == "move":
                next_paths.append(plan.target)
            else:
                next_paths.append(plan.source)
        self.paths = next_paths

    def _sync_paths_after_undo(self):
        self.paths = [plan.source if plan.status == "undone" else plan.target for plan in self.plans]

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                self._set_row(
                    row,
                    [
                        plan.source.name,
                        _path_size_text(plan.source),
                        self.dimension_text(plan.width, plan.height),
                        self.ratio_text(plan.ratio),
                        self.category_text(plan.category),
                        self.plan_status_text(plan),
                        str(plan.target),
                    ],
                )
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, _path_size_text(path), "", "", "", "", str(path.parent)])
        _configure_preview_table_columns(
            self.table,
            preferred_widths={0: 240, 1: 88, 2: 120, 3: 88, 4: 110, 5: 110, 6: 520},
        )
        self._refresh_apply_button_state()
        self._refresh_example_widget()
        self.refresh_detail_panel()

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            _set_table_text(self.table, row, column, value)

    def dimension_text(self, width: int, height: int) -> str:
        if width <= 0 or height <= 0:
            return "-"
        return f"{width} x {height}"

    def ratio_text(self, ratio: float) -> str:
        if ratio <= 0:
            return "-"
        return f"{ratio:.2f}"

    def category_text(self, category: str) -> str:
        mapping = {
            "조건 일치": "image_ratio_match",
            "조건 미달": "image_ratio_miss",
            "읽기 실패": "image_ratio_read_failed",
            "이미지 아님": "image_ratio_non_image",
        }
        key = mapping.get(category)
        return str(self.tr(key)) if key else category

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def plan_status_text(self, plan: ImageRatioPlan) -> str:
        status = self.status_text(plan.status)
        if plan.status == "completed":
            if self.language == "en":
                return "Move completed" if plan.operation == "move" else "Copy completed"
            return "이동 완료" if plan.operation == "move" else "복사 완료"
        if plan.status in {"skipped", "failed"} and plan.message:
            return f"{status}: {plan.message}"
        return status

    def _refresh_output_folder_label(self):
        if self.output_folder is None:
            self.output_folder_label.setText(str(self.tr("image_ratio_output_default")))
            return
        self.output_folder_label.setText(str(self.tr("output_folder_selected")).format(path=self.output_folder))

    def _refresh_reference_state(self):
        self.reference_base_ratio = None
        self.threshold_ratio = effective_threshold_ratio(self.current_options())
        if self.reference_image is None:
            self.reference_info_label.setText(str(self.tr("image_ratio_reference_empty")))
            self.min_ratio_spin.setEnabled(True)
            self.reference_multiplier_spin.setEnabled(False)
        else:
            try:
                width, height = image_dimensions(self.reference_image)
            except OSError:
                self.reference_info_label.setText(str(self.tr("image_ratio_reference_empty")))
            else:
                ratio = width / height if self.current_direction() == "wide" else height / width
                derived_threshold = ratio * self.reference_multiplier_spin.value()
                actual_threshold = effective_threshold_ratio(self.current_options())
                self.reference_base_ratio = ratio
                self.threshold_ratio = actual_threshold
                if self.language == "en":
                    text = (
                        f"Reference image: {width} x {height} / base ratio {ratio:.2f} / "
                        f"multiplied {derived_threshold:.2f} / actual condition {actual_threshold:.2f}+"
                    )
                    if actual_threshold > derived_threshold + 0.005:
                        text += " (minimum 1.00 applied for this direction)"
                else:
                    text = (
                        f"기준 이미지: {width} x {height} / 기준 비율 {ratio:.2f} / "
                        f"배율 적용 {derived_threshold:.2f} / 실제 조건 {actual_threshold:.2f} 이상"
                    )
                    if actual_threshold > derived_threshold + 0.005:
                        text += " (방향 조건 때문에 최소 1.00 적용)"
                self.reference_info_label.setText(text)
            self.min_ratio_spin.setEnabled(False)
            self.reference_multiplier_spin.setEnabled(True)
        self._refresh_example_widget()

    def _refresh_example_widget(self):
        self.threshold_ratio = effective_threshold_ratio(self.current_options())
        multiplied_ratio = None
        if self.reference_base_ratio:
            multiplied_ratio = self.reference_base_ratio * self.reference_multiplier_spin.value()
        self.example_widget.set_values(
            direction=self.current_direction(),
            threshold_ratio=self.threshold_ratio,
            reference_ratio=self.reference_base_ratio,
            multiplied_ratio=multiplied_ratio,
        )
        self.example_description_label.setText(self._example_description_text())

    def _example_description_text(self) -> str:
        ratio = self.threshold_ratio
        if self.reference_image is not None:
            try:
                width, height = image_dimensions(self.reference_image)
            except OSError:
                pass
            else:
                base_ratio = width / height if self.current_direction() == "wide" else height / width
                derived_threshold = base_ratio * self.reference_multiplier_spin.value()
                multiplier = self.reference_multiplier_spin.value()
                if self.current_direction() == "tall":
                    if self.language == "en":
                        return (
                            f"Applied condition: height / width >= {ratio:.2f}. "
                            f"Reference {width} x {height}, base {base_ratio:.2f}, "
                            f"multiplier {multiplier:.2f} -> {derived_threshold:.2f}; "
                            f"actual threshold {ratio:.2f}. Example: if width is 1000px, "
                            f"height must be {int(round(1000 * ratio))}px or more."
                        )
                    return (
                        f"적용 조건: 세로 / 가로 >= {ratio:.2f}. "
                        f"기준 {width} x {height}, 기준 비율 {base_ratio:.2f}, "
                        f"배율 {multiplier:.2f} 적용값 {derived_threshold:.2f}; "
                        f"실제 조건 {ratio:.2f}. 예: 가로 1000px이면 세로 "
                        f"{int(round(1000 * ratio))}px 이상."
                    )
                if self.language == "en":
                    return (
                        f"Applied condition: width / height >= {ratio:.2f}. "
                        f"Reference {width} x {height}, base {base_ratio:.2f}, "
                        f"multiplier {multiplier:.2f} -> {derived_threshold:.2f}; "
                        f"actual threshold {ratio:.2f}. Example: if height is 1000px, "
                        f"width must be {int(round(1000 * ratio))}px or more."
                    )
                return (
                    f"적용 조건: 가로 / 세로 >= {ratio:.2f}. "
                    f"기준 {width} x {height}, 기준 비율 {base_ratio:.2f}, "
                    f"배율 {multiplier:.2f} 적용값 {derived_threshold:.2f}; "
                    f"실제 조건 {ratio:.2f}. 예: 세로 1000px이면 가로 "
                    f"{int(round(1000 * ratio))}px 이상."
                )
                if self.current_direction() == "tall":
                    return str(self.tr("image_ratio_reference_condition_tall")).format(
                        width=width,
                        height=height,
                        multiplier=f"{self.reference_multiplier_spin.value():.2f}",
                        ratio=f"{ratio:.2f}",
                        target=int(round(1000 * ratio)),
                    )
                return str(self.tr("image_ratio_reference_condition_wide")).format(
                    width=width,
                    height=height,
                    multiplier=f"{self.reference_multiplier_spin.value():.2f}",
                    ratio=f"{ratio:.2f}",
                    target=int(round(1000 * ratio)),
                )
        if self.current_direction() == "tall":
            return str(self.tr("image_ratio_condition_tall")).format(
                ratio=f"{ratio:.2f}",
                height=int(round(1000 * ratio)),
            )
        return str(self.tr("image_ratio_condition_wide")).format(
            ratio=f"{ratio:.2f}",
            width=int(round(1000 * ratio)),
        )

    def _refresh_apply_button_state(self):
        adding = getattr(self, "_image_ratio_add_paths_running", False)
        self.apply_button.setEnabled(bool(self.paths) and not adding)

    def _status_counts(self) -> dict[str, int]:
        counts = {"completed": 0, "skipped": 0, "failed": 0, "matched": 0, "missed": 0, "other": 0}
        for plan in self.plans:
            if plan.status == "completed":
                counts["completed"] += 1
            elif plan.status == "skipped":
                counts["skipped"] += 1
            elif plan.status == "failed":
                counts["failed"] += 1
            if plan.category == "조건 일치":
                counts["matched"] += 1
            elif plan.category == "조건 미달":
                counts["missed"] += 1
            elif plan.category in {"읽기 실패", "이미지 아님"}:
                counts["other"] += 1
        return counts

    def _refresh_status_label(self):
        if not self.plans:
            self.status_label.setText(str(self.tr("image_ratio_idle")))
            return
        self._refresh_preview_status_label()

    def _refresh_preview_status_label(self):
        self.status_label.setText(str(self.tr("image_ratio_preview_summary")).format(**self._status_counts()))

    def _refresh_result_status_label(self):
        counts = self._status_counts()
        moved = sum(1 for plan in self.plans if plan.status == "completed" and plan.operation == "move")
        copied = sum(1 for plan in self.plans if plan.status == "completed" and plan.operation == "copy")
        if self.language == "en":
            self.status_label.setText(
                f"Result: moved {moved}, copied {copied}, skipped {counts['skipped']}, failed {counts['failed']}"
            )
            return
        self.status_label.setText(
            f"처리 결과: 이동 완료 {moved}, 복사 완료 {copied}, 건너뜀 {counts['skipped']}, 실패 {counts['failed']}"
        )

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.detail_panel.set_file(plan.source, planned_path=plan.target, status=self.plan_status_text(plan))
            return
        self.detail_panel.set_file(self.paths[row])

    def _selected_row(self) -> int | None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return 0 if self.table.rowCount() else None
        return selected_rows[0].row()


class ImageRotateToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.output_folder: Path | None = None
        self.plans: list[ImageRotationPlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.output_folder_button = QPushButton()
        self.output_folder_label = QLabel()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.options_group = QGroupBox()
        self.rotation_label = QLabel()
        self.rotation_combo = QComboBox()
        self.allow_lossy_jpeg_checkbox = QCheckBox()
        self.status_label = QLabel()
        self.table = FileToolTable(4, self.add_paths)
        self.preview_panel = ImagePreviewPanel(language)
        self.detail_panel = FileDetailPanel(language)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.output_folder_button.clicked.connect(self.pick_output_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_rotations)
        self.apply_button.clicked.connect(self.apply_rotations)
        self.allow_lossy_jpeg_checkbox.stateChanged.connect(self.clear_preview_plan)
        self.rotation_combo.currentIndexChanged.connect(self.refresh_detail_panel)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.output_folder_button)
        actions.addWidget(self.output_folder_label)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)

        options_layout = QGridLayout()
        options_layout.addWidget(self.rotation_label, 0, 0)
        options_layout.addWidget(self.rotation_combo, 0, 1)
        options_layout.addWidget(self.allow_lossy_jpeg_checkbox, 0, 2)
        options_layout.setColumnStretch(3, 1)
        self.options_group.setLayout(options_layout)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.preview_panel, 2)
        side_layout.addWidget(self.detail_panel, 1)
        content_layout.addLayout(side_layout, 1)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        layout.addWidget(self.status_label)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_angle = self.rotation_combo.currentData() or 90
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.output_folder_button.setText(str(self.tr("select_output_folder_button")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.options_group.setTitle(str(self.tr("image_rotate_options")))
        self.rotation_label.setText(str(self.tr("rotation")))
        self.allow_lossy_jpeg_checkbox.setText(str(self.tr("allow_lossy_jpeg")))
        self.table.setHorizontalHeaderLabels(self.tr("image_rotate_headers"))
        self.preview_panel.set_language(language)
        self.detail_panel.set_language(language)
        self._set_rotation_items(selected_angle)
        self._refresh_output_folder_label()
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def _set_rotation_items(self, selected: int):
        self.rotation_combo.blockSignals(True)
        self.rotation_combo.clear()
        for key, angle in (("right_90", 90), ("left_90", 270), ("rotate_180", 180)):
            self.rotation_combo.addItem(str(self.tr(key)), angle)
        self.rotation_combo.blockSignals(False)
        self.rotation_combo.setCurrentIndex(self.rotation_combo.findData(selected))

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("image_files_filter")),
        )
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if folder:
            self.add_paths([Path(folder)])

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_output_folder")), "")
        if folder:
            self.set_output_folder(Path(folder))

    def set_output_folder(self, folder: Path):
        self.output_folder = Path(folder)
        self.plans = []
        self._refresh_output_folder_label()
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def current_angle(self) -> int:
        return int(self.rotation_combo.currentData() or 90)

    def clear_preview_plan(self, *_):
        self.plans = []
        self.refresh_table()
        self._refresh_status_label()
        self.refresh_detail_panel()

    def preview_rotations(self):
        jpegtran_status = detect_jpegtran()
        self.plans = build_image_rotation_plan(
            self.paths,
            angle=self.current_angle(),
            output_folder=self.output_folder,
            jpegtran_executable=jpegtran_status.executable,
            allow_lossy_jpeg=self.allow_lossy_jpeg_checkbox.isChecked(),
        )
        self.refresh_table()
        self._refresh_preview_status_label()
        self.refresh_detail_panel()

    def apply_rotations(self):
        if not self.plans:
            self.preview_rotations()
        self.status_label.setText(str(self.tr("image_rotate_processing")))
        QApplication.processEvents()
        self.plans = apply_image_rotation_plan(self.plans)
        self.refresh_table()
        self._refresh_result_status_label()
        self.refresh_detail_panel()

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                self._set_row(
                    row,
                    [
                        plan.source.name,
                        self.rotation_text(plan.angle),
                        self.plan_status_text(plan),
                        str(plan.target),
                    ],
                )
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, "", "", str(path.parent)])
        _configure_preview_table_columns(self.table, preferred_widths={0: 280, 1: 140, 2: 220, 3: 620})
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def plan_status_text(self, plan: ImageRotationPlan) -> str:
        status = self.status_text(plan.status)
        if plan.status in {"skipped", "failed"} and plan.message:
            return f"{status}: {self.message_text(plan.message)}"
        if plan.status == "completed" and plan.message == "Rotated with JPEG re-encoding.":
            return f"{status}: {self.message_text(plan.message)}"
        return status

    def message_text(self, message: str) -> str:
        if self.language == "ko":
            if message.startswith("jpegtran is required"):
                return "jpegtran 필요"
            if "transformation is not perfect" in message or message == "JPEG cannot be rotated losslessly.":
                return "무손실 회전 불가(원본 유지)"
            if message == "Rotated with JPEG re-encoding.":
                return "손실 회전"
            if message == "Unsupported image format.":
                return "지원하지 않는 형식"
            if message == "Source file does not exist.":
                return "원본 파일 없음"
            if message == "Target file already exists.":
                return "출력 파일이 이미 있음"
        return message

    def rotation_text(self, angle: int) -> str:
        key = {90: "right_90", 180: "rotate_180", 270: "left_90"}.get(angle, "right_90")
        return str(self.tr(key))

    def _refresh_output_folder_label(self):
        if self.output_folder is None:
            self.output_folder_label.setText(str(self.tr("output_folder_default")))
            return
        self.output_folder_label.setText(str(self.tr("output_folder_selected")).format(path=self.output_folder))

    def _refresh_status_label(self):
        if not self.plans:
            self.status_label.setText(str(self.tr("image_rotate_idle")))
            return
        self._refresh_preview_status_label()

    def _refresh_preview_status_label(self):
        counts = self._status_counts()
        self.status_label.setText(
            str(self.tr("image_rotate_preview_summary")).format(
                ready=counts["ready"],
                skipped=counts["skipped"],
                failed=counts["failed"],
            )
        )

    def _refresh_result_status_label(self):
        counts = self._status_counts()
        self.status_label.setText(
            str(self.tr("image_rotate_result_summary")).format(
                completed=counts["completed"],
                skipped=counts["skipped"],
                failed=counts["failed"],
            )
        )

    def _status_counts(self) -> dict[str, int]:
        counts = {"ready": 0, "completed": 0, "skipped": 0, "failed": 0}
        for plan in self.plans:
            if plan.status in counts:
                counts[plan.status] += 1
        return counts

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            _set_table_text(self.table, row, column, value)

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.preview_panel.clear()
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.preview_panel.set_image(
                plan.source,
                angle=plan.angle,
                rotation_text=self.rotation_text(plan.angle),
            )
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.target,
                status=self.plan_status_text(plan),
            )
            return
        path = self.paths[row]
        self.preview_panel.set_image(
            path,
            angle=self.current_angle(),
            rotation_text=self.rotation_text(self.current_angle()),
        )
        self.detail_panel.set_file(path)

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if not selected:
            return 0 if row_count > 0 else None
        row = selected[0].row()
        if 0 <= row < row_count:
            return row
        return None


def _child_folders(folder: Path) -> list[Path]:
    try:
        return sorted(
            (child for child in folder.iterdir() if child.is_dir()),
            key=lambda path: path.name.lower(),
        )
    except OSError:
        return []


def _has_child_folders(folder: Path) -> bool:
    try:
        for child in folder.iterdir():
            if child.is_dir():
                return True
    except OSError:
        return False
    return False


def _count_files_in_folder(folder: Path) -> int:
    try:
        return sum(1 for child in folder.iterdir() if child.is_file())
    except OSError:
        return 0


def _is_relative_to(path: Path, folder: Path) -> bool:
    try:
        Path(path).relative_to(folder)
    except ValueError:
        return False
    return True


def _folder_summary_display_rows(summary: dict[Path, int]) -> list[tuple[Path, str, int]]:
    base_name_counts: dict[str, int] = {}
    for folder in summary:
        base_name = _folder_display_base_name(folder)
        base_name_counts[base_name] = base_name_counts.get(base_name, 0) + 1

    rows: list[tuple[Path, str, int]] = []
    display_counts: dict[str, int] = {}
    pending: list[tuple[Path, str, int]] = []
    for folder, count in summary.items():
        base_name = _folder_display_base_name(folder)
        display_name = base_name
        if base_name_counts[base_name] > 1:
            display_name = f"{base_name} ({_folder_context_label(folder)})"
        pending.append((folder, display_name, count))
        display_counts[display_name] = display_counts.get(display_name, 0) + 1

    used_display_counts: dict[str, int] = {}
    for folder, display_name, count in pending:
        if display_counts[display_name] > 1:
            used_display_counts[display_name] = used_display_counts.get(display_name, 0) + 1
            display_name = f"{display_name} #{used_display_counts[display_name]}"
        rows.append((folder, display_name, count))
    return rows


def _populate_folder_summary_files(table: QTableWidget, plans: list[ClassificationPlan]):
    table.setRowCount(len(plans))
    for row, plan in enumerate(plans):
        _set_table_text(table, row, 0, plan.source.name, tooltip=str(plan.source))
        _set_table_text(table, row, 1, str(plan.target), tooltip=str(plan.target))


def _folder_display_base_name(folder: Path) -> str:
    return Path(folder).name or str(folder)


def _folder_context_label(folder: Path) -> str:
    parent = Path(folder).parent
    labels: list[str] = []
    if parent.parent.name:
        labels.append(parent.parent.name)
    if parent.name:
        labels.append(parent.name)
    return " > ".join(labels) if labels else str(parent)


def _unique_organized_folder(root: Path, occupied: set[Path]) -> Path:
    root = Path(root)
    base = root / "정리"
    candidate = base
    counter = 1
    while candidate.exists() or candidate in occupied:
        candidate = root / f"정리_{counter}"
        counter += 1
    return candidate


def _unique_preview_path(path: Path, occupied: set[Path]) -> Path:
    path = Path(path)
    if path not in occupied and not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if candidate not in occupied and not candidate.exists():
            return candidate
        counter += 1


def _files_have_same_content(left: Path, right: Path) -> bool:
    try:
        if left.stat().st_size != right.stat().st_size:
            return False
        with left.open("rb") as left_file, right.open("rb") as right_file:
            while True:
                left_chunk = left_file.read(1024 * 1024)
                right_chunk = right_file.read(1024 * 1024)
                if left_chunk != right_chunk:
                    return False
                if not left_chunk:
                    return True
    except OSError:
        return False


def _expand_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*") if child.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def _is_relative_to_any(path: Path, folders: tuple[Path, ...]) -> bool:
    for folder in folders:
        if _is_relative_to(path, folder):
            return True
    return False


def _files_from_scan_roots(paths):
    for raw_path in paths:
        excluded_folders: tuple[Path, ...] = ()
        if isinstance(raw_path, tuple) and len(raw_path) == 2:
            path = Path(raw_path[0])
            excluded_folders = tuple(Path(folder) for folder in raw_path[1])
        else:
            path = Path(raw_path)

        if path.is_dir():
            try:
                children = sorted(child for child in path.rglob("*") if child.is_file())
            except OSError:
                continue
            for child in children:
                if excluded_folders and _is_relative_to_any(child, excluded_folders):
                    continue
                yield child
        elif path.is_file():
            if not excluded_folders or not _is_relative_to_any(path, excluded_folders):
                yield path


def _image_ratio_files(paths: list[Path]) -> list[Path]:
    return [
        path
        for path in _files_from_scan_roots(paths)
        if path.suffix.lower() in RATIO_SUPPORTED_IMAGE_SUFFIXES
    ]


def _set_table_text(table: QTableWidget, row: int, column: int, value: str, *, tooltip: str | None = None):
    item = QTableWidgetItem(value)
    item.setToolTip(tooltip or value)
    table.setItem(row, column, item)
    return item


def _configure_preview_table_columns(table: FileToolTable, *, preferred_widths: dict[int, int]):
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    for column in range(table.columnCount()):
        header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        if column in preferred_widths:
            table.setColumnWidth(column, preferred_widths[column])
        else:
            table.resizeColumnToContents(column)


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _path_size_text(path: Path) -> str:
    path = Path(path)
    if not path.exists() or not path.is_file():
        return "-"
    return _format_size(path.stat().st_size)


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
