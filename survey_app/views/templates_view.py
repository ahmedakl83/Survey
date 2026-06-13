from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database.db_manager import DatabaseManager
from utils.excel_importer import import_responses_from_excel, ImportError
from models.session import Session


class TemplatesView(QWidget):
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

        title = QLabel("إدارة القوالب")
        title.setStyleSheet("color: white; font-size: 17px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 16)
        content_layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "اسم القالب", "عدد الأسئلة", "مرات الاستخدام",
            "تاريخ الإنشاء", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for col in [1, 2, 3]:
            self.table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.Fixed
            )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 450)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        content_layout.addWidget(self.table)

        # صف أزرار التحكم بالقوالب
        btn_row = QHBoxLayout()
        btn_import_template = QPushButton("📥 استيراد قالب من ملف (.json)")
        btn_import_template.setObjectName("btn_secondary")
        btn_import_template.clicked.connect(self._import_template_from_file)
        btn_row.addWidget(btn_import_template)
        btn_row.addStretch()
        content_layout.addLayout(btn_row)

        root.addWidget(content)

    def refresh(self):
        self.table.setRowCount(0)
        templates = self.db.load_all_templates()

        for i, t in enumerate(templates):
            self.table.insertRow(i)

            self.table.setItem(i, 0, QTableWidgetItem(t.name))

            q_item = QTableWidgetItem(str(t.question_count))
            q_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, q_item)

            use_item = QTableWidgetItem(str(t.use_count))
            use_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, use_item)

            date_item = QTableWidgetItem(t.created_at.strftime("%Y-%m-%d"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, date_item)

            # أزرار الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 4, 6, 4)
            actions_layout.setSpacing(6)

            btn_use = QPushButton("استخدام")
            btn_use.setFixedWidth(82)
            btn_use.clicked.connect(
                lambda _, tid=t.id: self._use_template(tid)
            )
            actions_layout.addWidget(btn_use)

            btn_import = QPushButton("📥 استيراد إجابات")
            btn_import.setObjectName("btn_secondary")
            btn_import.setFixedWidth(130)
            btn_import.setToolTip("استورد ملف Excel يحتوي على أرقام الإجابات وطبّق عليه هذا القالب")
            btn_import.clicked.connect(
                lambda _, tid=t.id: self._import_responses(tid)
            )
            actions_layout.addWidget(btn_import)

            btn_edit = QPushButton("تعديل")
            btn_edit.setObjectName("btn_secondary")
            btn_edit.setFixedWidth(70)
            btn_edit.clicked.connect(
                lambda _, tid=t.id: self._edit_template(tid)
            )
            actions_layout.addWidget(btn_edit)

            btn_export = QPushButton("📤 تصدير")
            btn_export.setObjectName("btn_secondary")
            btn_export.setFixedWidth(70)
            btn_export.clicked.connect(
                lambda _, tid=t.id: self._export_template(tid)
            )
            actions_layout.addWidget(btn_export)

            btn_delete = QPushButton("حذف")
            btn_delete.setObjectName("btn_danger")
            btn_delete.setFixedWidth(60)
            btn_delete.clicked.connect(
                lambda _, tid=t.id: self._delete_template(tid)
            )
            actions_layout.addWidget(btn_delete)
            actions_layout.addStretch()

            self.table.setCellWidget(i, 4, actions_widget)
            self.table.setRowHeight(i, 52)

    def _use_template(self, template_id: int):
        template = self.db.load_template(template_id)
        if template:
            self.main_window.show_review(template)

    def _edit_template(self, template_id: int):
        template = self.db.load_template(template_id)
        if template:
            self.main_window.show_review(template)

    def _import_responses(self, template_id: int):
        """استيراد ملف إجابات رقمية وتطبيق القالب المحدد عليه"""
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القالب.")
            return

        # اختيار الملف
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"اختر ملف الإجابات الرقمية — {template.name}",
            "",
            "ملفات Excel (*.xlsx *.xls)"
        )
        if not path:
            return

        try:
            forms, warnings = import_responses_from_excel(path, template)
        except ImportError as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", str(e))
            return

        if warnings:
            msg = (
                f"تم قراءة الملف مع {len(warnings)} تحذير:\n\n"
                + "\n".join(f"• {w}" for w in warnings[:10])
                + (f"\n... و{len(warnings) - 10} تحذير آخر" if len(warnings) > 10 else "")
                + "\n\nهل تريد المتابعة؟"
            )
            reply = QMessageBox.warning(
                self, "تحذيرات الاستيراد", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # اسم الجلسة
        name, ok = QInputDialog.getText(
            self, "اسم الجلسة",
            f"القالب: {template.name}\n"
            f"عدد الاستمارات المستوردة: {len(forms)}\n\n"
            f"أدخل اسماً لهذه الجلسة:",
            text=f"جلسة {template.name}"
        )
        if not ok or not name.strip():
            return

        # حفظ الجلسة
        session = Session(
            template_id=template.id,
            name=name.strip(),
            total_forms=len(forms)
        )
        session.forms = forms
        for i, f in enumerate(session.forms):
            f.form_index = i

        self.db.save_session(session)
        self.db.increment_template_use(template.id)

        QMessageBox.information(
            self, "تم الاستيراد بنجاح",
            f"✅ تم استيراد {len(forms)} استمارة بنجاح\n"
            f"القالب: {template.name}\n\n"
            f"يمكنك الآن عرض النتائج أو تصديرها."
        )
        self.main_window.show_results()

    def _delete_template(self, template_id: int):
        # التحقق من وجود جلسات مرتبطة
        linked_sessions = self.db.get_sessions_for_template(template_id)

        if linked_sessions:
            names = "\n".join(f"  • {s.name}" for s in linked_sessions[:5])
            extra = f"\n  ... و{len(linked_sessions) - 5} جلسة أخرى" if len(linked_sessions) > 5 else ""
            msg = (
                f"هذا القالب مرتبط بـ {len(linked_sessions)} جلسة تفريغ:\n"
                f"{names}{extra}\n\n"
                "حذف القالب سيؤدي إلى حذف هذه الجلسات وجميع بياناتها نهائياً.\n"
                "هل تريد المتابعة؟"
            )
        else:
            msg = "هل تريد حذف هذا القالب وجميع أسئلته؟\nلا يمكن التراجع عن هذا الإجراء."

        reply = QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_template(template_id)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحذف", str(e))

    def _export_template(self, template_id: int):
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القالب.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير القالب",
            f"{template.name}.json",
            "ملفات القوالب (*.json)"
        )
        if not path:
            return

        try:
            from utils.template_exporter import export_template_to_json
            export_template_to_json(template, path)
            QMessageBox.information(
                self, "تم التصدير بنجاح",
                f"✅ تم تصدير القالب بنجاح إلى:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التصدير", str(e))

    def _import_template_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "استيراد قالب", "",
            "ملفات القوالب (*.json)"
        )
        if not path:
            return

        try:
            from utils.template_exporter import import_template_from_json
            template = import_template_from_json(path)
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", f"تعذر قراءة ملف القالب:\n{str(e)}")
            return

        # طلب اسم القالب الجديد (أو المحافظة على الاسم الأصلي)
        name, ok = QInputDialog.getText(
            self, "اسم القالب المستورد",
            "تأكيد أو تعديل اسم القالب:",
            text=template.name
        )
        if not ok or not name.strip():
            return
        template.name = name.strip()

        try:
            # حفظ القالب
            self.db.save_template(template)
            self.refresh()
            QMessageBox.information(
                self, "تم الاستيراد بنجاح",
                f"✅ تم استيراد قالب '{template.name}' بنجاح وحفظه في قاعدة البيانات."
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"فشل حفظ القالب المستورد:\n{str(e)}")
