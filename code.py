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
import displayio
import digitalio
import microcontroller
from fourwire import FourWire
from adafruit_st7789 import ST7789
import terminalio
from adafruit_display_text import label

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
clap_fp, clap_wav = load_wav("clap-drum.wav")
success_fp, success_wav = load_wav("success.wav")
fail_fp, fail_wav = load_wav("fail.wav")
go_fp, go_wav = load_wav("go.wav")
boot_fp, boot_wav = load_wav("boot.wav")

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
# SCREEN
# ============================================================


# =========================
# AJUSTES
# =========================
ROTATION = 180  # 0, 90, 180, 270

FRAME_DURATION = 0.005  # tiempo por frame (segundos)

# Rutas de los BMP (135x240)
FRAME_FILES = [
    "calibrating-0.bmp",
    "calibrating-1.bmp",
    "calibrating-2.bmp",
    "calibrating-3.bmp",
]
# =========================
# INICIALIZAR BACKLIGHT
# =========================
backlight = digitalio.DigitalInOut(microcontroller.pin.PA06)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = False  # activo en LOW → encendido

# =========================
# INICIALIZAR DISPLAY
# =========================
displayio.release_displays()

spi = board.LCD_SPI()
tft_cs = board.LCD_CS
tft_dc = board.D4

DISPLAY_WIDTH = 135
DISPLAY_HEIGHT = 240  # pantalla en vertical

display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs)
display = ST7789(
    display_bus,
    rotation=ROTATION,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=40,
    colstart=53,
)

# Grupo raíz
splash = displayio.Group()
display.root_group = splash

def start(tiempo):
    """
    Muestra la imagen 'start.bmp' a pantalla completa
    durante 'tiempo' segundos y luego la quita.
    """
    # Abrir el BMP (debe estar en CIRCUITPY como /start.bmp)
    f = open("/start.bmp", "rb")
    bmp = displayio.OnDiskBitmap(f)
    tile = displayio.TileGrid(bmp, pixel_shader=bmp.pixel_shader)

    # Mostrar la imagen
    splash.append(tile)

    # Mantenerla en pantalla el tiempo indicado
    time.sleep(tiempo)

    # Quitar la imagen y cerrar el archivo
    splash.remove(tile)
    f.close()

# Fondo (paleta de 1 color)
background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)

# =========================
# FUNCIÓN success(tiempo)
# =========================
def success(tiempo):
    """
    Muestra el fondo verde y los textos:
        WELL
        DONE
    centrados durante 'tiempo' segundos.
    Luego elimina los textos.
    """
    background_palette = displayio.Palette(1)
    background_palette[0] = 0x00FF00  # verde
    background = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)
    splash.append(background)

    # LABEL "WELL"
    well_label = label.Label(
        terminalio.FONT,
        text="WELL",
        color=0x000000,  # negro sobre verde
        scale=4          # tamaño del texto
    )
    well_label.anchor_point = (0.5, 0.5)
    well_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 - 20)

    # LABEL "DONE"
    done_label = label.Label(
        terminalio.FONT,
        text="DONE",
        color=0x000000,
        scale=4
    )
    done_label.anchor_point = (0.5, 0.5)
    done_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 20)

    # Mostrar ambos labels
    splash.append(well_label)
    splash.append(done_label)
    
    # Mantener en pantalla
    time.sleep(tiempo)

    # Quitar los labels (el fondo verde permanece)
    splash.remove(well_label)
    splash.remove(done_label)
    splash.remove(background)

def failure(tiempo):
    background_palette = displayio.Palette(1)
    background_palette[0] = 0xFF0000  # rojo
    background = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)
    splash.append(background)
    """
    Muestra el fondo rojo y los textos:
        TRY
        AGAIN
    centrados durante 'tiempo' segundos.
    Luego elimina los textos.
    """

    # LABEL "TRY"
    try_label = label.Label(
        terminalio.FONT,
        text="TRY",
        color=0x000000,  # negro sobre rojo
        scale=4          # tamaño del texto
    )
    try_label.anchor_point = (0.5, 0.5)
    try_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 - 20)

    # LABEL "AGAIN"
    again_label = label.Label(
        terminalio.FONT,
        text="AGAIN",
        color=0x000000,
        scale=4
    )
    again_label.anchor_point = (0.5, 0.5)
    again_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 20)

    # Mostrar ambos labels
    splash.append(try_label)
    splash.append(again_label)
    
    # Mantener en pantalla
    time.sleep(tiempo)

    # Quitar los labels (el fondo rojo permanece)
    splash.remove(try_label)
    splash.remove(again_label)
    splash.remove(background)


# ============================================================
# QUICK CALIBRATION
# ============================================================

