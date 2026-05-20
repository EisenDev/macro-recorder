import time
import json
import threading
from pynput import mouse, keyboard

class MacroEngine:
    def __init__(self):
        self.events = []
        self.is_recording = False
        self.is_playing = False
        self.start_time = 0
        
        self.mouse_listener = None
        self.keyboard_listener = None
        
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        self.pressed_keys = set()
        self.on_stop_callback = None

    def set_on_stop_callback(self, callback):
        self.on_stop_callback = callback

    def start_recording(self):
        if self.is_recording or self.is_playing:
            return
            
        self.events = []
        self.is_recording = True
        self.start_time = time.time()
        
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        if self.on_stop_callback:
            self.on_stop_callback()

    def _record_event(self, event_data):
        if self.is_recording:
            event_data['time'] = time.time() - self.start_time
            self.events.append(event_data)

    def _on_move(self, x, y):
        self._record_event({'type': 'mouse_move', 'x': x, 'y': y})

    def _on_click(self, x, y, button, pressed):
        self._record_event({
            'type': 'mouse_click', 
            'x': x, 
            'y': y, 
            'button': str(button), 
            'pressed': pressed
        })

    def _on_scroll(self, x, y, dx, dy):
        self._record_event({
            'type': 'mouse_scroll', 
            'x': x, 
            'y': y, 
            'dx': dx, 
            'dy': dy
        })

    def _on_press(self, key):
        try:
            self.pressed_keys.add(key)
        except Exception:
            pass

        # Check for Alt + X
        if (keyboard.Key.alt_l in self.pressed_keys or keyboard.Key.alt_r in self.pressed_keys) and \
           (getattr(key, 'char', None) == 'x' or getattr(key, 'char', None) == 'X'):
            self.stop_recording()
            return False
            
        # Try to get char if possible, else use string representation
        key_str = getattr(key, 'char', str(key))
        self._record_event({'type': 'key_press', 'key': key_str})

    def _on_release(self, key):
        try:
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
        except Exception:
            pass

        # Check for Alt + X release just in case
        if (keyboard.Key.alt_l in self.pressed_keys or keyboard.Key.alt_r in self.pressed_keys) and \
           (getattr(key, 'char', None) == 'x' or getattr(key, 'char', None) == 'X'):
            return False
            
        key_str = getattr(key, 'char', str(key))
        self._record_event({'type': 'key_release', 'key': key_str})

    def _parse_key(self, key_str):
        # Convert string back to keyboard.Key or char
        if key_str.startswith('Key.'):
            return getattr(keyboard.Key, key_str.split('.')[1])
        elif len(key_str) == 1:
            return key_str # it's a character
        elif key_str.startswith("'") and key_str.endswith("'") and len(key_str) == 3:
            return key_str[1]
        else:
            return key_str

    def _parse_mouse_button(self, button_str):
        if button_str.startswith('Button.'):
            return getattr(mouse.Button, button_str.split('.')[1])
        return mouse.Button.left

    def start_playback(self, loop_count=1):
        if self.is_recording or self.is_playing or not self.events:
            return
            
        self.is_playing = True
        self.loop_count = loop_count
        
        self.pressed_keys = set()
        
        # Start a listener just for the stop key
        self.playback_listener = keyboard.Listener(
            on_press=self._on_playback_keypress,
            on_release=self._on_playback_keyrelease
        )
        self.playback_listener.start()
        
        # Run playback in a separate thread so we don't block
        threading.Thread(target=self._play_events, daemon=True).start()

    def _on_playback_keypress(self, key):
        try:
            self.pressed_keys.add(key)
        except Exception:
            pass
            
        if (keyboard.Key.alt_l in self.pressed_keys or keyboard.Key.alt_r in self.pressed_keys) and \
           (getattr(key, 'char', None) == 'x' or getattr(key, 'char', None) == 'X'):
            self.stop_playback()
            return False

    def _on_playback_keyrelease(self, key):
        try:
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
        except Exception:
            pass

    def stop_playback(self):
        self.is_playing = False
        if hasattr(self, 'playback_listener') and self.playback_listener:
            self.playback_listener.stop()
            
        if self.on_stop_callback:
            self.on_stop_callback()

    def _play_events(self):
        loops_done = 0
        while self.is_playing and (self.loop_count == 0 or loops_done < self.loop_count):
            current_time = 0
            for event in self.events:
                if not self.is_playing:
                    break
                    
                sleep_time = event['time'] - current_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                current_time = event['time']
                
                try:
                    if event['type'] == 'mouse_move':
                        self.mouse_controller.position = (event['x'], event['y'])
                    elif event['type'] == 'mouse_click':
                        button = self._parse_mouse_button(event['button'])
                        if event['pressed']:
                            self.mouse_controller.press(button)
                        else:
                            self.mouse_controller.release(button)
                    elif event['type'] == 'mouse_scroll':
                        self.mouse_controller.scroll(event['dx'], event['dy'])
                    elif event['type'] == 'key_press':
                        key = self._parse_key(event['key'])
                        self.keyboard_controller.press(key)
                    elif event['type'] == 'key_release':
                        key = self._parse_key(event['key'])
                        self.keyboard_controller.release(key)
                except Exception as e:
                    print(f"Error executing event {event}: {e}")
            loops_done += 1
                
        self.stop_playback()

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=4)

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                self.events = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return False
