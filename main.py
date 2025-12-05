import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from config.logging_config import setup_logging

def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    qss_path = Path(__file__).resolve().parent / "gui" / "app.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
