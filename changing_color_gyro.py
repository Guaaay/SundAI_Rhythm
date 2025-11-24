import time
import math
import board
import displayio
import digitalio
import microcontroller
from fourwire import FourWire
from adafruit_st7789 import ST7789
from adafruit_display_text import label
import terminalio
import adafruit_icm20x

# Change this to False to hide debug print statements
Debug = True

# -------------------------
# Retroiluminación en PA06
# -------------------------
if Debug:
    print("Init backlight on PA06")
backlight = digitalio.DigitalInOut(microcontroller.pin.PA06)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = False  # activo en LOW → encendido

# -------------------------
# Display ST7789
# -------------------------
if Debug:
    print("Release displays")
displayio.release_displays()

if Debug:
    print("Create SPI object for display")
spi = board.LCD_SPI()
tft_cs = board.LCD_CS
tft_dc = board.D4

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 135

if Debug:
    print("Create display bus and display")
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
if Debug:
    print("Create root group")
splash = displayio.Group()
display.root_group = splash

# Fondo negro (con paleta para poder cambiar color si queremos)
if Debug:
    print("Create background")
background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
background_palette = displayio.Palette(1)
background_palette[0] = 0x000000  # negro
background = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)
splash.append(background)

# Texto grande (muestra la magnitud de la aceleración)
if Debug:
    print("Create big text label")
text_area = label.Label(
    terminalio.FONT,
    text="0.0",
    color=0xFFFFFF,
    scale=4   # tamaño del texto
)

# Posición del texto
text_area.x = 40
text_area.y = 80
splash.append(text_area)

# -------------------------
# IMU adafruit_icm20x (ICM20948)
# -------------------------
if Debug:
    print("Init ICM20948")

i2c = board.I2C()  # usa SCL y SDA de la placa

icm = None
try:
    icm = adafruit_icm20x.ICM20948(i2c, address=0x69)
    if Debug:
        print("ICM20948 found at 0x69")
except Exception as e:
    print("No ICM20948 at 0x69:", e)
    print("Trying 0x68...")
    try:
        icm = adafruit_icm20x.ICM20948(i2c, address=0x68)
        if Debug:
            print("ICM20948 found at 0x68")
    except Exception as e2:
        print("No ICM20948 device found!", e2)
        # Si no hay IMU, nos quedamos aquí
        while True:
            time.sleep(1)

# -------------------------
# Bucle principal
# -------------------------
while True:
    # Lectura de acelerómetro (m/s^2) y giroscopio (rad/s)
    Xa, Ya, Za = icm.acceleration
    Xg, Yg, Zg = icm.gyro

    # Magnitud de la aceleración (restando ~1g ≈ 9.8–10 m/s^2)
    magnitude_acc = math.sqrt(Xa * Xa + Ya * Ya + Za * Za) - 10.0

    # Magnitud del giroscopio
    magnitude_gyro = math.sqrt(Xg * Xg + Yg * Yg + Zg * Zg)

    if Debug:
        print("Magnitude acc:  {:.2f} m/s^2".format(magnitude_acc))
        print("Magnitude gyro: {:.2f} rad/s".format(magnitude_gyro))
        print("")

    # Mostrar en el display la magnitud de la aceleración
    # (formato con 1 decimal, por ejemplo)
    text_area.text = "{:.1f}".format(magnitude_acc)

    # Si quieres, aquí puedes usar Xa para cambiar color de fondo:
    # Ejemplo: derecha = rojo, izquierda = verde, centro = negro
    TILT_THRESHOLD = 2.0  # m/s^2 (ajusta sensibilidad)
    if Xa > TILT_THRESHOLD:
        background_palette[0] = 0xFF0000  # rojo
    elif Xa < -TILT_THRESHOLD:
        background_palette[0] = 0x00FF00  # verde
    else:
        background_palette[0] = 0x000000  # negro

    time.sleep(0.1)
