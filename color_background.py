import time
import board
import displayio
import digitalio
import microcontroller
from fourwire import FourWire
from adafruit_st7789 import ST7789
from adafruit_display_text import label
import terminalio

# Retroiluminación en PA06
backlight = digitalio.DigitalInOut(microcontroller.pin.PA06)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = False  # activo en LOW → encendido

# Liberar displays previos
displayio.release_displays()

# SPI y pines de la pantalla
spi = board.LCD_SPI()
tft_cs = board.LCD_CS
tft_dc = board.D4

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 135

# Bus y display
display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs)
display = ST7789(
    display_bus,
    rotation=90,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=40,
    colstart=53
)

# Grupo raíz
splash = displayio.Group()
display.root_group = splash

# Fondo negro
background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
background_palette = displayio.Palette(1)
background_palette[0] = 0x00FF00  # negro
background = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)
splash.append(background)

# Bucle para mantener el programa vivo (no hace nada más)
while True:
    time.sleep(1)
