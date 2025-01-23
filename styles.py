"""
Styles for the PING Optimizer application.
Contains all Qt StyleSheet definitions and theme colors.
"""

# Theme Colors
CYAN = "#00ffff"
BLACK = "#000000"
TRANSPARENT_BLACK = "rgba(0, 0, 0, 0.7)"
TRANSPARENT_CYAN = "rgba(0, 255, 255, 0.3)"

# Main Window Style
MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: black;
    }
"""

# Tab Widget Style
TAB_WIDGET_STYLE = """
    QTabWidget::pane {
        border: none;
        background: transparent;
    }
    QTabBar::tab {
        background: rgba(0, 0, 0, 0.7);
        color: #00ffff;
        border: 1px solid #00ffff;
        border-radius: 10px;
        padding: 12px 30px;
        margin-right: 8px;
        font-size: 16px;
        font-weight: bold;
        min-width: 180px;
        text-align: center;
    }
    QTabBar::tab:selected {
        background: rgba(0, 255, 255, 0.1);
        border: 1px solid #00ffff;
    }
    QTabBar::tab:hover {
        background: rgba(0, 255, 255, 0.05);
    }
"""

# Frame Styles
TRANSPARENT_FRAME_STYLE = """
    QFrame {
        background-color: rgba(0, 0, 0, 0.5);
        border: 2px solid rgba(0, 255, 255, 0.3);
        border-radius: 15px;
        padding: 15px;
    }
"""

# Ping Statistics Frame Style
PING_STATS_FRAME_STYLE = """
    QFrame {
        background: rgba(0, 0, 0, 0.7);
        border: 2px solid rgba(0, 255, 255, 0.3);
        border-radius: 15px;
        padding: 20px;
    }
"""

# Stats Box Style (for individual ping values)
STATS_BOX_STYLE = """
    QFrame {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        padding: 15px;
        margin: 5px;
    }
"""

# Value Display Styles
VALUE_DISPLAY_STYLE = """
    QLabel {
        color: #00ffff;
        font-size: 24px;
        font-weight: bold;
        background-color: rgba(0, 0, 0, 0.5);
        border: 2px solid #00ffff;
        border-radius: 10px;
        padding: 10px 20px;
        min-width: 120px;
    }
"""

CURRENT_VALUE_DISPLAY_STYLE = """
    QLabel {
        color: #00ff00;
        font-family: 'Segoe UI', sans-serif;
        font-size: 48px;
        font-weight: bold;
        padding: 15px;
    }
"""

# Label Styles
TITLE_LABEL_STYLE = """
    QLabel {
        color: #00ffff;
        font-size: 20px;
        font-weight: bold;
        padding: 5px;
    }
"""

HEADING_LABEL_STYLE = """
    QLabel {
        color: #00ffff;
        font-size: 16px;
        font-weight: bold;
        padding: 5px;
    }
"""

SUBHEADING_LABEL_STYLE = """
    QLabel {
        color: rgba(0, 255, 255, 0.7);
        font-family: 'Segoe UI', sans-serif;
        font-size: 16px;
        font-weight: 500;
        padding: 5px;
    }
"""

SUCCESS_LABEL_STYLE = """
    QLabel {
        color: #00ff00;  /* Green color for success */
        font-size: 16px;
        font-weight: bold;
    }
"""

# Button Styles
BUTTON_STYLE = """
    QPushButton {
        background-color: rgba(0, 0, 0, 0.7);
        color: #00ffff;
        border: 2px solid #00ffff;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
        min-width: 150px;
        min-height: 40px;
    }
    QPushButton:hover {
        background-color: rgba(0, 255, 255, 0.1);
    }
    QPushButton:pressed {
        background-color: rgba(0, 255, 255, 0.2);
    }
    QPushButton:disabled {
        color: rgba(0, 255, 255, 0.3);
        border-color: rgba(0, 255, 255, 0.3);
        background-color: rgba(0, 0, 0, 0.5);
    }
"""

PRIMARY_BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                  stop:0 #00ffff, 
                                  stop:1 #00ff00);
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 15px 30px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 16px;
        font-weight: bold;
        min-width: 180px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                  stop:0 #4DFFF3, 
                                  stop:1 #00ff00);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                  stop:0 #00ffff, 
                                  stop:1 #00cc00);
    }
    QPushButton:disabled {
        background: rgba(128, 128, 128, 0.2);
        color: rgba(255, 255, 255, 0.3);
    }
"""

# ComboBox Style
COMBO_BOX_STYLE = """
    QComboBox {
        background: rgba(0, 0, 0, 0.7);
        color: #00ffff;
        border: 1px solid #00ffff;
        border-radius: 8px;
        padding: 8px 15px;
        min-width: 200px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        image: none;
    }
    QComboBox:on {
        border: 1px solid #00ff00;
    }
    QComboBox QAbstractItemView {
        background: rgba(0, 0, 0, 0.9);
        color: #00ffff;
        selection-background-color: rgba(0, 255, 255, 0.2);
        border: 1px solid #00ffff;
    }
"""

# Progress Bar Style
PROGRESS_BAR_STYLE = """
    QProgressBar {
        border: 1px solid #00ffff;
        border-radius: 5px;
        text-align: center;
        color: #00ffff;
    }
    QProgressBar::chunk {
        background-color: rgba(0, 255, 255, 0.3);
    }
"""

# Checkbox Style
CHECKBOX_STYLE = """
    QCheckBox {
        color: #00ffff;
        spacing: 8px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }
    QCheckBox::indicator {
        width: 24px;
        height: 24px;
        background-color: rgba(0, 0, 0, 0.7);
        border: 1px solid #00ffff;
        border-radius: 6px;
    }
    QCheckBox::indicator:checked {
        background-color: rgba(0, 255, 255, 0.3);
        border: 1px solid #00ff00;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #00ff00;
    }
"""

# Input Style
INPUT_STYLE = """
    QLineEdit {
        background: rgba(0, 0, 0, 0.7);
        color: #00ffff;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 8px;
        padding: 12px 20px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        min-height: 20px;
    }
    QLineEdit:focus {
        border: 1px solid #00ffff;
        background: rgba(0, 0, 0, 0.9);
    }
    QLineEdit::placeholder {
        color: rgba(0, 255, 255, 0.5);
    }
"""

# Glass Panel Style
GLASS_PANEL_STYLE = """
    QFrame {
        background-color: rgba(0, 0, 0, 0.7);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        padding: 20px;
    }
"""

# Popup Style
POPUP_STYLE = """
    QLabel {
        background-color: rgba(0, 0, 0, 0.8);
        color: #00ffff;
        border: 2px solid #00ffff;
        border-radius: 15px;
        padding: 15px 30px;
        font-size: 16px;
        font-weight: bold;
    }
"""
