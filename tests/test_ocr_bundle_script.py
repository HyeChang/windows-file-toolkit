from pathlib import Path


def test_ocr_bundle_script_packages_exe_and_local_tesseract_tree():
    script = Path("scripts/package_ocr_bundle.ps1")

    text = script.read_text(encoding="utf-8")

    assert "FileCompressor-OCR.zip" in text
    assert "tools/tesseract" in text
    assert "Extract this zip as a folder" in text
    assert "No system Tesseract install" in text
    assert "tesseract.exe" in text
    assert "kor.traineddata" in text
    assert "eng.traineddata" in text
    assert "Compress-Archive" in text


def test_prepare_tesseract_runtime_script_downloads_runtime_and_languages():
    script = Path("scripts/prepare_tesseract_runtime.ps1")

    text = script.read_text(encoding="utf-8")

    assert "dist/tesseract-runtime" in text
    assert "digi.bib.uni-mannheim.de/tesseract" in text
    assert "tessdata_fast/raw/main/kor.traineddata" in text
    assert "tessdata_fast/raw/main/eng.traineddata" in text
    assert "LICENSE-tesseract.txt" in text


def test_pyinstaller_spec_includes_local_jpegtran_when_available():
    spec = Path("file-compressor.spec")

    text = spec.read_text(encoding="utf-8")

    assert "tools/jpegtran/jpegtran.exe" in text
    assert "jpeg62.dll" in text
    assert "tools/jpegtran" in text


def test_build_script_reports_jpegtran_bundle_status():
    script = Path("scripts/build_exe.ps1")

    text = script.read_text(encoding="utf-8")

    assert "tools/jpegtran/jpegtran.exe" in text
    assert "tools/jpegtran/jpeg62.dll" in text
    assert "JPEG rotation bundle" in text
