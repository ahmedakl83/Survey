from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager
from utils.excel_importer import import_responses_from_excel, ImportError
from models.session import Session
from utils.translator import tr, get_layout_direction, get_text_alignment


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

        self.btn_back = QPushButton(tr("back"))
        self.btn_back.setStyleSheet(
            "background-color: transparent; color: white; border: none; font-size: 13px;"
        )
        self.btn_back.clicked.connect(self.main_window.show_home)
        h_layout.addWidget(self.btn_back)

        self.title_lbl = QLabel(tr("templates_title"))
        self.title_lbl.setStyleSheet("color: white; font-size: 17px; font-weight: bold;")
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 16)
        content_layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_header_labels()
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
        self.btn_import_template = QPushButton(tr("btn_import_template_json"))
        self.btn_import_template.setObjectName("btn_secondary")
        self.btn_import_template.clicked.connect(self._import_template_from_file)
        btn_row.addWidget(self.btn_import_template)
        btn_row.addStretch()
        content_layout.addLayout(btn_row)

        root.addWidget(content)

    def _update_header_labels(self):
        self.table.setHorizontalHeaderLabels([
            tr("th_template_name"),
            tr("questions_count"),
            tr("usage_count"),
            tr("created_date"),
            tr("actions")
        ])

    def refresh(self):
        self.setLayoutDirection(get_layout_direction())
        self.btn_back.setText(tr("back"))
        self.title_lbl.setText(tr("templates_title"))
        self.btn_import_template.setText(tr("btn_import_template_json"))
        self._update_header_labels()

        self.table.setRowCount(0)
        templates = self.db.load_all_templates()

        for i, t in enumerate(templates):
            self.table.insertRow(i)

            name_item = QTableWidgetItem(t.name)
            name_item.setTextAlignment(get_text_alignment() | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 0, name_item)

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

            btn_use = QPushButton(tr("use"))
            btn_use.setFixedWidth(82)
            btn_use.clicked.connect(
                lambda _, tid=t.id: self._use_template(tid)
            )
            actions_layout.addWidget(btn_use)

            btn_import = QPushButton(tr("btn_numeric_answers"))
            btn_import.setObjectName("btn_secondary")
            btn_import.setFixedWidth(130)
            btn_import.setToolTip(tr("tooltip_import_responses_template"))
            btn_import.clicked.connect(
                lambda _, tid=t.id: self._import_responses(tid)
            )
            actions_layout.addWidget(btn_import)

            btn_edit = QPushButton(tr("edit"))
            btn_edit.setObjectName("btn_secondary")
            btn_edit.setFixedWidth(70)
            btn_edit.clicked.connect(
                lambda _, tid=t.id: self._edit_template(tid)
            )
            actions_layout.addWidget(btn_edit)

            btn_export = QPushButton(tr("export"))
            btn_export.setObjectName("btn_secondary")
            btn_export.setFixedWidth(70)
            btn_export.clicked.connect(
                lambda _, tid=t.id: self._export_template(tid)
            )
            actions_layout.addWidget(btn_export)

            btn_delete = QPushButton(tr("delete"))
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
            QMessageBox.warning(self, tr("error"), tr("template_not_found"))
            return

        # اختيار الملف
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("choose_responses_file_title", template_name=template.name),
            "",
            tr("excel_files_filter")
        )
        if not path:
            return

        try:
            forms, warnings = import_responses_from_excel(path, template)
        except ImportError as e:
            QMessageBox.critical(self, tr("import_error"), str(e))
            return

        if warnings:
            msg = tr(
                "import_responses_warning_msg",
                count=len(warnings),
                warnings="\n".join(f"• {w}" for w in warnings[:10])
            )
            reply = QMessageBox.warning(
                self, tr("import_warnings_title"), msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # اسم الجلسة
        name, ok = QInputDialog.getText(
            self, tr("session_name_title"),
            tr("session_name_prompt", template=template.name, count=len(forms)),
            text=tr("default_session_name", template=template.name)
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
            self, tr("import_success_title"),
            tr("import_responses_success_msg", count=len(forms), template=template.name)
        )
        self.main_window.show_results()

    def _delete_template(self, template_id: int):
        # التحقق من وجود جلسات مرتبطة
        linked_sessions = self.db.get_sessions_for_template(template_id)

        if linked_sessions:
            names = "\n".join(f"  • {s.name}" for s in linked_sessions[:5])
            extra = f"\n  ... +{len(linked_sessions) - 5}" if len(linked_sessions) > 5 else ""
            msg = tr(
                "delete_template_linked_msg",
                count=len(linked_sessions),
                names=names,
                extra=extra
            )
        else:
            msg = tr("delete_template_msg")

        reply = QMessageBox.question(
            self, tr("confirm_delete"), msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_template(template_id)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, tr("delete_error_title"), str(e))

    def _export_template(self, template_id: int):
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, tr("error"), tr("template_not_found"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, tr("export_template_title"),
            f"{template.name}.json",
            tr("json_files_filter")
        )
        if not path:
            return

        try:
            from utils.template_exporter import export_template_to_json
            export_template_to_json(template, path)
            QMessageBox.information(
                self, tr("success"),
                tr("export_template_success", path=path)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("export_error_title"), str(e))

    def _import_template_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("import_template_title"), "",
            tr("json_files_filter")
        )
        if not path:
            return

        try:
            from utils.template_exporter import import_template_from_json
            template = import_template_from_json(path)
        except Exception as e:
            QMessageBox.critical(self, tr("import_error"), tr("import_template_error", error=str(e)))
            return

        name, ok = QInputDialog.getText(
            self, tr("imported_template_name_title"),
            tr("imported_template_name_prompt"),
            text=template.name
        )
        if not ok or not name.strip():
            return
        template.name = name.strip()

        try:
            self.db.save_template(template)
            self.refresh()
            QMessageBox.information(
                self, tr("success"),
                tr("imported_template_success", name=template.name)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("imported_template_save_failed", error=str(e)))
