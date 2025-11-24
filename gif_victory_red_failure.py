import time
import random
import board
import displayio
import digitalio
import microcontroller
from fourwire import FourWire
from adafruit_st7789 import ST7789
from adafruit_display_text import label
import terminalio

# =========================
# AJUSTES GENERALES
# =========================
# Rotación del display (0, 90, 180, 270)
ROTATION = 180

# Tiempo entre números (en segundos)
DELAY_BETWEEN_SCORES = 3.0

# Duración de cada frame de la animación (en segundos)
FRAME_DURATION = 0.15

# Rutas de los BMP de la animación (135x240)
FRAME_FILES = [
    "/sprite_0.bmp",
    "/sprite_1.bmp",
    "/sprite_2.bmp",
    "/sprite_3.bmp",
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

# Pantalla en vertical
DISPLAY_WIDTH = 135
DISPLAY_HEIGHT = 240

display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs)
display = ST7789(
    display_bus,
    rotation=ROTATION,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=40,
    colstart=53
)

# Grupo raíz
splash = displayio.Group()
display.root_group = splash

# =========================
# FONDO (PALETA DE 1 COLOR)
# =========================
background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
background_palette = displayio.Palette(1)
background_palette[0] = 0xFF0000  # empezamos en rojo (score < 80)
background = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)
splash.append(background)  # índice 0

# =========================
# LABEL "SCORE" (TÍTULO)
# =========================
score_title = label.Label(
    terminalio.FONT,
    text="SCORE",
    color=0xFFFFFF,
    scale=3
)
score_title.anchor_point = (0.5, 0.0)      # centro horizontal, parte superior
score_title.anchored_position = (DISPLAY_WIDTH // 2, 10)
splash.append(score_title)                 # índice 1

# =========================
# LABEL DEL NÚMERO
# =========================
score_label = label.Label(
    terminalio.FONT,
    text="0",
    color=0xFFFFFF,
    scale=4
)
score_label.anchor_point = (0.5, 0.5)
score_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
splash.append(score_label)                 # índice 2

# =========================
# FUNCIÓN: ANIMACIÓN EN BUCLE HASTA CUBRIR UN TIEMPO
# =========================
def play_animation_until(frame_paths, parent_group, total_duration, frame_duration=0.1, insert_index=1):
    """
    Reproduce en bucle la secuencia de BMPs en frame_paths hasta que
    haya pasado total_duration segundos.
    """
    start_time = time.monotonic()

    while True:
        for path in frame_paths:
            # ¿Ya hemos llegado al tiempo total?
            now = time.monotonic()
            elapsed = now - start_time
            if elapsed >= total_duration:
                return

            remaining = total_duration - elapsed
            this_duration = frame_duration if remaining > frame_duration else remaining

            # Abrir el archivo BMP
            f = open(path, "rb")
            bmp = displayio.OnDiskBitmap(f)

            # Crear TileGrid para mostrar el BMP
            frame_tilegrid = displayio.TileGrid(
                bmp,
                pixel_shader=bmp.pixel_shader
            )

            # Insertar justo encima del fondo, pero debajo del texto
            # Orden: [background, FRAME, score_title, score_label]
            parent_group.insert(insert_index, frame_tilegrid)

            # Mantener el frame en pantalla
            time.sleep(this_duration)

            # Quitar el frame
            parent_group.remove(frame_tilegrid)

            # Liberar recursos
            f.close()
            del bmp
            del frame_tilegrid

            # Comprobamos otra vez por si justo hemos llegado al final
            if time.monotonic() - start_time >= total_duration:
                return

# =========================
# FUNCIÓN PARA ACTUALIZAR SCORE Y FONDO / ANIMACIÓN
# =========================
def update_screen_for_score(score):
    """
    - Actualiza el número que se muestra en el display.
    - Si score >= 80 → reproduce la secuencia de BMPs en bucle
      hasta cubrir DELAY_BETWEEN_SCORES.
    - Si score <  80 → fondo rojo fijo durante DELAY_BETWEEN_SCORES.
    """
    # Actualizar número
    score_label.text = str(int(score))

    if score >= 80:
        # Reproducir animación tipo "gif" en bucle
        play_animation_until(
            FRAME_FILES,
            splash,
            total_duration=DELAY_BETWEEN_SCORES,
            frame_duration=FRAME_DURATION,
            insert_index=1  # debajo del texto, encima del fondo
        )
    else:
        # Fondo rojo cuando no hay "premio"
        background_palette[0] = 0xFF0000
        time.sleep(DELAY_BETWEEN_SCORES)

# =========================
# BUCLE PRINCIPAL
# =========================
while True:
    # Número aleatorio entero entre 0 y 100
    score = random.randint(0, 100)

    update_screen_for_score(score)
