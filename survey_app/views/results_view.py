from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QAbstractItemView, QInputDialog,
    QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database.db_manager import DatabaseManager
from utils.excel_exporter import export_session_to_excel


class ResultsView(QWidget):
    def __init__(self, db: DatabaseManager, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── شريط العنوان ─────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #1565C0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        btn_back = QPushButton("→ رجوع")
        btn_back.setStyleSheet(
            "background-color: transparent; color: white; border: none; font-size: 13px;"
        )
        btn_back.clicked.connect(self.main_window.show_home)
        h_layout.addWidget(btn_back)

        title = QLabel("النتائج المحفوظة")
        title.setStyleSheet("color: white; font-size: 17px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 16)
        content_layout.setSpacing(12)

        # شريط البحث
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        search_lbl = QLabel("بحث:")
        search_lbl.setStyleSheet("font-weight: bold; color: #546E7A;")
        search_layout.addWidget(search_lbl)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم الجلسة أو القالب...")
        self.search_input.setStyleSheet("padding: 6px 10px; font-size: 13px;")
        self.search_input.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_input, 1)
        
        content_layout.addLayout(search_layout)

        # جدول الجلسات
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "اسم الجلسة", "القالب", "الاستمارات",
            "مكتملة", "آخر تعديل", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for col in [2, 3, 4]:
            self.table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.Fixed
            )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 290)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        content_layout.addWidget(self.table)

        root.addWidget(content)

    def refresh(self):
        self.table.setRowCount(0)
        sessions = self.db.load_all_sessions()
        search_text = self.search_input.text().lower()

        filtered_sessions = []
        for s in sessions:
            template = self.db.load_template(s.template_id)
            template_name = template.name.lower() if template else ""
            if search_text in s.name.lower() or search_text in template_name:
                filtered_sessions.append((s, template))

        for i, (session, template) in enumerate(filtered_sessions):
            self.table.insertRow(i)

            # اسم الجلسة
            self.table.setItem(i, 0, QTableWidgetItem(session.name))

            # اسم القالب
            template_name = template.name if template else "—"
            self.table.setItem(i, 1, QTableWidgetItem(template_name))

            # عدد الاستمارات
            total_item = QTableWidgetItem(str(session.total_forms))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, total_item)

            # مكتملة
            completed = session.completed_forms
            comp_item = QTableWidgetItem(str(completed))
            comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if completed == session.total_forms:
                comp_item.setForeground(QColor("#2E7D32"))
            self.table.setItem(i, 3, comp_item)

            # آخر تعديل
            date_item = QTableWidgetItem(
                session.updated_at.strftime("%Y-%m-%d %H:%M")
            )
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 4, date_item)

            # أزرار الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 4, 6, 4)
            actions_layout.setSpacing(6)

            btn_resume = QPushButton("استئناف")
            btn_resume.setFixedWidth(82)
            btn_resume.clicked.connect(
                lambda _, sid=session.id: self._resume_session(sid)
            )
            actions_layout.addWidget(btn_resume)

            btn_export = QPushButton("تصدير Excel")
            btn_export.setObjectName("btn_success")
            btn_export.setFixedWidth(100)
            btn_export.clicked.connect(
                lambda _, sid=session.id: self._export_session(sid)
            )
            actions_layout.addWidget(btn_export)

            btn_delete = QPushButton("حذف")
            btn_delete.setObjectName("btn_danger")
            btn_delete.setFixedWidth(60)
            btn_delete.clicked.connect(
                lambda _, sid=session.id: self._delete_session(sid)
            )
            actions_layout.addWidget(btn_delete)
            actions_layout.addStretch()

            self.table.setCellWidget(i, 5, actions_widget)
            self.table.setRowHeight(i, 52)

    def _resume_session(self, session_id: int):
        session = self.db.load_session(session_id)
        if not session:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الجلسة.")
            return
        template = self.db.load_template(session.template_id)
        if not template:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القالب المرتبط.")
            return
        self.main_window.show_entry(session, template)

    def _export_session(self, session_id: int):
        session = self.db.load_session(session_id)
        if not session:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الجلسة.")
            return
        template = self.db.load_template(session.template_id)
        if not template:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القالب.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ ملف Excel",
            f"{session.name}.xlsx",
            "ملفات Excel (*.xlsx)"
        )
        if not path:
            return

        try:
            export_session_to_excel(session, template, path)
            QMessageBox.information(
                self, "تم التصدير",
                f"تم تصدير النتائج بنجاح إلى:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التصدير", str(e))

    def _delete_session(self, session_id: int):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل تريد حذف هذه الجلسة وجميع بياناتها؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_session(session_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "خطأ في الحذف", str(e))
