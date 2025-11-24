# ------------------------------------------------------------
# RHYTHM GAME WITH REAL IMU SHAKE DETECTION (NO DISPLAY)
# ------------------------------------------------------------

import time
import math
import board
import adafruit_icm20x
from adafruit_icm20x import AccelRange, GyroRange
from audioio import AudioOut
from audiocore import WaveFile

GRAVITY = 9.8

# ============================================================
# AUDIO SETUP
# ============================================================

audio = AudioOut(board.DAC)

def load_wav(filename):
    try:
        fp = open(filename, "rb")
        wav = WaveFile(fp)
        print("Loaded:", filename)
        return fp, wav
    except Exception as e:
        print("ERROR loading", filename, ":", e)
        return None, None

# WAV locations (same directories as your working test!)
beat_fp, beat_wav = load_wav("beat.wav")
success_fp, success_wav = load_wav("success.wav")
fail_fp, fail_wav = load_wav("fail.wav")

def play_wav(fp, wav):
    if not wav:
        print("[Missing WAV]")
        return
    if audio.playing:
        audio.stop()
    fp.seek(0)
    audio.play(wav)

# ============================================================
# IMU SETUP
# ============================================================

i2c = board.I2C()
icm = adafruit_icm20x.ICM20948(i2c, 0x69)

icm.accelerometer_range = AccelRange.RANGE_4G
icm.gyro_range = GyroRange.RANGE_1000_DPS

print("IMU configured: accel=±4g, gyro=±1000dps\n")

# ============================================================
# QUICK CALIBRATION
# ============================================================

def quick_calibration(duration=3.0):
    print(f"\nCalibrating for {duration}s... Move the baton.\n")
    end = time.monotonic() + duration
    max_acc_g = 0.0
    max_gyro = 0.0

    while time.monotonic() < end:
        ax, ay, az = icm.acceleration
        gx, gy, gz = icm.gyro

        accel_mag = math.sqrt(ax*ax + ay*ay + az*az)
        accel_extra = max(0, (accel_mag - GRAVITY)/GRAVITY)
        gyro_mag = math.sqrt(gx*gx + gy*gy + gz*gz)

        max_acc_g = max(max_acc_g, accel_extra)
        max_gyro = max(max_gyro, gyro_mag)

        time.sleep(0.02)

    accel_th = max(0.8, max_acc_g * 0.35)
    gyro_th = max(3.0, max_gyro * 0.45)

    print("\nCalibration done.")
    print(f"Max accel extra g: {max_acc_g:.2f}")
    print(f"Max gyro rad/s:   {max_gyro:.2f}")
    print(f"Accel threshold:  {accel_th:.2f}")
    print(f"Gyro threshold:   {gyro_th:.2f}\n")

    return accel_th, gyro_th

ACCEL_TH, GYRO_TH = quick_calibration()

# ============================================================
# REAL SHAKE DETECTOR
# ============================================================

COOLDOWN = 0.25
FILTER_ALPHA = 0.30

accel_f = 0
gyro_f = 0
last_shake_time = 0

def detect_shake():
    """Returns True exactly when a beat/shake happens."""
    global accel_f, gyro_f, last_shake_time

    ax, ay, az = icm.acceleration
    gx, gy, gz = icm.gyro

    accel_mag = math.sqrt(ax*ax + ay*ay + az*az)
    accel_extra = max(0, (accel_mag - GRAVITY)/GRAVITY)
    gyro_mag = math.sqrt(gx*gx + gy*gy + gz*gz)

    # filtering
    accel_f = accel_f*(1-FILTER_ALPHA) + accel_extra*FILTER_ALPHA
    gyro_f = gyro_f*(1-FILTER_ALPHA) + gyro_mag*FILTER_ALPHA

    now = time.monotonic()

    shake = (accel_f > ACCEL_TH) or (gyro_f > GYRO_TH)
    cooldown_ok = (now - last_shake_time) > COOLDOWN

    if shake and cooldown_ok:
        last_shake_time = now
        play_wav(beat_fp, beat_wav)
        return True

    return False

