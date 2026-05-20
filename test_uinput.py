import evdev
from evdev import ecodes
import time

caps = {
    ecodes.EV_KEY: list(range(0, 255)) + [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE],
    ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL, ecodes.REL_HWHEEL]
}
try:
    ui = evdev.UInput(events=caps, name="MacroAutomator")
    print("Created UInput")
    time.sleep(1) # wait for libinput to detect it
    # Move mouse right 100 pixels
    ui.write(ecodes.EV_REL, ecodes.REL_X, 100)
    ui.syn()
    print("Injected event")
    time.sleep(1)
    ui.close()
    print("Closed")
except Exception as e:
    print("Error:", e)
