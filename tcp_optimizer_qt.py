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
import styles  # Import the styles module

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

        # Apply button
        apply_btn = QPushButton("Apply Interface Settings")
        apply_btn.setStyleSheet(styles.BUTTON_STYLE)
        apply_btn.clicked.connect(self.apply_interface_settings)
        interface_layout.addWidget(apply_btn)

        layout.addWidget(interface_frame)

    def setup_game_tab(self, layout):
        # Game Mode Options with matching transparency
        game_frame = QFrame()
        game_frame.setStyleSheet(styles.TRANSPARENT_FRAME_STYLE)
        game_layout = QVBoxLayout(game_frame)
        game_layout.setSpacing(15)

        # Game Mode Button
        game_mode_btn = QPushButton("Enable Game Mode")
        game_mode_btn.setStyleSheet(styles.BUTTON_STYLE)
        game_mode_btn.clicked.connect(self.apply_game_settings)
        game_layout.addWidget(game_mode_btn)

        # QoS Button
        qos_btn = QPushButton("Optimize QoS Settings")
        qos_btn.setStyleSheet(styles.BUTTON_STYLE)
        qos_btn.clicked.connect(self.optimize_qos)
        game_layout.addWidget(qos_btn)

        layout.addWidget(game_frame)

    def start_ping(self):
        if not self.running_ping:
            try:
                self.running_ping = True
                self.measure_ping_btn.setText("Stop Ping")
                self.ping_values = []
                self.show_improvement = False  # Reset improvement display when starting new ping
                self.baseline_ping = None  # Reset baseline ping
                
                # Start the ping process
                self.ping_process = subprocess.Popen(
                    ["ping", "-t", "8.8.8.8"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Start the timer to update ping stats
                self.ping_timer = QTimer()
                self.ping_timer.timeout.connect(self.update_ping_stats)
                self.ping_timer.start(100)  # Update every 100ms
                
            except Exception as e:
                self.running_ping = False
                logging.error(f"Error starting ping: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to start ping: {str(e)}")
        else:
            self.stop_ping()

    def stop_ping(self):
        if self.ping_process:
            self.ping_timer.stop()
            self.ping_process.kill()
            self.ping_process = None
            self.measure_ping_btn.setText("Measure Ping")
            
    def update_ping_stats(self):
        if self.ping_process and self.ping_process.poll() is None:
            try:
                line = self.ping_process.stdout.readline().strip()
                if "time=" in line:
                    # Extract ping time value
                    time_str = line.split("time=")[1].split("ms")[0].strip()
                    try:
                        current = float(time_str)
                        self.ping_values.append(current)
                        
                        # Calculate statistics
                        min_ping = min(self.ping_values)
                        max_ping = max(self.ping_values)
                        avg = sum(self.ping_values) / len(self.ping_values)
                        
                        # Store current ping for improvement calculation
                        self.current_ping = avg  # Use average for more stable comparison
                        
                        # Calculate improvement if baseline exists and improvement display is enabled
                        improvement_text = ""
                        if self.show_improvement and self.baseline_ping is not None and self.current_ping is not None:
                            improvement = ((self.baseline_ping - self.current_ping) / self.baseline_ping) * 100
                            if improvement > 0:  # Ping reduced (improved)
                                improvement_text = f" ⬆️ {int(improvement)}%"  # Up arrow for improvement
                            elif improvement < 0:  # Ping increased (degraded)
                                improvement_text = f" ⬇️ {abs(int(improvement))}%"  # Down arrow for degradation
                        
                        # Update displays with raw values
                        stats_updates = {
                            'current': int(round(current)),
                            'minimum': int(round(min_ping)),
                            'maximum': int(round(max_ping)),
                            'average': f"{int(round(avg))}{improvement_text}"
                        }
                        
                        for key, value in stats_updates.items():
                            if key in self.ping_displays:
                                self.ping_displays[key].setText(f"{value} ms" if isinstance(value, (int, float)) else value)
                        
                        # Log stats for debugging
                        logging.debug(f"Ping stats - Current: {int(current)}ms, Min: {int(min_ping)}ms, Max: {int(max_ping)}ms, Avg: {int(avg)}ms{improvement_text}")
                        
                    except ValueError as e:
                        logging.error(f"Error parsing ping time: {e}")
                        
            except Exception as e:
                logging.error(f"Error reading ping output: {e}")

    def optimize_tcp(self):
        try:
            # Set the baseline ping before optimization if not already set
            if self.current_ping is not None and self.baseline_ping is None:
                self.baseline_ping = self.current_ping
                logging.info(f"Setting baseline ping before optimization: {self.baseline_ping:.1f}ms")
            
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
            improvement = ((self.baseline_ping - final) / self.baseline_ping * 100) if self.baseline_ping != "N/A" and final != "N/A" else "N/A"
            logging.info(f"Final Ping: {final}ms")
            logging.info(f"TCP Optimization Impact: {improvement:.1f}% improvement")
            logging.info("================================\n")
            
            self.update_settings_display()
            self.progress_bar.setValue(100)
            self.tcp_optimized = True  # Set flag to indicate TCP optimization
            self.show_improvement = True  # Enable improvement display
            QMessageBox.information(self, "Success", "TCP settings have been optimized successfully!")
            
        except Exception as e:
            logging.error(f"Unexpected error during TCP optimization: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"An unexpected error occurred:\n{str(e)}")
        finally:
            self.progress_bar.hide()

    def revert_tcp_settings(self):
        try:
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            # Commands to revert TCP settings
            commands = [
                ['netsh', 'int', 'tcp', 'set', 'global', 'initialRto=3000'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'rss=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'chimney=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'autotuninglevel=normal'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'ecncapability=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'timestamps=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'netdma=enabled'],
                ['netsh', 'int', 'tcp', 'set', 'global', 'congestionprovider=default']
            ]
            
            success_count = 0
            total_commands = len(commands)
            
            for i, cmd in enumerate(commands, 1):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        success_count += 1
                        logging.info(f"Successfully reverted: {' '.join(cmd)}")
                    else:
                        logging.warning(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")
                    
                    self.progress_bar.setValue(int((i / total_commands) * 100))
                    
                except Exception as e:
                    logging.warning(f"Error executing command: {' '.join(cmd)}\nError: {str(e)}")
                    continue
            
            # Update the status regardless of individual command failures
            if success_count > 0:
                self.tcp_status.setText("TCP Settings: Default")
                self.tcp_status.setStyleSheet(styles.HEADING_LABEL_STYLE)
                self.update_settings_display()
                self.tcp_optimized = False  # Reset optimization flag
                self.show_improvement = False  # Disable improvement display
                QMessageBox.information(self, "Success", 
                    f"Successfully reverted {success_count} out of {total_commands} TCP settings to default values.")
            else:
                raise Exception("Failed to revert any TCP settings")
            
        except Exception as e:
            logging.error(f"Error in revert_tcp_settings: {str(e)}")
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
            
            self.baseline_ping = self.current_ping  # Store baseline before optimization
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
            
            # Call optimize_network_interface without passing interface_name
            self.optimize_network_interface()
            
        except Exception as e:
            logging.error(f"Failed to apply interface settings: {str(e)}")
            QMessageBox.critical(self, "Error", 
                f"Failed to apply interface settings: {str(e)}")
        finally:
            self.progress_bar.hide()

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
            
            self.baseline_ping = self.current_ping  # Store baseline before optimization
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
                
            self.baseline_ping = self.current_ping  # Store baseline before optimization
            self.show_improvement = True  # Enable improvement display
            
        except Exception as e:
            logging.error(f"Error in QoS optimization: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to optimize QoS settings: {str(e)}")

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

    def create_ping_stats_ui(self):
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

        # Stats setup
        stats_info = [
            ("CURRENT", 0, 0),
            ("MINIMUM", 0, 1),
            ("MAXIMUM", 1, 0),
            ("AVERAGE", 1, 1)
        ]
        
        self.ping_displays = {}
        
        for label, row, col in stats_info:
            container = QFrame()
            container.setStyleSheet(styles.TRANSPARENT_FRAME_STYLE)
            layout = QVBoxLayout(container)
            layout.setSpacing(5)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Label
            label_widget = QLabel(label)
            label_widget.setStyleSheet(styles.HEADING_LABEL_STYLE)
            label_widget.setAlignment(Qt.AlignCenter)
            layout.addWidget(label_widget)
            
            # Value
            value_display = QLabel("--")
            value_display.setStyleSheet(styles.VALUE_DISPLAY_STYLE)
            value_display.setAlignment(Qt.AlignCenter)
            layout.addWidget(value_display)
            
            stats_grid.addWidget(container, row, col)
            self.ping_displays[label.lower()] = value_display

        ping_stats_layout.addLayout(stats_grid)

        # Stop Ping Button
        self.measure_ping_btn = QPushButton("Stop Ping")
        self.measure_ping_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.measure_ping_btn.setFixedWidth(200)
        self.measure_ping_btn.clicked.connect(self.start_ping)
        ping_stats_layout.addWidget(self.measure_ping_btn, 0, Qt.AlignCenter)

        return ping_stats_container

    def update_ping_displays(self, ping_stats):
        if ping_stats:
            for key, value in ping_stats.items():
                if key in self.ping_displays:
                    if isinstance(value, (int, float)):
                        # Round to whole number for display
                        formatted_value = f"{int(round(value))} ms"
                    elif isinstance(value, str) and "%" in value:
                        # Handle improvement percentage
                        base_value = value.split(" ")[0]
                        try:
                            base_value = f"{int(round(float(base_value)))} ms"
                        except ValueError:
                            base_value = value
                        formatted_value = base_value + value[value.find(" ⬆️") if "⬆️" in value else value.find(" ⬇️"):]
                    else:
                        formatted_value = f"{value} ms" if value != "--" else "--"
                    self.ping_displays[key].setText(formatted_value)
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
