from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QFrame
)
from PyQt6.QtCore import Qt

from models.template import Template
from utils.translator import tr, get_layout_direction


class TemplatePickerDialog(QDialog):
    """
    حوار لاختيار قالب من القوالب المحفوظة.
    يُستخدم عند استيراد ملف إجابات رقمية.
    """

    def __init__(self, templates: List[Template], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("template_picker_title"))
        self.setMinimumSize(480, 380)
        self.setLayoutDirection(get_layout_direction())
        self._templates = templates
        self._selected: Optional[Template] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ─── العنوان ──────────────────────────────────────────────────────────
        title = QLabel(tr("template_picker_heading"))
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1565C0;")
        layout.addWidget(title)

        hint = QLabel(tr("template_picker_hint"))
        hint.setStyleSheet("color: #546E7A; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ─── قائمة القوالب ────────────────────────────────────────────────────
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget::item { padding: 10px 12px; border-bottom: 1px solid #ECEFF1; }"
            "QListWidget::item:selected { background-color: #1565C0; color: white; }"
            "QListWidget::item:hover { background-color: #E3F2FD; }"
        )
        self.list_widget.itemDoubleClicked.connect(self._on_double_click)

        for t in self._templates:
            q_count_str = tr("questions_num", count=t.question_count)
            use_count_str = tr("used_num_times", count=t.use_count)
            item = QListWidgetItem(
                f"{t.name}  —  {q_count_str}  |  {use_count_str}  |  {t.updated_at.strftime('%Y-%m-%d')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        layout.addWidget(self.list_widget)

        # ─── الأزرار ──────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText(tr("btn_select"))
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setText(tr("cancel"))
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        current = self.list_widget.currentItem()
        if current is None:
            return
        template_id = current.data(Qt.ItemDataRole.UserRole)
        self._selected = next((t for t in self._templates if t.id == template_id), None)
        self.accept()

    def _on_double_click(self, item: QListWidgetItem):
        self._on_accept()

    def selected_template(self) -> Optional[Template]:
        return self._selected