# ============================================================
# RHYTHM GAME LOGIC
# ============================================================

class Level:
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern  # list of seconds: [0.5, 1.0, 1.5...]

    def duration(self):
        return self.pattern[-1] if self.pattern else 0

LEVELS = [
    Level("Level 1", [0.5, 1.0, 1.5, 2.0]),                     # 4 straight beats
    Level("Level 2", [0.5, 1.25, 2.0, 2.75]),                   # evenly spaced, slower

    Level("Level 3", [0.5, 1.0, 1.75, 2.5]),                    # slight syncopation
    Level("Level 4", [0.5, 1.0, 1.5, 2.25, 3.0]),               # 5 steady beats

    Level("Level 5", [0.5, 1.1, 1.7, 2.4, 3.1]),                # gentle irregularity
    Level("Level 6", [0.4, 0.9, 1.5, 2.2, 3.0]),                # simple but varied

    Level("Level 7", [0.5, 1.0, 1.4, 1.9, 2.5, 3.1]),           # 6-beat pattern
    Level("Level 8", [0.4, 1.0, 1.6, 2.2, 2.8, 3.4]),           # evenly spaced quick 6

    Level("Level 9", [0.35, 0.95, 1.6, 2.3, 2.9, 3.6]),         # slightly more syncopated
    Level("Level 10", [0.5, 1.0, 1.25, 1.75, 2.25, 2.75, 3.25]) # 7 beats, structured pattern
]

MIN_SCORE = 80


def run_level(level: Level):
    """Play rhythm once, record user's shakes, return score."""
    print(f"\n=== Starting {level.name} ===")
    print("Listen to the pattern...")

    pattern = level.pattern
    play_start = time.monotonic()
    play_idx = 0
    user_shakes = []

    # ---- PLAY THE PATTERN ----
    while True:
        now = time.monotonic()
        elapsed = now - play_start

        # play the next beat in pattern
        if play_idx < len(pattern) and elapsed >= pattern[play_idx]:
            play_wav(beat_fp, beat_wav)
            print(f"Beat {play_idx+1} at t={elapsed:.2f}")
            play_idx += 1

        # done playing pattern → move to input phase
        if play_idx == len(pattern) and elapsed >= level.duration() + 0.2:
            print("Now you repeat the rhythm...")
            break

        time.sleep(0.005)

    # ---- USER INPUT PHASE ----
    input_offset = play_start + level.duration()
    user_shakes = []

    while True:
        now = time.monotonic()
        elapsed_total = now - play_start

        # shakes relative to input phase
        if detect_shake():
            shake_t = now - input_offset
            if shake_t >= 0:  # ignore shakes before input
                user_shakes.append(shake_t)
                print(f"User shake at t={shake_t:.2f}")

        # Give as much time to respond as the pattern itself + some buffer
        input_window = level.duration() * 1.3   # 30% more time than pattern length

        if elapsed_total >= level.duration() + input_window:
            break

        time.sleep(0.005)


    # ---- SCORE ----
    used = set()
    correct = 0

    for beat in pattern:
        best_idx = None
        best_diff = 0.25  # tolerance

        for i, t in enumerate(user_shakes):
            if i in used:
                continue
            diff = abs(t - beat)
            if diff <= best_diff:
                best_diff = diff
                best_idx = i

        if best_idx is not None:
            used.add(best_idx)
            correct += 1

    score = int(100 * correct / len(pattern))
    print(f"Score: {score}% ({correct}/{len(pattern)})")

    return score


# ============================================================
# MASTER GAME LOOP
# ============================================================

current_level = 0

while True:
    level = LEVELS[current_level]
    score = run_level(level)

    if score >= MIN_SCORE:
        play_wav(success_fp, success_wav)
        print(f"🎉 SUCCESS! Advancing to next level.\n")
        current_level = (current_level + 1) % len(LEVELS)
    else:
        play_wav(fail_fp, fail_wav)
        print("❌ FAILED — try again.\n")

    time.sleep(1.0)
