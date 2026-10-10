import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from views.main_window import MainWindow
from database.db_manager import DatabaseManager
from utils.translator import set_language, get_layout_direction, tr


def main():
    # تعيين معرف التطبيق على ويندوز لضمان إظهار الأيقونة الخاصة به في شريط المهام وصينية النظام
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ccs.surveyapp.app.1.0.9")
        except Exception:
            pass

    # تهيئة قاعدة البيانات
    db = DatabaseManager()
    db.initialize()

    # تحميل اللغة المحفوظة وضبط التوجيه المبدئي
    saved_lang = db.get_setting("language", "ar")
    set_language(saved_lang, db)

    app = QApplication(sys.argv)
    app.setApplicationName(tr("app_name"))
    app.setLayoutDirection(get_layout_direction())

    # تعيين الأيقونة للتطبيق بالكامل
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_path, 'assets', 'icon.png')
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
