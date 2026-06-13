APP_STYLESHEET = """
/* ─── عام ─────────────────────────────────────────────────────────────── */
QWidget {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #1a1a2e;
    background-color: #f5f7fa;
}

QMainWindow {
    background-color: #f5f7fa;
}

/* ─── أزرار ────────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1565C0;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: bold;
    min-height: 36px;
}
QPushButton:hover {
    background-color: #1976D2;
}
QPushButton:pressed {
    background-color: #0D47A1;
}
QPushButton:disabled {
    background-color: #B0BEC5;
    color: #78909C;
}

/* أزرار داخل خلايا الجداول - بدون min-height لتتناسب مع الصف */
QTableWidget QPushButton {
    min-height: 0px;
    padding: 4px 10px;
    font-size: 12px;
}

QPushButton#btn_secondary {
    background-color: #F0F4F8;
    color: #102A43;
    border: 1.5px solid #D9E2EC;
}
QPushButton#btn_secondary:hover {
    background-color: #D9E2EC;
    border-color: #BCCCDC;
}

QPushButton#btn_danger {
    background-color: #D32F2F;
    color: white;
    border: none;
}
QPushButton#btn_danger:hover {
    background-color: #B71C1C;
}

QPushButton#btn_success {
    background-color: #388E3C;
    color: white;
    border: none;
}
QPushButton#btn_success:hover {
    background-color: #2E7D32;
}

/* ─── حقول الإدخال ─────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: white;
    border: 1.5px solid #CFD8DC;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #1565C0;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #1565C0;
}

/* ─── جداول ────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: white;
    border: 1px solid #CFD8DC;
    border-radius: 6px;
    gridline-color: #ECEFF1;
    selection-background-color: #E3F2FD;
    selection-color: #1a1a2e;
}
QTableWidget::item {
    padding: 6px 10px;
}
QHeaderView::section {
    background-color: #1565C0;
    color: white;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-right: 1px solid #1976D2;
}

/* ─── قوائم ────────────────────────────────────────────────────────────── */
QListWidget {
    background-color: white;
    border: 1px solid #CFD8DC;
    border-radius: 6px;
}
QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #ECEFF1;
}
QListWidget::item:selected {
    background-color: #E3F2FD;
    color: #1a1a2e;
}
QListWidget::item:hover {
    background-color: #F5F5F5;
}

/* ─── ComboBox ──────────────────────────────────────────────────────────── */
QComboBox {
    background-color: white;
    border: 1.5px solid #CFD8DC;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 32px;
}
QComboBox:focus {
    border-color: #1565C0;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* ─── شريط التقدم ───────────────────────────────────────────────────────── */
QProgressBar {
    border: none;
    border-radius: 6px;
    background-color: #ECEFF1;
    height: 12px;
    text-align: center;
    font-size: 11px;
    color: #37474F;
}
QProgressBar::chunk {
    background-color: #1565C0;
    border-radius: 6px;
}

/* ─── تبويبات ───────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #CFD8DC;
    border-radius: 6px;
    background-color: white;
}
QTabBar::tab {
    background-color: #ECEFF1;
    color: #546E7A;
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #1565C0;
    color: white;
}

/* ─── مجموعات ───────────────────────────────────────────────────────────── */
QGroupBox {
    border: 1.5px solid #CFD8DC;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: #1565C0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
    right: 12px;
}

/* ─── شريط الحالة ───────────────────────────────────────────────────────── */
QStatusBar {
    background-color: #1565C0;
    color: white;
    font-size: 12px;
    padding: 2px 8px;
}

/* ─── Splitter ──────────────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #CFD8DC;
    width: 2px;
}

/* ─── ScrollBar ─────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    border: none;
    background: #ECEFF1;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #90A4AE;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #607D8B;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""
