from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QPushButton
)
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager
from utils.translator import tr, is_rtl, get_layout_direction


class StatisticsView(QWidget):
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

        self.title = QLabel(tr("stats_title"))
        self.title.setStyleSheet("color: white; font-size: 17px; font-weight: bold;")
        h_layout.addWidget(self.title)
        h_layout.addStretch()

        root.addWidget(header)

        # ─── المحتوى ──────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        root.addWidget(scroll)

        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(32, 24, 32, 24)
        self.layout.setSpacing(24)

    def refresh(self):
        self.setLayoutDirection(get_layout_direction())
        self.btn_back.setText(tr("back"))
        self.title.setText(tr("stats_title"))

        # مسح المحتوى الحالي
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = self.db.get_overall_stats()

        # ─── بطاقات الأرقام الكبيرة ───────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(16)

        grid.addWidget(self._make_stat_card(tr("stat_total_templates"), str(stats["templates_count"]), "#1976D2"), 0, 0)
        grid.addWidget(self._make_stat_card(tr("stat_total_sessions"), str(stats["sessions_count"]), "#388E3C"), 0, 1)
        grid.addWidget(self._make_stat_card(tr("stat_completed_forms"), str(stats["completed_forms"]), "#F57C00"), 1, 0)
        
        avg_time_str = tr("seconds_unit", count=stats["avg_form_time"])
        grid.addWidget(self._make_stat_card(tr("stat_avg_form_time"), avg_time_str, "#7B1FA2"), 1, 1)

        self.layout.addLayout(grid)

        # ─── القوالب الأكثر استخداماً ──────────────────────────────────────────
        top_label = QLabel(tr("top_used_templates"))
        top_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0; margin-top: 12px;")
        self.layout.addWidget(top_label)

        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #CFD8DC;")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(16, 16, 16, 16)
        top_layout.setSpacing(12)

        if not stats["top_templates"]:
            top_layout.addWidget(QLabel(tr("no_data_yet")))
        else:
            for t in stats["top_templates"]:
                row = QHBoxLayout()
                name_lbl = QLabel(t["name"])
                name_lbl.setStyleSheet("font-weight: bold; border: none;")
                row.addWidget(name_lbl)
                row.addStretch()
                count_lbl = QLabel(tr("times_unit", count=t["count"]))
                count_lbl.setStyleSheet("color: #546E7A; border: none;")
                row.addWidget(count_lbl)
                
                row_widget = QWidget()
                row_widget.setLayout(row)
                row_widget.setStyleSheet("border: none; border-bottom: 1px solid #ECEFF1;")
                top_layout.addWidget(row_widget)

        self.layout.addWidget(top_frame)
        self.layout.addStretch()

    def _make_stat_card(self, title, value, color) -> QFrame:
        card = QFrame()
        accent_side = "border-right" if is_rtl() else "border-left"
        other_sides = "border-left: 1px solid #CFD8DC;" if is_rtl() else "border-right: 1px solid #CFD8DC;"
        card.setStyleSheet(
            f"QFrame {{ background-color: white; border-radius: 12px; "
            f"{accent_side}: 5px solid {color}; border-top: 1px solid #CFD8DC; "
            f"{other_sides} border-bottom: 1px solid #CFD8DC; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #546E7A; font-size: 13px; border: none;")
        layout.addWidget(title_lbl)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(val_lbl)

        return card
