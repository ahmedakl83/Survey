from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QAbstractItemView, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database.db_manager import DatabaseManager
from utils.excel_exporter import export_session_to_excel
from utils.translator import tr, get_layout_direction, get_text_alignment


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

        self.btn_back = QPushButton(tr("back"))
        self.btn_back.setStyleSheet(
            "background-color: transparent; color: white; border: none; font-size: 13px;"
        )
        self.btn_back.clicked.connect(self.main_window.show_home)
        h_layout.addWidget(self.btn_back)

        self.title_lbl = QLabel(tr("results_title"))
        self.title_lbl.setStyleSheet("color: white; font-size: 17px; font-weight: bold;")
        h_layout.addWidget(self.title_lbl)
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
        
        self.search_lbl = QLabel(tr("search"))
        self.search_lbl.setStyleSheet("font-weight: bold; color: #546E7A;")
        search_layout.addWidget(self.search_lbl)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search_results_placeholder"))
        self.search_input.setStyleSheet("padding: 6px 10px; font-size: 13px;")
        self.search_input.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_input, 1)

        self.btn_import_session = QPushButton(tr("btn_import_session"))
        self.btn_import_session.setObjectName("btn_secondary")
        self.btn_import_session.clicked.connect(self._import_session)
        search_layout.addWidget(self.btn_import_session)
        
        content_layout.addLayout(search_layout)

        # جدول الجلسات
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self._update_header_labels()
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
        self.table.setColumnWidth(5, 380)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        content_layout.addWidget(self.table)

        root.addWidget(content)

    def _update_header_labels(self):
        self.table.setHorizontalHeaderLabels([
            tr("th_session_name"),
            tr("th_template"),
            tr("th_forms"),
            tr("th_completed"),
            tr("last_modified"),
            tr("actions")
        ])

    def refresh(self):
        self.setLayoutDirection(get_layout_direction())
        self.btn_back.setText(tr("back"))
        self.title_lbl.setText(tr("results_title"))
        self.search_lbl.setText(tr("search"))
        self.search_input.setPlaceholderText(tr("search_results_placeholder"))
        self.btn_import_session.setText(tr("btn_import_session"))
        self._update_header_labels()

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
            session_item = QTableWidgetItem(session.name)
            session_item.setTextAlignment(get_text_alignment() | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 0, session_item)

            # اسم القالب
            template_name = template.name if template else "—"
            template_item = QTableWidgetItem(template_name)
            template_item.setTextAlignment(get_text_alignment() | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, template_item)

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

            btn_resume = QPushButton(tr("btn_resume"))
            btn_resume.setFixedWidth(82)
            btn_resume.clicked.connect(
                lambda _, sid=session.id: self._resume_session(sid)
            )
            actions_layout.addWidget(btn_resume)

            btn_export = QPushButton(tr("btn_export_excel"))
            btn_export.setObjectName("btn_success")
            btn_export.setFixedWidth(95)
            btn_export.clicked.connect(
                lambda _, sid=session.id: self._export_session(sid)
            )
            actions_layout.addWidget(btn_export)

            btn_backup = QPushButton(tr("btn_backup_session_action"))
            btn_backup.setObjectName("btn_secondary")
            btn_backup.setFixedWidth(85)
            btn_backup.clicked.connect(
                lambda _, sid=session.id: self._backup_session(sid)
            )
            actions_layout.addWidget(btn_backup)

            btn_delete = QPushButton(tr("delete"))
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
            QMessageBox.warning(self, tr("error"), tr("session_not_found"))
            return
        template = self.db.load_template(session.template_id)
        if not template:
            QMessageBox.warning(self, tr("error"), tr("template_linked_not_found"))
            return
        self.main_window.show_entry(session, template)

    def _export_session(self, session_id: int):
        session = self.db.load_session(session_id)
        if not session:
            QMessageBox.warning(self, tr("error"), tr("session_not_found"))
            return
        template = self.db.load_template(session.template_id)
        if not template:
            QMessageBox.warning(self, tr("error"), tr("template_not_found"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_excel_title"),
            f"{session.name}.xlsx",
            tr("excel_files_filter")
        )
        if not path:
            return

        try:
            export_session_to_excel(session, template, path)
            QMessageBox.information(
                self, tr("export_success_title"),
                tr("export_success_msg", path=path)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("export_error_title"), str(e))

    def _backup_session(self, session_id: int):
        session = self.db.load_session(session_id)
        if not session:
            QMessageBox.warning(self, tr("error"), tr("session_not_found"))
            return
        template = self.db.load_template(session.template_id)
        if not template:
            QMessageBox.warning(self, tr("error"), tr("template_not_found"))
            return

        from utils.session_exporter import export_session_backup
        path, _ = QFileDialog.getSaveFileName(
            self, tr("backup_session_save_title"),
            f"{session.name}_backup.surveysession",
            tr("session_backup_filter")
        )
        if not path:
            return

        try:
            export_session_backup(session, template, path)
            QMessageBox.information(
                self, tr("success"),
                tr("backup_session_success_msg", path=path)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("backup_session_failed_msg", error=str(e)))

    def _import_session(self):
        from PyQt6.QtWidgets import QInputDialog
        from utils.session_exporter import read_session_backup_info, import_session_into_db

        path, _ = QFileDialog.getOpenFileName(
            self, tr("import_session_title"), "",
            tr("session_backup_filter")
        )
        if not path:
            return

        try:
            info = read_session_backup_info(path)
        except Exception as e:
            QMessageBox.critical(self, tr("import_error"), f"{tr('import_session_invalid_file')}\n\n{e}")
            return

        s_name = info["session_name"]
        existing = self.db.get_session_by_name(s_name)

        overwrite_id = None
        final_name = s_name

        if existing:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(tr("import_session_conflict_title"))
            msg_box.setText(tr("import_session_conflict_msg", name=s_name))
            msg_box.setIcon(QMessageBox.Icon.Question)

            btn_replace = msg_box.addButton(tr("btn_replace_existing"), QMessageBox.ButtonRole.AcceptRole)
            btn_new = msg_box.addButton(tr("btn_save_as_new"), QMessageBox.ButtonRole.ActionRole)
            btn_cancel = msg_box.addButton(QMessageBox.StandardButton.Cancel)

            msg_box.exec()
            clicked = msg_box.clickedButton()

            if clicked == btn_cancel:
                return
            elif clicked == btn_replace:
                overwrite_id = existing.id
                final_name = s_name
            elif clicked == btn_new:
                new_name, ok = QInputDialog.getText(
                    self, tr("import_session_name_title"),
                    tr("import_session_name_prompt"),
                    text=f"{s_name} (مستوردة)"
                )
                if not ok or not new_name.strip():
                    return
                final_name = new_name.strip()
        else:
            new_name, ok = QInputDialog.getText(
                self, tr("import_session_name_title"),
                tr("import_session_name_prompt"),
                text=s_name
            )
            if not ok or not new_name.strip():
                return
            final_name = new_name.strip()

        try:
            imported_session = import_session_into_db(
                raw_data=info["raw_data"],
                db=self.db,
                custom_session_name=final_name,
                overwrite_session_id=overwrite_id
            )
            self.refresh()
            QMessageBox.information(
                self, tr("import_session_success_title"),
                tr("import_session_success_msg",
                   name=imported_session.name,
                   template=info["template_name"],
                   total=imported_session.total_forms,
                   completed=imported_session.completed_forms)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("import_session_failed_msg", error=str(e)))

    def _delete_session(self, session_id: int):
        reply = QMessageBox.question(
            self, tr("delete_session_confirm_title"),
            tr("delete_session_confirm_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_session(session_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, tr("delete_error_title"), str(e))

