import sys
import os
import subprocess
import threading
import time
import re
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame, QLineEdit, QGridLayout,
                           QMessageBox, QApplication, QComboBox, QTabWidget, 
                           QRadioButton, QButtonGroup, QScrollArea, QProgressBar, 
                           QSizePolicy, QCheckBox)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPalette
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QRect, QEasingCurve
import logging
import psutil

# Configure logging
logging.basicConfig(filename='tcp_optimizer.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ModernTheme:
    # Color scheme
    PRIMARY_BG = "rgba(26, 26, 46, 0.90)"  # Less transparent dark blue
    SECONDARY_BG = "rgba(38, 38, 68, 0.95)"  # Less transparent lighter blue
    ACCENT = "#ffffff"  # White
    TEXT_PRIMARY = "#ffffff"  # White
    TEXT_SECONDARY = "#ffffff"  # White
    BUTTON_PRIMARY = "#ff69b4"  # Pink
    BUTTON_HOVER = "#ff8ac1"    # Lighter pink
    BUTTON_PRESSED = "#ff5ba7"  # Darker pink
    SUCCESS = "#4caf50"  # Green
    ERROR = "#f44336"  # Red
    
    # Styles
    GLASS_PANEL = """
        QFrame#glassFrame {
            background-color: rgba(0, 0, 0, 0.4);  
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            padding: 25px;
        }
    """
    
    SECTION_TITLE = """
        font-size: 22px;
        font-weight: 800;
        color: white;
        padding: 15px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 20px;
    """
    
    DNS_OPTION = """
        QRadioButton {
            color: white;
            font-size: 13px;
            padding: 5px;
            margin: 2px 0;
        }
        QRadioButton::indicator {
            width: 15px;
            height: 15px;
        }
    """
    
    TCP_SETTINGS = """
        QLabel {
            color: #ffd700;  
            font-size: 18px;
            font-family: 'Consolas', monospace;
            font-weight: 600;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.4);  
            border-radius: 10px;
            margin: 5px;
            border: 1px solid rgba(255, 215, 0, 0.4);
            line-height: 1.4;  
        }
    """
    
    TCP_CARD = """
        QFrame#tcpCard {
            background-color: rgba(255, 255, 255, 0.15);
            border: 2px solid rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 25px;
        }
    """
    
    TCP_STATUS = """
        QLabel {
            color: white;
            font-size: 18px;
            font-weight: 600;
            padding: 15px;
            background-color: rgba(0, 0, 0, 0.4);  
            border-radius: 10px;
            margin: 5px 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    """
    
    STATS_LABEL = """
        QLabel {
            color: #00ffff;  
            font-size: 16px;
            font-weight: 600;
            padding: 8px;
            background-color: rgba(0, 0, 0, 0.3);  
            border-radius: 8px;
            text-transform: uppercase;  
            letter-spacing: 1px;  
        }
    """
    
    VALUE_DISPLAY = """
        QLabel {
            color: #00ff00;
            font-size: 20px;
            font-weight: 600;
            padding: 15px;
            background-color: rgba(0, 0, 0, 0.5);
            border: 2px solid rgba(0, 255, 0, 0.4);
            border-radius: 12px;
            min-width: 120px;
            min-height: 50px;
        }
    """
    
    UNIT_LABEL = """
        QLabel {
            color: #00ffff;  
            font-size: 12px;
            font-weight: bold;
            padding: 5px 10px;
            background-color: rgba(0, 0, 0, 0.7);  
            border-radius: 6px;
            border: 1px solid rgba(0, 255, 255, 0.4);  
        }
    """
    
    BUTTON_STYLE = """
        QPushButton {
            background-color: rgba(255, 105, 180, 0.8);
            color: white;
            border: none;
            padding: 15px 32px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 10px;
            margin-top: 15px;
        }
        QPushButton:hover {
            background-color: rgba(255, 105, 180, 1.0);
        }
        QPushButton:pressed {
            background-color: rgba(255, 20, 147, 1.0);
        }
    """
    
    OPTIMIZE_BUTTON = """
        QPushButton {
            background-color: rgba(255, 105, 180, 0.8);
            color: white;
            border: none;
            padding: 20px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 10px;
            margin-top: 15px;
        }
        QPushButton:hover {
            background-color: rgba(255, 105, 180, 1.0);
        }
        QPushButton:pressed {
            background-color: rgba(255, 20, 147, 1.0);
        }
    """
    
    INPUT_STYLE = """
        QLineEdit {
            background-color: rgba(0, 0, 0, 0.4);
            color: white;
            border: 2px solid rgba(0, 255, 255, 0.3);
            border-radius: 10px;
            padding: 12px;
            font-size: 16px;
            font-weight: 600;
        }
        QLineEdit:focus {
            border: 2px solid rgba(0, 255, 255, 0.8);
        }
        QLineEdit::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
    """

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassFrame")
        self.setStyleSheet(ModernTheme.GLASS_PANEL)
        
        # Add only shadow effect for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

class ValueDisplay(QFrame):
    def __init__(self, label, unit=''):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.6);
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 10px;
                padding: 8px;
            }
        """)
        
        # Set size policy to allow horizontal expansion
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Label at the top
        self.label = QLabel(label)
        self.label.setStyleSheet("""
            QLabel {
                color: #00ff99;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Value in the middle
        self.value = QLabel("--")
        self.value.setStyleSheet(ModernTheme.VALUE_DISPLAY)
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setWordWrap(True)  
        layout.addWidget(self.value)

    def setValue(self, value):
        if isinstance(value, (int, float)):
            self.value.setText(f"{value:.1f}")
        else:
            self.value.setText(str(value))

class TCPOptimizerQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCP Optimizer Pro")
        self.setGeometry(150, 150, 1400, 900)
        
        # Initialize variables
        self.running_ping = False
        self.ping_stats = {
            'current': '--',
            'min': '--',
            'max': '--',
            'avg': '--'
        }
        # Store baseline ping stats for improvement calculation
        self.baseline_ping = None
        self.current_ping = None
        self.interface_combo = None  
        self.tcp_optimized = False  # Flag to track TCP optimization
        
        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Left Panel (DNS Settings)
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_panel.setStyleSheet("""
            QFrame#leftPanel {
                background-color: rgba(0, 0, 0, 0.4);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        # Left Panel Layout
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(25)
        left_layout.setContentsMargins(30, 30, 30, 30)
        
        # Ping Statistics Section
        ping_stats_frame = QFrame()
        ping_stats_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 20, 20, 0.7);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 15px;
                padding: 25px;
            }
        """)
        ping_stats_layout = QVBoxLayout(ping_stats_frame)
        ping_stats_layout.setSpacing(20)
        ping_stats_layout.setContentsMargins(15, 15, 15, 15)
        
        # Ping Stats Title
        ping_title = QLabel("Ping Statistics")
        ping_title.setStyleSheet("""
            QLabel {
                color: #00ffff;
                font-size: 20px;
                font-weight: 600;
                padding: 5px;
                margin-bottom: 10px;
            }
        """)
        ping_stats_layout.addWidget(ping_title, 0, Qt.AlignCenter)
        
        # Grid layout for ping stats with better spacing
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        stats_grid.setContentsMargins(10, 10, 10, 10)
        
        # Create ping stat displays with improved styling
        self.ping_displays = {}
        stats = [
            ("Current", "ms"),
            ("Minimum", "ms"),
            ("Maximum", "ms"),
            ("Average", "ms")
        ]
        
        for i, (label, unit) in enumerate(stats):
            display = ValueDisplay(label.lower(), unit)
            self.ping_displays[label.lower()] = display
            # Arrange in 2x2 grid with proper spacing
            stats_grid.addWidget(display, i // 2, i % 2, Qt.AlignCenter)
        
        ping_stats_layout.addLayout(stats_grid)
        
        # Measure Ping Button with improved styling
        self.measure_ping_btn = QPushButton("Measure Ping")
        self.measure_ping_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        self.measure_ping_btn.clicked.connect(self.start_ping)
        ping_stats_layout.addWidget(self.measure_ping_btn, 0, Qt.AlignCenter)
        
        left_layout.addWidget(ping_stats_frame)

        # DNS Settings Section with improved styling
        dns_frame = QFrame()
        dns_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 20, 20, 0.7);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 15px;
                padding: 25px;
            }
        """)
        dns_layout = QVBoxLayout(dns_frame)
        dns_layout.setSpacing(20)
        dns_layout.setContentsMargins(15, 15, 15, 15)
        
        # DNS Settings Title
        dns_title = QLabel("DNS Settings")
        dns_title.setStyleSheet("""
            QLabel {
                color: #00ffff;
                font-size: 20px;
                font-weight: 600;
                padding: 5px;
                margin-bottom: 10px;
            }
        """)
        dns_layout.addWidget(dns_title, 0, Qt.AlignCenter)

        # DNS Servers Input with improved styling
        dns_input_layout = QHBoxLayout()
        dns_input_layout.setSpacing(15)
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("Enter DNS servers (comma-separated)")
        self.dns_input.setStyleSheet(ModernTheme.INPUT_STYLE)
        dns_input_layout.addWidget(self.dns_input)
        
        # Apply DNS Button with improved styling
        apply_dns_btn = QPushButton("Apply DNS")
        apply_dns_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        apply_dns_btn.clicked.connect(self.apply_dns_settings)
        dns_input_layout.addWidget(apply_dns_btn)
        dns_layout.addLayout(dns_input_layout)
        
        # DNS Status Label with improved styling
        self.dns_status_label = QLabel("")
        self.dns_status_label.setWordWrap(True)
        self.dns_status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                padding: 10px;
                font-size: 14px;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        dns_layout.addWidget(self.dns_status_label)
        
        left_layout.addWidget(dns_frame)
        left_layout.addStretch()

        # Right Panel (TCP Settings)
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_panel.setStyleSheet("""
            QFrame#rightPanel {
                background-color: rgba(0, 0, 0, 0.4);
                border-radius: 15px;
                padding: 20px;
                min-width: 500px;
            }
        """)
        
        # Add panels to main layout with stretch
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
        
        # Set background image
        self.set_background_image()
        
        # Create panels
        self.create_right_panel(right_panel)
        
        # Set window attributes for transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Initialize ping process and timer
        self.ping_process = None
        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.update_ping_stats)
        self.ping_values = []

        # Check initial TCP settings
        self.check_initial_tcp_settings()

    def set_background_image(self):
        try:
            # Create background label
            self.bg_label = QLabel(self)
            self.bg_label.setObjectName("bgLabel")
            
            # Load and scale background image using absolute path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            background_path = os.path.join(current_dir, "background.jpg")
            
            background_image = QPixmap(background_path)
            if not background_image.isNull():
                scaled_image = background_image.scaled(
                    self.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                self.bg_label.setPixmap(scaled_image)
                self.bg_label.setGeometry(0, 0, self.width(), self.height())
                
                # Add semi-transparent overlay
                self.bg_label.setStyleSheet("""
                    QLabel#bgLabel {
                        background-color: rgba(0, 0, 0, 0.3);
                    }
                """)
                
                # Ensure background stays behind other widgets
                self.bg_label.lower()
            else:
                logging.error(f"Failed to load background image from {background_path}")
                
        except Exception as e:
            logging.error(f"Error setting background: {str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'bg_label'):
            # Update background image size using absolute path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            background_path = os.path.join(current_dir, "background.jpg")
            bg_image = QPixmap(background_path)
            if not bg_image.isNull():
                source_rect = QRect(-200, 0, bg_image.width(), bg_image.height())
                scaled_image = bg_image.copy(source_rect).scaled(
                    self.width(), self.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                self.bg_label.setPixmap(scaled_image)
                self.bg_label.setGeometry(0, 0, self.width(), self.height())
    
    def create_right_panel(self, right_panel):
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # Create tabs for different optimizations
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(0, 255, 255, 0.2);
                background: rgba(0, 0, 0, 0.4);
                border-radius: 10px;
            }
            QTabBar::tab {
                background: rgba(0, 0, 0, 0.6);
                color: #00ffff;
                padding: 10px 15px;
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: rgba(0, 0, 0, 0.8);
                border-bottom: 2px solid #00ffff;
            }
            QTabBar::tab:hover {
                background: rgba(0, 0, 0, 0.7);
            }
        """)

        # TCP Optimization Tab
        tcp_tab = QWidget()
        tcp_layout = QVBoxLayout(tcp_tab)
        self.setup_tcp_tab(tcp_layout)
        tabs.addTab(tcp_tab, "TCP Settings")

        # Network Interface Tab
        interface_tab = QWidget()
        interface_layout = QVBoxLayout(interface_tab)
        self.setup_interface_tab(interface_layout)
        tabs.addTab(interface_tab, "Network Interface")

        # Game Mode Tab
        game_tab = QWidget()
        game_layout = QVBoxLayout(game_tab)
        self.setup_game_tab(game_layout)
        tabs.addTab(game_tab, "Game Mode")

        right_layout.addWidget(tabs)

    def setup_tcp_tab(self, layout):
        # Create main frame
        main_frame = QFrame()
        main_frame.setObjectName("tcpFrame")
        main_frame.setStyleSheet("""
            QFrame#tcpFrame {
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        # Create layout for main frame
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setSpacing(20)
        
        # Status label
        self.tcp_status = QLabel("TCP Settings: Default")
        self.tcp_status.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 600;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 10px;
            }
        """)
        self.tcp_status.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.tcp_status)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 5px;
                text-align: center;
                background-color: rgba(0, 0, 0, 0.3);
                color: white;
            }
            QProgressBar::chunk {
                background-color: #ff69b4;
                border-radius: 3px;
            }
        """)
        self.progress_bar.hide()
        frame_layout.addWidget(self.progress_bar)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Optimize button
        self.optimize_btn = QPushButton("OPTIMIZE TCP SETTINGS")
        self.optimize_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        self.optimize_btn.clicked.connect(self.optimize_tcp)
        button_layout.addWidget(self.optimize_btn)
        
        # Revert button
        self.revert_btn = QPushButton("REVERT TO DEFAULT")
        self.revert_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        self.revert_btn.clicked.connect(self.revert_tcp_settings)
        self.revert_btn.setEnabled(False)
        button_layout.addWidget(self.revert_btn)
        
        frame_layout.addLayout(button_layout)
        layout.addWidget(main_frame)

    def setup_interface_tab(self, layout):
        # Main frame for interface settings
        interface_frame = QFrame()
        interface_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        interface_layout = QVBoxLayout(interface_frame)
        interface_layout.setSpacing(15)

        # Network interface selection
        self.interface_combo = QComboBox()
        self.interface_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(0, 0, 0, 0.4);
                color: white;
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 5px;
                padding: 5px;
                min-width: 200px;
                height: 30px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid rgba(0, 0, 0, 0);
                border-right: 5px solid rgba(0, 0, 0, 0);
                border-top: 5px solid white;
                width: 0;
                height: 0;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                selection-background-color: rgba(0, 255, 255, 0.2);
                selection-color: white;
            }
        """)
        
        # Populate interface combo
        for iface in psutil.net_if_addrs().keys():
            self.interface_combo.addItem(iface)
        
        interface_layout.addWidget(QLabel("Select Network Interface:"))
        interface_layout.addWidget(self.interface_combo)

        # Apply button
        apply_btn = QPushButton("Apply Interface Settings")
        apply_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        apply_btn.clicked.connect(self.apply_interface_settings)
        interface_layout.addWidget(apply_btn)

        layout.addWidget(interface_frame)

    def setup_game_tab(self, layout):
        # Game Mode Options
        game_frame = QFrame()
        game_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        game_layout = QVBoxLayout(game_frame)
        game_layout.setSpacing(15)

        # Game Mode Button
        game_mode_btn = QPushButton("Enable Game Mode")
        game_mode_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        game_mode_btn.clicked.connect(self.apply_game_settings)
        game_layout.addWidget(game_mode_btn)

        # QoS Button
        qos_btn = QPushButton("Optimize QoS Settings")
        qos_btn.setStyleSheet(ModernTheme.BUTTON_STYLE)
        qos_btn.clicked.connect(self.optimize_qos)
        game_layout.addWidget(qos_btn)

        layout.addWidget(game_frame)

    def start_ping(self):
        if not self.ping_process:
            try:
                # Kill any existing ping process
                if hasattr(self, 'ping_process') and self.ping_process:
                    self.ping_process.kill()
                    self.ping_process = None

                # Start new ping process
                self.ping_process = subprocess.Popen(
                    ['ping', '8.8.8.8', '-t'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Clear previous values
                self.ping_values = []
                
                # Start the timer to read ping output
                self.ping_timer.start(100)  
                
                self.measure_ping_btn.setText("Stop Ping")
                
            except Exception as e:
                print(f"Error starting ping: {str(e)}")
        else:
            self.stop_ping()

    def stop_ping(self):
        if self.ping_process:
            self.ping_timer.stop()
            self.ping_process.kill()
            self.ping_process = None
            self.measure_ping_btn.setText("Measure Ping")
            
    def update_ping_stats(self):
        if not self.ping_process:
            return
            
        try:
            # Read the latest ping output
            line = self.ping_process.stdout.readline().strip()
            
            if line:
                # Extract ping time using regex
                match = re.search(r'time[=<](\d+)ms', line)
                if match:
                    ping_time = int(match.group(1))
                    self.ping_values.append(ping_time)
                    
                    # Keep only last 100 values
                    if len(self.ping_values) > 100:
                        self.ping_values.pop(0)
                    
                    # Calculate statistics
                    current = ping_time
                    avg = sum(self.ping_values) / len(self.ping_values)
                    min_ping = min(self.ping_values)
                    max_ping = max(self.ping_values)
                    
                    # Update current ping average for improvement calculation
                    self.current_ping = avg
                    
                    # Calculate improvement if baseline exists and TCP optimization was performed
                    improvement_text = ""
                    if hasattr(self, 'tcp_optimized') and self.tcp_optimized and self.baseline_ping is not None and self.current_ping is not None:
                        improvement = ((self.baseline_ping - self.current_ping) / self.baseline_ping) * 100
                        logging.info(f"Ping Improvement Calculation: Baseline={self.baseline_ping:.1f}ms, Current={self.current_ping:.1f}ms, Improvement={improvement:.1f}%")
                        if improvement > 0:
                            improvement_text = f" (⬆️ {improvement:.1f}%)"
                        elif improvement < 0:
                            improvement_text = f" (⬇️ {abs(improvement):.1f}%)"
                    
                    # Store baseline if not set
                    if self.baseline_ping is None:
                        self.baseline_ping = avg
                    
                    # Update all stats displays with proper formatting
                    stats_updates = {
                        'current': f"{current:.1f}",
                        'minimum': f"{min_ping:.1f}",
                        'maximum': f"{max_ping:.1f}",
                        'average': f"{avg:.1f}{improvement_text}"
                    }
                    
                    for key, value in stats_updates.items():
                        if key in self.ping_displays:
                            self.ping_displays[key].setValue(f"{value} ms")
                    
                    # Log stats for debugging
                    logging.debug(f"Ping stats - Current: {current:.1f}ms, Min: {min_ping:.1f}ms, Max: {max_ping:.1f}ms, Avg: {avg:.1f}ms{improvement_text}")
                    
        except Exception as e:
            logging.error(f"Error updating ping stats: {str(e)}")

    def optimize_tcp(self):
        try:
            # Log baseline ping before optimization
            baseline = self.current_ping if self.current_ping else "N/A"
            logging.info(f"\n=== TCP OPTIMIZATION IMPACT ===")
            logging.info(f"Baseline Ping: {baseline}ms")

            # First, explicitly check admin rights
            import ctypes, sys
            if not ctypes.windll.shell32.IsUserAnAdmin():
                QMessageBox.warning(self, "Admin Rights Required", 
                    "Please run the application as administrator.\n"
                    "Right-click the application and select 'Run as administrator'")
                return

            self.progress_bar.setValue(0)
            self.progress_bar.show()
            
            # First, check available congestion providers
            try:
                check_result = subprocess.run(
                    ['netsh', 'int', 'tcp', 'show', 'global'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logging.debug(f"Current TCP settings: {check_result.stdout}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to check TCP settings: {e.stderr}")
            
            # Try alternative optimization commands
            commands = [
                # Optimize TCP window size
                ['netsh', 'interface', 'tcp', 'set', 'global', 'autotuning=normal'],
                # Disable TCP chimney offload
                ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=disabled'],
                # Disable ECN capability
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecncapability=disabled'],
                # Optimize TCP timestamps
                ['netsh', 'int', 'tcp', 'set', 'global', 'timestamps=disabled'],
                # Set initial RTO (Retransmission Timeout)
                ['netsh', 'int', 'tcp', 'set', 'global', 'initialRto=2000'],
                # Enable RSS (Receive Side Scaling)
                ['netsh', 'int', 'tcp', 'set', 'global', 'rss=enabled']
            ]
            
            total_commands = len(commands)
            for i, cmd in enumerate(commands, 1):
                try:
                    # Store ping before the command
                    before_ping = self.current_ping
                    
                    # Execute command
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    progress = int((i / total_commands) * 100)
                    self.progress_bar.setValue(progress)
                    
                    # Wait briefly for the change to take effect
                    time.sleep(1)
                    
                    # Log the impact of this setting
                    if before_ping and self.current_ping:
                        change = ((before_ping - self.current_ping) / before_ping) * 100
                        logging.info(f"TCP Setting Impact - Command: {' '.join(cmd)}")
                        logging.info(f"  Before: {before_ping:.1f}ms, After: {self.current_ping:.1f}ms, Change: {change:.1f}%")
                    
                    QApplication.processEvents()
                    
                except subprocess.CalledProcessError as e:
                    logging.error(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    continue
            
            # Verify the changes
            try:
                verify_result = subprocess.run(
                    ['netsh', 'int', 'tcp', 'show', 'global'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logging.debug(f"TCP settings after optimization: {verify_result.stdout}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to verify TCP settings: {e.stderr}")
            
            # Log final ping after optimization
            final = self.current_ping if self.current_ping else "N/A"
            improvement = ((baseline - final) / baseline * 100) if baseline != "N/A" and final != "N/A" else "N/A"
            logging.info(f"Final Ping: {final}ms")
            logging.info(f"TCP Optimization Impact: {improvement:.1f}% improvement")
            logging.info("================================\n")
            
            self.update_settings_display()
            self.progress_bar.setValue(100)
            self.tcp_optimized = True  # Set flag to indicate TCP optimization
            QMessageBox.information(self, "Success", "TCP settings have been optimized successfully!")
            
        except Exception as e:
            logging.error(f"Unexpected error during TCP optimization: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"An unexpected error occurred:\n{str(e)}")
        finally:
            self.progress_bar.hide()

    def revert_tcp_settings(self):
        try:
            self.progress_bar.setValue(0)
            self.progress_bar.show()

            # Check if running as administrator
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                QMessageBox.warning(
                    self,
                    "Administrator Rights Required",
                    "This operation requires administrator privileges.\n"
                    "Please run the application as administrator."
                )
                self.progress_bar.hide()
                return

            # List of commands to revert TCP settings
            commands = [
                "netsh int tcp set global congestionprovider=default",
                "netsh int tcp set global autotuninglevel=default",
                "netsh int tcp set global ecncapability=default",
                "netsh int tcp set global timestamps=default"
            ]

            total_commands = len(commands)
            for i, cmd in enumerate(commands, 1):
                try:
                    # Run the command with shell=True for proper command interpretation
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode != 0:
                        error_msg = f"Command failed: {cmd}\nError: {result.stderr if result.stderr else result.stdout}"
                        logging.error(error_msg)
                        # Don't raise exception, just log and continue
                        QMessageBox.warning(self, "Warning", error_msg)
                    else:
                        logging.info(f"Successfully executed command: {cmd}")
                    
                    progress = int((i / total_commands) * 100)
                    self.progress_bar.setValue(progress)
                    QApplication.processEvents()
                except Exception as e:
                    error_msg = f"Error executing command: {cmd}\nError: {str(e)}"
                    logging.error(error_msg)
                    QMessageBox.warning(self, "Warning", error_msg)

            # Update the status regardless of individual command failures
            self.tcp_status.setText("TCP Settings: Default")
            self.tcp_status.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    padding: 10px;
                    background-color: rgba(0, 0, 0, 0.4);
                    border-radius: 8px;
                }
            """)
            self.update_settings_display()
            self.tcp_optimized = False  # Reset optimization flag
            QMessageBox.information(self, "Success", "TCP settings have been reverted to default values.")

        except Exception as e:
            logging.error(f"Error in revert_tcp_settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while reverting TCP settings:\n{str(e)}")
        finally:
            self.progress_bar.hide()

    def apply_dns_settings(self):
        try:
            # Get the selected DNS option
            dns_text = self.dns_input.text()
            
            # Simulate DNS change (you would add actual DNS change commands here)
            if dns_text:
                dns_servers = dns_text.split(',')
                dns_servers = [server.strip() for server in dns_servers]
            else:
                dns_servers = []  
            
            # Show progress message
            self.show_dns_status("Changing DNS settings...", "progress")
            
            # Execute the DNS change commands
            if dns_servers:
                for i, server in enumerate(dns_servers, 1):
                    cmd = f'netsh interface ip set dns name="Ethernet" static {server} validate=no'
                    subprocess.run(cmd, shell=True, check=True)
                    self.show_dns_status(f"Setting DNS {i} of {len(dns_servers)}...", "progress")
            else:
                cmd = 'netsh interface ip set dns name="Ethernet" dhcp'
                subprocess.run(cmd, shell=True, check=True)
            
            # Show success message with animation
            self.show_dns_status("DNS changed successfully!", "success")
            
            # Create a confirmation popup
            self.dns_popup = QLabel(self)
            self.dns_popup.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 255, 0, 0.2);
                    color: #00ff00;
                    font-size: 18px;
                    font-weight: 600;
                    padding: 20px;
                    border: 2px solid #00ff00;
                    border-radius: 15px;
                }
            """)
            self.dns_popup.setText("DNS Settings Updated!")
            self.dns_popup.adjustSize()
            
            # Position popup in the center
            popup_x = (self.width() - self.dns_popup.width()) // 2
            popup_y = (self.height() - self.dns_popup.height()) // 2
            self.dns_popup.move(popup_x, popup_y)
            self.dns_popup.show()
            
            # Create fade out animation
            self.fade_animation = QPropertyAnimation(self.dns_popup, b"windowOpacity")
            self.fade_animation.setDuration(3000)  
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(self.dns_popup.deleteLater)
            self.fade_animation.start()
            
        except Exception as e:
            self.show_dns_status(f"Error: {str(e)}", "error")

    def show_dns_status(self, message, status_type="info"):
        if not hasattr(self, 'dns_status_label'):
            logging.error("DNS status label not initialized")
            return
            
        style = """
            QLabel {
                padding: 5px;
                color: %s;
            }
        """
        
        if status_type == "error":
            color = "#ff4444"
        elif status_type == "success":
            color = "#44ff44"
        else:
            color = "#ffffff"
            
        self.dns_status_label.setStyleSheet(style % color)
        self.dns_status_label.setText(message)

    def closeEvent(self, event):
        # Clean up ping process when closing
        if self.ping_process:
            self.stop_ping()
        super().closeEvent(event)

    def update_settings_display(self):
        try:
            # Get current TCP settings using netsh commands
            settings = {
                'congestionprovider': 'default',
                'autotuninglevel': 'default',
                'ecncapability': 'default',
                'timestamps': 'default'
            }

            try:
                # Get current TCP settings
                for setting in settings.keys():
                    cmd = ['netsh', 'int', 'tcp', 'show', 'global']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        # Parse the output to find current settings
                        lines = result.stdout.split('\n')
                        for line in lines:
                            for key in settings.keys():
                                if key.lower() in line.lower():
                                    value = line.split(':')[-1].strip()
                                    settings[key] = value

            except subprocess.CalledProcessError:
                # If command fails, keep default values
                pass

            # Update TCP status based on settings
            if all(val == 'default' for val in settings.values()):
                self.tcp_status.setText("TCP Settings: Default")
                self.tcp_status.setStyleSheet("""
                    QLabel {
                        color: #00ffff;
                        font-size: 18px;
                        font-weight: 600;
                    }
                """)
                self.revert_btn.setEnabled(False)
                self.optimize_btn.setEnabled(True)
            else:
                self.tcp_status.setText("TCP Settings: Optimized")
                self.tcp_status.setStyleSheet("""
                    QLabel {
                        color: #00ff99;
                        font-size: 18px;
                        font-weight: 600;
                    }
                """)
                self.revert_btn.setEnabled(True)
                self.optimize_btn.setEnabled(False)

        except Exception as e:
            logging.error(f"Error updating settings display: {str(e)}")

    def check_initial_tcp_settings(self):
        try:
            # Check current TCP settings
            result = subprocess.run(['netsh', 'int', 'tcp', 'show', 'global'], 
                                 capture_output=True, 
                                 text=True,
                                 shell=True)
            
            # Default settings
            self.tcp_status.setText("TCP Settings: Default")
            self.optimize_btn.setEnabled(True)
            self.revert_btn.setEnabled(False)
            
        except Exception as e:
            logging.error(f"Error checking initial TCP settings: {str(e)}")

    def optimize_network_interface(self, interface_name):
        try:
            # Log baseline ping before optimization
            baseline = self.current_ping if self.current_ping else "N/A"
            logging.info(f"\n=== NETWORK INTERFACE OPTIMIZATION IMPACT ===")
            logging.info(f"Baseline Ping: {baseline}ms")
            logging.info(f"Interface: {interface_name}")

            # Escape quotes and spaces in interface name for PowerShell
            escaped_name = f'"{interface_name}"'
            
            # Commands to optimize network interface
            powershell_commands = [
                f'Disable-NetAdapterLso -Name {escaped_name}',
                f'Disable-NetAdapterChecksumOffload -Name {escaped_name}',
                f'Set-NetAdapterAdvancedProperty -Name {escaped_name} -DisplayName "Receive Descriptors" -DisplayValue 512',
                f'Set-NetAdapterAdvancedProperty -Name {escaped_name} -DisplayName "Transmit Descriptors" -DisplayValue 512',
                f'Set-NetAdapterAdvancedProperty -Name {escaped_name} -DisplayName "Flow Control" -DisplayValue "Disabled"'
            ]
            
            for cmd in powershell_commands:
                try:
                    # Run PowerShell command with proper argument handling
                    full_cmd = ['powershell', '-Command', cmd]
                    result = subprocess.run(
                        full_cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logging.debug(f"Command succeeded: {cmd}")
                    logging.debug(f"Output: {result.stdout}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Command failed: {cmd}")
                    logging.error(f"Error output: {e.stderr}")
                    # Continue with other commands even if one fails
                    continue
            
            # Additional netsh commands
            netsh_commands = [
                ['netsh', 'interface', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'chimney=disabled'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'ecncapability=disabled'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'timestamps=disabled']
            ]
            
            for cmd in netsh_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    logging.debug(f"Netsh command succeeded: {' '.join(cmd)}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Netsh command failed: {' '.join(cmd)}")
                    logging.error(f"Error: {e.stderr}")
                    continue
            
            # Log final ping after optimization
            final = self.current_ping if self.current_ping else "N/A"
            improvement = ((baseline - final) / baseline * 100) if baseline != "N/A" and final != "N/A" else "N/A"
            logging.info(f"Final Ping: {final}ms")
            logging.info(f"Network Interface Optimization Impact: {improvement:.1f}% improvement")
            logging.info("================================\n")
            
            QMessageBox.information(self, "Success", 
                f"Network interface {interface_name} has been optimized successfully!")
            
        except Exception as e:
            logging.error(f"Error optimizing network interface: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"Failed to optimize network interface:\n{str(e)}")

    def optimize_for_gaming(self):
        try:
            # Log baseline ping before optimization
            baseline = self.current_ping if self.current_ping else "N/A"
            logging.info(f"\n=== GAME MODE OPTIMIZATION IMPACT ===")
            logging.info(f"Baseline Ping: {baseline}ms")

            # List of commands to optimize for gaming
            commands = [
                ['powershell', 'Set-NetTCPSetting -SettingName InternetCustom -AutoTuningLevelLocal Normal'],
                ['powershell', 'Set-NetTCPSetting -SettingName InternetCustom -ScalingHeuristics Disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecncapability=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'timestamps=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'heuristics', 'disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'rss=enabled'],
                ['powershell', 'Disable-NetAdapterLso -Name *'],  
                ['powershell', 'Set-NetOffloadGlobalSetting -PacketCoalescingFilter Disabled']
            ]
            
            total_commands = len(commands)
            for i, cmd in enumerate(commands, 1):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    progress = int((i / total_commands) * 100)
                    self.progress_bar.setValue(progress)
                    QApplication.processEvents()
                except subprocess.CalledProcessError as e:
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Warning")
                    msg_box.setText(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
                    msg_box.exec_()
                    logging.warning(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    # Continue with other commands even if one fails
                    continue
            
            # Log final ping after optimization
            final = self.current_ping if self.current_ping else "N/A"
            improvement = ((baseline - final) / baseline * 100) if baseline != "N/A" and final != "N/A" else "N/A"
            logging.info(f"Final Ping: {final}ms")
            logging.info(f"Game Mode Optimization Impact: {improvement:.1f}% improvement")
            logging.info("================================\n")
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Success")
            msg_box.setText("Game optimizations applied successfully!")
            msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            msg_box.exec_()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"Failed to apply game optimizations: {str(e)}")
            msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            msg_box.exec_()
            logging.error(f"Error applying game optimizations: {str(e)}")

    def optimize_qos(self):
        try:
            # Log baseline ping before optimization
            baseline = self.current_ping if self.current_ping else "N/A"
            logging.info(f"\n=== QoS OPTIMIZATION IMPACT ===")
            logging.info(f"Baseline Ping: {baseline}ms")

            # First remove any existing Gaming QoS policy
            remove_cmd = 'Remove-NetQosPolicy -Name "Gaming" -ErrorAction SilentlyContinue -Confirm:$false'
            subprocess.run(['powershell', remove_cmd], capture_output=True, text=True, shell=True)
            
            # Ask user for confirmation before creating QoS policy
            reply = QMessageBox.question(self, 'QoS Optimization',
                                      'Do you want to create a new QoS policy for gaming?\n\n'
                                      'This will prioritize gaming traffic on your network.',
                                      QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Create new Gaming QoS policy
                create_cmd = 'New-NetQosPolicy -Name "Gaming" -IPProtocolMatchCondition Both -DSCPAction 46 -IPSrcPortMatchCondition 3074 -Confirm:$false'
                result = subprocess.run(['powershell', create_cmd], capture_output=True, text=True, shell=True)
                
                # Log final ping after optimization
                final = self.current_ping if self.current_ping else "N/A"
                improvement = ((baseline - final) / baseline * 100) if baseline != "N/A" and final != "N/A" else "N/A"
                logging.info(f"Final Ping: {final}ms")
                logging.info(f"QoS Optimization Impact: {improvement:.1f}% improvement")
                logging.info("================================\n")
                
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "QoS settings optimized successfully!")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to optimize QoS settings.\nError: {result.stderr}")
            else:
                QMessageBox.information(self, "Cancelled", "QoS optimization was cancelled.")
                
        except Exception as e:
            logging.error(f"Error in QoS optimization: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to optimize QoS settings: {str(e)}")

    def apply_interface_settings(self):
        try:
            # Get the selected interface
            interface_name = self.interface_combo.currentText()
            
            # Apply network interface optimizations
            self.optimize_network_interface(interface_name)
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"Failed to apply interface settings: {str(e)}")
            msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            msg_box.exec_()
            logging.error(f"Error applying interface settings: {str(e)}")

    def apply_game_settings(self):
        try:
            # Apply game optimizations
            self.optimize_for_gaming()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"Failed to apply game settings: {str(e)}")
            msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            msg_box.exec_()
            logging.error(f"Error applying game settings: {str(e)}")

def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

if __name__ == '__main__':
    logging.debug('Starting TCP Optimizer...')
    if not is_admin():
        print("Please run as administrator")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    window = TCPOptimizerQt()
    window.show()
    sys.exit(app.exec_())
