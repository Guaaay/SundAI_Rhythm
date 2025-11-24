import time
import board
import displayio
import digitalio
import microcontroller
from fourwire import FourWire
from adafruit_st7789 import ST7789
from adafruit_display_text import label
import terminalio

# =========================
# AJUSTE DE ROTACIÓN
# =========================
# 0 o 180 para vertical, 90 o 270 para horizontal
ROTATION = 180

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

DISPLAY_WIDTH = 135
DISPLAY_HEIGHT = 240

# Bus y display
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

# Fondo (paleta de 1 color)
background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
background_palette = displayio.Palette(1)
background_palette[0] = 0xFF0000  # rojo
background = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)
splash.append(background)

# =========================
# FUNCIÓN failure(tiempo)
# =========================
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


# =========================
# EJEMPLO DE USO
# =========================
while True:
    # Muestra TRY / AGAIN durante 3 segundos
    failure(3)
    # Pausa entre mensajes
    time.sleep(2)
