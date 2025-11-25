"""
ST7789 LCD Display Driver for MicroPython on Raspberry Pi Pico
Supports 240x240 1.3" LCD displays

This driver provides basic functionality for displaying text and graphics
on ST7789-based LCD displays.
"""

from machine import Pin, SPI
import time
import struct


class ST7789:
    """
    ST7789 LCD Display Driver

    This class provides methods to control an ST7789-based LCD display
    using SPI communication on a Raspberry Pi Pico.
    """

    # ST7789 Commands
    CMD_NOP = 0x00
    CMD_SWRESET = 0x01
    CMD_SLPIN = 0x10
    CMD_SLPOUT = 0x11
    CMD_NORON = 0x13
    CMD_INVOFF = 0x20
    CMD_INVON = 0x21
    CMD_DISPOFF = 0x28
    CMD_DISPON = 0x29
    CMD_CASET = 0x2A
    CMD_RASET = 0x2B
    CMD_RAMWR = 0x2C
    CMD_MADCTL = 0x36
    CMD_COLMOD = 0x3A

    # MADCTL bit definitions
    MADCTL_MY = 0x80   # Row Address Order
    MADCTL_MX = 0x40   # Column Address Order
    MADCTL_MV = 0x20   # Row/Column Exchange
    MADCTL_ML = 0x10   # Vertical Refresh Order
    MADCTL_RGB = 0x00  # RGB Order
    MADCTL_BGR = 0x08  # BGR Order

    def __init__(self, spi, dc, rst, cs, bl=None,
                 width=320, height=240, rotation=0):
        """
        Initialize the ST7789 display.

        Args:
            spi: SPI object
            dc: Data/Command pin
            rst: Reset pin
            cs: Chip Select pin
            bl: Backlight pin (optional)
            width: Display width in pixels (default 320)
            height: Display height in pixels (default 240)
            rotation: Display rotation (0, 90, 180, 270)
        """
        self.spi = spi
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        self.bl = Pin(bl, Pin.OUT) if bl is not None else None

        self._init_width = width
        self._init_height = height
        self.width = width
        self.height = height
        self.rotation = rotation

        # X and Y offset for different display sizes
        self.xoffset = 0
        self.yoffset = 0

        self._init_display()

    def _init_display(self):
        """Initialize the display with default settings."""
        self.cs.value(1)
        self.dc.value(1)

        # Hardware reset
        self.rst.value(1)
        time.sleep_ms(50)
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(150)

        # Software reset
        self._write_cmd(self.CMD_SWRESET)
        time.sleep_ms(150)

        # Exit sleep mode
        self._write_cmd(self.CMD_SLPOUT)
        time.sleep_ms(255)

        # Set color mode to 16-bit RGB565
        self._write_cmd(self.CMD_COLMOD)
        self._write_data(bytes([0x55]))  # 16-bit color
        time.sleep_ms(10)

        # Set rotation
        self.set_rotation(self.rotation)

        # Normal display mode
        self._write_cmd(self.CMD_NORON)
        time.sleep_ms(10)

        # Display on
        self._write_cmd(self.CMD_DISPON)
        time.sleep_ms(255)

        # Turn on backlight if available
        if self.bl is not None:
            self.bl.value(1)

    def _write_cmd(self, cmd):
        """Write a command to the display."""
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)

    def _write_data(self, data):
        """Write data to the display."""
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(data)
        self.cs.value(1)

    def set_rotation(self, rotation):
        """
        Set display rotation.

        Args:
            rotation: 0, 90, 180, or 270 degrees
        """
        self.rotation = rotation

        # For 320x240 display
        if rotation == 0:
            madctl = self.MADCTL_MX | self.MADCTL_MY | self.MADCTL_RGB
            self.width = self._init_width
            self.height = self._init_height
            self.xoffset = 0
            self.yoffset = 0
        elif rotation == 90:
            madctl = self.MADCTL_MY | self.MADCTL_MV | self.MADCTL_RGB
            self.width = self._init_height
            self.height = self._init_width
            self.xoffset = 0
            self.yoffset = 0
        elif rotation == 180:
            madctl = self.MADCTL_RGB
            self.width = self._init_width
            self.height = self._init_height
            self.xoffset = 0
            self.yoffset = 0
        else:  # 270
            madctl = self.MADCTL_MX | self.MADCTL_MV | self.MADCTL_RGB
            self.width = self._init_height
            self.height = self._init_width
            self.xoffset = 0
            self.yoffset = 0

        self._write_cmd(self.CMD_MADCTL)
        self._write_data(bytes([madctl]))

    def _set_window(self, x0, y0, x1, y1):
        """Set the drawing window."""
        x0 += self.xoffset
        x1 += self.xoffset
        y0 += self.yoffset
        y1 += self.yoffset

        self._write_cmd(self.CMD_CASET)
        self._write_data(struct.pack(">HH", x0, x1))

        self._write_cmd(self.CMD_RASET)
        self._write_data(struct.pack(">HH", y0, y1))

        self._write_cmd(self.CMD_RAMWR)

    def fill(self, color):
        """
        Fill the entire display with a color.

        Args:
            color: RGB565 color value
        """
        self._set_window(0, 0, self.width - 1, self.height - 1)

        # Create a buffer for one line
        buf = struct.pack(">H", color) * self.width

        for _ in range(self.height):
            self._write_data(buf)

    def fill_rect(self, x, y, w, h, color):
        """
        Fill a rectangle with a color.

        Args:
            x: X coordinate
            y: Y coordinate
            w: Width
            h: Height
            color: RGB565 color value
        """
        if x + w > self.width:
            w = self.width - x
        if y + h > self.height:
            h = self.height - y

        self._set_window(x, y, x + w - 1, y + h - 1)

        buf = struct.pack(">H", color) * w

        for _ in range(h):
            self._write_data(buf)

    def pixel(self, x, y, color):
        """
        Set a single pixel.

        Args:
            x: X coordinate
            y: Y coordinate
            color: RGB565 color value
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self._set_window(x, y, x, y)
            self._write_data(struct.pack(">H", color))

    def hline(self, x, y, w, color):
        """Draw a horizontal line."""
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        """Draw a vertical line."""
        self.fill_rect(x, y, 1, h, color)

    def rect(self, x, y, w, h, color):
        """Draw a rectangle outline."""
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def text(self, font, text, x, y, color, bg_color=None, scale=1):
        """
        Draw text on the display.

        Args:
            font: Font object with get_ch method
            text: Text string to display
            x: X coordinate
            y: Y coordinate
            color: Text color (RGB565)
            bg_color: Background color (RGB565), None for transparent
            scale: Font scaling factor
        """
        for char in text:
            ch_data, ch_width, ch_height = font.get_ch(char)
            if ch_data is None:
                continue

            for row in range(ch_height):
                for col in range(ch_width):
                    byte_idx = row * ((ch_width + 7) // 8) + col // 8
                    bit_idx = 7 - (col % 8)

                    if byte_idx < len(ch_data):
                        if (ch_data[byte_idx] >> bit_idx) & 1:
                            if scale == 1:
                                self.pixel(x + col, y + row, color)
                            else:
                                self.fill_rect(
                                    x + col * scale,
                                    y + row * scale,
                                    scale, scale, color
                                )
                        elif bg_color is not None:
                            if scale == 1:
                                self.pixel(x + col, y + row, bg_color)
                            else:
                                self.fill_rect(
                                    x + col * scale,
                                    y + row * scale,
                                    scale, scale, bg_color
                                )

            x += (ch_width + 1) * scale

    def backlight(self, on):
        """Turn backlight on or off."""
        if self.bl is not None:
            self.bl.value(1 if on else 0)

    def sleep(self, sleep=True):
        """Put display into sleep mode or wake up."""
        if sleep:
            self._write_cmd(self.CMD_SLPIN)
        else:
            self._write_cmd(self.CMD_SLPOUT)
        time.sleep_ms(120)

    def invert(self, invert=True):
        """Invert display colors."""
        if invert:
            self._write_cmd(self.CMD_INVON)
        else:
            self._write_cmd(self.CMD_INVOFF)
