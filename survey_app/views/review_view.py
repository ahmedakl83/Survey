from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QInputDialog, QMessageBox, QDialog,
    QDialogButtonBox, QListWidget, QListWidgetItem, QAbstractItemView,
    QStackedWidget, QFileDialog, QApplication, QSpinBox, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QEvent, QMimeData, QTimer
from PyQt6.QtGui import QColor, QDrag

from database.db_manager import DatabaseManager
from models.template import Template, LikertScale
from models.question import Question, QuestionType
from models.session import Session
from utils.translator import tr, get_layout_direction, get_text_alignment, is_rtl


class DragHandle(QLabel):
    def __init__(self, q_idx, answer_text, parent=None):
        super().__init__(parent)
        self.q_idx = q_idx
        self.answer_text = answer_text
        self.setText("🔗")
        self.setToolTip(tr("drag_handle_tooltip"))
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
            mime_data.setData("application/x-survey-branch", f"{self.q_idx}:{self.answer_text}".encode('utf-8'))
            drag.setMimeData(mime_data)
            
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
            
        ans_container = QWidget()
        ans_layout = QHBoxLayout(ans_container)
        ans_layout.setContentsMargins(0, 0, 0, 0)
        ans_layout.setSpacing(8)
        
        if not scale_picker_widget:
            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(24, 24)
            edit_btn.clicked.connect(edit_callback)
            edit_btn.setToolTip(tr("tooltip_edit_custom"))
            edit_btn.setStyleSheet("font-size: 11px; padding: 0;")
            ans_layout.addWidget(edit_btn)
            
        if q.answers:
            for ans in q.answers:
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(4, 2, 4, 2)
                item_layout.setSpacing(4)
                
                bg_color = "#FFF9C4" if q.question_type == QuestionType.LIKERT else "#E8F5E9" if q.question_type in (QuestionType.DEMOGRAPHIC_SINGLE, QuestionType.DEMOGRAPHIC_SINGLE_OTHER) else "#E3F2FD"
                border_color = "#FFE082" if q.question_type == QuestionType.LIKERT else "#C8E6C9" if q.question_type in (QuestionType.DEMOGRAPHIC_SINGLE, QuestionType.DEMOGRAPHIC_SINGLE_OTHER) else "#BBDEFB"
                item_widget.setStyleSheet(
                    f"background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px;"
                )
                
                is_single_choice = q.is_single_choice
                if is_single_choice:
                    handle = DragHandle(self.row_idx, ans, self)
                    item_layout.addWidget(handle)
                
                lbl_text = QLabel(ans)
                lbl_text.setStyleSheet("font-size: 11px; color: #263238; border: none; background: transparent;")
                item_layout.addWidget(lbl_text)
                
                if hasattr(q, "branching_rules") and ans in q.branching_rules:
                    target = q.branching_rules[ans]
                    target_num = target.column_index + 1 if isinstance(target, Question) else target + 1
                    
                    badge = QLabel(tr("branch_badge", target=target_num))
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
                    del_btn.setToolTip(tr("delete_branch_tooltip"))
                    del_btn.clicked.connect(lambda checked, a=ans: delete_branch_callback(self.row_idx, a))
                    item_layout.addWidget(del_btn)
                    
                ans_layout.addWidget(item_widget)
        else:
            lbl_empty = QLabel("—")
            lbl_empty.setStyleSheet("color: #90A4AE; font-size: 12px; border: none;")
            ans_layout.addWidget(lbl_empty)
            
        ans_layout.addStretch()
        main_layout.addWidget(ans_container)


