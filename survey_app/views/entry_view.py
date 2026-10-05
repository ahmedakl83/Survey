from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QLineEdit, QScrollArea,
    QButtonGroup, QCheckBox, QRadioButton, QMessageBox,
    QSizePolicy, QSpacerItem, QListWidget, QListWidgetItem,
    QSplitter, QAbstractItemView, QTextEdit, QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QDate, QTime
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QColor, QDoubleValidator


class QuickNumberInput(QLineEdit):
    """
    حقل إدخال رقم سريع:
    - Enter أو Tab → يؤكد الإجابة فوراً
    - يمنع Tab من الانتقال إلى عنصر آخر
    """
    def __init__(self, on_confirm, parent=None):
        super().__init__(parent)
        self._on_confirm = on_confirm
        self.returnPressed.connect(self._on_confirm)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self._on_confirm()
            event.accept()
        else:
            super().keyPressEvent(event)

class QuickTextEdit(QTextEdit):
    """
    حقل إدخال نص متعدد الأسطر (فقرة):
    - يمنع Tab من ترك مسافات، وبدلاً من ذلك ينتقل للحقل التالي (setTabChangesFocus)
    - Ctrl+Enter أو Ctrl+Return يؤكد الإجابة وينتقل للتالي
    """
    def __init__(self, on_confirm, parent=None):
        super().__init__(parent)
        self._on_confirm = on_confirm
        self.setTabChangesFocus(True)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._on_confirm()
            event.accept()
        else:
            super().keyPressEvent(event)

from database.db_manager import DatabaseManager
from models.session import Session, FormResponse
from models.template import Template
from models.question import Question, QuestionType

