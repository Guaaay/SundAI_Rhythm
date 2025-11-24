import time
import board
import displayio
import digitalio
import microcontroller
from fourwire import FourWire
from adafruit_st7789 import ST7789

# =========================
# AJUSTES
# =========================
ROTATION = 180  # 0, 90, 180, 270
FRAME_DURATION = 0.005  # tiempo por frame (segundos)

# Rutas de los BMP (135x240)
FRAME_FILES = [
    "/calibrating-0.bmp",
    "/calibrating-1.bmp",
    "/calibrating-2.bmp",
    "/calibrating-3.bmp",
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
    colstart=53
)

# Grupo raíz
splash = displayio.Group()
display.root_group = splash

# =========================
# FUNCIÓN SIMPLE DE ANIMACIÓN
# =========================
def success(duration_seconds):
    """
    Muestra en bucle las imágenes BMP de FRAME_FILES
    durante 'duration_seconds' segundos.
    """
    start = time.monotonic()

    while time.monotonic() - start < duration_seconds:
        for path in FRAME_FILES:
            # Si ya se ha acabado el tiempo, salimos
            if time.monotonic() - start >= duration_seconds:
                return

            # Abrir BMP
            f = open(path, "rb")
            bmp = displayio.OnDiskBitmap(f)

            # Crear TileGrid para mostrarlo a pantalla completa
            tile = displayio.TileGrid(bmp, pixel_shader=bmp.pixel_shader)

            # Mostrar el frame
            splash.append(tile)

            # Calcular cuánto tiempo queda para no pasarnos
            elapsed = time.monotonic() - start
            remaining = duration_seconds - elapsed
            frame_time = FRAME_DURATION if remaining > FRAME_DURATION else remaining

            time.sleep(frame_time)

            # Quitar el frame
            splash.remove(tile)

            # Cerrar archivo y limpiar
            f.close()
            del bmp
            del tile

# =========================
# EJEMPLO DE USO
# =========================
while True:
    # Reproduce la animación durante 5 segundos
    success(5)

    # Pequeña pausa con la pantalla en negro entre animaciones (opcional)
    time.sleep(1)
