# Macro Recorder / Automator

A clean, minimalist, and highly functional Macro Automator built with Python (PyQt6 and pynput). This tool allows you to easily record your mouse movements, clicks, and keyboard strokes, and play them back later. You can also save your macros to JSON files and load them up anytime!

> **⚠️ Important Notice for Linux Users**
> This application requires absolute mouse positioning. The Wayland display server prevents apps from interacting with absolute global coordinates for security reasons. Therefore, to record and play macros on Ubuntu/Linux, you must use **Xorg**.
> 
> *To switch to Xorg: Log out of your session, click your username, click the gear icon in the bottom right corner, and select **"Ubuntu on Xorg"** before logging back in.*

## Features
- **Record & Playback:** Seamlessly record and reproduce exact mouse movements, clicks, scrolls, and keystrokes.
- **Loop Settings:** Run your macros once, twice, or endlessly with the Loop dropdown.
- **Save & Load Macros:** Export your recorded workflows as `.json` files and reuse them later.
- **Minimalist GUI:** An elegant, portfolio-style aesthetic that stays out of your way.
- **Mini-Recorder Mode:** When recording, the main app minimizes into a tiny, distraction-free widget.
- **Emergency Stop:** Press `Alt + X` at any time to instantly stop recording or playback.

## How to Run Locally (via Terminal)

This project comes with a handy shell script to automatically set up your virtual environment, install dependencies, and launch the application.

1. Open your terminal.
2. Navigate to the project directory:
   ```bash
   cd /path/to/macro_recorder
   ```
3. Run the startup script:
   ```bash
   ./run.sh
   ```
*If you get a permissions error, make the script executable first by running: `chmod +x run.sh`*

## Troubleshooting

- **"Wayland Strictly Prohibited" Error:** You are running a Wayland session. Please log out and switch to Xorg (see the important notice above).
- **No module named PyQt6 / pynput:** The `run.sh` script should install these automatically. If it fails, ensure `python3-venv` is installed on your system (`sudo apt install python3-venv`).
