import evdev
import selectors
import time

def read_events():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    sel = selectors.DefaultSelector()
    for dev in devices:
        sel.register(dev, selectors.EVENT_READ)
    
    print("Listening... Press Ctrl+C to stop.")
    start = time.time()
    try:
        while time.time() - start < 5: # Listen for 5 seconds
            for key, mask in sel.select(timeout=1.0):
                device = key.fileobj
                for event in device.read():
                    if event.type == evdev.ecodes.EV_KEY:
                        key_event = evdev.categorize(event)
                        print(f"Key: {key_event.keycode} {'DOWN' if key_event.keystate == 1 else 'UP'}")
                    elif event.type == evdev.ecodes.EV_REL:
                        print(f"Rel: {evdev.ecodes.REL[event.code]} {event.value}")
    except Exception as e:
        print("Error:", e)
    finally:
        for dev in devices:
            dev.close()
            
read_events()
