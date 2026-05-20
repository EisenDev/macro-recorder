import evdev
import sys

try:
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    if devices:
        print("SUCCESS reading devices")
    else:
        print("No devices found")
except Exception as e:
    print("FAILED reading", e)

try:
    ui = evdev.UInput()
    print("SUCCESS creating uinput")
    ui.close()
except Exception as e:
    print("FAILED uinput", e)
