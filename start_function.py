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

# =========================
# FUNCIÓN start(tiempo)
# =========================
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

# =========================
# EJEMPLO DE USO
# =========================
while True:
    start(5)

    time.sleep(2)