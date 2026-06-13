from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QInputDialog, QMessageBox, QDialog,
    QDialogButtonBox, QListWidget, QListWidgetItem, QAbstractItemView,
    QSplitter, QTextEdit, QScrollArea, QStackedWidget, QFileDialog,
    QApplication, QSpinBox
)
from PyQt6.QtCore import Qt, QSize, QEvent, QMimeData
from PyQt6.QtGui import QColor, QDrag

from database.db_manager import DatabaseManager
from models.template import Template, LikertScale
from models.question import Question, QuestionType
from models.session import Session


class DragHandle(QLabel):
    def __init__(self, q_idx, answer_text, parent=None):
        super().__init__(parent)
        self.q_idx = q_idx
        self.answer_text = answer_text
        self.setText("🔗")
        self.setToolTip("اسحب هذا الرمز وأفلته على السؤال المراد التفريع إليه")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet("font-size: 14px; padding: 2px; color: #1565C0; background: transparent; border: none;")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        try:
            drag = QDrag(self)
            mime_data = QMimeData()
            # تخزين رقم السؤال والنص
            mime_data.setData("application/x-survey-branch", f"{self.q_idx}:{self.answer_text}".encode('utf-8'))
            drag.setMimeData(mime_data)
            
            # صورة تعبيرية أثناء السحب
            pixmap = self.parent().grab() if self.parent() else self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            drag.exec(Qt.DropAction.LinkAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        except Exception as e:
            print(f"Error during drag and drop operation: {e}")


class AnswersCellWidget(QWidget):
    def __init__(self, row_idx, q, edit_callback, delete_branch_callback, scale_picker_widget=None, parent=None):
        super().__init__(parent)
        self.row_idx = row_idx
        self.q = q
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        if scale_picker_widget:
            main_layout.addWidget(scale_picker_widget)
            
        # قائمة الإجابات
        ans_container = QWidget()
        ans_layout = QHBoxLayout(ans_container)
        ans_layout.setContentsMargins(0, 0, 0, 0)
        ans_layout.setSpacing(8)
        
        # زر التعديل إذا لم يكن هناك scale picker
        if not scale_picker_widget:
            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(24, 24)
            edit_btn.clicked.connect(edit_callback)
            edit_btn.setToolTip("تعديل الإجابات المخصصة")
            edit_btn.setStyleSheet("font-size: 11px; padding: 0;")
            ans_layout.addWidget(edit_btn)
            
        if q.answers:
            for ans in q.answers:
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(4, 2, 4, 2)
                item_layout.setSpacing(4)
                
                # تلوين حسب نوع السؤال
                bg_color = "#FFF9C4" if q.question_type == QuestionType.LIKERT else "#E8F5E9" if q.question_type == QuestionType.DEMOGRAPHIC_SINGLE else "#E3F2FD"
                border_color = "#FFE082" if q.question_type == QuestionType.LIKERT else "#C8E6C9" if q.question_type == QuestionType.DEMOGRAPHIC_SINGLE else "#BBDEFB"
                item_widget.setStyleSheet(
                    f"background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px;"
                )
                
                # مقبض السحب (فقط لأسئلة الاختيار الواحد)
                is_single_choice = q.is_single_choice
                if is_single_choice:
                    handle = DragHandle(self.row_idx, ans, self)
                    item_layout.addWidget(handle)
                
                # نص الإجابة
                lbl_text = QLabel(ans)
                lbl_text.setStyleSheet("font-size: 11px; color: #263238; border: none; background: transparent;")
                item_layout.addWidget(lbl_text)
                
                # وسام التفريع المشروط إن وجد
                if hasattr(q, "branching_rules") and ans in q.branching_rules:
                    target = q.branching_rules[ans]
                    target_num = target.column_index + 1 if isinstance(target, Question) else target + 1
                    
                    badge = QLabel(f"➔ س{target_num}")
                    badge.setStyleSheet(
                        "background-color: #E65100; color: white; border-radius: 3px; "
                        "padding: 1px 4px; font-size: 10px; font-weight: bold; border: none;"
                    )
                    item_layout.addWidget(badge)
                    
                    del_btn = QPushButton("×")
                    del_btn.setFixedSize(14, 14)
                    del_btn.setStyleSheet(
                        "background: transparent; color: #D32F2F; font-weight: bold; "
                        "font-size: 11px; border: none; padding: 0;"
                    )
                    del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    del_btn.setToolTip("حذف التفريع")
                    del_btn.clicked.connect(lambda checked, a=ans: delete_branch_callback(self.row_idx, a))
                    item_layout.addWidget(del_btn)
                    
                ans_layout.addWidget(item_widget)
        else:
            lbl_empty = QLabel("—")
            lbl_empty.setStyleSheet("color: #90A4AE; font-size: 12px; border: none;")
            ans_layout.addWidget(lbl_empty)
            
        ans_layout.addStretch()
        main_layout.addWidget(ans_container)


class ReviewView(QWidget):
    def __init__(self, db: DatabaseManager, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.template: Template = None
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

        self.title_lbl = QLabel("مراجعة الأسئلة")
        self.title_lbl.setStyleSheet(
            "color: white; font-size: 17px; font-weight: bold;"
        )
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()

        btn_save = QPushButton("حفظ التعديلات")
        btn_save.clicked.connect(self._save_changes)
        h_layout.addWidget(btn_save)

        btn_start = QPushButton("▶  بدء التفريغ")
        btn_start.setObjectName("btn_success")
        btn_start.clicked.connect(self._start_entry)
        h_layout.addWidget(btn_start)
 
        btn_import = QPushButton("📥 استيراد إجابات رقمية")
        btn_import.setObjectName("btn_secondary")
        btn_import.clicked.connect(self._import_responses)
        h_layout.addWidget(btn_import)

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 16)
        content_layout.setSpacing(12)

        # معلومات القالب
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet("color: #546E7A; font-size: 12px;")
        content_layout.addWidget(self.info_lbl)

        # جدول الأسئلة
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "نص السؤال", "النوع", "الإجابات"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 180)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        
        # تفعيل السحب والإفلات لإنشاء تفريعات مشروطة
        self.table.setAcceptDrops(True)
        self.table.viewport().setAcceptDrops(True)
        self.table.viewport().installEventFilter(self)
        
        content_layout.addWidget(self.table)

        # أزرار إضافية
        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ إضافة سؤال")
        btn_add.setObjectName("btn_secondary")
        btn_add.clicked.connect(self._add_question)
        btn_row.addWidget(btn_add)

        btn_dup = QPushButton("📋 نسخ السؤال")
        btn_dup.setObjectName("btn_secondary")
        btn_dup.clicked.connect(self._duplicate_selected)
        btn_row.addWidget(btn_dup)

        btn_del = QPushButton("حذف المحدد")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._delete_selected)
        btn_row.addWidget(btn_del)

        btn_likert = QPushButton("📋 إدارة مقاييس ليكرت")
        btn_likert.setObjectName("btn_secondary")
        btn_likert.clicked.connect(self._manage_likert_scales)
        btn_row.addWidget(btn_likert)

        btn_row.addStretch()
        content_layout.addLayout(btn_row)

        root.addWidget(content)

    def keyPressEvent(self, event):
        # الاستجابة لمفتاح (+) أو Shift + (=)
        is_plus = (event.key() == Qt.Key.Key_Plus) or \
                  (event.key() == Qt.Key.Key_Equal and event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        
        if is_plus:
            focus_widget = self.focusWidget()
            if focus_widget:
                from PyQt6.QtWidgets import QLineEdit, QTextEdit
                if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                    super().keyPressEvent(event)
                    return
            self._add_question()
            event.accept()
        else:
            super().keyPressEvent(event)

    def load_template(self, template: Template):
        self.template = template
        self.title_lbl.setText(f"مراجعة الأسئلة — {template.name}")
        self.info_lbl.setText(
            f"عدد الأسئلة: {len(template.questions)}  |  "
            f"مقاييس ليكرت: {len(template.likert_scales)}"
        )
        self._populate_table()

    def _clean_and_sync_questions(self):
        # 1. تحديث الفهارس لتطابق الترتيب الحالي في القائمة
        for i, q in enumerate(self.template.questions):
            q.column_index = i
        
        # 2. تنظيف أي قواعد تفريع تشير إلى أسئلة لم تعد موجودة في القالب أو تسبق السؤال الحالي
        for q in self.template.questions:
            if hasattr(q, "branching_rules") and q.branching_rules:
                invalid_answers = []
                for ans, target_q in list(q.branching_rules.items()):
                    if isinstance(target_q, Question):
                        if target_q not in self.template.questions:
                            invalid_answers.append(ans)
                        elif target_q.column_index <= q.column_index:
                            invalid_answers.append(ans)
                    elif isinstance(target_q, int):
                        if target_q >= len(self.template.questions):
                            invalid_answers.append(ans)
                        elif target_q <= q.column_index:
                            invalid_answers.append(ans)
                for ans in invalid_answers:
                    del q.branching_rules[ans]


    def _populate_table(self):
        self._clean_and_sync_questions()
        self.table.setRowCount(0)
        for i, q in enumerate(self.template.questions):
            self.table.insertRow(i)

            # رقم
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, num_item)

            # نص السؤال
            text_item = QTableWidgetItem(q.text)
            self.table.setItem(i, 1, text_item)

            # النوع - ComboBox
            combo = QComboBox()
            combo.addItems([
                "عام",
                "ديموغرافي (واحدة)",
                "ديموغرافي (متعددة)",
                "ليكرت",
                "ديموغرافي (مع أخرى)"
            ])
            combo.setCurrentIndex(int(q.question_type))
            combo.currentIndexChanged.connect(
                lambda idx, row=i: self._on_type_changed(row, idx)
            )
            self.table.setCellWidget(i, 2, combo)

            # الإجابات والتفريع المشروط
            if q.question_type == QuestionType.GENERAL:
                subtypes_ar = {
                    "text": "نص حر",
                    "paragraph": "فقرة",
                    "number": "رقم",
                    "date": "تاريخ",
                    "time": "وقت"
                }
                subtype = q.answers[0] if q.answers else "text"
                answers_text = f"تقييد: {subtypes_ar.get(subtype, 'نص حر')}"
                ans_item = QTableWidgetItem(answers_text)
                ans_item.setFlags(ans_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ans_item.setToolTip("انقر مرتين لتعديل نوع التقييد")
                self.table.setItem(i, 3, ans_item)
                self.table.removeCellWidget(i, 3)
            elif q.question_type == QuestionType.LIKERT:
                scale_picker = self._create_scale_picker_widget(i, q)
                cell_widget = AnswersCellWidget(
                    row_idx=i,
                    q=q,
                    edit_callback=lambda row=i, question=q: self._edit_answers(row, question),
                    delete_branch_callback=self._delete_branching_rule,
                    scale_picker_widget=scale_picker,
                    parent=self
                )
                self.table.setCellWidget(i, 3, cell_widget)
            else:
                cell_widget = AnswersCellWidget(
                    row_idx=i,
                    q=q,
                    edit_callback=lambda row=i, question=q: self._edit_answers(row, question),
                    delete_branch_callback=self._delete_branching_rule,
                    parent=self
                )
                self.table.setCellWidget(i, 3, cell_widget)

            # تلوين حسب النوع
            self._color_row(i, q.question_type)

        self.table.resizeRowsToContents()
        for row in range(self.table.rowCount()):
            if self.table.rowHeight(row) < 56:
                self.table.setRowHeight(row, 56)

    def _color_row(self, row: int, qtype: QuestionType):
        colors = {
            QuestionType.GENERAL: "#FFFFFF",
            QuestionType.DEMOGRAPHIC_SINGLE: "#E8F5E9",
            QuestionType.DEMOGRAPHIC_MULTIPLE: "#E3F2FD",
            QuestionType.LIKERT: "#FFF8E1",
            QuestionType.DEMOGRAPHIC_SINGLE_OTHER: "#E8F5E9",
        }
        color = QColor(colors.get(qtype, "#FFFFFF"))
        for col in [0, 1, 3]:
            item = self.table.item(row, col)
            if item:
                item.setBackground(color)

    def _on_type_changed(self, row: int, type_idx: int):
        if row >= len(self.template.questions):
            return
        q = self.template.questions[row]
        q.question_type = QuestionType(type_idx)
        if type_idx == 0:  # عام
            q.answers = ["text"]
        
        # مسح أي تفرعات تالفة قد لا تناسب النوع الجديد
        q.branching_rules = {}
        
        self._populate_table()

    def _create_scale_picker_widget(self, row: int, q: Question) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        combo = QComboBox()
        combo.addItem("— إجابات مخصصة —", 0)
        for scale in self.template.likert_scales:
            combo.addItem(scale.name, scale.id or id(scale))
            if q.likert_scale_id == scale.id or (q.likert_scale_id == 0 and q.answers == scale.answers):
                combo.setCurrentIndex(combo.count() - 1)
        
        combo.currentIndexChanged.connect(lambda idx: self._on_scale_selected(row, q, combo))
        layout.addWidget(combo, 1)
        
        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(28, 28)
        edit_btn.clicked.connect(lambda: self._edit_answers(row, q))
        layout.addWidget(edit_btn)
        
        return container

    def _on_scale_selected(self, row: int, q: Question, combo: QComboBox):
        idx = combo.currentIndex()
        if idx == 0:
            q.likert_scale_id = 0
        else:
            scale_id = combo.currentData()
            for scale in self.template.likert_scales:
                if scale.id == scale_id or id(scale) == scale_id:
                    q.likert_scale_id = scale.id or 0
                    q.answers = scale.answers
                    break
        
        # تصفية أي قواعد تفريع مشروط أصبحت غير مطابقة للخيارات الجديدة
        q.branching_rules = {ans: target for ans, target in q.branching_rules.items() if ans in q.answers}
        self._populate_table()

    def _on_cell_double_clicked(self, row: int, col: int):
        if col == 0 and row < len(self.template.questions):
            self._reorder_question_prompt(row)
        elif col == 3 and row < len(self.template.questions):
            q = self.template.questions[row]
            if q.question_type == QuestionType.GENERAL:
                self._edit_general_subtype(row, q)
            else:
                self._edit_answers(row, q)

    def _reorder_question_prompt(self, current_row: int):
        current_num = current_row + 1
        max_num = len(self.template.questions)
        new_num, ok = QInputDialog.getInt(
            self, "إعادة ترتيب السؤال",
            f"أدخل الرقم الجديد للسؤال (من 1 إلى {max_num}):",
            current_num, 1, max_num, 1
        )
        if ok and new_num != current_num:
            target_row = new_num - 1
            
            # 1. مزامنة تعديلات الخلايا الجارية
            self._sync_from_table()
            
            # 2. نقل السؤال في مصفوفة النموذج
            q = self.template.questions.pop(current_row)
            self.template.questions.insert(target_row, q)
            
            # 3. تنظيف التفرعات العكسية وحفظ القالب
            self._clean_and_sync_questions()
            
            # 4. تحديث الجدول وتحديد الصف الجديد
            self._populate_table()
            self.table.selectRow(target_row)

    def _edit_general_subtype(self, row: int, q: Question):
        subtypes = [
            ("نص حر (سطر واحد)", "text"),
            ("فقرة (نص متعدد الأسطر)", "paragraph"),
            ("رقم (أرقام فقط)", "number"),
            ("تاريخ (يوم/شهر/سنة)", "date"),
            ("وقت (ساعة:دقيقة)", "time")
        ]
        current_subtype = q.answers[0] if q.answers else "text"
        current_idx = 0
        for idx, (_, val) in enumerate(subtypes):
            if val == current_subtype:
                current_idx = idx
                break
                
        item, ok = QInputDialog.getItem(
            self, "تقييد الإجابة",
            "اختر نوع التقييد للإجابة:",
            [name for name, _ in subtypes],
            current_idx, False
        )
        if ok and item:
            selected_val = next(val for name, val in subtypes if name == item)
            q.answers = [selected_val]
            subtypes_ar = {
                "text": "نص حر",
                "paragraph": "فقرة",
                "number": "رقم",
                "date": "تاريخ",
                "time": "وقت"
            }
            self.table.item(row, 3).setText(f"تقييد: {subtypes_ar.get(selected_val, 'نص حر')}")

    def _edit_answers(self, row: int, q: Question):
        dialog = AnswersEditDialog(q, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            q.answers = dialog.get_answers()
            # إزالة أي قواعد تفريع لإجابات تم حذفها
            q.branching_rules = {ans: target for ans, target in q.branching_rules.items() if ans in q.answers}
            self._populate_table()

    def _set_branching_rule(self, source_q_idx: int, answer_text: str, target_q_idx: int):
        source_q = self.template.questions[source_q_idx]
        target_q = self.template.questions[target_q_idx]
        source_q.branching_rules[answer_text] = target_q
        self._populate_table()

    def _delete_branching_rule(self, row_idx: int, answer_text: str):
        q = self.template.questions[row_idx]
        if answer_text in q.branching_rules:
            del q.branching_rules[answer_text]
            self._populate_table()

    def eventFilter(self, source, event) -> bool:
        if source == self.table.viewport():
            if event.type() == QEvent.Type.DragEnter:
                if event.mimeData().hasFormat("application/x-survey-branch"):
                    event.acceptProposedAction()
                    return True
            
            elif event.type() == QEvent.Type.DragMove:
                if event.mimeData().hasFormat("application/x-survey-branch"):
                    pos = event.position().toPoint()
                    row = self.table.rowAt(pos.y())
                    if row != -1:
                        self.table.selectRow(row)
                    event.acceptProposedAction()
                    return True
            
            elif event.type() == QEvent.Type.Drop:
                if event.mimeData().hasFormat("application/x-survey-branch"):
                    pos = event.position().toPoint()
                    target_row = self.table.rowAt(pos.y())
                    
                    try:
                        data = event.mimeData().data("application/x-survey-branch").data().decode('utf-8')
                        source_q_idx_str, answer_text = data.split(":", 1)
                        source_q_idx = int(source_q_idx_str)
                        
                        if target_row != -1:
                            if target_row <= source_q_idx:
                                QMessageBox.warning(
                                    self, "خطأ في التفريع",
                                    "يجب أن يكون السؤال المستهدف بعد السؤال الحالي لتجنب الدوران اللانهائي."
                                )
                            else:
                                self._set_branching_rule(source_q_idx, answer_text, target_row)
                                event.acceptProposedAction()
                        else:
                            event.ignore()
                    except Exception:
                        event.ignore()
                    return True
        return super().eventFilter(source, event)


    def _add_question(self):
        dialog = AddQuestionDialog(self.template, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 1. المزامنة أولاً لحفظ أي تعديلات نصية جارية في الجدول
            self._sync_from_table()
            
            # 2. جلب السؤال الجديد وموضع الإدراج المطلوب
            q = dialog.get_question()
            target_pos = dialog.get_target_position()
            target_idx = target_pos - 1
            
            # 3. إدراج السؤال في الموضع المحدد
            self.template.questions.insert(target_idx, q)
            
            # 4. تحديث الجدول وتظليل الصف الجديد
            self._populate_table()
            self.table.selectRow(target_idx)

    def _duplicate_selected(self):
        selected = self.table.selectedIndexes()
        if not selected:
            return
        
        row = selected[0].row()
        if row >= len(self.template.questions):
            return
            
        original = self.template.questions[row]
        from dataclasses import replace
        new_q = replace(original)
        new_q.id = 0  # سؤال جديد
        new_q.column_index = len(self.template.questions)
        
        # نسخ قائمة الإجابات بشكل منفصل لتجنب مشاركة المرجع
        new_q.answers = list(original.answers)
        
        self.template.questions.append(new_q)
        self._populate_table()
        QMessageBox.information(self, "تم النسخ", f"تم نسخ السؤال: {original.text}")

    def _delete_selected(self):
        rows = sorted(
            set(idx.row() for idx in self.table.selectedIndexes()),
            reverse=True
        )
        if not rows:
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف {len(rows)} سؤال/أسئلة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for row in rows:
                if row < len(self.template.questions):
                    self.template.questions.pop(row)
            self._populate_table()

    def _sync_from_table(self):
        """مزامنة التعديلات من الجدول إلى النموذج"""
        self._clean_and_sync_questions()
        for i, q in enumerate(self.template.questions):
            item = self.table.item(i, 1)
            if item:
                q.text = item.text().strip() or q.text

    def _save_changes(self):
        self._sync_from_table()
        self.db.update_template(self.template)
        QMessageBox.information(self, "تم الحفظ", "تم حفظ التعديلات بنجاح.")

    def _start_entry(self):
        self._sync_from_table()
        self.db.update_template(self.template)

        # إعادة تحميل القالب من DB للحصول على IDs المحدّثة بعد update_template
        self.template = self.db.load_template(self.template.id)

        # طلب عدد الاستمارات واسم الجلسة
        count, ok = QInputDialog.getInt(
            self, "عدد الاستمارات",
            "كم عدد الاستمارات الورقية التي ستفرّغها؟",
            value=1, min=1, max=10000
        )
        if not ok:
            return

        name, ok2 = QInputDialog.getText(
            self, "اسم الجلسة",
            "أدخل اسماً لهذه الجلسة:",
            text=f"جلسة {self.template.name}"
        )
        if not ok2 or not name.strip():
            return

        session = Session(
            template_id=self.template.id,
            name=name.strip(),
            total_forms=count
        )
        session.ensure_forms()
        self.db.save_session(session)
        self.db.increment_template_use(self.template.id)

        self.main_window.show_entry(session, self.template)
 
    def _import_responses(self):
        """استيراد إجابات رقمية لهذا القالب مباشرة"""
        from utils.excel_importer import import_responses_from_excel, ImportError
        
        path, _ = QFileDialog.getOpenFileName(
            self, f"اختر ملف الإجابات الرقمية — {self.template.name}", "",
            "ملفات Excel (*.xlsx *.xls)"
        )
        if not path:
            return
 
        try:
            forms, warnings = import_responses_from_excel(path, self.template)
        except ImportError as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", str(e))
            return
 
        if warnings:
            msg = (f"تم قراءة الملف مع {len(warnings)} تحذير:\n\n" + 
                   "\n".join(f"• {w}" for w in warnings[:5]) + "\n\nهل تريد المتابعة؟")
            reply = QMessageBox.warning(self, "تحذيرات", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
 
        name, ok = QInputDialog.getText(self, "اسم الجلسة", "أدخل اسماً لهذه الجلسة:", text=f"جلسة {self.template.name}")
        if not ok or not name.strip(): return
 
        session = Session(template_id=self.template.id, name=name.strip(), total_forms=len(forms))
        session.forms = forms
        for i, f in enumerate(session.forms): f.form_index = i
 
        self.db.save_session(session)
        self.db.increment_template_use(self.template.id)
        
        QMessageBox.information(self, "تم الاستيراد", "✅ تم استيراد البيانات بنجاح.")
        self.main_window.show_results()
 
    def _manage_likert_scales(self):
        dialog = LikertScalesManagerDialog(self.template, self)
        dialog.exec()
        self.load_template(self.template)  # تحديث لتنعكس الأسماء الجديدة
 
class LikertScalesManagerDialog(QDialog):
    def __init__(self, template: Template, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("إدارة مقاييس ليكرت المشتركة")
        self.setMinimumSize(500, 400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        self.list = QListWidget()
        for scale in self.template.likert_scales:
            item = QListWidgetItem(f"{scale.name} ({len(scale.answers)} خيارات)")
            item.setData(Qt.ItemDataRole.UserRole, scale)
            self.list.addItem(item)
        layout.addWidget(self.list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ إضافة مقياس جديد")
        btn_add.clicked.connect(self._add_scale)
        btn_row.addWidget(btn_add)

        btn_edit = QPushButton("تعديل المحدد")
        btn_edit.clicked.connect(self._edit_scale)
        btn_row.addWidget(btn_edit)

        btn_del = QPushButton("حذف")
        btn_del.clicked.connect(self._delete_scale)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _add_scale(self):
        name, ok = QInputDialog.getText(self, "مقياس جديد", "اسم المقياس (مثلاً: خماسي موافقة):")
        if not ok or not name.strip(): return
        
        scale = LikertScale(name=name.strip(), answers=["موافق بشدة", "موافق", "محايد", "غير موافق", "غير موافق بشدة"])
        dialog = LikertAnswersEditDialog(scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            scale.answers = dialog.get_answers()
            self.template.likert_scales.append(scale)
            item = QListWidgetItem(f"{scale.name} ({len(scale.answers)} خيارات)")
            item.setData(Qt.ItemDataRole.UserRole, scale)
            self.list.addItem(item)

    def _edit_scale(self):
        item = self.list.currentItem()
        if not item: return
        scale = item.data(Qt.ItemDataRole.UserRole)
        
        dialog = LikertAnswersEditDialog(scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            scale.answers = dialog.get_answers()
            item.setText(f"{scale.name} ({len(scale.answers)} خيارات)")

    def _delete_scale(self):
        item = self.list.currentItem()
        if not item: return
        scale = item.data(Qt.ItemDataRole.UserRole)
        self.template.likert_scales.remove(scale)
        self.list.takeItem(self.list.row(item))

class LikertAnswersEditDialog(QDialog):
    def __init__(self, scale: LikertScale, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"تعديل مقياس: {scale.name}")
        self.setMinimumSize(350, 300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("خيارات المقياس (واحد في كل سطر):"))
        self.text_edit = QTextEdit()
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setPlainText("\n".join(scale.answers))
        layout.addWidget(self.text_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_answers(self):
        return [l.strip() for l in self.text_edit.toPlainText().splitlines() if l.strip()]

class AddQuestionDialog(QDialog):
    def __init__(self, template: Template, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("إضافة سؤال جديد")
        self.setMinimumSize(500, 450)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # نص السؤال
        layout.addWidget(QLabel("نص السؤال:"))
        self.text_edit = QTextEdit()
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setFixedHeight(60)
        layout.addWidget(self.text_edit)

        # نوع السؤال
        layout.addWidget(QLabel("نوع السؤال:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "عام (نص حر)",
            "ديموغرافي (إجابة واحدة)",
            "ديموغرافي (إجابات متعددة)",
            "ليكرت (مقياس)"
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        # موضع السؤال
        layout.addWidget(QLabel("موضع السؤال (الرقم المطلوب):"))
        self.pos_spin = QSpinBox()
        self.pos_spin.setRange(1, len(self.template.questions) + 1)
        self.pos_spin.setValue(len(self.template.questions) + 1)
        layout.addWidget(self.pos_spin)

        # منطقة الإجابات
        self.ans_stack = QStackedWidget()
        
        # 0: خيارات التقييد (للعام)
        general_opts = QWidget()
        g_layout = QVBoxLayout(general_opts)
        g_layout.setContentsMargins(0, 10, 0, 0)
        g_layout.addWidget(QLabel("تقييد الإجابة (نوع الإدخال المتوقع):"))
        self.general_subtype_combo = QComboBox()
        self.general_subtype_combo.addItem("نص حر (سطر واحد)", "text")
        self.general_subtype_combo.addItem("فقرة (نص متعدد الأسطر)", "paragraph")
        self.general_subtype_combo.addItem("رقم (أرقام فقط)", "number")
        self.general_subtype_combo.addItem("تاريخ (يوم/شهر/سنة)", "date")
        self.general_subtype_combo.addItem("وقت (ساعة:دقيقة)", "time")
        g_layout.addWidget(self.general_subtype_combo)
        self.ans_stack.addWidget(general_opts)

        # 1: إدخال يدوي (للديموغرافي)
        manual = QWidget()
        m_layout = QVBoxLayout(manual)
        m_layout.setContentsMargins(0, 10, 0, 0)
        m_layout.addWidget(QLabel("خيارات الإجابة (واحد في كل سطر):"))
        self.manual_edit = QTextEdit()
        self.manual_edit.setTabChangesFocus(True)
        m_layout.addWidget(self.manual_edit)
        self.ans_stack.addWidget(manual)

        # 2: اختيار مقياس (لليكرت)
        likert = QWidget()
        l_layout = QVBoxLayout(likert)
        l_layout.setContentsMargins(0, 10, 0, 0)
        l_layout.addWidget(QLabel("اختر مقياس ليكرت:"))
        self.scale_combo = QComboBox()
        for scale in self.template.likert_scales:
            self.scale_combo.addItem(scale.name, scale.id or id(scale))
        l_layout.addWidget(self.scale_combo)
        
        btn_manage = QPushButton("⚙ إدارة المقاييس...")
        btn_manage.clicked.connect(self._manage_scales)
        l_layout.addWidget(btn_manage)
        
        self.ans_stack.addWidget(likert)
        
        layout.addWidget(self.ans_stack)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_type_changed(self, index):
        if index == 0: # عام
            self.ans_stack.setCurrentIndex(0)
        elif index in (1, 2): # ديموغرافي
            self.ans_stack.setCurrentIndex(1)
        elif index == 3: # ليكرت
            self.ans_stack.setCurrentIndex(2)

    def _manage_scales(self):
        dialog = LikertScalesManagerDialog(self.template, self)
        dialog.exec()
        # تحديث قائمة المقاييس
        self.scale_combo.clear()
        for scale in self.template.likert_scales:
            self.scale_combo.addItem(scale.name, scale.id or id(scale))

    def _validate_and_accept(self):
        if not self.text_edit.toPlainText().strip():
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال نص السؤال.")
            return
        
        idx = self.type_combo.currentIndex()
        if idx in (1, 2) and not self.manual_edit.toPlainText().strip():
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال خيارات الإجابة.")
            return
        
        if idx == 3 and self.scale_combo.count() == 0:
            QMessageBox.warning(self, "تنبيه", "لا توجد مقاييس ليكرت معرفة. يرجى إضافة مقياس أولاً.")
            return
            
        self.accept()

    def get_question(self) -> Question:
        qtype = QuestionType(self.type_combo.currentIndex())
        q = Question(
            text=self.text_edit.toPlainText().strip(),
            question_type=qtype
        )
        
        if qtype == QuestionType.GENERAL:
            subtype = self.general_subtype_combo.currentData() or "text"
            q.answers = [subtype]
        elif qtype in (QuestionType.DEMOGRAPHIC_SINGLE, QuestionType.DEMOGRAPHIC_MULTIPLE):
            q.answers = [l.strip() for l in self.manual_edit.toPlainText().splitlines() if l.strip()]
        elif qtype == QuestionType.LIKERT:
            scale_id = self.scale_combo.currentData()
            for scale in self.template.likert_scales:
                if scale.id == scale_id or id(scale) == scale_id:
                    q.likert_scale_id = scale.id or 0
                    q.answers = scale.answers
                    break
        return q

    def get_target_position(self) -> int:
        return self.pos_spin.value()

from models.template import LikertScale


class AnswersEditDialog(QDialog):
    def __init__(self, question: Question, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"تعديل إجابات: {question.text}")
        self.setMinimumSize(400, 350)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)

        lbl = QLabel("أدخل الإجابات (إجابة واحدة في كل سطر):")
        layout.addWidget(lbl)

        self.text_edit = QTextEdit()
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setPlainText("\n".join(question.answers))
        layout.addWidget(self.text_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_answers(self):
        text = self.text_edit.toPlainText()
        return [line.strip() for line in text.splitlines() if line.strip()]
