import sys
import os
import subprocess
import threading
import time
import re
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame, QTabWidget, QComboBox,
                           QMessageBox, QLineEdit, QProgressBar, QApplication,
                           QSizePolicy, QCheckBox, QScrollArea, QRadioButton, 
                           QButtonGroup, QGraphicsOpacityEffect, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QRect, QEasingCurve
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPalette, QBrush
import logging
import psutil
import styles  # Import the styles module
from cherry_blossom_animation import CherryBlossomAnimation
import json
from datetime import datetime

# Enhanced Logging Configuration
def setup_logging():
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, 'tcp_optimizer.log')
    metrics_file = os.path.join(log_dir, 'tcp_metrics.json')

    # Configure main logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Create a separate logger for metrics
    metrics_logger = logging.getLogger('metrics')
    metrics_logger.setLevel(logging.INFO)
    
    # Custom handler for JSON metrics
    class MetricsHandler(logging.Handler):
        def __init__(self, metrics_file):
            super().__init__()
            self.metrics_file = metrics_file
            self.metrics = {
                'sessions': []
            }
            # Load existing metrics if file exists
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r') as f:
                        self.metrics = json.load(f)
                except:
                    pass
            
            # Start new session
            self.current_session = {
                'start_time': datetime.now().isoformat(),
                'baseline_ping': None,
                'optimized_pings': [],
                'tcp_commands': {
                    'successful': [],
                    'failed': []
                },
                'improvements': []
            }
            self.metrics['sessions'].append(self.current_session)

        def emit(self, record):
            try:
                msg = self.format(record)
                if record.levelname == 'INFO':
                    # Parse and store metrics based on message type
                    if 'baseline_ping' in msg:
                        value = msg.split(': ')[1].replace('ms', '').strip()
                        self.current_session['baseline_ping'] = float(value)
                    elif 'Successfully applied' in msg:
                        self.current_session['tcp_commands']['successful'].append(msg)
                    elif 'Command failed' in msg:
                        self.current_session['tcp_commands']['failed'].append(msg)
                    elif 'Ping stats' in msg:
                        # Extract ping values and improvement
                        ping_data = {}
                        parts = msg.split(' - ')
                        for part in parts:
                            if ':' in part:
                                key = part.split(':')[0].strip()
                                value = part.split(':')[1].strip().replace('ms', '').strip()
                                if key == 'Improvement':
                                    ping_data[key] = value  # Keep the % symbol for improvement
                                else:
                                    try:
                                        ping_data[key] = float(value)
                                    except:
                                        ping_data[key] = value
                        self.current_session['optimized_pings'].append(ping_data)
                    
                    # Save metrics to file
                    with open(self.metrics_file, 'w') as f:
                        json.dump(self.metrics, f, indent=2)
            except Exception as e:
                print(f"Error in metrics handler: {e}")

    # Add metrics handler
    metrics_handler = MetricsHandler(metrics_file)
    metrics_formatter = logging.Formatter('%(asctime)s - %(message)s')
    metrics_handler.setFormatter(metrics_formatter)
    metrics_logger.addHandler(metrics_handler)

    return metrics_logger

# Initialize loggers
metrics_logger = setup_logging()

class ValueDisplay(QFrame):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.setStyleSheet(styles.TRANSPARENT_FRAME_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Label
        label = QLabel(label_text)
        label.setStyleSheet(styles.HEADING_LABEL_STYLE)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Value with unit
        self.value = QLabel("--")
        self.value.setStyleSheet(styles.VALUE_DISPLAY_STYLE)
        self.value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value)
        
    def update_value(self, value):
        if isinstance(value, (int, float)):
            # Format to exactly one decimal place
            formatted_value = f"{value:.1f} ms"
        elif isinstance(value, str) and any(indicator in value for indicator in ["⬆️", "⬇️"]):
            # Handle string with improvement indicators
            if " ms" in value:
                formatted_value = value
            else:
                base_value = value.split(" ")[0]
                try:
                    base_value = f"{float(base_value):.1f}"
                except ValueError:
                    base_value = value.split(" ")[0]
                formatted_value = f"{base_value} ms" + value[value.find(" ⬆️") if "⬆️" in value else value.find(" ⬇️"):]
        else:
            formatted_value = f"{value} ms" if value != "--" else "--"
        self.value.setText(formatted_value)

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(styles.GLASS_PANEL_STYLE)

class TCPOptimizerQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCP Optimizer")
        self.setStyleSheet(styles.MAIN_WINDOW_STYLE)
        self.setMinimumSize(1200, 800)
        
        # Initialize cherry blossom animation first
        self.cherry_animation = CherryBlossomAnimation(self)
        self.cherry_animation.resize(self.size())
        self.cherry_animation.lower()  # Ensure it stays behind other widgets
        self.cherry_animation.show()
        
        # Initialize variables
        self.running_ping = False
        self.ping_stats = {
            'current': '--',
            'min': '--',
            'max': '--',
            'avg': '--'
        }
        # Ping measurement variables
        self.window_size = 10  # Number of recent pings to consider for moving average
        self.ping_window = []  # Store recent pings
        self.last_ping = None  # Store last ping for immediate comparison
        self.baseline_ping = None  # Baseline ping before optimization
        self.baseline_window = []  # Store baseline window for better comparison
        self.interface_combo = None  
        self.tcp_optimized = False  # Flag to track TCP optimization
        self.interface_optimized = False  # Flag to track interface optimization
        self.qos_optimized = False  # Flag to track QoS optimization
        self.game_mode_enabled = False  # Flag to track game mode
        self.show_improvement = False  # New flag to control arrow display
        
        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create left and right panels with glass effect
        left_panel = GlassFrame()
        right_panel = GlassFrame()
        
        # Set size policies
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Create content for panels
        self.create_left_panel(left_panel)
        self.create_right_panel(right_panel)
        
        # Set background image
        self.set_background_image()
        
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
        
        if hasattr(self, 'cherry_animation'):
            self.cherry_animation.resize(self.size())

    def create_right_panel(self, right_panel):
        layout = QVBoxLayout(right_panel)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create tab widget with modern styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(styles.TAB_WIDGET_STYLE)

        # Create tabs
        tcp_tab = QWidget()
        interface_tab = QWidget()
        game_tab = QWidget()

        # Set up layouts for each tab
        tcp_layout = QVBoxLayout(tcp_tab)
        interface_layout = QVBoxLayout(interface_tab)
        game_layout = QVBoxLayout(game_tab)

        # Add tabs to widget
        self.tab_widget.addTab(tcp_tab, "TCP Settings")
        self.tab_widget.addTab(interface_tab, "Network Interface")
        self.tab_widget.addTab(game_tab, "Game Mode")

        # Set up each tab's content
        self.setup_tcp_tab(tcp_layout)
        self.setup_interface_tab(interface_layout)
        self.setup_game_tab(game_layout)

        layout.addWidget(self.tab_widget)

    def setup_tcp_tab(self, layout):
        # Use vertical layout without additional frame
        tab_layout = QVBoxLayout()
        tab_layout.setSpacing(20)
        tab_layout.setContentsMargins(20, 20, 20, 20)
        
        # Status label
        self.tcp_status = QLabel("TCP Settings: Default")
        self.tcp_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
        self.tcp_status.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(self.tcp_status)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        self.progress_bar.hide()
        tab_layout.addWidget(self.progress_bar)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # Optimize button
        self.optimize_btn = QPushButton("OPTIMIZE TCP SETTINGS")
        self.optimize_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.optimize_btn.clicked.connect(self.optimize_tcp)
        button_layout.addWidget(self.optimize_btn)
        
        # Revert button
        self.revert_btn = QPushButton("REVERT TO DEFAULT")
        self.revert_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.revert_btn.clicked.connect(self.revert_tcp_settings)
        self.revert_btn.setEnabled(False)
        button_layout.addWidget(self.revert_btn)
        
        tab_layout.addLayout(button_layout)
        
        # Add some spacing at the bottom
        tab_layout.addStretch()
        
        # Set the layout
        layout.addLayout(tab_layout)

    def setup_interface_tab(self, layout):
        # Main frame for interface settings with matching transparency
        interface_frame = QFrame()
        interface_frame.setStyleSheet(styles.TRANSPARENT_FRAME_STYLE)
        interface_layout = QVBoxLayout(interface_frame)
        interface_layout.setSpacing(15)

        # Network interface selection
        self.interface_combo = QComboBox()
        self.interface_combo.setStyleSheet(styles.COMBO_BOX_STYLE)
        
        # Populate interface combo
        for iface in psutil.net_if_addrs().keys():
            self.interface_combo.addItem(iface)
        
        interface_layout.addWidget(QLabel("Select Network Interface:"))
        interface_layout.addWidget(self.interface_combo)

        # Status label
        self.interface_status = QLabel("Interface Settings: Default")
        self.interface_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
        self.interface_status.setAlignment(Qt.AlignCenter)
        interface_layout.addWidget(self.interface_status)

        # Button layout
        button_layout = QHBoxLayout()
        
        # Optimize button
        self.interface_optimize_btn = QPushButton("Optimize Interface")
        self.interface_optimize_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.interface_optimize_btn.clicked.connect(self.apply_interface_settings)
        button_layout.addWidget(self.interface_optimize_btn)

        # Revert button
        self.interface_revert_btn = QPushButton("Revert Interface")
        self.interface_revert_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.interface_revert_btn.clicked.connect(self.revert_interface_settings)
        self.interface_revert_btn.setEnabled(False)
        button_layout.addWidget(self.interface_revert_btn)

        interface_layout.addLayout(button_layout)
        layout.addWidget(interface_frame)

    def setup_game_tab(self, layout):
        # Game Mode Options with matching transparency
        game_frame = QFrame()
        game_frame.setStyleSheet(styles.TRANSPARENT_FRAME_STYLE)
        game_layout = QVBoxLayout(game_frame)
        game_layout.setSpacing(15)

        # Status labels
        self.game_mode_status = QLabel("Game Mode: Disabled")
        self.game_mode_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
        self.game_mode_status.setAlignment(Qt.AlignCenter)
        game_layout.addWidget(self.game_mode_status)

        self.qos_status = QLabel("QoS Settings: Default")
        self.qos_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
        self.qos_status.setAlignment(Qt.AlignCenter)
        game_layout.addWidget(self.qos_status)

        # Game Mode buttons
        game_button_layout = QHBoxLayout()
        
        # Enable button
        self.game_mode_enable_btn = QPushButton("Enable Game Mode")
        self.game_mode_enable_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.game_mode_enable_btn.clicked.connect(self.apply_game_settings)
        game_button_layout.addWidget(self.game_mode_enable_btn)

        # Disable button
        self.game_mode_disable_btn = QPushButton("Disable Game Mode")
        self.game_mode_disable_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.game_mode_disable_btn.clicked.connect(self.revert_game_settings)
        self.game_mode_disable_btn.setEnabled(False)
        game_button_layout.addWidget(self.game_mode_disable_btn)

        game_layout.addLayout(game_button_layout)

        # QoS buttons
        qos_button_layout = QHBoxLayout()
        
        # Optimize button
        self.qos_optimize_btn = QPushButton("Optimize QoS")
        self.qos_optimize_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.qos_optimize_btn.clicked.connect(self.optimize_qos)
        qos_button_layout.addWidget(self.qos_optimize_btn)

        # Revert button
        self.qos_revert_btn = QPushButton("Revert QoS")
        self.qos_revert_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.qos_revert_btn.clicked.connect(self.revert_qos_settings)
        self.qos_revert_btn.setEnabled(False)
        qos_button_layout.addWidget(self.qos_revert_btn)

        game_layout.addLayout(qos_button_layout)
        layout.addWidget(game_frame)

    def start_ping(self):
        if not self.running_ping:
            try:
                self.running_ping = True
                self.measure_ping_btn.setText("Stop Measuring")
                self.ping_window = []  # Reset ping window
                self.last_ping = None  # Reset last ping
                self.show_improvement = False  # Reset improvement display
                self.baseline_ping = None  # Reset baseline
                self.baseline_window = []  # Reset baseline window
                
                # Start ping process
                self.ping_process = subprocess.Popen(
                    ['ping', '8.8.8.8', '-t'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Start timer to update stats
                self.ping_timer.start(1000)  # Update every second
                
            except Exception as e:
                self.running_ping = False
                logging.error(f"Error starting ping: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to start ping: {str(e)}")
                self.measure_ping_btn.setText("Start Measuring")

    def stop_ping(self):
        self.running_ping = False
        if self.ping_timer.isActive():
            self.ping_timer.stop()
        if self.ping_process:
            self.ping_process.kill()
            self.ping_process = None
        self.measure_ping_btn.setText("Start Measuring")
            
    def update_ping_stats(self):
        try:
            if self.ping_process and self.ping_process.poll() is None:
                line = self.ping_process.stdout.readline()
                if isinstance(line, bytes):
                    line = line.decode()
                line = line.strip()
                
                if "time=" in line:
                    # Extract ping time
                    match = re.search(r"time=(\d+)ms", line)
                    if match:
                        ping_time = float(match.group(1))
                        self.last_ping = ping_time
                        
                        # Update ping window for moving average
                        self.ping_window.append(ping_time)
                        if len(self.ping_window) > self.window_size:
                            self.ping_window.pop(0)
                        
                        # Calculate stats
                        current_avg = sum(self.ping_window) / len(self.ping_window)
                        stats = {
                            'current': ping_time,
                            'min': min(self.ping_window),
                            'max': max(self.ping_window),
                            'avg': current_avg
                        }
                        
                        # Calculate improvement if we have a baseline
                        improvement = None
                        if self.baseline_ping is not None and self.show_improvement and len(self.ping_window) >= 3:
                            improvement = ((self.baseline_ping - current_avg) / self.baseline_ping) * 100
                            if abs(improvement) >= 1:  # Only show if >= 1% change
                                if improvement > 0:
                                    stats['improvement'] = f"⬇️ {abs(improvement):.1f}%"
                                else:
                                    stats['improvement'] = f"⬆️ {abs(improvement):.1f}%"
                        
                        # Log metrics
                        metrics_logger.info(
                            f"Ping stats - Current: {stats['current']:.1f}ms - "
                            f"Min: {stats['min']:.1f}ms - "
                            f"Max: {stats['max']:.1f}ms - "
                            f"Avg: {stats['avg']:.1f}ms" +
                            (f" - Improvement: {stats['improvement']}" if 'improvement' in stats else "")
                        )
                        
                        # Update UI
                        self.update_ping_displays(stats)
                        
        except Exception as e:
            logging.error(f"Error in update_ping_stats: {str(e)}")

    def optimize_tcp(self):
        try:
            # Set the baseline ping before optimization if not already set
            if self.last_ping is not None and self.baseline_ping is None:
                self.baseline_ping = self.last_ping
                metrics_logger.info(f"Setting baseline ping before optimization: {self.baseline_ping}")
                logging.info(f"Setting baseline ping before optimization: {self.baseline_ping}")
                self.show_improvement = True  # Enable improvement display
            
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            # Essential TCP optimization commands that should work on all systems
            main_commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'initialRto=2000'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'rss=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=restricted'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecncapability=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'timestamps=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'netdma=disabled']
            ]
            
            # Optional TCP settings that might not be supported on all systems
            optional_commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'congestionprovider=ctcp']
            ]
            
            success_count = 0
            total_commands = len(main_commands)  # Only count main commands
            
            # Execute main commands first
            for i, cmd in enumerate(main_commands, 1):
                try:
                    cmd_str = ' '.join(cmd)
                    metrics_logger.info(f"Executing TCP command: {cmd_str}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        success_count += 1
                        metrics_logger.info(f"Successfully applied: {cmd_str}")
                    else:
                        metrics_logger.info(f"Command failed: {cmd_str}\nError: {result.stderr}")
                    
                    self.progress_bar.setValue(int((i / total_commands) * 100))
                    
                except Exception as e:
                    metrics_logger.error(f"Error executing command: {cmd_str}\nError: {str(e)}")
                    continue
            
            # Try optional commands but don't count in success/failure
            for cmd in optional_commands:
                try:
                    cmd_str = ' '.join(cmd)
                    metrics_logger.info(f"Trying optional TCP command: {cmd_str}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        metrics_logger.info(f"Successfully applied optional command: {cmd_str}")
                    else:
                        metrics_logger.info(f"Optional command not supported or failed: {cmd_str}\nError: {result.stderr}")
                except Exception as e:
                    metrics_logger.info(f"Optional command not supported: {cmd_str}\nError: {str(e)}")
            
            # Update status based on main commands only
            if success_count > 0:
                self.tcp_status.setText("TCP Settings: Optimized")
                self.tcp_status.setStyleSheet(styles.SUCCESS_LABEL_STYLE)
                self.update_settings_display()
                self.tcp_optimized = True
                metrics_logger.info(f"TCP Optimization completed - {success_count}/{total_commands} commands successful")
                QMessageBox.information(self, "Success", 
                    f"Successfully optimized {success_count} out of {total_commands} TCP settings.")
            else:
                raise Exception("Failed to apply any TCP optimizations")
            
        except Exception as e:
            metrics_logger.error(f"Error in optimize_tcp: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"An error occurred while optimizing TCP settings:\n{str(e)}")
        finally:
            self.progress_bar.hide()

    def revert_tcp_settings(self):
        try:
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            # Essential TCP reversion commands that should work on all systems
            main_commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'initialRto=3000'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'rss=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecncapability=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'timestamps=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'netdma=enabled']
            ]
            
            # Optional TCP settings that might not be supported on all systems
            optional_commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'congestionprovider=default']
            ]
            
            success_count = 0
            total_commands = len(main_commands)  # Only count main commands
            
            # Execute main commands first
            for i, cmd in enumerate(main_commands, 1):
                try:
                    cmd_str = ' '.join(cmd)
                    metrics_logger.info(f"Executing TCP revert command: {cmd_str}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        success_count += 1
                        metrics_logger.info(f"Successfully reverted: {cmd_str}")
                    else:
                        metrics_logger.info(f"Command failed: {cmd_str}\nError: {result.stderr}")
                    
                    self.progress_bar.setValue(int((i / total_commands) * 100))
                    
                except Exception as e:
                    metrics_logger.error(f"Error executing command: {cmd_str}\nError: {str(e)}")
                    continue
            
            # Try optional commands but don't count in success/failure
            for cmd in optional_commands:
                try:
                    cmd_str = ' '.join(cmd)
                    metrics_logger.info(f"Trying optional TCP revert command: {cmd_str}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        metrics_logger.info(f"Successfully executed optional command: {cmd_str}")
                    else:
                        metrics_logger.info(f"Optional command not supported or failed: {cmd_str}\nError: {result.stderr}")
                except Exception as e:
                    metrics_logger.info(f"Optional command not supported: {cmd_str}\nError: {str(e)}")
            
            # Update status based on main commands only
            if success_count > 0:
                self.tcp_status.setText("TCP Settings: Default")
                self.tcp_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
                self.update_settings_display()
                self.tcp_optimized = False  # Reset optimization flag
                self.show_improvement = False  # Disable improvement display
                self.optimize_btn.setEnabled(True)  # Re-enable optimize button
                self.revert_btn.setEnabled(False)  # Disable revert button since we're back to default
                metrics_logger.info(f"TCP Settings reverted - {success_count}/{total_commands} commands successful")
                QMessageBox.information(self, "Success", 
                    f"Successfully reverted {success_count} out of {total_commands} TCP settings to default values.")
            else:
                raise Exception("Failed to revert any TCP settings")
            
        except Exception as e:
            metrics_logger.error(f"Error in revert_tcp_settings: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"An error occurred while reverting TCP settings:\n{str(e)}")
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
            self.dns_popup.setStyleSheet(styles.POPUP_STYLE)
            self.dns_popup.setText("DNS Settings Updated!")
            self.dns_popup.adjustSize()
            
            # Position popup in the center
            popup_x = (self.width() - self.dns_popup.width()) // 2
            popup_y = (self.height() - self.dns_popup.height()) // 2
            self.dns_popup.move(popup_x, popup_y)
            
            # Set initial opacity
            opacity_effect = QGraphicsOpacityEffect(self.dns_popup)
            self.dns_popup.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(1.0)
            self.dns_popup.show()
            
            # Create fade out animation
            self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
            self.fade_animation.setDuration(2000)  # 2 seconds
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
            color = "#ff4444"  # Red for errors
        elif status_type == "success":
            color = "#00ffff"  # Cyan for success, matching UI theme
        else:
            color = "#00ffff"  # Cyan for info, matching UI theme
            
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
                self.tcp_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
                self.revert_btn.setEnabled(False)
                self.optimize_btn.setEnabled(True)
            else:
                self.tcp_status.setText("TCP Settings: Optimized")
                self.tcp_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
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

    def optimize_network_interface(self):
        try:
            # Get selected adapter
            adapter_name = self.interface_combo.currentText()
            if not adapter_name:
                raise ValueError("No network adapter selected")
            
            # Basic TCP/IP optimizations that work across most adapters
            netsh_commands = [
                ['netsh', 'interface', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'chimney=disabled'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'ecncapability=disabled'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'timestamps=disabled']
            ]
            
            success_count = 0
            total_commands = len(netsh_commands)
            
            # Apply netsh commands
            for i, cmd in enumerate(netsh_commands, 1):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        success_count += 1
                        logging.info(f"Successfully applied netsh command: {' '.join(cmd)}")
                    else:
                        logging.warning(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")
                    
                    self.progress_bar.setValue(int((i / total_commands) * 100))
                    
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue
            
            # Show results
            if success_count > 0:
                msg = f"Successfully optimized network settings ({success_count} out of {total_commands} optimizations applied)."
                QMessageBox.information(self, "Success", msg)
                logging.info(msg)
            else:
                raise Exception("Could not apply network optimizations. Please check if you have administrator privileges.")
            
            self.baseline_ping = self.last_ping  # Store baseline before optimization
            self.show_improvement = True  # Enable improvement display
            
        except Exception as e:
            logging.error(f"Error optimizing network interface: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"Failed to optimize network interface:\n{str(e)}")
        finally:
            self.progress_bar.hide()

    def apply_interface_settings(self):
        try:
            interface_name = self.interface_combo.currentText()
            if not interface_name:
                raise ValueError("No network interface selected")
            
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            # Call optimize_network_interface
            self.optimize_network_interface()
            
            # Update UI
            self.interface_status.setText("Interface Settings: Optimized")
            self.interface_optimize_btn.setEnabled(False)
            self.interface_revert_btn.setEnabled(True)
            self.interface_optimized = True
            
        except Exception as e:
            logging.error(f"Failed to apply interface settings: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"Failed to apply interface settings: {str(e)}")
        finally:
            self.progress_bar.hide()

    def optimize_for_gaming(self):
        try:
            # Log baseline ping before optimization
            baseline = self.last_ping if self.last_ping else "N/A"
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
            final = self.last_ping if self.last_ping else "N/A"
            if self.baseline_ping != "N/A" and final != "N/A":
                improvement = ((self.baseline_ping - final) / self.baseline_ping * 100)
                logging.info(f"Final Ping: {final}ms")
                logging.info(f"Game Mode Optimization Impact: {improvement:.1f}% improvement")
            else:
                logging.info(f"Final Ping: {final}ms")
                logging.info("Game Mode Optimization Impact: N/A")
            logging.info("================================\n")
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Success")
            msg_box.setText("Game optimizations applied successfully!")
            msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            msg_box.exec_()
            
            self.baseline_ping = self.last_ping  # Store baseline before optimization
            self.show_improvement = True  # Enable improvement display
            
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
            logging.info("Starting QoS optimization...")
            
            # QoS optimization commands
            commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'congestionprovider=ctcp'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'dca=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecn=disabled'],
                ['powershell', 'Set-NetQosPolicy -Name "Gaming Traffic" -IPProtocol Both -NetworkProfile All -Priority 1']
            ]
            
            success_count = 0
            total_commands = len(commands)
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    success_count += 1
                    logging.info(f"Successfully applied QoS command: {' '.join(cmd)}")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    continue
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue

            if success_count > 0:
                self.qos_status.setText("QoS Settings: Optimized")
                self.qos_optimize_btn.setEnabled(False)
                self.qos_revert_btn.setEnabled(True)
                self.qos_optimized = True
                msg = f"Successfully optimized QoS settings ({success_count} out of {total_commands} optimizations applied)."
                QMessageBox.information(self, "Success", msg)
            else:
                raise Exception("Failed to apply any QoS optimizations")

        except Exception as e:
            logging.error(f"Error in QoS optimization: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to optimize QoS settings:\n{str(e)}")

    def revert_qos_settings(self):
        try:
            logging.info("Reverting QoS settings...")
            
            # Commands to revert QoS settings
            commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'congestionprovider=default'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'dca=disabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecn=enabled'],
                ['powershell', 'Remove-NetQosPolicy -Name "Gaming Traffic" -Confirm:$false']
            ]
            
            success_count = 0
            total_commands = len(commands)
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    success_count += 1
                    logging.info(f"Successfully reverted QoS command: {' '.join(cmd)}")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    continue
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue

            if success_count > 0:
                self.qos_status.setText("QoS Settings: Default")
                self.qos_optimize_btn.setEnabled(True)
                self.qos_revert_btn.setEnabled(False)
                self.qos_optimized = False
                msg = f"Successfully reverted QoS settings ({success_count} out of {total_commands} settings reverted)."
                QMessageBox.information(self, "Success", msg)
            else:
                raise Exception("Failed to revert any QoS settings")

        except Exception as e:
            logging.error(f"Error reverting QoS settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to revert QoS settings:\n{str(e)}")

    def apply_game_settings(self):
        try:
            logging.info("\n=== GAME MODE OPTIMIZATION ===")
            
            # Game mode optimization commands
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
            
            success_count = 0
            total_commands = len(commands)
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    success_count += 1
                    logging.info(f"Successfully applied game mode command: {' '.join(cmd)}")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    continue
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue

            if success_count > 0:
                self.game_mode_status.setText("Game Mode: Enabled")
                self.game_mode_enable_btn.setEnabled(False)
                self.game_mode_disable_btn.setEnabled(True)
                self.game_mode_enabled = True
                msg = f"Successfully enabled game mode ({success_count} out of {total_commands} optimizations applied)."
                QMessageBox.information(self, "Success", msg)
            else:
                raise Exception("Failed to apply any game mode optimizations")

        except Exception as e:
            logging.error(f"Error enabling game mode: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to enable game mode:\n{str(e)}")

    def revert_game_settings(self):
        try:
            logging.info("Reverting game mode settings...")
            
            # Commands to revert game mode settings
            commands = [
                ['powershell', 'Set-NetTCPSetting -SettingName InternetCustom -AutoTuningLevelLocal Normal'],
                ['powershell', 'Set-NetTCPSetting -SettingName InternetCustom -ScalingHeuristics Enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecncapability=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'timestamps=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'heuristics', 'enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'rss=enabled'],
                ['powershell', 'Enable-NetAdapterLso -Name *'],
                ['powershell', 'Set-NetOffloadGlobalSetting -PacketCoalescingFilter Enabled']
            ]
            
            success_count = 0
            total_commands = len(commands)
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    success_count += 1
                    logging.info(f"Successfully reverted game mode command: {' '.join(cmd)}")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
                    continue
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue

            if success_count > 0:
                self.game_mode_status.setText("Game Mode: Disabled")
                self.game_mode_enable_btn.setEnabled(True)
                self.game_mode_disable_btn.setEnabled(False)
                self.game_mode_enabled = False
                msg = f"Successfully disabled game mode ({success_count} out of {total_commands} settings reverted)."
                QMessageBox.information(self, "Success", msg)
            else:
                raise Exception("Failed to revert any game mode settings")

        except Exception as e:
            logging.error(f"Error disabling game mode: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to disable game mode:\n{str(e)}")

    def create_ping_stats_ui(self):
        # Create container frame
        ping_stats_container = QFrame()
        ping_stats_container.setStyleSheet(styles.PING_STATS_FRAME_STYLE)
        ping_stats_layout = QVBoxLayout(ping_stats_container)
        ping_stats_layout.setSpacing(20)
        ping_stats_layout.setContentsMargins(25, 25, 25, 25)

        # Title with modern styling
        title_label = QLabel("PING STATISTICS")
        title_label.setStyleSheet(styles.TITLE_LABEL_STYLE)
        title_label.setAlignment(Qt.AlignCenter)
        ping_stats_layout.addWidget(title_label)

        # Stats Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)

        # Create displays for each stat
        self.ping_displays = {}
        
        # Current Ping
        current_display = QLabel("--")
        current_display.setStyleSheet(styles.VALUE_DISPLAY_STYLE)
        current_display.setAlignment(Qt.AlignCenter)
        current_label = QLabel("CURRENT")
        current_label.setStyleSheet(styles.HEADING_LABEL_STYLE)
        current_label.setAlignment(Qt.AlignCenter)
        stats_grid.addWidget(current_label, 0, 0)
        stats_grid.addWidget(current_display, 1, 0)
        self.ping_displays['current'] = current_display

        # Minimum Ping
        min_display = QLabel("--")
        min_display.setStyleSheet(styles.VALUE_DISPLAY_STYLE)
        min_display.setAlignment(Qt.AlignCenter)
        min_label = QLabel("MINIMUM")
        min_label.setStyleSheet(styles.HEADING_LABEL_STYLE)
        min_label.setAlignment(Qt.AlignCenter)
        stats_grid.addWidget(min_label, 0, 1)
        stats_grid.addWidget(min_display, 1, 1)
        self.ping_displays['min'] = min_display

        # Maximum Ping
        max_display = QLabel("--")
        max_display.setStyleSheet(styles.VALUE_DISPLAY_STYLE)
        max_display.setAlignment(Qt.AlignCenter)
        max_label = QLabel("MAXIMUM")
        max_label.setStyleSheet(styles.HEADING_LABEL_STYLE)
        max_label.setAlignment(Qt.AlignCenter)
        stats_grid.addWidget(max_label, 2, 0)
        stats_grid.addWidget(max_display, 3, 0)
        self.ping_displays['max'] = max_display

        # Average Ping
        avg_display = QLabel("--")
        avg_display.setStyleSheet(styles.VALUE_DISPLAY_STYLE)
        avg_display.setAlignment(Qt.AlignCenter)
        avg_label = QLabel("AVERAGE")
        avg_label.setStyleSheet(styles.HEADING_LABEL_STYLE)
        avg_label.setAlignment(Qt.AlignCenter)
        stats_grid.addWidget(avg_label, 2, 1)
        stats_grid.addWidget(avg_display, 3, 1)
        self.ping_displays['avg'] = avg_display

        ping_stats_layout.addLayout(stats_grid)

        # Measure Ping Button
        self.measure_ping_btn = QPushButton("Start Measuring")
        self.measure_ping_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.measure_ping_btn.setFixedWidth(200)
        self.measure_ping_btn.clicked.connect(self.toggle_ping)
        ping_stats_layout.addWidget(self.measure_ping_btn, 0, Qt.AlignCenter)

        return ping_stats_container

    def toggle_ping(self):
        if not self.running_ping:
            self.start_ping()
            self.measure_ping_btn.setText("Stop Measuring")
        else:
            self.stop_ping()
            self.measure_ping_btn.setText("Start Measuring")

    def update_ping_displays(self, ping_stats):
        if ping_stats:
            for key in ['current', 'min', 'max', 'avg']:
                if key in ping_stats and key in self.ping_displays:
                    value = ping_stats[key]
                    if isinstance(value, (int, float)):
                        self.ping_displays[key].setText(f"{int(round(value))} ms")
            
            # Handle improvement separately
            if 'improvement' in ping_stats and 'avg' in self.ping_displays:
                current_text = self.ping_displays['avg'].text()
                if current_text != "--":
                    self.ping_displays['avg'].setText(f"{current_text} {ping_stats['improvement']}")
        else:
            for display in self.ping_displays.values():
                display.setText("--")

    def create_left_panel(self, left_panel):
        # Left Panel Layout
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(25)
        left_layout.setContentsMargins(30, 30, 30, 30)

        # Ping Statistics Section
        ping_stats_frame = self.create_ping_stats_ui()
        left_layout.addWidget(ping_stats_frame)

        # DNS Settings Section with improved styling
        dns_frame = QFrame()
        dns_frame.setStyleSheet(styles.TRANSPARENT_FRAME_STYLE)
        dns_layout = QVBoxLayout(dns_frame)
        dns_layout.setSpacing(10)
        dns_layout.setContentsMargins(10, 10, 10, 10)

        # DNS Settings Title
        dns_title = QLabel("DNS Settings")
        dns_title.setStyleSheet(styles.HEADING_LABEL_STYLE)
        dns_layout.addWidget(dns_title)

        # DNS Servers Input with adjusted size
        dns_input_layout = QHBoxLayout()
        dns_input_layout.setSpacing(10)
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("Enter DNS servers (comma-separated)")
        self.dns_input.setStyleSheet(styles.INPUT_STYLE)
        self.dns_input.setMinimumHeight(35)
        dns_input_layout.addWidget(self.dns_input)
        
        # Apply DNS Button
        apply_dns_btn = QPushButton("Apply DNS")
        apply_dns_btn.setStyleSheet(styles.BUTTON_STYLE)
        apply_dns_btn.setMinimumHeight(35)
        apply_dns_btn.clicked.connect(self.apply_dns_settings)
        dns_input_layout.addWidget(apply_dns_btn)
        dns_layout.addLayout(dns_input_layout)
        
        # DNS Status Label
        self.dns_status_label = QLabel("")
        self.dns_status_label.setWordWrap(True)
        self.dns_status_label.setStyleSheet(styles.HEADING_LABEL_STYLE)
        dns_layout.addWidget(self.dns_status_label)
        
        left_layout.addWidget(dns_frame)
        
        # Add small spacing at the bottom instead of full stretch
        left_layout.addSpacing(10)

    def revert_interface_settings(self):
        try:
            # Get selected adapter
            adapter_name = self.interface_combo.currentText()
            if not adapter_name:
                raise ValueError("No network adapter selected")
            
            # Commands to revert interface settings
            netsh_commands = [
                ['netsh', 'interface', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'chimney=enabled'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'ecncapability=enabled'],
                ['netsh', 'interface', 'tcp', 'set', 'global', 'timestamps=enabled']
            ]
            
            success_count = 0
            total_commands = len(netsh_commands)
            
            # Apply netsh commands
            for i, cmd in enumerate(netsh_commands, 1):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        success_count += 1
                        logging.info(f"Successfully reverted netsh command: {' '.join(cmd)}")
                    else:
                        logging.warning(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue
            
            # Update UI
            if success_count > 0:
                self.interface_status.setText("Interface Settings: Default")
                self.interface_optimize_btn.setEnabled(True)
                self.interface_revert_btn.setEnabled(False)
                self.interface_optimized = False
                msg = f"Successfully reverted network settings ({success_count} out of {total_commands} settings reverted)."
                QMessageBox.information(self, "Success", msg)
                logging.info(msg)
            else:
                raise Exception("Could not revert network settings. Please check if you have administrator privileges.")
            
        except Exception as e:
            logging.error(f"Error reverting interface settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to revert interface settings:\n{str(e)}")

def is_admin():
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