class EntryView(QWidget):
    def __init__(self, db: DatabaseManager, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.session: Session = None
        self.template: Template = None
        self.questions: list[Question] = []
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.setInterval(10000)  # 10 ثوان
        self._form_start_time: datetime = None
        self._history: list[int] = []  # تتبع مسار الانتقال الفعلي للأسئلة
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── شريط العنوان ─────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("background-color: #1565C0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        h_layout.setSpacing(12)

        self.session_lbl = QLabel("جلسة التفريغ")
        self.session_lbl.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold;"
        )
        h_layout.addWidget(self.session_lbl)
        h_layout.addStretch()

        self.save_indicator = QLabel("✅ تم الحفظ")
        self.save_indicator.setStyleSheet(
            "color: rgba(255,255,255,0.8); font-size: 12px;"
        )
        h_layout.addWidget(self.save_indicator)

        btn_save = QPushButton("Ctrl+S  حفظ")
        btn_save.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; "
            "padding: 4px 12px;"
        )
        btn_save.clicked.connect(self._manual_save)
        h_layout.addWidget(btn_save)

        btn_finish = QPushButton("Ctrl+Q  إنهاء الاستمارة")
        btn_finish.setStyleSheet(
            "background-color: #2E7D32; color: white; border: none; "
            "border-radius: 6px; padding: 4px 12px; font-weight: bold;"
        )
        btn_finish.clicked.connect(self._finish_form)
        h_layout.addWidget(btn_finish)

        root.addWidget(header)

        # ─── شريط التقدم ──────────────────────────────────────────────────────
        progress_frame = QFrame()
        progress_frame.setFixedHeight(44)
        progress_frame.setStyleSheet("background-color: #E3F2FD; border-bottom: 1px solid #CFD8DC;")
        p_layout = QHBoxLayout(progress_frame)
        p_layout.setContentsMargins(16, 6, 16, 6)
        p_layout.setSpacing(12)

        self.form_lbl = QLabel("الاستمارة 1 من 1")
        self.form_lbl.setStyleSheet("font-weight: bold; color: #1565C0;")
        p_layout.addWidget(self.form_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        p_layout.addWidget(self.progress_bar, 1)

        self.progress_lbl = QLabel("0 / 0")
        self.progress_lbl.setStyleSheet("color: #546E7A; font-size: 12px;")
        p_layout.addWidget(self.progress_lbl)

        root.addWidget(progress_frame)

        # ─── المحتوى الرئيسي ──────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # قائمة الاستمارات (يسار)
        forms_panel = QFrame()
        forms_panel.setFixedWidth(200)
        forms_panel.setStyleSheet(
            "background-color: white; border-left: 1px solid #CFD8DC;"
        )
        forms_layout = QVBoxLayout(forms_panel)
        forms_layout.setContentsMargins(8, 8, 8, 8)
        forms_layout.setSpacing(4)

        forms_title = QLabel("الاستمارات")
        forms_title.setStyleSheet("font-weight: bold; color: #1565C0; font-size: 13px;")
        forms_layout.addWidget(forms_title)

        self.forms_list = QListWidget()
        self.forms_list.setStyleSheet(
            "QListWidget::item { padding: 6px 8px; border-radius: 4px; }"
            "QListWidget::item:selected { background-color: #1565C0; color: white; }"
        )
        self.forms_list.itemClicked.connect(self._on_form_selected)
        forms_layout.addWidget(self.forms_list)

        splitter.addWidget(forms_panel)

        # منطقة الإدخال (يمين)
        entry_scroll = QScrollArea()
        entry_scroll.setWidgetResizable(True)
        entry_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.entry_widget = QWidget()
        self.entry_layout = QVBoxLayout(self.entry_widget)
        self.entry_layout.setContentsMargins(32, 24, 32, 24)
        self.entry_layout.setSpacing(20)
        entry_scroll.setWidget(self.entry_widget)

        splitter.addWidget(entry_scroll)
        splitter.setSizes([200, 800])

        root.addWidget(splitter, 1)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._manual_save)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self._finish_form)
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self._undo_last)

    def load_session(self, session: Session, template: Template):
        self.session = session
        self.template = template
        self.questions = sorted(template.questions, key=lambda q: q.column_index)
        self.session_lbl.setText(f"جلسة: {session.name}")

        self._populate_forms_list()
        self._load_form(session.current_form_index)
        self._autosave_timer.start()

    def _populate_forms_list(self):
        self.forms_list.clear()
        for i in range(self.session.total_forms):
            form = self.session.forms[i] if i < len(self.session.forms) else None
            is_complete = form.is_complete if form else False
            item = QListWidgetItem(
                f"{'✅' if is_complete else '○'}  استمارة {i + 1}"
            )
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.forms_list.addItem(item)

        # تحديد الاستمارة الحالية
        self.forms_list.setCurrentRow(self.session.current_form_index)

    def _rebuild_history(self):
        """إعادة بناء مسار التاريخ عند فتح استمارة تم تفريغ جزء منها سابقاً"""
        self._history = []
        form = self.session.get_current_form()
        if not form:
            return
            
        current_idx = 0
        target_idx = self.session.current_question_index
        
        while current_idx < target_idx and current_idx < len(self.questions):
            q = self.questions[current_idx]
            ans = form.answers.get(q.id, "")
            
            self._history.append(current_idx)
            
            next_idx = None
            if hasattr(q, "branching_rules") and q.branching_rules and ans.strip() in q.branching_rules:
                target = q.branching_rules[ans.strip()]
                next_idx = target.column_index if isinstance(target, Question) else target
                
            if next_idx is not None:
                current_idx = next_idx
            else:
                current_idx += 1

    def _load_form(self, form_index: int):
        if form_index >= self.session.total_forms:
            self._show_completion()
            return

        self.session.current_form_index = form_index
        form = self.session.forms[form_index]

        if form.started_at is None:
            form.started_at = datetime.now()
        self._form_start_time = form.started_at

        # إعادة بناء التاريخ للاستمارة
        self._rebuild_history()

        # تحديث شريط التقدم
        answered = len([v for v in form.answers.values() if v != ""])
        total = len(self.questions)
        self.form_lbl.setText(
            f"الاستمارة {form_index + 1} من {self.session.total_forms}"
        )
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(answered)
        self.progress_lbl.setText(f"{answered} / {total}")

        # عرض السؤال الحالي
        q_idx = self.session.current_question_index
        if q_idx >= len(self.questions):
            q_idx = 0
            self.session.current_question_index = 0

        self._render_question(q_idx)

    def _render_question(self, q_idx: int):
        # مسح المحتوى السابق
        while self.entry_layout.count():
            item = self.entry_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if q_idx >= len(self.questions):
            self._show_form_done()
            return

        self.session.current_question_index = q_idx
        q = self.questions[q_idx]
        form = self.session.get_current_form()
        current_answer = form.answers.get(q.id, "") if form else ""

        # ─── رقم السؤال ───────────────────────────────────────────────────────
        nav_row = QHBoxLayout()
        btn_prev = QPushButton("→ السابق")
        btn_prev.setObjectName("btn_secondary")
        btn_prev.setEnabled(len(self._history) > 0)
        btn_prev.clicked.connect(self._go_to_prev_question)
        nav_row.addWidget(btn_prev)

        q_counter = QLabel(f"السؤال {q_idx + 1} من {len(self.questions)}")
        q_counter.setStyleSheet("color: #546E7A; font-size: 12px;")
        q_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_row.addWidget(q_counter, 1)

        btn_next = QPushButton("التالي ←")
        btn_next.setObjectName("btn_secondary")
        btn_next.setEnabled(q_idx < len(self.questions) - 1)
        btn_next.clicked.connect(lambda: self._go_to_next_question(q_idx))
        nav_row.addWidget(btn_next)

        nav_widget = QWidget()
        nav_widget.setLayout(nav_row)
        self.entry_layout.addWidget(nav_widget)

        # ─── بطاقة السؤال ─────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: white; border-radius: 12px; "
            "border: 1.5px solid #CFD8DC; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(16)

        # نوع السؤال
        type_badge = QLabel(q.get_type_label())
        badge_colors = {
            QuestionType.GENERAL: "#546E7A",
            QuestionType.DEMOGRAPHIC_SINGLE: "#2E7D32",
            QuestionType.DEMOGRAPHIC_MULTIPLE: "#1565C0",
            QuestionType.LIKERT: "#E65100",
            QuestionType.DEMOGRAPHIC_SINGLE_OTHER: "#2E7D32",
        }
        color = badge_colors.get(q.question_type, "#546E7A")
        type_badge.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: 4px; "
            f"padding: 2px 10px; font-size: 11px; font-weight: bold; "
            f"border: none; max-width: 140px;"
        )
        card_layout.addWidget(type_badge)

        # نص السؤال
        q_text = QLabel(q.text)
        q_text.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1a1a2e; border: none;"
        )
        q_text.setWordWrap(True)
        card_layout.addWidget(q_text)

        # ─── منطقة الإدخال ────────────────────────────────────────────────────
        if q.question_type == QuestionType.GENERAL:
            self._render_general_input(card_layout, q, current_answer, q_idx)
        elif q.question_type == QuestionType.DEMOGRAPHIC_MULTIPLE:
            self._render_multiple_input(card_layout, q, current_answer, q_idx)
        elif q.question_type == QuestionType.DEMOGRAPHIC_SINGLE_OTHER:
            self._render_single_other_input(card_layout, q, current_answer, q_idx)
        else:
            # DEMOGRAPHIC_SINGLE أو LIKERT
            self._render_single_input(card_layout, q, current_answer, q_idx)

        self.entry_layout.addWidget(card)
        self.entry_layout.addStretch()

    def _render_general_input(self, layout, q: Question, current: str, q_idx: int):
        subtype = q.answers[0] if q.answers else "text"
        
        if subtype == "paragraph":
            lbl = QLabel("أدخل الفقرة (اضغط Ctrl+Enter للحفظ أو Tab للتنقل):")
            lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
            layout.addWidget(lbl)
            
            self._text_field = QuickTextEdit(
                on_confirm=lambda: self._confirm_answer(q, self._text_field.toPlainText(), q_idx)
            )
            self._text_field.setPlainText(current)
            self._text_field.setPlaceholderText("اكتب الفقرة هنا...")
            self._text_field.setStyleSheet("font-size: 15px; padding: 10px;")
            self._text_field.setFixedHeight(120)
            layout.addWidget(self._text_field)
            
            btn_confirm = QPushButton("✔  تأكيد والتالي")
            btn_confirm.setStyleSheet(
                "background-color: #1565C0; color: white; font-size: 13px; "
                "font-weight: bold; padding: 8px 16px; border-radius: 6px;"
            )
            btn_confirm.clicked.connect(
                lambda: self._confirm_answer(q, self._text_field.toPlainText(), q_idx)
            )
            layout.addWidget(btn_confirm)
            
            QTimer.singleShot(0, self._text_field.setFocus)
            
        elif subtype == "number":
            lbl = QLabel("أدخل الرقم (Enter أو Tab للتالي):")
            lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
            layout.addWidget(lbl)
            
            self._input_field = QuickNumberInput(
                on_confirm=lambda: self._confirm_answer(q, self._input_field.text(), q_idx)
            )
            self._input_field.setValidator(QDoubleValidator())
            self._input_field.setText(current)
            self._input_field.setPlaceholderText("أدخل أرقاماً فقط...")
            self._input_field.setStyleSheet("font-size: 15px; padding: 10px;")
            layout.addWidget(self._input_field)
            
            QTimer.singleShot(0, self._input_field.setFocus)
            
        elif subtype == "date":
            lbl = QLabel("اختر التاريخ (اضغط Enter للتأكيد أو Tab للتنقل):")
            lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
            layout.addWidget(lbl)
            
            self._date_field = QDateEdit()
            self._date_field.setCalendarPopup(True)
            self._date_field.setDisplayFormat("yyyy-MM-dd")
            self._date_field.setStyleSheet("font-size: 15px; padding: 8px;")
            
            if current:
                self._date_field.setDate(QDate.fromString(current, "yyyy-MM-dd"))
            else:
                self._date_field.setDate(QDate.currentDate())
                
            layout.addWidget(self._date_field)
            
            btn_confirm = QPushButton("✔  تأكيد والتالي")
            btn_confirm.setStyleSheet(
                "background-color: #1565C0; color: white; font-size: 13px; "
                "font-weight: bold; padding: 8px 16px; border-radius: 6px;"
            )
            confirm_fn = lambda: self._confirm_answer(q, self._date_field.date().toString("yyyy-MM-dd"), q_idx)
            btn_confirm.clicked.connect(confirm_fn)
            self._date_field.lineEdit().returnPressed.connect(confirm_fn)
            layout.addWidget(btn_confirm)
            
            QTimer.singleShot(0, self._date_field.setFocus)
            
        elif subtype == "time":
            lbl = QLabel("اختر الوقت (اضغط Enter للتأكيد أو Tab للتنقل):")
            lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
            layout.addWidget(lbl)
            
            self._time_field = QTimeEdit()
            self._time_field.setDisplayFormat("HH:mm")
            self._time_field.setStyleSheet("font-size: 15px; padding: 8px;")
            
            if current:
                self._time_field.setTime(QTime.fromString(current, "HH:mm"))
            else:
                self._time_field.setTime(QTime.currentTime())
                
            layout.addWidget(self._time_field)
            
            btn_confirm = QPushButton("✔  تأكيد والتالي")
            btn_confirm.setStyleSheet(
                "background-color: #1565C0; color: white; font-size: 13px; "
                "font-weight: bold; padding: 8px 16px; border-radius: 6px;"
            )
            confirm_fn = lambda: self._confirm_answer(q, self._time_field.time().toString("HH:mm"), q_idx)
            btn_confirm.clicked.connect(confirm_fn)
            self._time_field.lineEdit().returnPressed.connect(confirm_fn)
            layout.addWidget(btn_confirm)
            
            QTimer.singleShot(0, self._time_field.setFocus)
            
        else: # text (نص حر)
            lbl = QLabel("أدخل الإجابة  (Enter أو Tab للتالي):")
            lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
            layout.addWidget(lbl)

            self._input_field = QuickNumberInput(
                on_confirm=lambda: self._confirm_answer(q, self._input_field.text(), q_idx)
            )
            self._input_field.setText(current)
            self._input_field.setPlaceholderText("اكتب الإجابة هنا...")
            self._input_field.setStyleSheet("font-size: 15px; padding: 10px;")
            layout.addWidget(self._input_field)

            QTimer.singleShot(0, self._input_field.setFocus)

    def _render_single_input(self, layout, q: Question, current: str, q_idx: int):
        """
        ديموغرافي-واحدة أو ليكرت:
        - حقل رقم كبير في الأعلى يأخذ التركيز فوراً
        - Enter أو Tab يؤكد ويتقدم
        - النقر على الخيار يؤكد فوراً أيضاً
        """
        # ─── حقل الرقم السريع (في الأعلى وبارز) ─────────────────────────────
        num_frame = QFrame()
        num_frame.setStyleSheet(
            "QFrame { background-color: #F0F7FF; border-radius: 8px; "
            "border: 1.5px solid #90CAF9; }"
        )
        num_layout = QHBoxLayout(num_frame)
        num_layout.setContentsMargins(16, 12, 16, 12)
        num_layout.setSpacing(12)

        num_hint = QLabel(f"اكتب رقم الإجابة (1–{len(q.answers)}):")
        num_hint.setStyleSheet("color: #1565C0; font-size: 13px; font-weight: bold; border: none;")
        num_layout.addWidget(num_hint)

        self._num_input = QuickNumberInput(
            on_confirm=lambda: self._confirm_by_number(q, self._num_input.text(), q_idx)
        )
        self._num_input.setPlaceholderText("رقم...")
        self._num_input.setFixedWidth(90)
        self._num_input.setStyleSheet(
            "font-size: 20px; font-weight: bold; padding: 6px 10px; "
            "border: 2px solid #1565C0; border-radius: 6px; "
            "background: white; color: #1565C0;"
        )
        num_layout.addWidget(self._num_input)

        enter_hint = QLabel("Enter / Tab")
        enter_hint.setStyleSheet(
            "color: #90A4AE; font-size: 11px; border: none;"
        )
        num_layout.addWidget(enter_hint)
        num_layout.addStretch()

        layout.addWidget(num_frame)

        # ─── قائمة الخيارات (للنقر) ───────────────────────────────────────────
        sep = QLabel("أو انقر على الإجابة مباشرة:")
        sep.setStyleSheet("color: #90A4AE; font-size: 11px; border: none; margin-top: 4px;")
        layout.addWidget(sep)

        self._radio_group = QButtonGroup(self)
        self._radio_group.setExclusive(True)

        for i, ans in enumerate(q.answers, start=1):
            btn = QPushButton(f"{i}.  {ans}")
            btn.setCheckable(True)
            btn.setChecked(ans == current)
            btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            btn.setStyleSheet(
                "QPushButton { padding: 8px 14px; "
                "background-color: #FAFAFA; border: 1px solid #E0E0E0; "
                "border-radius: 6px; font-size: 13px; color: #1a1a2e; }"
                "QPushButton:hover { background-color: #E3F2FD; border-color: #90CAF9; }"
                "QPushButton:checked { background-color: #1565C0; color: white; "
                "border-color: #1565C0; font-weight: bold; }"
            )
            btn.clicked.connect(
                lambda checked, a=ans: self._confirm_answer(q, a, q_idx)
            )
            self._radio_group.addButton(btn, i)
            layout.addWidget(btn)

        # التركيز على حقل الرقم فوراً
        QTimer.singleShot(0, self._num_input.setFocus)

    def _render_multiple_input(self, layout, q: Question, current: str, q_idx: int):
        hint = QLabel("اختر إجابة أو أكثر، ثم اضغط زر التأكيد:")
        hint.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
        layout.addWidget(hint)

        selected = set(current.split(",")) if current else set()
        self._checkboxes = []

        for i, ans in enumerate(q.answers, start=1):
            cb = QCheckBox(f"{i}.  {ans}")
            cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            cb.setStyleSheet("font-size: 14px; border: none; padding: 4px;")
            cb.setChecked(ans in selected)
            self._checkboxes.append((cb, ans))
            layout.addWidget(cb)

        # حقل الأرقام السريع
        num_row = QHBoxLayout()
        num_lbl = QLabel("أو اكتب الأرقام مفصولة بفواصل:")
        num_lbl.setStyleSheet("color: #546E7A; font-size: 12px; border: none;")
        num_row.addWidget(num_lbl)

        self._multi_num_input = QLineEdit()
        self._multi_num_input.setPlaceholderText("مثال: 1,3")
        self._multi_num_input.setFixedWidth(120)
        self._multi_num_input.textChanged.connect(
            lambda text: self._sync_checkboxes_from_text(text, q)
        )
        num_row.addWidget(self._multi_num_input)
        num_row.addStretch()
        layout.addLayout(num_row)

        # زر التأكيد إلزامي للمتعددة
        btn_confirm = QPushButton("✔  تأكيد والتالي")
        btn_confirm.setStyleSheet(
            "background-color: #1565C0; color: white; font-size: 14px; "
            "font-weight: bold; padding: 10px; border-radius: 6px; margin-top: 8px;"
        )
        btn_confirm.clicked.connect(lambda: self._confirm_multiple(q, q_idx))
        layout.addWidget(btn_confirm)

        QTimer.singleShot(0, self._multi_num_input.setFocus)

    def _sync_checkboxes_from_text(self, text: str, q: Question):
        """تحديث الـ checkboxes تلقائياً عند الكتابة في حقل الأرقام"""
        try:
            nums = {int(n.strip()) for n in text.split(",") if n.strip().isdigit()}
            for i, (cb, ans) in enumerate(self._checkboxes, start=1):
                cb.setChecked(i in nums)
        except Exception:
            pass

    def _render_single_other_input(self, layout, q: Question, current: str, q_idx: int):
        if not q.answers:
            q.answers = ["خيار 1", "أخرى"]

        num_frame = QFrame()
        num_frame.setStyleSheet(
            "QFrame { background-color: #F0F7FF; border-radius: 8px; border: 1.5px solid #90CAF9; }"
        )
        num_layout = QHBoxLayout(num_frame)
        num_layout.setContentsMargins(16, 12, 16, 12)
        num_layout.setSpacing(12)

        num_hint = QLabel(f"اكتب رقم الإجابة (1–{len(q.answers)}):")
        num_hint.setStyleSheet("color: #1565C0; font-size: 13px; font-weight: bold; border: none;")
        num_layout.addWidget(num_hint)

        self._num_input = QuickNumberInput(
            on_confirm=lambda: self._confirm_by_number_other(q, self._num_input.text(), q_idx)
        )
        self._num_input.setPlaceholderText("رقم...")
        self._num_input.setFixedWidth(90)
        self._num_input.setStyleSheet(
            "font-size: 20px; font-weight: bold; padding: 6px 10px; "
            "border: 2px solid #1565C0; border-radius: 6px; background: white; color: #1565C0;"
        )
        num_layout.addWidget(self._num_input)

        enter_hint = QLabel("Enter / Tab")
        enter_hint.setStyleSheet("color: #90A4AE; font-size: 11px; border: none;")
        num_layout.addWidget(enter_hint)
        num_layout.addStretch()
        layout.addWidget(num_frame)

        sep = QLabel("أو انقر على الإجابة مباشرة:")
        sep.setStyleSheet("color: #90A4AE; font-size: 11px; border: none; margin-top: 4px;")
        layout.addWidget(sep)

        self._radio_group = QButtonGroup(self)
        self._radio_group.setExclusive(True)
        
        self._other_text_input = QLineEdit()
        self._other_text_input.setPlaceholderText("اكتب الإجابة الحرة هنا...")
        self._other_text_input.setStyleSheet(
            "QLineEdit { font-size: 14px; padding: 6px 10px; border: 1.5px solid #1565C0; border-radius: 6px; background: white; color: #1a1a2e; }"
            "QLineEdit:disabled { background: #F5F5F5; border-color: #CFD8DC; color: #9E9E9E; }"
        )
        self._other_text_input.setEnabled(False)
        self._other_text_input.returnPressed.connect(lambda: self._confirm_other_text(q, q_idx))
        
        is_other_selected = False
        if current:
            if current in q.answers[:-1]:
                is_other_selected = False
            else:
                is_other_selected = True

        for i, ans in enumerate(q.answers, start=1):
            is_last = (i == len(q.answers))
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(10)
            
            btn = QRadioButton(f"{i}.  {ans}")
            btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            btn.setStyleSheet(
                "QRadioButton { font-size: 14px; padding: 6px; }"
                "QRadioButton:checked { font-weight: bold; color: #1565C0; }"
            )
            
            if is_last:
                btn.setChecked(is_other_selected)
                btn.toggled.connect(self._other_text_input.setEnabled)
                if is_other_selected:
                    self._other_text_input.setText(current if current != ans else "")
                    self._other_text_input.setEnabled(True)
                
                btn_layout.addWidget(btn)
                btn_layout.addWidget(self._other_text_input, 1)
                
                btn.clicked.connect(lambda checked, b=btn: self._on_other_radio_clicked(b))
            else:
                btn.setChecked(current == ans)
                btn_layout.addWidget(btn)
                btn_layout.addStretch()
                btn.clicked.connect(lambda checked, a=ans: self._confirm_answer(q, a, q_idx))

            self._radio_group.addButton(btn, i)
            row_widget = QWidget()
            row_widget.setLayout(btn_layout)
            layout.addWidget(row_widget)
            
        btn_confirm = QPushButton("✔  تأكيد الإجابة والتالي")
        btn_confirm.setStyleSheet(
            "background-color: #1565C0; color: white; font-size: 13px; "
            "font-weight: bold; padding: 8px 16px; border-radius: 6px; margin-top: 8px;"
        )
        btn_confirm.clicked.connect(lambda: self._confirm_other_text(q, q_idx))
        layout.addWidget(btn_confirm)

        if is_other_selected and current:
            QTimer.singleShot(0, self._other_text_input.setFocus)
        else:
            QTimer.singleShot(0, self._num_input.setFocus)
        
    def _on_other_radio_clicked(self, btn):
        btn.setChecked(True)
        self._other_text_input.setEnabled(True)
        self._other_text_input.setFocus()
        self._other_text_input.selectAll()
        
    def _confirm_other_text(self, q: Question, q_idx: int):
        btn = self._radio_group.checkedButton()
        btn_id = self._radio_group.id(btn) if btn else len(q.answers)
        
        if btn_id == len(q.answers):
            text = self._other_text_input.text().strip()
            if not text:
                text = q.answers[-1] if q.answers else "أخرى"
            self._confirm_answer(q, text, q_idx)
        elif 1 <= btn_id <= len(q.answers):
            self._confirm_answer(q, q.answers[btn_id - 1], q_idx)
            
    def _confirm_by_number_other(self, q: Question, num_text: str, q_idx: int):
        try:
            num = int(num_text.strip())
            if 1 <= num <= len(q.answers):
                btn = self._radio_group.button(num)
                if btn:
                    btn.setChecked(True)
                if num == len(q.answers):
                    self._other_text_input.setEnabled(True)
                    self._other_text_input.setFocus()
                    self._other_text_input.selectAll()
                else:
                    self._confirm_answer(q, q.answers[num - 1], q_idx)
            else:
                self._num_input.setStyleSheet(
                    "font-size: 20px; font-weight: bold; padding: 6px 10px; "
                    "border: 2px solid #C62828; border-radius: 6px; "
                    "background: #FFEBEE; color: #C62828;"
                )
                QTimer.singleShot(600, self._reset_num_input_style)
        except ValueError:
            pass

    # ─── منطق الإجابات ────────────────────────────────────────────────────────

    def _confirm_answer(self, q: Question, answer: str, q_idx: int):
        form = self.session.get_current_form()
        if form is None:
            return
        form.answers[q.id] = answer.strip()
        
        # تسجيل مؤشر السؤال الحالي في تاريخ التنقل
        if not self._history or self._history[-1] != q_idx:
            self._history.append(q_idx)
            
        # التحقق من وجود تفريع مشروط للإجابة
        next_idx = None
        clean_ans = answer.strip()
        if hasattr(q, "branching_rules") and q.branching_rules and clean_ans in q.branching_rules:
            target = q.branching_rules[clean_ans]
            next_idx = target.column_index if isinstance(target, Question) else target

        if next_idx is not None:
            self._go_to_question(next_idx)
        else:
            self._go_to_question(q_idx + 1)

    def _confirm_by_number(self, q: Question, num_text: str, q_idx: int):
        try:
            num = int(num_text.strip())
            if 1 <= num <= len(q.answers):
                # تمييز الخيار المحدد بصرياً قبل الانتقال
                btn = self._radio_group.button(num)
                if btn:
                    btn.setChecked(True)
                self._confirm_answer(q, q.answers[num - 1], q_idx)
            else:
                # رقم خارج النطاق - تلوين أحمر مؤقت
                self._num_input.setStyleSheet(
                    "font-size: 20px; font-weight: bold; padding: 6px 10px; "
                    "border: 2px solid #C62828; border-radius: 6px; "
                    "background: #FFEBEE; color: #C62828;"
                )
                QTimer.singleShot(600, self._reset_num_input_style)
        except ValueError:
            pass

    def _reset_num_input_style(self):
        if hasattr(self, '_num_input'):
            self._num_input.setStyleSheet(
                "font-size: 20px; font-weight: bold; padding: 6px 10px; "
                "border: 2px solid #1565C0; border-radius: 6px; "
                "background: white; color: #1565C0;"
            )
            self._num_input.clear()
            self._num_input.setFocus()

    def _confirm_multiple(self, q: Question, q_idx: int):
        selected = [ans for cb, ans in self._checkboxes if cb.isChecked()]
        self._confirm_answer(q, ",".join(selected), q_idx)

    def _confirm_multiple_by_number(self, q: Question, q_idx: int):
        text = self._multi_num_input.text().strip()
        try:
            nums = [int(n.strip()) for n in text.split(",") if n.strip()]
            selected = []
            for n in nums:
                if 1 <= n <= len(q.answers):
                    selected.append(q.answers[n - 1])
            if selected:
                self._confirm_answer(q, ",".join(selected), q_idx)
        except ValueError:
            pass

    def _go_to_question(self, q_idx: int):
        if q_idx < 0:
            return
        if q_idx >= len(self.questions):
            self._show_form_done()
            return
        self._update_progress()
        self._render_question(q_idx)

    def _update_progress(self):
        form = self.session.get_current_form()
        if not form:
            return
        answered = len([v for v in form.answers.values() if v != ""])
        total = len(self.questions)
        self.progress_bar.setValue(answered)
        self.progress_lbl.setText(f"{answered} / {total}")

    def _show_form_done(self):
        """عرض رسالة اكتمال الاستمارة"""
        while self.entry_layout.count():
            item = self.entry_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        done_card = QFrame()
        done_card.setStyleSheet(
            "QFrame { background-color: #E8F5E9; border-radius: 12px; "
            "border: 2px solid #2E7D32; }"
        )
        done_layout = QVBoxLayout(done_card)
        done_layout.setContentsMargins(32, 32, 32, 32)
        done_layout.setSpacing(16)
        done_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("✅")
        icon.setStyleSheet("font-size: 48px; border: none;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        done_layout.addWidget(icon)

        msg = QLabel("تم الانتهاء من جميع أسئلة هذه الاستمارة!")
        msg.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E7D32; border: none;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        done_layout.addWidget(msg)

        btn_next_form = QPushButton("الانتقال للاستمارة التالية  →")
        btn_next_form.clicked.connect(self._finish_form)
        done_layout.addWidget(btn_next_form)

        self.entry_layout.addStretch()
        self.entry_layout.addWidget(done_card)
        self.entry_layout.addStretch()

    def _show_completion(self):
        """عرض رسالة اكتمال جميع الاستمارات"""
        while self.entry_layout.count():
            item = self.entry_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: #E3F2FD; border-radius: 12px; "
            "border: 2px solid #1565C0; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("🎉")
        icon.setStyleSheet("font-size: 56px; border: none;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon)

        msg = QLabel("تم الانتهاء من جميع الاستمارات!")
        msg.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1565C0; border: none;"
        )
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(msg)

        stats = QLabel(
            f"إجمالي الاستمارات: {self.session.total_forms}\n"
            f"مكتملة: {self.session.completed_forms}"
        )
        stats.setStyleSheet("color: #546E7A; font-size: 13px; border: none;")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(stats)

        btn_export = QPushButton("تصدير النتائج إلى Excel")
        btn_export.setObjectName("btn_success")
        btn_export.clicked.connect(self._go_to_results)
        card_layout.addWidget(btn_export)

        self.entry_layout.addStretch()
        self.entry_layout.addWidget(card)
        self.entry_layout.addStretch()

    # ─── إجراءات ──────────────────────────────────────────────────────────────

    def _finish_form(self):
        form = self.session.get_current_form()
        if form:
            form.is_complete = True
            form.completed_at = datetime.now()
            if self._form_start_time:
                delta = datetime.now() - self._form_start_time
                form.duration_seconds = int(delta.total_seconds())

        self._manual_save()
        self._populate_forms_list()

        next_idx = self.session.current_form_index + 1
        self.session.current_question_index = 0
        self._load_form(next_idx)

    def _manual_save(self):
        if not self.session:
            return
        self.save_indicator.setText("⏳ جاري الحفظ...")
        self.main_window.set_save_status("saving")
        try:
            self.db.update_session(self.session)
            self.save_indicator.setText("✅ تم الحفظ")
            self.main_window.set_save_status("saved")
        except Exception as e:
            self.save_indicator.setText("❌ خطأ في الحفظ")
            self.main_window.set_save_status("error")

    def _autosave(self):
        if self.session:
            try:
                self.db.update_session(self.session)
                self.save_indicator.setText("✅ تم الحفظ تلقائياً")
            except Exception:
                self.save_indicator.setText("❌ خطأ في الحفظ")

    def _go_to_prev_question(self):
        """العودة للسؤال السابق بناء على التاريخ الفعلي"""
        if self._history:
            prev_idx = self._history.pop()
            self._go_to_question(prev_idx)

    def _go_to_next_question(self, q_idx: int):
        """الانتقال للسؤال التالي يدوياً (تخطي) مع تسجيل التاريخ"""
        if not self._history or self._history[-1] != q_idx:
            self._history.append(q_idx)
        self._go_to_question(q_idx + 1)

    def _undo_last(self):
        form = self.session.get_current_form()
        if not form or not form.answers:
            return
        if self._history:
            # سحب آخر سؤال تمت الإجابة عليه من التاريخ
            prev_idx = self._history[-1]  # لا نعمل pop هنا، دالة _go_to_prev_question ستعمل pop له
            prev_q = self.questions[prev_idx]
            form.answers.pop(prev_q.id, None)
            self._go_to_prev_question()

    def _on_form_selected(self, item: QListWidgetItem):
        form_idx = item.data(Qt.ItemDataRole.UserRole)
        self.session.current_question_index = 0
        self._load_form(form_idx)

    def _go_to_results(self):
        self._autosave_timer.stop()
        self.main_window.show_results()
