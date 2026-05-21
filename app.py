import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QHBoxLayout, QFileDialog, QSpacerItem, QSizePolicy, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QIcon

from macro_engine import MacroEngine

class WorkerSignals(QObject):
    finished = pyqtSignal()
    status_update = pyqtSignal(str)

class MiniRecorderWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QWidget()
        self.frame.setObjectName("miniFrame")
        self.frame.setStyleSheet("""
            QWidget#miniFrame {
                background-color: #FAF9F6;
                border: 2px solid #E0DED8;
                border-radius: 20px;
            }
        """)
        
        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(10)
        
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet("color: #1A1A1A; font-weight: bold; font-family: 'Inter', sans-serif; padding: 0 10px;")
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.start_clicked)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("outlineButton")
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.stop_btn.setEnabled(False)
        
        frame_layout.addWidget(self.status_lbl)
        frame_layout.addWidget(self.start_btn)
        frame_layout.addWidget(self.stop_btn)
        
        layout.addWidget(self.frame)
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_seconds = 0
        
    def update_timer(self):
        self.elapsed_seconds += 1
        mins, secs = divmod(self.elapsed_seconds, 60)
        self.status_lbl.setText(f"{mins:02d}:{secs:02d}")
        
    def start_clicked(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.elapsed_seconds = 0
        self.status_lbl.setText("00:00")
        self.status_lbl.setStyleSheet("color: #D32F2F; font-weight: bold; font-family: 'Inter', sans-serif; padding: 0 10px;")
        self.timer.start(1000)
        
        self.main_window.engine.start_recording()
        
    def stop_clicked(self):
        self.timer.stop()
        self.main_window.engine.stop_recording()
        
    def reset_state(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_lbl.setText("Ready")
        self.status_lbl.setStyleSheet("color: #1A1A1A; font-weight: bold; font-family: 'Inter', sans-serif; padding: 0 10px;")
        
    def showEvent(self, event):
        self.reset_state()
        screen = QApplication.primaryScreen().geometry()
        self.adjustSize()
        x = (screen.width() - self.width()) // 2
        self.move(x, 20)
        super().showEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = MacroEngine()
        
        # Setup signals for thread-safe UI updates
        self.signals = WorkerSignals()
        self.signals.status_update.connect(self.update_status)
        self.signals.finished.connect(self.on_process_finished)
        
        self.engine.set_on_stop_callback(self.on_engine_stopped)
        self.mini_window = MiniRecorderWindow(self)
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Macro Automator")
        self.setFixedSize(400, 500)
        
        # Portfolio styling: Beige background, clean sans-serif font
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAF9F6;
            }
            QLabel {
                color: #1A1A1A;
                font-family: 'Inter', 'Helvetica Neue', sans-serif;
            }
            QPushButton {
                font-family: 'Inter', 'Helvetica Neue', sans-serif;
                font-weight: 600;
                font-size: 14px;
                padding: 12px 24px;
                border-radius: 22px;
                border: none;
            }
            /* Primary Button Style (like Github button in portfolio) */
            QPushButton#primaryButton {
                background-color: #1A1A1A;
                color: #FFFFFF;
            }
            QPushButton#primaryButton:hover {
                background-color: #333333;
            }
            QPushButton#primaryButton:disabled {
                background-color: #999999;
            }
            
            /* Secondary/Accent Button Style (like Resume button) */
            QPushButton#secondaryButton {
                background-color: #A68A64;
                color: #FFFFFF;
            }
            QPushButton#secondaryButton:hover {
                background-color: #B89B73;
            }
            QPushButton#secondaryButton:disabled {
                background-color: #D3C4B1;
            }
            
            /* Outline Button */
            QPushButton#outlineButton {
                background-color: transparent;
                border: 2px solid #E0DED8;
                color: #1A1A1A;
            }
            QPushButton#outlineButton:hover {
                border-color: #1A1A1A;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo / Title
        title = QLabel("Automator.")
        font = QFont("Inter", 24, QFont.Weight.Bold)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Record and automate workflows.")
        subtitle.setStyleSheet("color: #666666; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #A68A64;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Record Button
        self.record_btn = QPushButton("Record Movement")
        self.record_btn.setObjectName("primaryButton")
        self.record_btn.clicked.connect(self.open_mini_recorder)
        layout.addWidget(self.record_btn)
        
        # Execute Layout (Button + Loop ComboBox)
        execute_layout = QHBoxLayout()
        
        # Execute Button
        self.execute_btn = QPushButton("Execute (Play)")
        self.execute_btn.setObjectName("primaryButton")
        self.execute_btn.clicked.connect(self.start_playback)
        self.execute_btn.setEnabled(False)
        
        # Loop ComboBox
        self.loop_combo = QComboBox()
        self.loop_combo.addItems(["1x", "2x", "5x", "10x", "Infinite"])
        self.loop_combo.setStyleSheet("""
            QComboBox {
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                padding: 10px 15px;
                border: 2px solid #E0DED8;
                border-radius: 20px;
                background-color: #FFFFFF;
                color: #1A1A1A;
            }
            QComboBox:disabled {
                background-color: #F5F5F5;
                color: #999999;
                border-color: #EAEAEA;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #1A1A1A;
                selection-background-color: #F0F0F0;
                selection-color: #1A1A1A;
                border: 2px solid #E0DED8;
                border-radius: 8px;
                outline: none;
            }
        """)
        self.loop_combo.setEnabled(False)
        
        execute_layout.addWidget(self.execute_btn, stretch=3)
        execute_layout.addWidget(self.loop_combo, stretch=1)
        
        layout.addLayout(execute_layout)
        
        # Save/Load buttons horizontally
        file_layout = QHBoxLayout()
        file_layout.setSpacing(15)
        
        self.load_btn = QPushButton("Load")
        self.load_btn.setObjectName("outlineButton")
        self.load_btn.clicked.connect(self.load_macro)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("secondaryButton")
        self.save_btn.clicked.connect(self.save_macro)
        self.save_btn.setEnabled(False)
        
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.save_btn)
        
        layout.addLayout(file_layout)
        
        # Instruction label
        instructions = QLabel("Press Alt + X to stop recording or playback.")
        instructions.setStyleSheet("color: #999999; font-size: 12px; margin-top: 10px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        main_widget.setLayout(layout)

    def update_status(self, text):
        self.status_label.setText(text)

    def on_engine_stopped(self):
        # This is called from the pynput thread, need to use signals to update UI
        self.signals.finished.emit()
        
    def on_process_finished(self):
        self.record_btn.setText("Record Movement")
        self.record_btn.setEnabled(True)
        self.execute_btn.setText("Execute (Play)")
        
        has_events = len(self.engine.events) > 0
        self.execute_btn.setEnabled(has_events)
        self.save_btn.setEnabled(has_events)
        self.load_btn.setEnabled(True)
        if hasattr(self, 'loop_combo'):
            self.loop_combo.setEnabled(has_events)
        
        self.status_label.setText(f"Ready ({len(self.engine.events)} events)" if has_events else "Ready")
        self.status_label.setStyleSheet("color: #A68A64;")
        
        # If mini window was open, close it
        if self.mini_window.isVisible():
            self.mini_window.timer.stop()
            self.mini_window.hide()
            
        self.show()
            
        if has_events:
            self.record_btn.setText("Retry Record")
            self.status_label.setText("Auto save/record")
            self.status_label.setStyleSheet("color: #A68A64;")

    def open_mini_recorder(self):
        # Check if there are existing events
        if len(self.engine.events) > 0:
            msg = QMessageBox(self)
            msg.setWindowTitle("Overwrite Record?")
            msg.setText("You already have a recorded macro. Are you sure you want to overwrite it and restart?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            # Match the portfolio aesthetic
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #FAF9F6;
                }
                QLabel {
                    color: #1A1A1A;
                    font-family: 'Inter', sans-serif;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #1A1A1A;
                    color: #FFFFFF;
                    font-family: 'Inter', sans-serif;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    border-radius: 16px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #333333;
                }
            """)
            reply = msg.exec()
            
            if reply == QMessageBox.StandardButton.No:
                return

        # Hide main window, show mini window
        self.hide()
        # Set stylesheet on mini window again to ensure it picks up main window's style
        self.mini_window.setStyleSheet(self.styleSheet())
        self.mini_window.show()

    def start_recording(self):
        self.record_btn.setText("Recording... (Alt + X to stop)")
        self.record_btn.setEnabled(False)
        self.execute_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.status_label.setText("Recording in progress...")
        self.status_label.setStyleSheet("color: #D32F2F;")
        
        self.engine.start_recording()

    def start_playback(self):
        self.execute_btn.setText("Playing... (Alt + X to stop)")
        self.execute_btn.setEnabled(False)
        self.record_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        if hasattr(self, 'loop_combo'):
            self.loop_combo.setEnabled(False)
            
        self.status_label.setText("Playing macro...")
        self.status_label.setStyleSheet("color: #388E3C;")
        
        self.hide()
        
        loop_count = 1  
        if hasattr(self, 'loop_combo'):
            loop_text = self.loop_combo.currentText()
            if loop_text == "Infinite":
                loop_count = 0
            else:
                loop_count = int(loop_text.replace("x", ""))
        
        self.engine.start_playback(loop_count)

    def save_macro(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Macro", "", "JSON Files (*.json)")
        if file_path:
            if not   file_path.endswith('.json'):
                file_path += '.json'
            self.engine.save_to_file(file_path)
            self.status_label.setText("Macro saved successfully.")

    def load_macro(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Macro", "", "JSON Files (*.json)")
        if file_path:
            if self.engine.load_from_file(file_path):
                self.status_label.setText(f"Loaded {len(self.engine.events)} events.")
                self.execute_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
            else:
                self.status_label.setText("Failed to load macro.")
                self.status_label.setStyleSheet("color: #D32F2F;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Wayland Strictly Prohibited")
        msg.setText("CRITICAL ERROR: This application requires absolute mouse positioning which is mathematically impossible under the Wayland security model.\n\nTo record macros, you MUST log out and switch to 'Ubuntu on Xorg' at your login screen.")
        msg.exec()
        sys.exit(1)
        
    # Try to set font
    font = QFont("Inter", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
