# FT8x7 CAT Display Configuration
# Configuration settings for the display and serial communication

# Display Configuration (ST7789 1.3" 240x240 LCD)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240
DISPLAY_ROTATION = 0

# SPI Pins for Display (adjust based on your wiring)
SPI_ID = 0
PIN_SCK = 18    # SPI Clock
PIN_MOSI = 19   # SPI MOSI (Data)
PIN_DC = 16     # Data/Command
PIN_RST = 17    # Reset
PIN_CS = 20     # Chip Select
PIN_BL = 21     # Backlight

# UART Configuration for CAT Protocol
UART_ID = 0
PIN_TX = 0      # UART TX (to radio RXD)
PIN_RX = 1      # UART RX (from radio TXD)
CAT_BAUDRATE = 4800  # FT-817/818 default is 4800 or 9600
CAT_BITS = 8
CAT_PARITY = None
CAT_STOP = 2

# Display Colors (RGB565 format)
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE = 0x001F
COLOR_YELLOW = 0xFFE0
COLOR_CYAN = 0x07FF
COLOR_MAGENTA = 0xF81F
COLOR_ORANGE = 0xFD20
COLOR_GRAY = 0x8410

# Display Theme
BG_COLOR = COLOR_BLACK
TEXT_COLOR = COLOR_WHITE
FREQ_COLOR = COLOR_GREEN
MODE_COLOR = COLOR_YELLOW
STATUS_COLOR = COLOR_CYAN

# Update interval in milliseconds
UPDATE_INTERVAL_MS = 200

# Radio Model
# 0 = FT-817/FT-818
# 1 = FT-857
# 2 = FT-897
RADIO_MODEL = 0
