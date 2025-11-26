# SundAI_Rhythm

A physical rhythm game for CircuitPython devices that uses a real IMU (accelerometer + gyro) to detect baton/shake hits and grades the player's timing against musical patterns. The project plays WAV audio feedback and shows simple display screens for calibration, success and failure.

This repository contains the CircuitPython code used to:
- play rhythmic patterns,
- detect real shakes from an IMU (ICM20948 in the reference code),
- provide audio feedback (beat, clap, success, failure),
- show simple full-screen bitmap/images for calibration and results.

---

## Features

- Real-time shake detection using accelerometer + gyroscope with filtering and cooldown.
- Quick calibration routine that computes sensible thresholds from user motion while animating BMP frames.
- Set of built-in rhythm levels (straight, swung, triplet and syncopated patterns).
- Audio feedback for beats, success, failure and boot/go cues.
- Simple display screens for start, calibration, success (green), failure (red).

---

## Hardware & CircuitPython requirements

This project targets a CircuitPython-capable board with:
- An IMU compatible with the Adafruit ICM20x library (the code instantiates `adafruit_icm20x.ICM20948`).
- A SPI-connected ST7789 display (code uses `adafruit_st7789` and a FourWire display bus).
- A DAC-capable audio output accessible as `board.DAC` (used by `audioio.AudioOut`).
- A suitable pin for backlight control (the reference uses `microcontroller.pin.PA06`).
- Sufficient filesystem storage to hold WAV and BMP assets on the CIRCUITPY drive.

CircuitPython libraries used (add these to /lib on the CIRCUITPY drive):
- adafruit_icm20x
- adafruit_st7789
- adafruit_display_text
- terminalio
- fourwire (display bus helper)
- audioio, audiocore (native to many CircuitPython builds)
- displayio, digitalio, board, microcontroller, time, math (core modules)

Make sure your CircuitPython build supports audio output, displayio, and the audio libraries used here.

---

## Repository layout

- code.py — Main game logic (beat playback, calibration, shake detection, level system, master loop).
- code_working.py, code_sound.py, analog.py, changing_color_gyro.py — experimental/utility scripts and variants.
- calibrating_function.py — calibration helper code.
- start_function.py, success_function.py, failure_function.py — display helper functions (start/success/failure screens).
- gif_victory_red_failure.py — alternate display/animation helper.
- color_background.py — small display helper.
- lib/ — place required CircuitPython library packages here on your device.
- sounds/ — (directory) recommended place for WAVs (code expects files in root, see notes).
- image/ — (directory) BMP images used for calibration and start screens.

Note: code.py expects the following WAV files to be present on the device root:
- beat.wav
- clap-drum.wav
- success.wav
- fail.wav
- go.wav
- boot.wav

And the following BMP files (frames for the calibration animation) with names and approximate size as used in the code:
- calibrating-0.bmp
- calibrating-1.bmp
- calibrating-2.bmp
- calibrating-3.bmp
- start.bmp (used by the start() helper)

Place these files at the root of the CIRCUITPY drive or update paths in the code.

---

## Installation / Quick setup

1. Flash CircuitPython to your supported board.
2. Copy required library files into CIRCUITPY/lib (see the Libraries list above).
3. Copy all Python files from this repository to the root of the CIRCUITPY drive.
4. Copy WAV files and BMPs to the device root (or adjust filenames/paths in code.py to where you place them).
5. Power the board. The game plays `boot.wav`, shows the start screen, then runs a quick calibration and starts the game loop.

---

## How to run (user flow)

- On power-up the code plays a boot sound and shows the start screen.
- Quick calibration runs: move the baton around so the code can estimate max accelerations and angular rates; this computes dynamic thresholds used by the shake detector.
- The game plays a rhythm pattern (you hear claps). After the pattern plays, repeat the rhythm by shaking the baton. The system records timing and scores you.
- Reaching the minimum score advances you to the next level; failing shows the failure screen and lets you retry.

---

## Calibration & tuning tips

- The quick calibration routine is automatic and typically produces usable thresholds. If the sensor or user's motion style differs, you can adjust constants in code.py:
  - ROTATION — display rotation (0, 90, 180, 270).
  - FRAME_DURATION — calibration animation frame timing.
  - COOLDOWN — minimum interval between detected shakes.
  - FILTER_ALPHA — smoothing used in the real-time detector.
  - MIN_SCORE — minimum percent to pass a level.
- If you find false positives or missed hits, tweak ACCEL_TH and GYRO_TH manually (they are computed after calibration but can be overridden if needed).

---

## Customizing patterns & levels

Levels are defined in code.py as Level(name, pattern) where pattern is a list of beat times (seconds) relative to the start of the pattern. To add or edit levels:
- Edit the LEVELS list in code.py.
- Each Level's pattern is a list of times (e.g., [0.5, 1.0, 1.5]).
- The scoring normalizes to the first user hit and uses a ±0.1s tolerance for matching beats.

---

## Contributing

Contributions, bug reports and improvements are welcome. If you submit changes, please:
- Keep CircuitPython compatibility in mind.
- Test on a device when possible (hardware-specific issues are common).
- Include sample WAV/BMP test assets if adding display or audio features.

---

## License & Credits

- Author: repository owners.
