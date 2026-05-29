import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from views.main_window import MainWindow

my_app_id = 'mycompany.satellite.groundstation.1.0' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./docs/img/logo2.ico"))
    with open("views/style/style.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
