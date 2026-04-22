from file_compressor_app.main import main


def test_main_reports_ui_not_implemented(capsys):
    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "File Compressor desktop UI is not implemented yet.\n"
    assert captured.err == ""
