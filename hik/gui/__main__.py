from .caputre_gui import HIKCaptureMain


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = HIKCaptureMain()
    window.show()
    sys.exit(app.exec())