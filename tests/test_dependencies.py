from file_compressor.dependencies import DependencyStatus, detect_ghostscript


def test_detect_ghostscript_reports_missing_when_lookup_fails():
    status = detect_ghostscript(which=lambda _: None)

    assert status == DependencyStatus(available=False, executable=None)


def test_detect_ghostscript_reports_available_path():
    status = detect_ghostscript(which=lambda _: "C:/Tools/gswin64c.exe")

    assert status == DependencyStatus(available=True, executable="C:/Tools/gswin64c.exe")
