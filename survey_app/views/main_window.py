from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QVBoxLayout,
    QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer

from database.db_manager import DatabaseManager
from views.styles import get_app_stylesheet
from views.home_view import HomeView
from views.review_view import ReviewView
from views.entry_view import EntryView
from views.results_view import ResultsView
from views.templates_view import TemplatesView
from views.statistics_view import StatisticsView
from utils.translator import tr, set_language, get_language, is_rtl, get_layout_direction


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        # تحميل اللغة المحفوظة
        saved_lang = self.db.get_setting("language", "ar")
        set_language(saved_lang, self.db)

        from build_info import APP_VERSION
        self.setWindowTitle(tr("app_title", version=APP_VERSION))
        self.setMinimumSize(1024, 680)
        self.resize(1280, 800)
        self.setLayoutDirection(get_layout_direction())
        self.setStyleSheet(get_app_stylesheet(is_rtl()))

        # حالة الحفظ
        self._save_status_timer = QTimer(self)
        self._save_status_timer.setSingleShot(True)
        self._save_status_timer.timeout.connect(self._clear_save_status)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # إنشاء الشاشات
        self.home_view = HomeView(self.db, self)
        self.review_view = ReviewView(self.db, self)
        self.entry_view = EntryView(self.db, self)
        self.results_view = ResultsView(self.db, self)
        self.templates_view = TemplatesView(self.db, self)
        self.statistics_view = StatisticsView(self.db, self)

        self.stack.addWidget(self.home_view)       # 0
        self.stack.addWidget(self.review_view)     # 1
        self.stack.addWidget(self.entry_view)      # 2
        self.stack.addWidget(self.results_view)    # 3
        self.stack.addWidget(self.templates_view)  # 4
        self.stack.addWidget(self.statistics_view) # 5

        # شريط الحالة
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr("ready"))

        # الشاشة الافتراضية
        self.show_home()

    # ─── تبديل اللغة ──────────────────────────────────────────────────────────

    def toggle_language(self):
        new_lang = "en" if get_language() == "ar" else "ar"
        set_language(new_lang, self.db)
        self.update_language_ui()

    def update_language_ui(self):
        app = QApplication.instance()
        if app:
            app.setLayoutDirection(get_layout_direction())
        self.setLayoutDirection(get_layout_direction())
        self.setStyleSheet(get_app_stylesheet(is_rtl()))

        from build_info import APP_VERSION
        self.setWindowTitle(tr("app_title", version=APP_VERSION))

        cur_idx = self.stack.currentIndex()
        if cur_idx == 0:
            self.show_home()
        elif cur_idx == 1:
            if self.review_view.template:
                self.show_review(self.review_view.template)
            else:
                self.show_home()
        elif cur_idx == 2:
            if self.entry_view.session and self.entry_view.template:
                self.show_entry(self.entry_view.session, self.entry_view.template)
            else:
                self.show_home()
        elif cur_idx == 3:
            self.show_results()
        elif cur_idx == 4:
            self.show_templates()
        elif cur_idx == 5:
            self.show_statistics()

    # ─── التنقل بين الشاشات ───────────────────────────────────────────────────

    def show_home(self):
        self.home_view.refresh()
        self.stack.setCurrentIndex(0)
        self.status_bar.showMessage(tr("nav_home"))

    def show_review(self, template):
        self.review_view.load_template(template)
        self.stack.setCurrentIndex(1)
        self.status_bar.showMessage(tr("nav_review"))

    def show_entry(self, session, template):
        self.entry_view.load_session(session, template)
        self.stack.setCurrentIndex(2)
        self.status_bar.showMessage(tr("nav_entry"))

    def show_results(self):
        self.results_view.refresh()
        self.stack.setCurrentIndex(3)
        self.status_bar.showMessage(tr("nav_results"))

    def show_templates(self):
        self.templates_view.refresh()
        self.stack.setCurrentIndex(4)
        self.status_bar.showMessage(tr("nav_templates"))

    def show_statistics(self):
        self.statistics_view.refresh()
        self.stack.setCurrentIndex(5)
        self.status_bar.showMessage(tr("nav_stats"))

    # ─── حالة الحفظ ───────────────────────────────────────────────────────────

    def set_save_status(self, status: str):
        """status: 'saving' | 'saved' | 'error'"""
        messages = {
            "saving": tr("saving"),
            "saved":  tr("saved"),
            "error":  tr("error_saving")
        }
        self.status_bar.showMessage(messages.get(status, status))
        if status in ("saved", "error"):
            self._save_status_timer.start(3000)

    def _clear_save_status(self):
        self.status_bar.showMessage(tr("ready"))

    def closeEvent(self, event):
        self.db.close()
        event.accept()
