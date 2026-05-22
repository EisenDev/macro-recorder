import sys
import os
import platform
import subprocess
import re
import time
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QHBoxLayout, QFileDialog, QSpacerItem, QSizePolicy, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QIcon, QGuiApplication
from pynput import keyboard

from macro_engine import MacroEngine

class WorkerSignals(QObject):
    finished = pyqtSignal()
    status_update = pyqtSignal(str)
    trigger_screenshot = pyqtSignal()

class MiniRecorderWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # BypassWindowManagerHint is Linux/X11 only — skip it on Windows to avoid broken window behavior
        _flags = Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if platform.system() != "Windows":
            _flags |= Qt.WindowType.BypassWindowManagerHint
        self.setWindowFlags(_flags)
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
        self.status_lbl.setStyleSheet("color: #1A1A1A; font-weight: bold; font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif; padding: 0 10px;")
        
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
        self.status_lbl.setStyleSheet("color: #D32F2F; font-weight: bold; font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif; padding: 0 10px;")
        self.timer.start(1000)
        
        self.main_window.engine.start_recording()
        
    def stop_clicked(self):
        self.timer.stop()
        self.main_window.engine.stop_recording()
        
    def reset_state(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_lbl.setText("Ready")
        self.status_lbl.setStyleSheet("color: #1A1A1A; font-weight: bold; font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif; padding: 0 10px;")
        
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
        self.signals.trigger_screenshot.connect(self.capture_background_window)
        
        self.engine.set_on_stop_callback(self.on_engine_stopped)
        self.mini_window = MiniRecorderWindow(self)
        self.screenshot_listener = None
        
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
                font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
            }
            QPushButton {
                font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
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
        _title_font = QFont("Inter", 24, QFont.Weight.Bold)
        if _title_font.family() != "Inter":  # Inter not available, use best OS alternative
            _title_font = QFont("Segoe UI" if platform.system() == "Windows" else "Helvetica Neue", 24, QFont.Weight.Bold)
        title.setFont(_title_font)
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
        
        # Background Screenshot Button
        self.bg_ss_btn = QPushButton("Enable Background Capture (F10)")
        self.bg_ss_btn.setObjectName("outlineButton")
        self.bg_ss_btn.setCheckable(True)
        self.bg_ss_btn.clicked.connect(self.toggle_background_screenshot)
        layout.addWidget(self.bg_ss_btn)
        
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
                font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
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
                    font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #1A1A1A;
                    color: #FFFFFF;
                    font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
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

    def toggle_background_screenshot(self, checked):
        if checked:
            self.bg_ss_btn.setText("Background Capture ACTIVE (F10)")
            self.bg_ss_btn.setStyleSheet("""
                QPushButton#outlineButton {
                    background-color: #388E3C;
                    color: #FFFFFF;
                    border: 2px solid #388E3C;
                }
                QPushButton#outlineButton:hover {
                    background-color: #2E7D32;
                    border-color: #2E7D32;
                }
            """)
            self.start_screenshot_listener()
            self.status_label.setText("Background capture enabled.")
            self.status_label.setStyleSheet("color: #388E3C;")
        else:
            self.bg_ss_btn.setText("Enable Background Capture (F10)")
            self.bg_ss_btn.setStyleSheet("")
            self.stop_screenshot_listener()
            self.status_label.setText("Background capture disabled.")
            self.status_label.setStyleSheet("color: #A68A64;")

    def start_screenshot_listener(self):
        self.stop_screenshot_listener()
        try:
            self.screenshot_listener = keyboard.Listener(
                on_press=self.on_global_key_press
            )
            self.screenshot_listener.start()
        except Exception as e:
            print("Failed to start screenshot listener:", e)

    def stop_screenshot_listener(self):
        if hasattr(self, 'screenshot_listener') and self.screenshot_listener:
            try:
                self.screenshot_listener.stop()
            except Exception:
                pass
            self.screenshot_listener = None

    def on_global_key_press(self, key):
        try:
            if key == keyboard.Key.f10:
                self.signals.trigger_screenshot.emit()
        except Exception:
            pass

    def capture_background_window(self):
        if getattr(self, "_capturing_screenshot", False):
            return
        self._capturing_screenshot = True
        
        try:
            if platform.system() == "Windows":
                # --- WINDOWS IMPLEMENTATION ---
                hwnd_active = ctypes.windll.user32.GetForegroundWindow()
                if not hwnd_active:
                    self.status_label.setText("No active window found.")
                    self.status_label.setStyleSheet("color: #D32F2F;")
                    self._capturing_screenshot = False
                    return
                
                # Find the next normal visible application window in Z-order
                hwnd_target = None
                hwnd_curr = hwnd_active
                target_name = "Unknown Window"
                
                # Exclude our own HWNDs
                our_hwnds = [self.winId()]
                if self.mini_window:
                    try:
                        our_hwnds.append(self.mini_window.winId())
                    except Exception:
                        pass
                
                while True:
                    # GW_HWNDNEXT = 2
                    hwnd_curr = ctypes.windll.user32.GetWindow(hwnd_curr, 2)
                    if not hwnd_curr:
                        break
                    
                    if not ctypes.windll.user32.IsWindowVisible(hwnd_curr):
                        continue
                        
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd_curr)
                    if length == 0:
                        continue
                        
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd_curr, buf, length + 1)
                    title = buf.value
                    
                    # Exclude our own windows
                    if hwnd_curr in our_hwnds or "Macro Automator" in title or "Automator" in title:
                        continue
                        
                    if title in ["Program Manager", "Start", "Taskbar", "Settings"]:
                        continue
                        
                    hwnd_target = hwnd_curr
                    target_name = title
                    break
                    
                if not hwnd_target:
                    self.status_label.setText("No background window found.")
                    self.status_label.setStyleSheet("color: #D32F2F;")
                    self._capturing_screenshot = False
                    return
                    
                self.status_label.setText(f"Capturing: {target_name[:25]}...")
                self.status_label.setStyleSheet("color: #388E3C;")
                
                os.makedirs("screenshots", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshots/screenshot_behind_{timestamp}.png"
                
                # --- HYBRID CAPTURE: TRY SILENT OFF-SCREEN GRAB FIRST ---
                screen = QGuiApplication.primaryScreen()
                pixmap = screen.grabWindow(hwnd_target)
                
                if not pixmap.isNull() and pixmap.width() > 100 and pixmap.height() > 100:
                    pixmap.save(filename)
                    self.status_label.setText(f"Captured: {target_name[:20]}")
                    self.status_label.setStyleSheet("color: #388E3C;")
                    self._capturing_screenshot = False
                    return
                
                # --- FALLBACK: SWITCH AND CAPTURE ---
                ctypes.windll.user32.ShowWindow(hwnd_target, 9) # SW_RESTORE = 9
                ctypes.windll.user32.SetForegroundWindow(hwnd_target)
                
                def check_and_grab_win(attempts=0):
                    curr_fg = ctypes.windll.user32.GetForegroundWindow()
                    if curr_fg == hwnd_target or attempts >= 15:
                        def do_grab_win():
                            try:
                                screen = QGuiApplication.primaryScreen()
                                pixmap = screen.grabWindow(0)
                                
                                ctypes.windll.user32.ShowWindow(hwnd_active, 9)
                                ctypes.windll.user32.SetForegroundWindow(hwnd_active)
                                
                                if not pixmap.isNull():
                                    pixmap.save(filename)
                                    self.status_label.setText(f"Captured: {target_name[:20]}")
                                    self.status_label.setStyleSheet("color: #388E3C;")
                                else:
                                    self.status_label.setText("Error: Screen grab failed.")
                                    self.status_label.setStyleSheet("color: #D32F2F;")
                            except Exception as ex:
                                print("Error during Windows screen grab:", ex)
                                self.status_label.setText("Capture failed.")
                                self.status_label.setStyleSheet("color: #D32F2F;")
                            finally:
                                self._capturing_screenshot = False
                        QTimer.singleShot(50, do_grab_win)
                    else:
                        QTimer.singleShot(20, lambda: check_and_grab_win(attempts + 1))
                        
                QTimer.singleShot(20, check_and_grab_win)

            else:
                # --- LINUX (X11) IMPLEMENTATION ---
                active_out = subprocess.check_output("xprop -root _NET_ACTIVE_WINDOW", shell=True).decode()
                m = re.search(r"window id # (0x[0-9a-fA-F]+)", active_out)
                if not m:
                    self.status_label.setText("No active window found.")
                    self.status_label.setStyleSheet("color: #D32F2F;")
                    self._capturing_screenshot = False
                    return
                active_id = int(m.group(1), 16)
                
                stack_out = subprocess.check_output("xprop -root _NET_CLIENT_LIST_STACKING", shell=True).decode()
                m_stack = re.search(r"window id # (.*)", stack_out)
                if not m_stack:
                    self.status_label.setText("No window stack found.")
                    self.status_label.setStyleSheet("color: #D32F2F;")
                    self._capturing_screenshot = False
                    return
                stack_ids = [int(x.strip(), 16) for x in m_stack.group(1).split(",") if x.strip()]
                
                if active_id not in stack_ids:
                    self.status_label.setText("Active window not in stack.")
                    self.status_label.setStyleSheet("color: #D32F2F;")
                    self._capturing_screenshot = False
                    return
                
                # Excluded window IDs (our own app windows)
                our_wids = [int(self.winId())]
                if self.mini_window:
                    try:
                        our_wids.append(int(self.mini_window.winId()))
                    except Exception:
                        pass
                
                # Find target window under active_id, skipping our own windows and utility windows
                target_wid = None
                target_name = "Unknown Window"
                
                idx = stack_ids.index(active_id)
                for i in range(idx - 1, -1, -1):
                    wid = stack_ids[i]
                    
                    if wid in our_wids:
                        continue
                        
                    name = "Unknown Window"
                    try:
                        name_out = subprocess.check_output(f"xprop -id {hex(wid)} WM_NAME", shell=True, stderr=subprocess.DEVNULL).decode()
                        name_match = re.search(r"WM_NAME\(STRING\) = \"(.*)\"", name_out)
                        if name_match:
                            name = name_match.group(1)
                        else:
                            name_out = subprocess.check_output(f"xprop -id {hex(wid)} _NET_WM_NAME", shell=True, stderr=subprocess.DEVNULL).decode()
                            name_match = re.search(r"_NET_WM_NAME\(UTF8_STRING\) = \"(.*)\"", name_out)
                            if name_match:
                                name = name_match.group(1)
                    except Exception:
                        pass
                        
                    if "Macro Automator" in name or "Automator" in name:
                        continue
                        
                    if name in ["", "Unknown Window", "Desktop", "xfce4-panel", "gnome-shell", "mutter", "Desktop Sharing"]:
                        continue
                    if name.startswith("@!"):
                        continue
                        
                    target_wid = wid
                    target_name = name
                    break
                    
                if not target_wid:
                    self.status_label.setText("No background window available.")
                    self.status_label.setStyleSheet("color: #D32F2F;")
                    self._capturing_screenshot = False
                    return
                    
                self.status_label.setText(f"Capturing: {target_name[:25]}...")
                self.status_label.setStyleSheet("color: #388E3C;")
                
                os.makedirs("screenshots", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshots/screenshot_behind_{timestamp}.png"
                
                # --- HYBRID CAPTURE: TRY SILENT OFF-SCREEN GRAB FIRST ---
                screen = QGuiApplication.primaryScreen()
                pixmap = screen.grabWindow(target_wid)
                
                if not pixmap.isNull() and pixmap.width() > 100 and pixmap.height() > 100:
                    pixmap.save(filename)
                    self.status_label.setText(f"Captured: {target_name[:20]}")
                    self.status_label.setStyleSheet("color: #388E3C;")
                    self._capturing_screenshot = False
                    return
                
                # --- FALLBACK: SWITCH AND CAPTURE ---
                subprocess.check_call(f"wmctrl -i -a {hex(target_wid)}", shell=True)
                
                # Poll active window status until target is active
                def check_and_grab_lin(attempts=0):
                    try:
                        curr_active = subprocess.check_output("xprop -root _NET_ACTIVE_WINDOW", shell=True).decode()
                        m_curr = re.search(r"window id # (0x[0-9a-fA-F]+)", curr_active)
                        is_target = m_curr and int(m_curr.group(1), 16) == target_wid
                        
                        if is_target or attempts >= 15:
                            def do_grab_lin():
                                try:
                                    screen = QGuiApplication.primaryScreen()
                                    pixmap = screen.grabWindow(0)
                                    
                                    # Switch back
                                    subprocess.check_call(f"wmctrl -i -a {hex(active_id)}", shell=True)
                                    
                                    if not pixmap.isNull():
                                        pixmap.save(filename)
                                        self.status_label.setText(f"Captured: {target_name[:20]}")
                                        self.status_label.setStyleSheet("color: #388E3C;")
                                    else:
                                        self.status_label.setText("Error: Screen grab failed.")
                                        self.status_label.setStyleSheet("color: #D32F2F;")
                                    self._capturing_screenshot = False
                                except Exception as ex:
                                    print("Error during Linux screen grab:", ex)
                                    self.status_label.setText("Capture failed.")
                                    self.status_label.setStyleSheet("color: #D32F2F;")
                                    self._capturing_screenshot = False
                            
                            QTimer.singleShot(50, do_grab_lin)
                        else:
                            QTimer.singleShot(20, lambda: check_and_grab_lin(attempts + 1))
                    except Exception:
                        self._capturing_screenshot = False
                
                QTimer.singleShot(20, check_and_grab_lin)
                
        except Exception as e:
            print("Capture error:", e)
            self.status_label.setText("Background capture error.")
            self.status_label.setStyleSheet("color: #D32F2F;")
            self._capturing_screenshot = False

    def closeEvent(self, event):
        self.stop_screenshot_listener()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Wayland Strictly Prohibited")
        msg.setText("CRITICAL ERROR: This application requires absolute mouse positioning which is mathematically impossible under the Wayland security model.\n\nTo record macros, you MUST log out and switch to 'Ubuntu on Xorg' at your login screen.")
        msg.exec()
        sys.exit(1)
        
    # Set best available font per platform
    _preferred = ["Inter", "Segoe UI", "Helvetica Neue", "Arial"]
    _app_font = None
    for _fname in _preferred:
        _f = QFont(_fname, 10)
        if _f.family() == _fname or _fname in ["Segoe UI", "Arial"]:  # system fonts always match
            _app_font = _f
            break
    app.setFont(_app_font if _app_font else QFont("Arial", 10))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
