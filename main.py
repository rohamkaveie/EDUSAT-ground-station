import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow

my_app_id = 'mycompany.satellite.groundstation.1.0' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

def main():
    app = QApplication(sys.argv)
    # app.setWindowIcon(QIcon("./img/logo2.png"))
    app.setWindowIcon(QIcon("./img/logo2.ico"))
    font = app.font()
    font.setPointSize(10) # Force a valid starting point
    app.setFont(font)
    with open("style/style.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    # window.setWindowIcon(QIcon("./img/logo.png"))
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
