from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QInputDialog, QMessageBox, QFrame, QScrollArea,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager
from utils.excel_importer import import_template_from_excel, import_responses_from_excel, ImportError
from models.session import Session
from utils.translator import tr, get_layout_direction, is_rtl


class HomeView(QWidget):
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
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #1565C0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        from build_info import APP_VERSION
        self.title_lbl = QLabel(tr("app_title", version=APP_VERSION))
        self.title_lbl.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()

        # زر تبديل اللغة
        self.btn_lang = QPushButton(tr("language_toggle"))
        self.btn_lang.setObjectName("btn_secondary")
        self.btn_lang.setStyleSheet(
            "background-color: #FFC107; color: #1a1a2e; "
            "border: none; border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold; margin-left: 4px; margin-right: 4px;"
        )
        self.btn_lang.clicked.connect(self.main_window.toggle_language)
        h_layout.addWidget(self.btn_lang)

        self.btn_templates = QPushButton(tr("nav_templates"))
        self.btn_templates.setObjectName("btn_secondary")
        self.btn_templates.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold;"
        )
        self.btn_templates.clicked.connect(self.main_window.show_templates)
        h_layout.addWidget(self.btn_templates)

        self.btn_results = QPushButton(tr("nav_results"))
        self.btn_results.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold; margin-right: 4px; margin-left: 4px;"
        )
        self.btn_results.clicked.connect(self.main_window.show_results)
        h_layout.addWidget(self.btn_results)
 
        self.btn_stats = QPushButton(tr("nav_stats"))
        self.btn_stats.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold; margin-right: 4px; margin-left: 4px;"
        )
        self.btn_stats.clicked.connect(self.main_window.show_statistics)
        h_layout.addWidget(self.btn_stats)

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        root.addWidget(scroll)

        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(32, 32, 32, 32)
        self.content_layout.setSpacing(24)

        # ─── بطاقات الإجراءات الرئيسية ────────────────────────────────────────
        self.actions_label = QLabel(tr("start_new_session"))
        self.actions_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0;")
        self.content_layout.addWidget(self.actions_label)

        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(16)
        self._build_action_cards()
        self.content_layout.addLayout(self.cards_layout)

        # ─── القوالب الأخيرة ──────────────────────────────────────────────────
        self.recent_label = QLabel(tr("recent_templates"))
        self.recent_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0;")
        self.content_layout.addWidget(self.recent_label)

        self.recent_frame = QFrame()
        self.recent_frame.setObjectName("recent_frame")
        self.recent_frame.setStyleSheet(
            "QFrame#recent_frame { background-color: white; border-radius: 8px; "
            "border: 1px solid #CFD8DC; }"
        )
        self.recent_layout = QVBoxLayout(self.recent_frame)
        self.recent_layout.setContentsMargins(16, 16, 16, 16)
        self.recent_layout.setSpacing(8)
        self.content_layout.addWidget(self.recent_frame)
 
        # ─── صيانة البيانات ───────────────────────────────────────────────────
        self.maint_label = QLabel(tr("data_maintenance"))
        self.maint_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0; margin-top: 12px;")
        self.content_layout.addWidget(self.maint_label)
 
        self.maint_frame = QFrame()
        self.maint_frame.setObjectName("maint_frame")
        self.maint_frame.setStyleSheet("QFrame#maint_frame { background-color: #F5F5F5; border-radius: 8px; border: 1px dashed #BDBDBD; }")
        self.maint_layout = QHBoxLayout(self.maint_frame)
        self.maint_layout.setContentsMargins(16, 12, 16, 12)
 
        self.maint_desc = QLabel(tr("maintenance_desc"))
        self.maint_desc.setStyleSheet("color: #616161; font-size: 12px; border: none;")
        self.maint_layout.addWidget(self.maint_desc)
        self.maint_layout.addStretch()
 
        self.btn_backup = QPushButton(tr("btn_backup"))
        self.btn_backup.setObjectName("btn_secondary")
        self.btn_backup.clicked.connect(self._on_backup)
        self.maint_layout.addWidget(self.btn_backup)
 
        self.btn_restore = QPushButton(tr("btn_restore"))
        self.btn_restore.setObjectName("btn_danger")
        self.btn_restore.clicked.connect(self._on_restore)
        self.maint_layout.addWidget(self.btn_restore)
 
        self.content_layout.addWidget(self.maint_frame)
        self.content_layout.addStretch()

    def _build_action_cards(self):
        # تنظيف البطاقات السابقة
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # بطاقة: استيراد ملف Excel
        import_card = self._make_action_card(
            tr("card_import_excel_title"),
            tr("card_import_excel_desc"),
            tr("card_import_excel_btn"),
            self._on_import_excel
        )
        self.cards_layout.addWidget(import_card, 0, 0)

        # بطاقة: إنشاء من الصفر
        create_card = self._make_action_card(
            tr("card_create_template_title"),
            tr("card_create_template_desc"),
            tr("card_create_template_btn"),
            self._on_create_template
        )
        self.cards_layout.addWidget(create_card, 0, 1)

        # بطاقة: فتح قالب محفوظ
        template_card = self._make_action_card(
            tr("card_open_template_title"),
            tr("card_open_template_desc"),
            tr("card_open_template_btn"),
            self._on_open_template
        )
        self.cards_layout.addWidget(template_card, 0, 2)

        # بطاقة: استئناف جلسة
        resume_card = self._make_action_card(
            tr("card_resume_session_title"),
            tr("card_resume_session_desc"),
            tr("card_resume_session_btn"),
            self._on_resume_session
        )
        self.cards_layout.addWidget(resume_card, 1, 0)

        # بطاقة: استيراد إجابات رقمية
        import_responses_card = self._make_action_card(
            tr("card_import_responses_title"),
            tr("card_import_responses_desc"),
            tr("card_import_responses_btn"),
            self._on_import_responses
        )
        self.cards_layout.addWidget(import_responses_card, 1, 1)

    def _make_action_card(self, title, description, btn_text, callback) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: white; border-radius: 10px; "
            "border: 1px solid #CFD8DC; }"
        )
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setFixedHeight(180)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #1565C0; border: none;"
        )
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        layout.addStretch()

        btn = QPushButton(btn_text)
        btn.clicked.connect(callback)
        layout.addWidget(btn)

        return card

    def refresh(self):
        self.setLayoutDirection(get_layout_direction())
        from build_info import APP_VERSION
        self.title_lbl.setText(tr("app_title", version=APP_VERSION))
        self.btn_lang.setText(tr("language_toggle"))
        self.btn_templates.setText(tr("nav_templates"))
        self.btn_results.setText(tr("nav_results"))
        self.btn_stats.setText(tr("nav_stats"))
        self.actions_label.setText(tr("start_new_session"))
        self.recent_label.setText(tr("recent_templates"))
        self.maint_label.setText(tr("data_maintenance"))
        self.maint_desc.setText(tr("maintenance_desc"))
        self.btn_backup.setText(tr("btn_backup"))
        self.btn_restore.setText(tr("btn_restore"))

        self._build_action_cards()

        # تحديث القوالب الأخيرة
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        templates = self.db.load_all_templates()
        if not templates:
            lbl = QLabel(tr("no_templates_yet"))
            lbl.setStyleSheet("color: #90A4AE; padding: 8px;")
            self.recent_layout.addWidget(lbl)
            return

        for t in templates[:5]:
            row = QFrame()
            row.setObjectName("recent_row")
            row.setStyleSheet(
                "QFrame#recent_row { border: none; border-bottom: 1px solid #ECEFF1; }"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 6, 4, 6)

            q_count_str = tr("questions_num", count=t.question_count)
            use_count_str = tr("used_num_times", count=t.use_count)
            info = QLabel(
                f"<b>{t.name}</b>  "
                f"<span style='color:#90A4AE; font-size:11px;'>"
                f"{q_count_str} · {use_count_str} · {t.updated_at.strftime('%Y-%m-%d')}"
                f"</span>"
            )
            info.setStyleSheet("border: none;")
            row_layout.addWidget(info)
            row_layout.addStretch()

            btn_use = QPushButton(tr("use"))
            btn_use.setFixedWidth(90)
            btn_use.clicked.connect(lambda _, tid=t.id: self._start_from_template(tid))
            row_layout.addWidget(btn_use)

            btn_import = QPushButton(tr("btn_numeric_answers"))
            btn_import.setFixedWidth(130)
            btn_import.setObjectName("btn_secondary")
            btn_import.setToolTip(tr("tooltip_numeric_answers"))
            btn_import.clicked.connect(lambda _, tid=t.id: self._import_responses_for_template(tid))
            row_layout.addWidget(btn_import)

            self.recent_layout.addWidget(row)

    def _on_create_template(self):
        name, ok = QInputDialog.getText(
            self, tr("create_new_template_title"),
            tr("create_new_template_prompt"),
            text=tr("default_template_name")
        )
        if not ok or not name.strip():
            return

        from models.template import Template
        template = Template(name=name.strip())
        
        template_id = self.db.save_template(template)
        template.id = template_id
        
        self.main_window.show_review(template)

    def _on_import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("choose_excel_file"), "",
            tr("excel_files_filter")
        )
        if not path:
            return

        try:
            template, warnings = import_template_from_excel(path)
        except ImportError as e:
            QMessageBox.critical(self, tr("import_error"), str(e))
            return

        if warnings:
            msg = tr("import_warnings_msg", warnings="\n".join(f"• {w}" for w in warnings))
            QMessageBox.warning(self, tr("import_warnings_title"), msg)

        # طلب اسم القالب
        name, ok = QInputDialog.getText(
            self, tr("template_name_prompt_title"),
            tr("template_name_prompt_msg"),
            text=template.name or tr("default_template_name")
        )
        if not ok or not name.strip():
            return
        template.name = name.strip()

        # حفظ القالب
        template_id = self.db.save_template(template)
        template.id = template_id

        # تحديث معرفات مقاييس ليكرت في الأسئلة
        saved_template = self.db.load_template(template_id)
        self.main_window.show_review(saved_template)

    def _on_open_template(self):
        templates = self.db.load_all_templates()
        if not templates:
            QMessageBox.information(self, tr("no_templates_title"), tr("no_templates_yet"))
            return
        self.main_window.show_templates()

    def _on_resume_session(self):
        sessions = self.db.load_all_sessions()
        incomplete = [s for s in sessions if s.completed_forms < s.total_forms]
        if not incomplete:
            QMessageBox.information(self, tr("no_sessions_title"), tr("no_sessions_msg"))
            return
        self.main_window.show_results()

    def _start_from_template(self, template_id: int):
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, tr("error"), tr("template_not_found"))
            return
        self.main_window.show_review(template)

    def _import_responses_for_template(self, template_id: int):
        """استيراد إجابات رقمية مباشرة من قائمة القوالب الأخيرة"""
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, tr("error"), tr("template_not_found"))
            return

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

        name, ok = QInputDialog.getText(
            self, tr("session_name_title"),
            tr("session_name_prompt", template=template.name, count=len(forms)),
            text=tr("default_session_name", template=template.name)
        )
        if not ok or not name.strip():
            return

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

    def _on_import_responses(self):
        """استيراد ملف إجابات رقمية بالاستناد إلى قالب محفوظ"""
        templates = self.db.load_all_templates()
        if not templates:
            QMessageBox.information(
                self, tr("no_templates_title"),
                tr("need_template_first")
            )
            return

        from views.template_picker_dialog import TemplatePickerDialog
        dialog = TemplatePickerDialog(templates, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        template = dialog.selected_template()
        if template is None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, tr("choose_responses_file_title", template_name=template.name), "",
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

        name, ok = QInputDialog.getText(
            self, tr("session_name_title"),
            tr("session_name_prompt_simple", count=len(forms)),
            text=tr("default_session_name", template=template.name)
        )
        if not ok or not name.strip():
            return

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
 
    def _on_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("backup_save_title"),
            f"survey_backup_{datetime.now().strftime('%Y%m%d')}.db",
            tr("db_files_filter")
        )
        if not path:
            return
        try:
            self.db.backup_database(path)
            QMessageBox.information(self, tr("success"), tr("backup_success_msg", path=path))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("backup_failed_msg", error=str(e)))
 
    def _on_restore(self):
        reply = QMessageBox.warning(
            self, tr("restore_confirm_title"),
            tr("restore_confirm_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
 
        path, _ = QFileDialog.getOpenFileName(
            self, tr("choose_backup_file"), "",
            tr("db_files_filter")
        )
        if not path:
            return
 
        try:
            self.db.restore_database(path)
            QMessageBox.information(self, tr("success"), tr("restore_success_msg"))
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("restore_failed_msg", error=str(e)))
