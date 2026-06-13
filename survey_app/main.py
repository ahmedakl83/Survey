import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from views.main_window import MainWindow
from database.db_manager import DatabaseManager


def main():
    # تعيين معرف التطبيق على ويندوز لضمان إظهار الأيقونة الخاصة به في شريط المهام وصينية النظام
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ccs.surveyapp.app.1.0.5")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("تفريغ الاستبيانات")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # تعيين الأيقونة للتطبيق بالكامل
    from PyQt6.QtGui import QIcon
    import os
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_path, 'assets', 'icon.png')
    app.setWindowIcon(QIcon(icon_path))

    # تهيئة قاعدة البيانات
    db = DatabaseManager()
    db.initialize()

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
