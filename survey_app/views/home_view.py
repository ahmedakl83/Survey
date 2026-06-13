from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QInputDialog, QMessageBox, QFrame, QScrollArea,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from database.db_manager import DatabaseManager
from utils.excel_importer import import_template_from_excel, import_responses_from_excel, ImportError
from models.session import Session


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
        title = QLabel(f"تفريغ الاستبيانات - الإصدار {APP_VERSION}")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        btn_templates = QPushButton("إدارة القوالب")
        btn_templates.setObjectName("btn_secondary")
        btn_templates.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold;"
        )
        btn_templates.clicked.connect(self.main_window.show_templates)
        h_layout.addWidget(btn_templates)

        btn_results = QPushButton("النتائج المحفوظة")
        btn_results.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold; margin-right: 8px;"
        )
        btn_results.clicked.connect(self.main_window.show_results)
        h_layout.addWidget(btn_results)
 
        btn_stats = QPushButton("الإحصائيات")
        btn_stats.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 6px 16px; font-weight: bold; margin-right: 8px;"
        )
        btn_stats.clicked.connect(self.main_window.show_statistics)
        h_layout.addWidget(btn_stats)

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        root.addWidget(scroll)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(24)

        # ─── بطاقات الإجراءات الرئيسية ────────────────────────────────────────
        actions_label = QLabel("ابدأ جلسة تفريغ جديدة")
        actions_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0;")
        content_layout.addWidget(actions_label)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)

        # بطاقة: استيراد ملف Excel
        import_card = self._make_action_card(
            "📂  استيراد ملف Excel",
            "استورد ملف Excel يحتوي على الأسئلة\nوإجاباتها وابدأ جلسة تفريغ جديدة",
            "استيراد",
            self._on_import_excel
        )
        cards_layout.addWidget(import_card, 0, 0)

        # بطاقة: إنشاء من الصفر
        create_card = self._make_action_card(
            "✨  إنشاء قالب من الصفر",
            "أنشئ قالباً جديداً يدوياً وقم بإضافة\nالأسئلة والخيارات بنفسك",
            "إنشاء جديد",
            self._on_create_template
        )
        cards_layout.addWidget(create_card, 0, 1)

        # بطاقة: فتح قالب محفوظ
        template_card = self._make_action_card(
            "📋  فتح قالب محفوظ",
            "اختر قالباً محفوظاً مسبقاً\nوابدأ جلسة تفريغ جديدة",
            "فتح قالب",
            self._on_open_template
        )
        cards_layout.addWidget(template_card, 0, 2)

        # بطاقة: استئناف جلسة
        resume_card = self._make_action_card(
            "▶️  استئناف جلسة",
            "استأنف جلسة تفريغ سابقة\nمن النقطة التي توقفت عندها",
            "استئناف",
            self._on_resume_session
        )
        cards_layout.addWidget(resume_card, 1, 0)

        # بطاقة: استيراد إجابات رقمية
        import_responses_card = self._make_action_card(
            "🔢  استيراد إجابات رقمية",
            "لديك ملف Excel جاهز بأرقام الإجابات؟\nاختر قالباً وسيتم تحويل الأرقام\nإلى نصوص الإجابات تلقائياً",
            "استيراد إجابات",
            self._on_import_responses
        )
        cards_layout.addWidget(import_responses_card, 1, 1)

        content_layout.addLayout(cards_layout)

        # ─── القوالب الأخيرة ──────────────────────────────────────────────────
        recent_label = QLabel("القوالب الأخيرة")
        recent_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0;")
        content_layout.addWidget(recent_label)

        self.recent_frame = QFrame()
        self.recent_frame.setObjectName("recent_frame")
        self.recent_frame.setStyleSheet(
            "QFrame#recent_frame { background-color: white; border-radius: 8px; "
            "border: 1px solid #CFD8DC; }"
        )
        self.recent_layout = QVBoxLayout(self.recent_frame)
        self.recent_layout.setContentsMargins(16, 16, 16, 16)
        self.recent_layout.setSpacing(8)
        content_layout.addWidget(self.recent_frame)
 
        # ─── صيانة البيانات ───────────────────────────────────────────────────
        maint_label = QLabel("صيانة البيانات")
        maint_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0; margin-top: 12px;")
        content_layout.addWidget(maint_label)
 
        maint_frame = QFrame()
        maint_frame.setObjectName("maint_frame")
        maint_frame.setStyleSheet("QFrame#maint_frame { background-color: #F5F5F5; border-radius: 8px; border: 1px dashed #BDBDBD; }")
        maint_layout = QHBoxLayout(maint_frame)
        maint_layout.setContentsMargins(16, 12, 16, 12)
 
        maint_desc = QLabel("قم بحماية بياناتك عن طريق أخذ نسخة احتياطية دورية أو استعادتها.")
        maint_desc.setStyleSheet("color: #616161; font-size: 12px; border: none;")
        maint_layout.addWidget(maint_desc)
        maint_layout.addStretch()
 
        btn_backup = QPushButton("📦 نسخة احتياطية")
        btn_backup.setObjectName("btn_secondary")
        btn_backup.clicked.connect(self._on_backup)
        maint_layout.addWidget(btn_backup)
 
        btn_restore = QPushButton("🔄 استعادة البيانات")
        btn_restore.setObjectName("btn_danger")
        btn_restore.clicked.connect(self._on_restore)
        maint_layout.addWidget(btn_restore)
 
        content_layout.addWidget(maint_frame)

        content_layout.addStretch()

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
        # تحديث القوالب الأخيرة
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        templates = self.db.load_all_templates()
        if not templates:
            lbl = QLabel("لا توجد قوالب محفوظة بعد.")
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

            info = QLabel(
                f"<b>{t.name}</b>  "
                f"<span style='color:#90A4AE; font-size:11px;'>"
                f"{t.question_count} سؤال · "
                f"استُخدم {t.use_count} مرة · "
                f"{t.updated_at.strftime('%Y-%m-%d')}"
                f"</span>"
            )
            info.setStyleSheet("border: none;")
            row_layout.addWidget(info)
            row_layout.addStretch()

            btn_use = QPushButton("استخدام")
            btn_use.setFixedWidth(90)
            btn_use.clicked.connect(lambda _, tid=t.id: self._start_from_template(tid))
            row_layout.addWidget(btn_use)

            btn_import = QPushButton("📥 إجابات رقمية")
            btn_import.setFixedWidth(120)
            btn_import.setObjectName("btn_secondary")
            btn_import.setToolTip("استورد ملف Excel بأرقام الإجابات وطبّق هذا القالب عليه")
            btn_import.clicked.connect(lambda _, tid=t.id: self._import_responses_for_template(tid))
            row_layout.addWidget(btn_import)

            self.recent_layout.addWidget(row)

    def _on_create_template(self):
        name, ok = QInputDialog.getText(
            self, "إنشاء قالب جديد",
            "أدخل اسماً للقالب الجديد:",
            text="قالب جديد"
        )
        if not ok or not name.strip():
            return

        from models.template import Template
        template = Template(name=name.strip())
        
        # حفظ القالب للحصول على ID
        template_id = self.db.save_template(template)
        template.id = template_id
        
        self.main_window.show_review(template)

    # ─── معالجات الأحداث ──────────────────────────────────────────────────────

    def _on_import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف Excel", "",
            "ملفات Excel (*.xlsx *.xls)"
        )
        if not path:
            return

        try:
            template, warnings = import_template_from_excel(path)
        except ImportError as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", str(e))
            return

        if warnings:
            msg = "تم الاستيراد مع التحذيرات التالية:\n\n" + "\n".join(f"• {w}" for w in warnings)
            QMessageBox.warning(self, "تحذيرات", msg)

        # طلب اسم القالب
        name, ok = QInputDialog.getText(
            self, "اسم القالب",
            "أدخل اسماً للقالب:",
            text="قالب جديد"
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
            QMessageBox.information(self, "لا توجد قوالب", "لا توجد قوالب محفوظة بعد.")
            return
        self.main_window.show_templates()

    def _on_resume_session(self):
        sessions = self.db.load_all_sessions()
        incomplete = [s for s in sessions if s.completed_forms < s.total_forms]
        if not incomplete:
            QMessageBox.information(self, "لا توجد جلسات", "لا توجد جلسات غير مكتملة.")
            return
        self.main_window.show_results()

    def _start_from_template(self, template_id: int):
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القالب.")
            return
        self.main_window.show_review(template)

    def _import_responses_for_template(self, template_id: int):
        """استيراد إجابات رقمية مباشرة من قائمة القوالب الأخيرة"""
        template = self.db.load_template(template_id)
        if not template:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القالب.")
            return

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

        name, ok = QInputDialog.getText(
            self, "اسم الجلسة",
            f"القالب: {template.name}\n"
            f"عدد الاستمارات المستوردة: {len(forms)}\n\n"
            f"أدخل اسماً لهذه الجلسة:",
            text=f"جلسة {template.name}"
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
            self, "تم الاستيراد بنجاح",
            f"✅ تم استيراد {len(forms)} استمارة بنجاح\n"
            f"القالب: {template.name}\n\n"
            f"يمكنك الآن عرض النتائج أو تصديرها."
        )
        self.main_window.show_results()

    def _on_import_responses(self):
        """استيراد ملف إجابات رقمية بالاستناد إلى قالب محفوظ"""
        # ─── الخطوة 1: اختيار القالب ──────────────────────────────────────────
        templates = self.db.load_all_templates()
        if not templates:
            QMessageBox.information(
                self, "لا توجد قوالب",
                "لا توجد قوالب محفوظة بعد.\n"
                "يجب استيراد قالب أولاً قبل استيراد ملف الإجابات."
            )
            return

        from views.template_picker_dialog import TemplatePickerDialog
        dialog = TemplatePickerDialog(templates, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        template = dialog.selected_template()
        if template is None:
            return

        # ─── الخطوة 2: اختيار ملف الإجابات ───────────────────────────────────
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف الإجابات الرقمية", "",
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
                f"تم الاستيراد مع {len(warnings)} تحذير:\n\n"
                + "\n".join(f"• {w}" for w in warnings[:10])
                + (f"\n... و{len(warnings) - 10} تحذير آخر" if len(warnings) > 10 else "")
            )
            reply = QMessageBox.warning(
                self, "تحذيرات الاستيراد", msg + "\n\nهل تريد المتابعة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # ─── الخطوة 3: اسم الجلسة ─────────────────────────────────────────────
        name, ok = QInputDialog.getText(
            self, "اسم الجلسة",
            f"تم استيراد {len(forms)} استمارة.\nأدخل اسماً لهذه الجلسة:",
            text=f"جلسة {template.name}"
        )
        if not ok or not name.strip():
            return

        # ─── الخطوة 4: حفظ الجلسة ─────────────────────────────────────────────
        session = Session(
            template_id=template.id,
            name=name.strip(),
            total_forms=len(forms)
        )
        session.forms = forms
        # تصحيح form_index لكل استمارة
        for i, f in enumerate(session.forms):
            f.form_index = i

        self.db.save_session(session)
        self.db.increment_template_use(template.id)

        QMessageBox.information(
            self, "تم الاستيراد",
            f"تم استيراد {len(forms)} استمارة بنجاح.\n"
            f"يمكنك الآن عرض النتائج أو تصديرها."
        )
        self.main_window.show_results()
 
    def _on_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ نسخة احتياطية",
            f"survey_backup_{datetime.now().strftime('%Y%m%d')}.db",
            "قاعدة بيانات (*.db)"
        )
        if not path:
            return
        try:
            self.db.backup_database(path)
            QMessageBox.information(self, "نجاح", f"تم إنشاء النسخة الاحتياطية بنجاح في:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل النسخ الاحتياطي: {str(e)}")
 
    def _on_restore(self):
        reply = QMessageBox.warning(
            self, "تأكيد استعادة البيانات",
            "تحذير: استعادة البيانات سيؤدي إلى استبدال قاعدة البيانات الحالية بالكامل.\n"
            "هل تريد الاستمرار؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
 
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف النسخة الاحتياطية", "",
            "قاعدة بيانات (*.db)"
        )
        if not path:
            return
 
        try:
            self.db.restore_database(path)
            QMessageBox.information(self, "نجاح", "تمت استعادة البيانات بنجاح. سيتم إعادة تحميل الواجهة.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الاستعادة: {str(e)}")
from datetime import datetime