def quick_calibration(duration=3.0):
    print(f"\nCalibrating for {duration}s... Move the baton.\n")

    start_t = time.monotonic()
    next_frame_t = start_t
    frame_index = 0

    max_acc_g = 0.0
    max_gyro = 0.0

    # Pre-load bitmaps once for speed
    frames = []
    for path in FRAME_FILES:
        f = open(path, "rb")
        bmp = displayio.OnDiskBitmap(f)
        tile = displayio.TileGrid(bmp, pixel_shader=bmp.pixel_shader)
        frames.append((tile, f))

    # Show first frame
    splash.append(frames[0][0])

    while True:
        now = time.monotonic()
        elapsed = now - start_t

        # End calibration
        if elapsed >= duration:
            break

        # ---- IMU SAMPLING ----
        ax, ay, az = icm.acceleration
        gx, gy, gz = icm.gyro

        accel_mag = math.sqrt(ax*ax + ay*ay + az*az)
        accel_extra = max(0, (accel_mag - GRAVITY)/GRAVITY)
        gyro_mag = math.sqrt(gx*gx + gy*gy + gz*gz)

        if accel_extra > max_acc_g:
            max_acc_g = accel_extra
        if gyro_mag > max_gyro:
            max_gyro = gyro_mag

        # ---- FRAME UPDATE (non-blocking) ----
        if now >= next_frame_t:
            # Remove old frame
            splash.pop()

            # Move to next frame
            frame_index = (frame_index + 1) % len(frames)
            splash.append(frames[frame_index][0])

            next_frame_t = now + FRAME_DURATION

        # Tiny sleep to allow USB tasks + display refresh
        time.sleep(0.005)

    # Cleanup — remove animation and close files
    if len(splash) > 0:
        splash.pop()

    for tile, f in frames:
        f.close()

    # ---- Compute thresholds ----
    accel_th = max(0.8, max_acc_g * 0.35)
    gyro_th = max(3.0, max_gyro * 0.45)

    print("\nCalibration done.")
    print(f"Max accel extra g: {max_acc_g:.2f}")
    print(f"Max gyro rad/s:   {max_gyro:.2f}")
    print(f"Accel threshold:  {accel_th:.2f}")
    print(f"Gyro threshold:   {gyro_th:.2f}\n")

    return accel_th, gyro_th


play_wav(boot_fp,boot_wav)
start(5)

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
    
    def first(self):
        return self.pattern[0]

    def duration(self):
        return self.pattern[-1] if self.pattern else 0

LEVELS = [
    # -------------------------------
    # EASY: Quarter + light eighths
    # -------------------------------
    Level("Level 1",  [0.5, 1.0, 1.5, 2.0]),

    Level("Level 2",  [0.5, 0.75, 1.0, 1.25]),

    Level("Level 3",  [0.25, 0.50, 1.0, 1.25, 1.5]),

    Level("Level 4",  [0.25, 0.50, 1.0, 1.25, 1.75]),

    Level("Level 11 (Swing A)",
      [0.50, 1.16, 1.66, 2.33, 2.83]),
    # Swung eighths → long–short–long–short feel
    # (1.16 ≈ 0.5 + 2/3 beat, 1.66 ≈ 1.16 + 1/2 beat)

    Level("Level 12 (Triplet Clave)",
        [0.33, 0.66, 1.00, 1.66, 2.33, 2.66]),
    # Pure triplet grid; extremely musical, very fun


    Level("Level 5",  [0.5, 1.50, 1.75, 2.25, 3.0]),

    Level("Level 6",  [0.25, 0.75, 1.25, 1.75, 2.25]),  
    # “Clap… clap… clapclap… clap” pattern

    Level("Level 14 (3-3-2 Afro Pulse)",
        [0.33, 0.66, 1.00, 1.66, 2.33, 2.66]),
    # Classic 3-3-2 rhythmic cell, repeated twice

    Level("Level 15 (Slow–Fast–Fast)",
        [0.75, 1.25, 1.45, 1.65, 2.15, 2.65, 2.85]),


    Level("Level 7",  [0.50, 1.00, 1.50, 1.75, 2.25, 2.75]),  
    # Straight quarters → spicy eighth → quarter

    Level("Level 8",  [0.25, 0.50, 0.75, 1.50, 2.00, 2.50]),  
    # Triplet-ish feel then big spaces

    Level("Level 9",  [0.50, 1.25, 1.50, 2.00, 2.75]),  
    # Quarter → syncopated pair → quarter → big hit

    Level("Level 10",[0.25, 0.75, 1.00, 1.25, 1.75, 2.25, 2.75]),  
    # Fun fast 8ths, ends with a clean spaced outro
    
    Level("Level 13 (Dotted Quarter Pulse)",
        [0.50, 2.00, 2.75, 3.25]),
    # Dotted quarter (1.5s), then tight syncopations

    

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
            play_wav(clap_fp, clap_wav)
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
        input_window = level.duration() * 2   # 30% more time than pattern length

        if elapsed_total >= level.duration() + input_window:
            break

        time.sleep(0.005)


    # ---- SCORE (normalized to first user hit) ----

    # 1) CHECK COUNT FIRST (hard fail)
    expected = len(pattern)
    actual = len(user_shakes)

    if actual != expected:
        print(f"❌ Wrong number of shakes! Expected {expected}, got {actual}.")
        print(f"Score: 0% (0/{expected})")
        return 0

    # 2) Normal case: compute timing alignment
    offset = user_shakes[0] - level.first()
    normalized_user = [t - offset for t in user_shakes]

    print("User normalized shakes:", ["{:.2f}".format(t) for t in normalized_user])

    used = set()
    correct = 0


    for beat in pattern:
        best_idx = None
        best_diff = 0.1  # tolerance

        for i, t in enumerate(normalized_user):
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

play_wav(go_fp, go_wav)

while True:
    level = LEVELS[current_level]
    
    score = run_level(level)

    if score >= MIN_SCORE:
        play_wav(success_fp, success_wav)
        success(3)
        print(f"🎉 SUCCESS! Advancing to next level.\n")
        
        current_level = (current_level + 1) % len(LEVELS)
        play_wav(go_fp, go_wav)
    else:
        play_wav(fail_fp, fail_wav)
        failure(3)
        print("❌ FAILED — try again.\n")
        play_wav(go_fp, go_wav)

    time.sleep(1.0)
