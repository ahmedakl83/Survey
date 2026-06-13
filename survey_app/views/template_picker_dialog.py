from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QFrame
)
from PyQt6.QtCore import Qt

from models.template import Template


class TemplatePickerDialog(QDialog):
    """
    حوار لاختيار قالب من القوالب المحفوظة.
    يُستخدم عند استيراد ملف إجابات رقمية.
    """

    def __init__(self, templates: List[Template], parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختر القالب")
        self.setMinimumSize(480, 380)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._templates = templates
        self._selected: Optional[Template] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ─── العنوان ──────────────────────────────────────────────────────────
        title = QLabel("اختر القالب الذي يتوافق مع ملف الإجابات:")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1565C0;")
        layout.addWidget(title)

        hint = QLabel(
            "يجب أن تتطابق أسماء الأعمدة في ملف الإجابات مع أسماء الأسئلة في القالب."
        )
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
            item = QListWidgetItem(
                f"{t.name}  —  {t.question_count} سؤال  |  "
                f"استُخدم {t.use_count} مرة  |  "
                f"{t.updated_at.strftime('%Y-%m-%d')}"
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
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("اختيار")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
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
