import time
import math
import board
import adafruit_icm20x
from adafruit_icm20x import AccelRange, GyroRange
from audioio import AudioOut
from audiocore import WaveFile

# Audio output (same as your other project)
audio = AudioOut(board.DAC)



GRAVITY = 9.8

# -------------------------
# IMU INITIALIZATION
# -------------------------
i2c = board.I2C()
icm = adafruit_icm20x.ICM20948(i2c, 0x69)

icm.accelerometer_range = AccelRange.RANGE_4G      # RANGE_2G / RANGE_4G / RANGE_8G / RANGE_16G
icm.gyro_range = GyroRange.RANGE_1000_DPS          # RANGE_250_DPS / RANGE_500_DPS / RANGE_1000_DPS / RANGE_2000_DPS

print("Initial ranges: accel=±4g, gyro=±1000dps")

# -------------------------
# QUICK CALIBRATION
# -------------------------
def quick_calibration(duration=3.0, sample_interval=0.02):
    print(f"\nCalibrating for {duration}s... Move the baton.\n")
    end_time = time.monotonic() + duration
    max_acc_g = 0.0
    max_gyro_rads = 0.0

    while time.monotonic() < end_time:
        ax, ay, az = icm.acceleration
        gx, gy, gz = icm.gyro

        accel_mag = math.sqrt(ax*ax + ay*ay + az*az)
        accel_extra_g = max(0.0, (accel_mag - GRAVITY) / GRAVITY)
        gyro_mag = math.sqrt(gx*gx + gy*gy + gz*gz)

        if accel_extra_g > max_acc_g:
            max_acc_g = accel_extra_g
        if gyro_mag > max_gyro_rads:
            max_gyro_rads = gyro_mag

        time.sleep(sample_interval)

    # Auto thresholds (fraction of max)
    accel_th = max(0.8, max_acc_g * 0.4)
    gyro_th = max(3.0, max_gyro_rads * 0.5)

    print("Calibration done.")
    print(f"Max extra accel: {max_acc_g:.2f} g")
    print(f"Max angular speed: {max_gyro_rads:.2f} rad/s")
    print(f"Suggested accel threshold: {accel_th:.2f} g")
    print(f"Suggested gyro threshold:  {gyro_th:.2f} rad/s\n")
    return accel_th, gyro_th

ACCEL_THRESHOLD_G, GYRO_THRESHOLD_RAD = quick_calibration()

# -------------------------
# BEAT DETECTION CONFIG
# -------------------------
COOLDOWN_SEC = 0.25      # Minimum time between beats
USE_FILTER = True
FILTER_ALPHA = 0.30      # Higher = more responsive, lower = smoother

last_beat_time = 0.0
beat_count = 0
bpm_start_time = None

accel_f = 0.0
gyro_f = 0.0

print("Beat detection started (printing ONLY beats).")
print(f"Accel threshold: {ACCEL_THRESHOLD_G:.2f} g | Gyro threshold: {GYRO_THRESHOLD_RAD:.2f} rad/s\n")

# Preload the beat sound
try:
    beat_file = WaveFile(open("beat.wav", "rb"))
    print("Loaded beat.wav")
except Exception as e:
    print("ERROR loading sounds/beat.wav:", e)
    beat_file = None


# Keep references to currently playing sound(s)
active_sounds = []   # each entry: {"file": fp, "wave": wf}

# preload + keep file open the whole program
try:
    beat_fp = open("beat.wav", "rb")
    beat_wav = WaveFile(beat_fp)
    print("Loaded beat.wav")
except Exception as e:
    print("ERROR loading beat.wav:", e)
    beat_fp = None
    beat_wav = None


def play_beat_sound():
    if not beat_wav:
        print("[No WAV loaded]")
        return

    # Immediately cut current playback.
    if audio.playing:
        audio.stop()

    # Restart from beginning.
    beat_fp.seek(0)
    audio.play(beat_wav)


# -------------------------
# MAIN LOOP
# -------------------------
while True:
    ax, ay, az = icm.acceleration
    gx, gy, gz = icm.gyro

    accel_mag = math.sqrt(ax*ax + ay*ay + az*az)
    accel_extra_g = max(0.0, (accel_mag - GRAVITY) / GRAVITY)
    gyro_mag = math.sqrt(gx*gx + gy*gy + gz*gz)

    if USE_FILTER:
        accel_f = accel_f * (1 - FILTER_ALPHA) + accel_extra_g * FILTER_ALPHA
        gyro_f = gyro_f * (1 - FILTER_ALPHA) + gyro_mag * FILTER_ALPHA
        accel_used = accel_f
        gyro_used = gyro_f
    else:
        accel_used = accel_extra_g
        gyro_used = gyro_mag

    now = time.monotonic()
    beat_condition = (accel_used > ACCEL_THRESHOLD_G) or (gyro_used > GYRO_THRESHOLD_RAD)
    can_trigger = (now - last_beat_time) > COOLDOWN_SEC

    if beat_condition and can_trigger:
        beat_count += 1
        last_beat_time = now

        if bpm_start_time is None:
            bpm_start_time = now
            bpm_text = "BPM: (estimating)"
        else:
            elapsed = now - bpm_start_time
            bpm = (beat_count - 1) / elapsed * 60.0
            bpm_text = f"BPM: {bpm:.1f}"

        source = "ACCEL" if accel_used > ACCEL_THRESHOLD_G else "GYRO"
        play_beat_sound()
        print(f"🎵 Beat #{beat_count} [{source}] accel={accel_used:.2f}g gyro={gyro_used:.2f}rad/s")

    time.sleep(0.01)  # ~50 Hz