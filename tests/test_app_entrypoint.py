from file_compressor_app import main as app_main


class FakeApplication:
    def __init__(self, argv):
        self.argv = argv

    def exec(self):
        return 0


class FakeWindow:
    shown = False

    def show(self):
        FakeWindow.shown = True


def test_main_starts_desktop_window(monkeypatch, capsys):
    monkeypatch.setattr(app_main, "QApplication", FakeApplication)
    monkeypatch.setattr(app_main, "MainWindow", FakeWindow)

    exit_code = app_main.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert FakeWindow.shown is True
    assert captured.out == ""
    assert captured.err == ""
