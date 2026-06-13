from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QVBoxLayout,
    QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from database.db_manager import DatabaseManager
from views.styles import APP_STYLESHEET
from views.home_view import HomeView
from views.review_view import ReviewView
from views.entry_view import EntryView
from views.results_view import ResultsView
from views.templates_view import TemplatesView
from views.statistics_view import StatisticsView


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        from build_info import APP_VERSION
        self.setWindowTitle(f"تفريغ الاستبيانات - الإصدار {APP_VERSION}")
        self.setMinimumSize(1024, 680)
        self.resize(1280, 800)
        self.setStyleSheet(APP_STYLESHEET)

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
        self.status_bar.showMessage("جاهز")

        # الشاشة الافتراضية
        self.show_home()

    # ─── التنقل بين الشاشات ───────────────────────────────────────────────────

    def show_home(self):
        self.home_view.refresh()
        self.stack.setCurrentIndex(0)
        self.status_bar.showMessage("الصفحة الرئيسية")

    def show_review(self, template):
        self.review_view.load_template(template)
        self.stack.setCurrentIndex(1)
        self.status_bar.showMessage("مراجعة الأسئلة")

    def show_entry(self, session, template):
        self.entry_view.load_session(session, template)
        self.stack.setCurrentIndex(2)
        self.status_bar.showMessage("تفريغ البيانات")

    def show_results(self):
        self.results_view.refresh()
        self.stack.setCurrentIndex(3)
        self.status_bar.showMessage("النتائج")

    def show_templates(self):
        self.templates_view.refresh()
        self.stack.setCurrentIndex(4)
        self.status_bar.showMessage("إدارة القوالب")

    def show_statistics(self):
        self.statistics_view.refresh()
        self.stack.setCurrentIndex(5)
        self.status_bar.showMessage("إحصائيات النظام")

    # ─── حالة الحفظ ───────────────────────────────────────────────────────────

    def set_save_status(self, status: str):
        """status: 'saving' | 'saved' | 'error'"""
        messages = {
            "saving": "⏳ جاري الحفظ...",
            "saved":  "✅ تم الحفظ",
            "error":  "❌ خطأ في الحفظ"
        }
        self.status_bar.showMessage(messages.get(status, status))
        if status in ("saved", "error"):
            self._save_status_timer.start(3000)

    def _clear_save_status(self):
        self.status_bar.showMessage("جاهز")

    def closeEvent(self, event):
        self.db.close()
        event.accept()
