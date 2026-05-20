import macro_engine
engine = macro_engine.MacroEngine()
engine.start_recording()
print("Recording started. Please press some keys and move the mouse.")
import time
time.sleep(3)
engine.stop_recording()
print(f"Recorded {len(engine.events)} events.")
engine.start_playback()
time.sleep(3)
print("Done.")