class QuestionTextCellWidget(QWidget):
    def __init__(self, q: Question, edit_callback=None, parent=None):
        super().__init__(parent)
        self.q = q
        self.edit_callback = edit_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        header_text = getattr(q, 'section_header', '') or ''
        if header_text.strip():
            header_widget = QWidget()
            h_layout = QHBoxLayout(header_widget)
            h_layout.setContentsMargins(14, 8, 14, 8)
            h_layout.setSpacing(8)
            h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_widget.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4A148C, stop:0.5 #6A1B9A, stop:1 #4A148C); "
                "border-radius: 6px; border: 1px solid #311B92;"
            )
            
            sec_lbl = QLabel(f"📑  {header_text.strip()}")
            sec_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sec_lbl.setStyleSheet(
                "font-weight: bold; color: #FFFFFF; font-size: 13px; "
                "border: none; background: transparent;"
            )
            h_layout.addWidget(sec_lbl)
            layout.addWidget(header_widget)
            
        self.txt_lbl = QLabel(q.text)
        self.txt_lbl.setWordWrap(True)
        self.txt_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #1a1a2e; border: none; background: transparent;")
        layout.addWidget(self.txt_lbl)

    def mouseDoubleClickEvent(self, event):
        if self.edit_callback:
            self.edit_callback()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


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

        self.btn_back = QPushButton(tr("back"))
        self.btn_back.setStyleSheet(
            "background-color: transparent; color: white; border: none; font-size: 13px;"
        )
        self.btn_back.clicked.connect(self.main_window.show_home)
        h_layout.addWidget(self.btn_back)

        self.title_lbl = QLabel(tr("review_questions_title"))
        self.title_lbl.setStyleSheet(
            "color: white; font-size: 17px; font-weight: bold;"
        )
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()

        self.btn_save = QPushButton(tr("btn_save_changes"))
        self.btn_save.clicked.connect(self._save_changes)
        h_layout.addWidget(self.btn_save)

        self.btn_start = QPushButton(tr("btn_start_entry"))
        self.btn_start.setObjectName("btn_success")
        self.btn_start.clicked.connect(self._start_entry)
        h_layout.addWidget(self.btn_start)
 
        self.btn_import = QPushButton(tr("btn_import_responses"))
        self.btn_import.setObjectName("btn_secondary")
        self.btn_import.clicked.connect(self._import_responses)
        h_layout.addWidget(self.btn_import)

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
        self._update_header_labels()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 220)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        
        self.table.setAcceptDrops(True)
        self.table.viewport().setAcceptDrops(True)
        self.table.viewport().installEventFilter(self)
        
        content_layout.addWidget(self.table)

        # أزرار إضافية
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton(tr("btn_add_question"))
        self.btn_add.setObjectName("btn_secondary")
        self.btn_add.clicked.connect(self._add_question)
        btn_row.addWidget(self.btn_add)

        self.btn_dup = QPushButton(tr("btn_duplicate_question"))
        self.btn_dup.setObjectName("btn_secondary")
        self.btn_dup.clicked.connect(self._duplicate_selected)
        btn_row.addWidget(self.btn_dup)

        self.btn_section = QPushButton(tr("btn_section_header"))
        self.btn_section.setObjectName("btn_secondary")
        self.btn_section.setToolTip(tr("tooltip_section_header"))
        self.btn_section.clicked.connect(self._set_section_header_prompt)
        btn_row.addWidget(self.btn_section)

        self.btn_del = QPushButton(tr("btn_delete_selected"))
        self.btn_del.setObjectName("btn_danger")
        self.btn_del.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.btn_del)

        self.btn_likert = QPushButton(tr("btn_manage_likert"))
        self.btn_likert.setObjectName("btn_secondary")
        self.btn_likert.clicked.connect(self._manage_likert_scales)
        btn_row.addWidget(self.btn_likert)

        btn_row.addStretch()
        content_layout.addLayout(btn_row)

        root.addWidget(content)

    def _update_header_labels(self):
        self.table.setHorizontalHeaderLabels([
            tr("th_num"),
            tr("th_question_text"),
            tr("th_question_type"),
            tr("th_answers")
        ])

    def keyPressEvent(self, event):
        is_plus = (event.key() == Qt.Key.Key_Plus) or \
                  (event.key() == Qt.Key.Key_Equal and event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        
        if is_plus:
            focus_widget = self.focusWidget()
            if focus_widget:
                if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                    super().keyPressEvent(event)
                    return
            self._add_question()
            event.accept()
        else:
            super().keyPressEvent(event)

    def load_template(self, template: Template, target_row: int = 0):
        self.setLayoutDirection(get_layout_direction())
        self.template = template
        self.btn_back.setText(tr("back"))
        self.title_lbl.setText(tr("review_questions_template", name=template.name))
        self.info_lbl.setText(
            tr("review_info_lbl", questions=len(template.questions), scales=len(template.likert_scales))
        )
        self.btn_save.setText(tr("btn_save_changes"))
        self.btn_start.setText(tr("btn_start_entry"))
        self.btn_import.setText(tr("btn_import_responses"))
        self.btn_add.setText(tr("btn_add_question"))
        self.btn_dup.setText(tr("btn_duplicate_question"))
        self.btn_section.setText(tr("btn_section_header"))
        self.btn_section.setToolTip(tr("tooltip_section_header"))
        self.btn_del.setText(tr("btn_delete_selected"))
        self.btn_likert.setText(tr("btn_manage_likert"))
        self._update_header_labels()

        self._populate_table(target_row=target_row)

    def _clean_and_sync_questions(self):
        for i, q in enumerate(self.template.questions):
            q.column_index = i
        
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

    def _populate_table(self, target_row: int = None):
        if target_row is None:
            selected_indexes = self.table.selectedIndexes()
            if selected_indexes:
                target_row = selected_indexes[0].row()

        current_scroll = self.table.verticalScrollBar().value()

        self._clean_and_sync_questions()
        self.table.setRowCount(0)
        
        type_options = [
            tr("qtype_general"),
            tr("qtype_demographic_single"),
            tr("qtype_demographic_multiple"),
            tr("qtype_likert"),
            tr("qtype_demographic_single_other")
        ]

        subtypes_labels = {
            "text": tr("subtype_text"),
            "paragraph": tr("subtype_paragraph"),
            "number": tr("subtype_number"),
            "date": tr("subtype_date"),
            "time": tr("subtype_time")
        }

        for i, q in enumerate(self.template.questions):
            self.table.insertRow(i)

            # رقم
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, num_item)

            # نص السؤال
            text_widget = QuestionTextCellWidget(
                q=q,
                edit_callback=lambda row=i, question=q: self._edit_question(row, question),
                parent=self.table
            )
            self.table.setCellWidget(i, 1, text_widget)

            # النوع - ComboBox
            combo = QComboBox()
            combo.addItems(type_options)
            combo.setCurrentIndex(int(q.question_type))
            combo.currentIndexChanged.connect(
                lambda idx, row=i: self._on_type_changed(row, idx)
            )
            self.table.setCellWidget(i, 2, combo)

            # الإجابات والتفريع المشروط
            if q.question_type == QuestionType.GENERAL:
                subtype = q.answers[0] if q.answers else "text"
                answers_text = tr("constraint_prefix", subtype=subtypes_labels.get(subtype, tr("subtype_text")))
                ans_item = QTableWidgetItem(answers_text)
                ans_item.setTextAlignment(get_text_alignment() | Qt.AlignmentFlag.AlignVCenter)
                ans_item.setFlags(ans_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                ans_item.setToolTip(tr("subtype_tooltip"))
                self.table.setItem(i, 3, ans_item)
                self.table.removeCellWidget(i, 3)
            elif q.question_type == QuestionType.LIKERT:
                scale_picker = self._create_scale_picker_widget(i, q)
                cell_widget = AnswersCellWidget(
                    row_idx=i,
                    q=q,
                    edit_callback=lambda row=i, question=q: self._edit_question(row, question),
                    delete_branch_callback=self._delete_branching_rule,
                    scale_picker_widget=scale_picker,
                    parent=self
                )
                self.table.setCellWidget(i, 3, cell_widget)
            else:
                cell_widget = AnswersCellWidget(
                    row_idx=i,
                    q=q,
                    edit_callback=lambda row=i, question=q: self._edit_question(row, question),
                    delete_branch_callback=self._delete_branching_rule,
                    parent=self
                )
                self.table.setCellWidget(i, 3, cell_widget)

            self._color_row(i, q.question_type)

        self.table.resizeRowsToContents()
        for row in range(self.table.rowCount()):
            q = self.template.questions[row] if row < len(self.template.questions) else None
            has_section = bool(getattr(q, 'section_header', '').strip()) if q else False
            min_h = 105 if has_section else 56
            if self.table.rowHeight(row) < min_h:
                self.table.setRowHeight(row, min_h)

        if target_row is not None and 0 <= target_row < self.table.rowCount():
            self._scroll_to_target_row(target_row)
            QTimer.singleShot(50, lambda r=target_row: self._scroll_to_target_row(r))
        else:
            self.table.verticalScrollBar().setValue(current_scroll)

    def _scroll_to_target_row(self, row: int):
        if 0 <= row < self.table.rowCount():
            self.table.setCurrentCell(row, 0)
            self.table.selectRow(row)
            item = self.table.item(row, 0)
            if item:
                self.table.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)

    def _color_row(self, row: int, qtype: QuestionType):
        colors = {
            QuestionType.GENERAL: "#FFFFFF",
            QuestionType.DEMOGRAPHIC_SINGLE: "#E8F5E9",
            QuestionType.DEMOGRAPHIC_MULTIPLE: "#E3F2FD",
            QuestionType.LIKERT: "#FFF8E1",
            QuestionType.DEMOGRAPHIC_SINGLE_OTHER: "#E8F5E9",
        }
        color = QColor(colors.get(qtype, "#FFFFFF"))
        for col in [0, 3]:
            item = self.table.item(row, col)
            if item:
                item.setBackground(color)

    def _on_type_changed(self, row: int, type_idx: int):
        if row >= len(self.template.questions):
            return
        q = self.template.questions[row]
        q.question_type = QuestionType(type_idx)
        if type_idx == 0:  # general
            q.answers = ["text"]
        elif type_idx in (1, 2, 4) and (not q.answers or q.answers in [["text"], ["paragraph"], ["number"], ["date"], ["time"]]):
            if type_idx == 4:
                q.answers = [tr("default_option_1"), tr("default_option_2"), tr("default_option_other")]
            else:
                q.answers = [tr("default_option_1"), tr("default_option_2")]
        
        q.branching_rules = {}
        self._populate_table(target_row=row)

    def _create_scale_picker_widget(self, row: int, q: Question) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        combo = QComboBox()
        combo.addItem(tr("custom_answers_picker"), 0)
        for scale in self.template.likert_scales:
            combo.addItem(scale.name, scale.id or id(scale))
            if q.likert_scale_id == scale.id or (q.likert_scale_id == 0 and q.answers == scale.answers):
                combo.setCurrentIndex(combo.count() - 1)
        
        combo.currentIndexChanged.connect(lambda idx: self._on_scale_selected(row, q, combo))
        layout.addWidget(combo, 1)
        
        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip(tr("tooltip_edit_question"))
        edit_btn.clicked.connect(lambda: self._edit_question(row, q))
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
                    q.answers = list(scale.answers)
                    break
        
        q.branching_rules = {ans: target for ans, target in q.branching_rules.items() if ans in q.answers}
        self._populate_table(target_row=row)

    def _on_cell_double_clicked(self, row: int, col: int):
        if col == 0 and row < len(self.template.questions):
            self._reorder_question_prompt(row)
        elif col in (1, 3) and row < len(self.template.questions):
            q = self.template.questions[row]
            self._edit_question(row, q)

    def _reorder_question_prompt(self, current_row: int):
        current_num = current_row + 1
        max_num = len(self.template.questions)
        new_num, ok = QInputDialog.getInt(
            self, tr("reorder_title"),
            tr("reorder_prompt", max=max_num),
            current_num, 1, max_num, 1
        )
        if ok and new_num != current_num:
            target_row = new_num - 1
            self._sync_from_table()
            
            q = self.template.questions.pop(current_row)
            self.template.questions.insert(target_row, q)
            
            self._clean_and_sync_questions()
            self._populate_table(target_row=target_row)

    def _edit_question(self, row: int, q: Question):
        self._sync_from_table()
        dialog = EditQuestionDialog(q, self.template, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.apply_to_question(q)
            self._populate_table(target_row=row)

    def _set_branching_rule(self, source_q_idx: int, answer_text: str, target_q_idx: int):
        source_q = self.template.questions[source_q_idx]
        target_q = self.template.questions[target_q_idx]
        source_q.branching_rules[answer_text] = target_q
        self._populate_table(target_row=source_q_idx)

    def _delete_branching_rule(self, row_idx: int, answer_text: str):
        q = self.template.questions[row_idx]
        if answer_text in q.branching_rules:
            del q.branching_rules[answer_text]
            self._populate_table(target_row=row_idx)

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
                    
                    data = event.mimeData().data("application/x-survey-branch").data().decode('utf-8')
                    source_idx_str, ans_text = data.split(":", 1)
                    source_idx = int(source_idx_str)
                    
                    if target_row != -1 and target_row > source_idx:
                        self._set_branching_rule(source_idx, ans_text, target_row)
                    elif target_row != -1 and target_row <= source_idx:
                        QMessageBox.warning(
                            self, tr("warning"),
                            "التفريع المشروط يجب أن ينتقل إلى سؤال لاحق وليس سابقاً." if is_rtl() else "Branching target must be a subsequent question."
                        )
                    event.acceptProposedAction()
                    return True
                    
        return super().eventFilter(source, event)

    def _add_question(self):
        self._sync_from_table()
        dialog = AddQuestionDialog(self.template, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            q = dialog.get_question()
            target_pos = dialog.get_target_position()
            target_idx = max(0, min(target_pos - 1, len(self.template.questions)))
            self.template.questions.insert(target_idx, q)
            self._populate_table(target_row=target_idx)

    def _duplicate_selected(self):
        selected = self.table.selectedIndexes()
        if not selected:
            return
        row = selected[0].row()
        if row >= len(self.template.questions):
            return

        self._sync_from_table()
        original = self.template.questions[row]
        new_q = Question(
            text=f"{original.text} ({tr('duplicate_success_title')})",
            question_type=original.question_type,
            likert_scale_id=original.likert_scale_id,
            section_header=getattr(original, 'section_header', '') or ''
        )
        new_q.answers = list(original.answers)
        
        target_idx = row + 1
        self.template.questions.insert(target_idx, new_q)
        self._populate_table(target_row=target_idx)
        QMessageBox.information(self, tr("duplicate_success_title"), tr("duplicate_success_msg", text=original.text))

    def _set_section_header_prompt(self):
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.information(self, tr("warning"), tr("select_question_first_section"))
            return
        
        row = selected[0].row()
        if row >= len(self.template.questions):
            return
            
        q = self.template.questions[row]
        current_header = getattr(q, 'section_header', '') or ''
        
        text, ok = QInputDialog.getText(
            self, tr("section_prompt_title"),
            tr("section_prompt_msg", num=row + 1),
            text=current_header
        )
        if ok:
            q.section_header = text.strip()
            self._populate_table(target_row=row)

    def _delete_selected(self):
        rows = sorted(
            set(idx.row() for idx in self.table.selectedIndexes()),
            reverse=True
        )
        if not rows:
            return

        reply = QMessageBox.question(
            self, tr("confirm_delete"),
            tr("delete_questions_confirm_msg", count=len(rows)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for row in rows:
                if row < len(self.template.questions):
                    self.template.questions.pop(row)
            next_row = max(0, min(rows) - 1) if self.template.questions else None
            self._populate_table(target_row=next_row)

    def _sync_from_table(self):
        for i, q in enumerate(self.template.questions):
            cell_widget = self.table.cellWidget(i, 1)
            if isinstance(cell_widget, QuestionTextCellWidget):
                pass
            combo = self.table.cellWidget(i, 2)
            if isinstance(combo, QComboBox):
                q.question_type = QuestionType(combo.currentIndex())

    def _save_changes(self):
        self._sync_from_table()
        self.db.update_template(self.template)
        self.main_window.set_save_status("saved")
        self.load_template(self.template)

    def _start_entry(self):
        self._sync_from_table()
        self.db.update_template(self.template)

        if not self.template.questions:
            QMessageBox.warning(
                self, tr("error"),
                tr("no_questions_error")
            )
            return

        name, ok = QInputDialog.getText(
            self, tr("start_session_dialog_title"),
            tr("start_session_prompt", template=self.template.name, count=len(self.template.questions)),
            text=tr("default_session_name", template=self.template.name)
        )
        if not ok or not name.strip():
            return

        total_forms, ok = QInputDialog.getInt(
            self, tr("total_forms_prompt_title"),
            tr("total_forms_prompt_msg"),
            value=30, min=1, max=10000
        )
        if not ok:
            return

        session = Session(
            template_id=self.template.id,
            name=name.strip(),
            total_forms=total_forms
        )
        session.init_empty_forms()

        session_id = self.db.save_session(session)
        session.id = session_id

        self.db.increment_template_use(self.template.id)
        self.main_window.show_entry(session, self.template)

    def _import_responses(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("choose_responses_file_title", template_name=self.template.name),
            "",
            tr("excel_files_filter")
        )
        if not path:
            return

        from utils.excel_importer import import_responses_from_excel, ImportError
        try:
            forms, warnings = import_responses_from_excel(path, self.template)
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
            tr("session_name_prompt", template=self.template.name, count=len(forms)),
            text=tr("default_session_name", template=self.template.name)
        )
        if not ok or not name.strip():
            return

        session = Session(
            template_id=self.template.id,
            name=name.strip(),
            total_forms=len(forms)
        )
        session.forms = forms
        for i, f in enumerate(session.forms):
            f.form_index = i

        self.db.save_session(session)
        self.db.increment_template_use(self.template.id)

        QMessageBox.information(
            self, tr("import_success_title"),
            tr("import_responses_success_msg", count=len(forms), template=self.template.name)
        )
        self.main_window.show_results()
 
    def _manage_likert_scales(self):
        selected_idx = self.table.selectedIndexes()[0].row() if self.table.selectedIndexes() else 0
        dialog = LikertScalesManagerDialog(self.template, self)
        dialog.exec()
        self.load_template(self.template, target_row=selected_idx)
 

class LikertScalesManagerDialog(QDialog):
    def __init__(self, template: Template, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle(tr("likert_manager_title"))
        self.setMinimumSize(500, 400)
        self.setLayoutDirection(get_layout_direction())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        self.list = QListWidget()
        for scale in self.template.likert_scales:
            item = QListWidgetItem(f"{scale.name} {tr('scale_options_count', count=len(scale.answers))}")
            item.setData(Qt.ItemDataRole.UserRole, scale)
            self.list.addItem(item)
        layout.addWidget(self.list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton(tr("btn_add_scale"))
        btn_add.clicked.connect(self._add_scale)
        btn_row.addWidget(btn_add)

        btn_edit = QPushButton(tr("btn_edit_selected"))
        btn_edit.clicked.connect(self._edit_scale)
        btn_row.addWidget(btn_edit)

        btn_del = QPushButton(tr("delete"))
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._delete_scale)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _add_scale(self):
        name, ok = QInputDialog.getText(self, tr("new_scale_dialog_title"), tr("new_scale_prompt"))
        if not ok or not name.strip():
            return
        
        scale = LikertScale(name=name.strip(), answers=list(tr("default_likert_agree_5")))
        dialog = LikertAnswersEditDialog(scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            scale.answers = dialog.get_answers()
            self.template.likert_scales.append(scale)
            item = QListWidgetItem(f"{scale.name} {tr('scale_options_count', count=len(scale.answers))}")
            item.setData(Qt.ItemDataRole.UserRole, scale)
            self.list.addItem(item)

    def _edit_scale(self):
        item = self.list.currentItem()
        if not item:
            return
        scale = item.data(Qt.ItemDataRole.UserRole)
        dialog = LikertAnswersEditDialog(scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            scale.answers = dialog.get_answers()
            item.setText(f"{scale.name} {tr('scale_options_count', count=len(scale.answers))}")
            # تحديث الأسئلة المرتبطة بهذا المقياس
            for q in self.template.questions:
                if q.likert_scale_id == scale.id or (q.likert_scale_id == 0 and q.answers == scale.answers):
                    q.answers = list(scale.answers)

    def _delete_scale(self):
        item = self.list.currentItem()
        if not item:
            return
        scale = item.data(Qt.ItemDataRole.UserRole)
        self.template.likert_scales.remove(scale)
        self.list.takeItem(self.list.row(item))


class LikertAnswersEditDialog(QDialog):
    def __init__(self, scale: LikertScale, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("edit_scale_title", name=scale.name))
        self.setMinimumSize(350, 300)
        self.setLayoutDirection(get_layout_direction())
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(tr("scale_options_label")))
        self.text_edit = QTextEdit()
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setPlainText("\n".join(scale.answers))
        layout.addWidget(self.text_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_btn = btns.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText(tr("ok"))
        cancel_btn = btns.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setText(tr("cancel"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_answers(self):
        return [l.strip() for l in self.text_edit.toPlainText().splitlines() if l.strip()]


class AddQuestionDialog(QDialog):
    def __init__(self, template: Template, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle(tr("add_question_title"))
        self.setMinimumSize(500, 450)
        self.setLayoutDirection(get_layout_direction())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # نص السؤال
        layout.addWidget(QLabel(tr("question_text_lbl")))
        self.text_edit = QTextEdit()
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setFixedHeight(60)
        layout.addWidget(self.text_edit)

        # فاصل مقطعي (اختياري)
        layout.addWidget(QLabel(tr("section_header_optional")))
        self.sec_header_edit = QLineEdit()
        self.sec_header_edit.setPlaceholderText(tr("section_header_placeholder"))
        layout.addWidget(self.sec_header_edit)

        # نوع السؤال
        layout.addWidget(QLabel(tr("question_type_lbl")))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            tr("qtype_combo_general"),
            tr("qtype_combo_single"),
            tr("qtype_combo_multiple"),
            tr("qtype_combo_likert"),
            tr("qtype_combo_single_other")
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        # موضع السؤال
        layout.addWidget(QLabel(tr("question_position_lbl")))
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
        g_layout.addWidget(QLabel(tr("constraint_lbl")))
        self.general_subtype_combo = QComboBox()
        self.general_subtype_combo.addItem(tr("constraint_opt_text"), "text")
        self.general_subtype_combo.addItem(tr("constraint_opt_paragraph"), "paragraph")
        self.general_subtype_combo.addItem(tr("constraint_opt_number"), "number")
        self.general_subtype_combo.addItem(tr("constraint_opt_date"), "date")
        self.general_subtype_combo.addItem(tr("constraint_opt_time"), "time")
        g_layout.addWidget(self.general_subtype_combo)
        self.ans_stack.addWidget(general_opts)

        # 1: إدخال يدوي (للديموغرافي)
        manual = QWidget()
        m_layout = QVBoxLayout(manual)
        m_layout.setContentsMargins(0, 10, 0, 0)
        self.manual_lbl = QLabel(tr("options_per_line"))
        m_layout.addWidget(self.manual_lbl)
        self.manual_edit = QTextEdit()
        self.manual_edit.setTabChangesFocus(True)
        m_layout.addWidget(self.manual_edit)
        self.ans_stack.addWidget(manual)

        # 2: اختيار مقياس (لليكرت)
        likert = QWidget()
        l_layout = QVBoxLayout(likert)
        l_layout.setContentsMargins(0, 10, 0, 0)
        l_layout.addWidget(QLabel(tr("choose_likert_scale")))
        self.scale_combo = QComboBox()
        for scale in self.template.likert_scales:
            self.scale_combo.addItem(scale.name, scale.id or id(scale))
        l_layout.addWidget(self.scale_combo)
        
        btn_manage = QPushButton(tr("btn_manage_scales"))
        btn_manage.clicked.connect(self._manage_scales)
        l_layout.addWidget(btn_manage)
        
        self.ans_stack.addWidget(likert)
        
        layout.addWidget(self.ans_stack)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText(tr("ok"))
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setText(tr("cancel"))
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_type_changed(self, index):
        if index == 0:  # عام
            self.ans_stack.setCurrentIndex(0)
        elif index in (1, 2, 4):  # ديموغرافي
            self.ans_stack.setCurrentIndex(1)
            if index == 4:
                self.manual_lbl.setText(tr("options_last_other"))
                if not self.manual_edit.toPlainText().strip():
                    self.manual_edit.setPlainText(f"{tr('default_option_1')}\n{tr('default_option_2')}\n{tr('default_option_other')}")
            else:
                self.manual_lbl.setText(tr("options_per_line"))
                if not self.manual_edit.toPlainText().strip():
                    self.manual_edit.setPlainText(f"{tr('default_option_1')}\n{tr('default_option_2')}")
        elif index == 3:  # ليكرت
            self.ans_stack.setCurrentIndex(2)

    def _manage_scales(self):
        dialog = LikertScalesManagerDialog(self.template, self)
        dialog.exec()
        self.scale_combo.clear()
        for scale in self.template.likert_scales:
            self.scale_combo.addItem(scale.name, scale.id or id(scale))

    def _validate_and_accept(self):
        if not self.text_edit.toPlainText().strip():
            QMessageBox.warning(self, tr("warning"), tr("enter_question_text_warning"))
            return
        
        idx = self.type_combo.currentIndex()
        if idx in (1, 2, 4) and not self.manual_edit.toPlainText().strip():
            QMessageBox.warning(self, tr("warning"), tr("enter_options_warning"))
            return
        
        if idx == 3 and self.scale_combo.count() == 0:
            QMessageBox.warning(self, tr("warning"), tr("no_likert_scales_warning"))
            return
            
        self.accept()

    def get_question(self) -> Question:
        qtype = QuestionType(self.type_combo.currentIndex())
        q = Question(
            text=self.text_edit.toPlainText().strip(),
            question_type=qtype,
            section_header=self.sec_header_edit.text().strip()
        )
        
        if qtype == QuestionType.GENERAL:
            subtype = self.general_subtype_combo.currentData() or "text"
            q.answers = [subtype]
        elif qtype in (QuestionType.DEMOGRAPHIC_SINGLE, QuestionType.DEMOGRAPHIC_MULTIPLE, QuestionType.DEMOGRAPHIC_SINGLE_OTHER):
            q.answers = [l.strip() for l in self.manual_edit.toPlainText().splitlines() if l.strip()]
        elif qtype == QuestionType.LIKERT:
            scale_id = self.scale_combo.currentData()
            for scale in self.template.likert_scales:
                if scale.id == scale_id or id(scale) == scale_id:
                    q.likert_scale_id = scale.id or 0
                    q.answers = list(scale.answers)
                    break
        return q

    def get_target_position(self) -> int:
        return self.pos_spin.value()


class EditQuestionDialog(QDialog):
    def __init__(self, question: Question, template: Template, parent=None):
        super().__init__(parent)
        self.question = question
        self.template = template
        self.setWindowTitle(tr("edit_question_title", text=question.text))
        self.setMinimumSize(520, 480)
        self.setLayoutDirection(get_layout_direction())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # نص السؤال
        layout.addWidget(QLabel(tr("question_text_lbl")))
        self.text_edit = QTextEdit()
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setFixedHeight(60)
        self.text_edit.setPlainText(self.question.text)
        layout.addWidget(self.text_edit)

        # فاصل مقطعي (اختياري)
        layout.addWidget(QLabel(tr("section_header_optional")))
        self.sec_header_edit = QLineEdit()
        self.sec_header_edit.setPlaceholderText(tr("section_header_placeholder"))
        self.sec_header_edit.setText(getattr(self.question, "section_header", "") or "")
        layout.addWidget(self.sec_header_edit)

        # نوع السؤال
        layout.addWidget(QLabel(tr("question_type_lbl")))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            tr("qtype_combo_general"),
            tr("qtype_combo_single"),
            tr("qtype_combo_multiple"),
            tr("qtype_combo_likert"),
            tr("qtype_combo_single_other")
        ])
        self.type_combo.setCurrentIndex(int(self.question.question_type))
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        # منطقة الإجابات (Stack)
        self.ans_stack = QStackedWidget()

        # 0: خيارات التقييد (للعام)
        general_opts = QWidget()
        g_layout = QVBoxLayout(general_opts)
        g_layout.setContentsMargins(0, 10, 0, 0)
        g_layout.addWidget(QLabel(tr("constraint_lbl")))
        self.general_subtype_combo = QComboBox()
        self.general_subtype_combo.addItem(tr("constraint_opt_text"), "text")
        self.general_subtype_combo.addItem(tr("constraint_opt_paragraph"), "paragraph")
        self.general_subtype_combo.addItem(tr("constraint_opt_number"), "number")
        self.general_subtype_combo.addItem(tr("constraint_opt_date"), "date")
        self.general_subtype_combo.addItem(tr("constraint_opt_time"), "time")

        current_subtype = self.question.answers[0] if self.question.is_general and self.question.answers else "text"
        for idx in range(self.general_subtype_combo.count()):
            if self.general_subtype_combo.itemData(idx) == current_subtype:
                self.general_subtype_combo.setCurrentIndex(idx)
                break
        g_layout.addWidget(self.general_subtype_combo)
        self.ans_stack.addWidget(general_opts)

        # 1: إدخال يدوي (للديموغرافي)
        manual = QWidget()
        m_layout = QVBoxLayout(manual)
        m_layout.setContentsMargins(0, 10, 0, 0)
        self.manual_lbl = QLabel(tr("options_per_line"))
        m_layout.addWidget(self.manual_lbl)
        self.manual_edit = QTextEdit()
        self.manual_edit.setTabChangesFocus(True)
        if not self.question.is_general and self.question.question_type != QuestionType.LIKERT:
            self.manual_edit.setPlainText("\n".join(self.question.answers))
        elif self.question.question_type == QuestionType.LIKERT:
            self.manual_edit.setPlainText("\n".join(self.question.answers))
        m_layout.addWidget(self.manual_edit)
        self.ans_stack.addWidget(manual)

        # 2: اختيار مقياس (لليكرت)
        likert = QWidget()
        l_layout = QVBoxLayout(likert)
        l_layout.setContentsMargins(0, 10, 0, 0)
        l_layout.addWidget(QLabel(tr("choose_likert_scale")))
        self.scale_combo = QComboBox()
        for scale in self.template.likert_scales:
            self.scale_combo.addItem(scale.name, scale.id or id(scale))
            if self.question.likert_scale_id == scale.id or (self.question.likert_scale_id == 0 and self.question.answers == scale.answers):
                self.scale_combo.setCurrentIndex(self.scale_combo.count() - 1)
        l_layout.addWidget(self.scale_combo)

        btn_manage = QPushButton(tr("btn_manage_scales"))
        btn_manage.clicked.connect(self._manage_scales)
        l_layout.addWidget(btn_manage)
        self.ans_stack.addWidget(likert)

        layout.addWidget(self.ans_stack)

        self._on_type_changed(int(self.question.question_type))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText(tr("ok"))
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setText(tr("cancel"))
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_type_changed(self, index):
        if index == 0:  # general
            self.ans_stack.setCurrentIndex(0)
        elif index in (1, 2, 4):  # demographic
            self.ans_stack.setCurrentIndex(1)
            if index == 4:
                self.manual_lbl.setText(tr("options_last_other"))
                if not self.manual_edit.toPlainText().strip():
                    self.manual_edit.setPlainText(f"{tr('default_option_1')}\n{tr('default_option_2')}\n{tr('default_option_other')}")
            else:
                self.manual_lbl.setText(tr("options_per_line"))
                if not self.manual_edit.toPlainText().strip():
                    self.manual_edit.setPlainText(f"{tr('default_option_1')}\n{tr('default_option_2')}")
        elif index == 3:  # likert
            self.ans_stack.setCurrentIndex(2)

    def _manage_scales(self):
        dialog = LikertScalesManagerDialog(self.template, self)
        dialog.exec()
        self.scale_combo.clear()
        for scale in self.template.likert_scales:
            self.scale_combo.addItem(scale.name, scale.id or id(scale))

    def _validate_and_accept(self):
        if not self.text_edit.toPlainText().strip():
            QMessageBox.warning(self, tr("warning"), tr("enter_question_text_warning"))
            return

        idx = self.type_combo.currentIndex()
        if idx in (1, 2, 4) and not self.manual_edit.toPlainText().strip():
            QMessageBox.warning(self, tr("warning"), tr("enter_options_warning"))
            return

        if idx == 3 and self.scale_combo.count() == 0:
            QMessageBox.warning(self, tr("warning"), tr("no_likert_scales_warning"))
            return

        self.accept()

    def apply_to_question(self, q: Question):
        q.text = self.text_edit.toPlainText().strip()
        q.section_header = self.sec_header_edit.text().strip()
        new_qtype = QuestionType(self.type_combo.currentIndex())
        q.question_type = new_qtype

        if new_qtype == QuestionType.GENERAL:
            subtype = self.general_subtype_combo.currentData() or "text"
            q.answers = [subtype]
            q.likert_scale_id = 0
            q.branching_rules = {}
        elif new_qtype in (QuestionType.DEMOGRAPHIC_SINGLE, QuestionType.DEMOGRAPHIC_MULTIPLE, QuestionType.DEMOGRAPHIC_SINGLE_OTHER):
            q.answers = [l.strip() for l in self.manual_edit.toPlainText().splitlines() if l.strip()]
            q.likert_scale_id = 0
            q.branching_rules = {ans: target for ans, target in q.branching_rules.items() if ans in q.answers}
        elif new_qtype == QuestionType.LIKERT:
            scale_id = self.scale_combo.currentData()
            for scale in self.template.likert_scales:
                if scale.id == scale_id or id(scale) == scale_id:
                    q.likert_scale_id = scale.id or 0
                    q.answers = list(scale.answers)
                    break
            q.branching_rules = {ans: target for ans, target in q.branching_rules.items() if ans in q.answers}
