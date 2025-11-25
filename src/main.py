"""
FT8x7 CAT Display Main Application

This is the main application for displaying FT-817/818/857/897 radio
information on a 240x240 LCD display connected to a Raspberry Pi Pico.

Hardware Requirements:
- Raspberry Pi Pico (or Pico W)
- 1.3" 240x240 LCD with ST7789 controller
- Connection to FT8x7 radio CAT port

Usage:
    Copy all files to the Pico and this file will run automatically
    as main.py
"""

from machine import Pin, SPI
import time

# Import local modules
from config import (
    SPI_ID, PIN_SCK, PIN_MOSI, PIN_DC, PIN_RST, PIN_CS, PIN_BL,
    DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_ROTATION,
    UART_ID, PIN_TX, PIN_RX, CAT_BAUDRATE, CAT_BITS, CAT_PARITY, CAT_STOP,
    BG_COLOR, TEXT_COLOR, FREQ_COLOR, MODE_COLOR, STATUS_COLOR,
    COLOR_BLACK, COLOR_WHITE, COLOR_RED, COLOR_GREEN, COLOR_YELLOW,
    COLOR_CYAN, COLOR_GRAY, COLOR_ORANGE,
    UPDATE_INTERVAL_MS
)
from st7789 import ST7789
from font import Font8x8
from ft8x7_cat import FT8x7CAT


class RadioDisplay:
    """
    Main display controller for FT8x7 CAT Display.

    This class manages the LCD display and radio communication,
    showing frequency, mode, and status information.
    """

    def __init__(self):
        """Initialize the display and radio connection."""
        # Initialize SPI for display
        self.spi = SPI(
            SPI_ID,
            baudrate=40000000,
            polarity=1,
            phase=0,
            sck=Pin(PIN_SCK),
            mosi=Pin(PIN_MOSI)
        )

        # Initialize display
        self.display = ST7789(
            self.spi,
            dc=PIN_DC,
            rst=PIN_RST,
            cs=PIN_CS,
            bl=PIN_BL,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            rotation=DISPLAY_ROTATION
        )

        # Initialize font
        self.font = Font8x8()

        # Initialize CAT interface
        self.cat = FT8x7CAT(
            uart_id=UART_ID,
            tx_pin=PIN_TX,
            rx_pin=PIN_RX,
            baudrate=CAT_BAUDRATE,
            bits=CAT_BITS,
            parity=CAT_PARITY,
            stop=CAT_STOP
        )

        # Display state
        self.last_freq = 0
        self.last_mode = ""
        self.last_s_meter = 0
        self.last_tx = False
        self.connected = False

        # Layout constants
        self.HEADER_Y = 5
        self.FREQ_Y = 40
        self.MODE_Y = 90
        self.SMETER_Y = 130
        self.STATUS_Y = 180
        self.FOOTER_Y = 220

    def _draw_text(self, text, x, y, color, scale=1, bg_color=None):
        """Draw text with optional background."""
        if bg_color is not None:
            # Calculate text width and height
            text_w = len(text) * 8 * scale
            text_h = 8 * scale
            self.display.fill_rect(x, y, text_w, text_h, bg_color)

        self.display.text(self.font, text, x, y, color, scale=scale)

    def _draw_centered_text(self, text, y, color, scale=1, bg_color=None):
        """Draw centered text."""
        text_w = len(text) * 8 * scale
        x = (DISPLAY_WIDTH - text_w) // 2
        self._draw_text(text, x, y, color, scale, bg_color)

    def _draw_header(self):
        """Draw the header section."""
        self._draw_centered_text("FT8x7 CAT Display", self.HEADER_Y,
                                 TEXT_COLOR, scale=1)
        self.display.hline(0, self.HEADER_Y + 15, DISPLAY_WIDTH, COLOR_GRAY)

    def _draw_frequency(self):
        """Draw the frequency display."""
        freq_str = self.cat.format_frequency()
        band = self.cat.get_band()

        # Clear previous frequency area
        self.display.fill_rect(0, self.FREQ_Y, DISPLAY_WIDTH, 40, BG_COLOR)

        # Draw frequency with large scale
        self._draw_centered_text(freq_str, self.FREQ_Y, FREQ_COLOR, scale=3)

        # Draw band indicator
        self._draw_centered_text("MHz  [" + band + "]", self.FREQ_Y + 30,
                                 TEXT_COLOR, scale=1)

    def _draw_mode(self):
        """Draw the operating mode."""
        mode_str = self.cat.mode_name if self.cat.mode_name else "---"

        # Clear previous mode area
        self.display.fill_rect(0, self.MODE_Y, DISPLAY_WIDTH, 30, BG_COLOR)

        # Draw mode label
        self._draw_text("MODE:", 10, self.MODE_Y, TEXT_COLOR, scale=2)

        # Draw mode value
        mode_color = MODE_COLOR
        if mode_str in ["LSB", "USB"]:
            mode_color = COLOR_GREEN
        elif mode_str in ["CW", "CW-R"]:
            mode_color = COLOR_YELLOW
        elif mode_str == "FM":
            mode_color = COLOR_CYAN
        elif mode_str == "AM":
            mode_color = COLOR_ORANGE

        self._draw_text(mode_str, 100, self.MODE_Y, mode_color, scale=2)

    def _draw_s_meter(self):
        """Draw the S-meter display."""
        # Clear previous S-meter area
        self.display.fill_rect(0, self.SMETER_Y, DISPLAY_WIDTH, 40, BG_COLOR)

        # Draw S-meter label
        self._draw_text("S:", 10, self.SMETER_Y, TEXT_COLOR, scale=2)

        # Draw S-meter bar
        bar_x = 40
        bar_y = self.SMETER_Y + 4
        bar_width = 180
        bar_height = 12

        # Draw bar background
        self.display.rect(bar_x, bar_y, bar_width, bar_height, COLOR_GRAY)

        # Draw filled portion
        if self.cat.s_meter > 0:
            fill_width = min(self.cat.s_meter * bar_width // 15, bar_width - 2)
            fill_color = COLOR_GREEN
            if self.cat.s_meter > 9:
                fill_color = COLOR_YELLOW
            if self.cat.s_meter > 12:
                fill_color = COLOR_RED

            self.display.fill_rect(bar_x + 1, bar_y + 1,
                                   fill_width, bar_height - 2, fill_color)

        # Draw S-meter value
        if self.cat.s_meter <= 9:
            s_str = "S{}".format(self.cat.s_meter)
        else:
            s_str = "S9+{}".format((self.cat.s_meter - 9) * 10)

        self._draw_text(s_str, bar_x, self.SMETER_Y + 22, TEXT_COLOR, scale=1)

    def _draw_status(self):
        """Draw status indicators."""
        # Clear previous status area
        self.display.fill_rect(0, self.STATUS_Y, DISPLAY_WIDTH, 30, BG_COLOR)

        y = self.STATUS_Y
        x = 10

        # TX/RX indicator
        if self.cat.tx_active:
            self.display.fill_rect(x, y, 40, 20, COLOR_RED)
            self._draw_text("TX", x + 8, y + 4, COLOR_WHITE, scale=1)
        else:
            self.display.fill_rect(x, y, 40, 20, COLOR_GREEN)
            self._draw_text("RX", x + 8, y + 4, COLOR_BLACK, scale=1)

        x += 50

        # Squelch indicator
        if self.cat.squelch_open:
            self.display.fill_rect(x, y, 40, 20, COLOR_GREEN)
            self._draw_text("SQ", x + 8, y + 4, COLOR_BLACK, scale=1)
        else:
            self.display.rect(x, y, 40, 20, COLOR_GRAY)
            self._draw_text("SQ", x + 8, y + 4, COLOR_GRAY, scale=1)

        x += 50

        # Split indicator
        if self.cat.split_active:
            self.display.fill_rect(x, y, 50, 20, COLOR_YELLOW)
            self._draw_text("SPL", x + 6, y + 4, COLOR_BLACK, scale=1)
        else:
            self.display.rect(x, y, 50, 20, COLOR_GRAY)
            self._draw_text("SPL", x + 6, y + 4, COLOR_GRAY, scale=1)

        x += 60

        # SWR indicator
        if self.cat.swr_high:
            self.display.fill_rect(x, y, 50, 20, COLOR_RED)
            self._draw_text("SWR", x + 4, y + 4, COLOR_WHITE, scale=1)
        else:
            self.display.rect(x, y, 50, 20, COLOR_GRAY)
            self._draw_text("SWR", x + 4, y + 4, COLOR_GRAY, scale=1)

    def _draw_footer(self):
        """Draw the footer section."""
        self.display.hline(0, self.FOOTER_Y - 5, DISPLAY_WIDTH, COLOR_GRAY)

        if self.connected:
            status = "Connected"
            color = COLOR_GREEN
        else:
            status = "No Connection"
            color = COLOR_RED

        self._draw_centered_text(status, self.FOOTER_Y, color, scale=1)

    def _draw_splash(self):
        """Draw splash screen."""
        self.display.fill(BG_COLOR)

        # Title
        self._draw_centered_text("FT8x7 CAT", 60, FREQ_COLOR, scale=3)
        self._draw_centered_text("Display", 100, FREQ_COLOR, scale=3)

        # Version info
        self._draw_centered_text("v1.0.0", 150, TEXT_COLOR, scale=1)

        # Hardware info
        self._draw_centered_text("Pi Pico + ST7789", 180, COLOR_GRAY, scale=1)
        self._draw_centered_text("240x240 LCD", 195, COLOR_GRAY, scale=1)

        time.sleep(2)

    def _draw_no_connection(self):
        """Draw no connection screen."""
        self.display.fill(BG_COLOR)

        self._draw_header()

        # No connection message
        self._draw_centered_text("No Radio", 80, COLOR_RED, scale=2)
        self._draw_centered_text("Connection", 110, COLOR_RED, scale=2)

        self._draw_centered_text("Check CAT cable", 160, COLOR_GRAY, scale=1)
        self._draw_centered_text("and baud rate", 175, COLOR_GRAY, scale=1)

        self._draw_footer()

    def _full_update(self):
        """Perform a full display update."""
        self.display.fill(BG_COLOR)
        self._draw_header()
        self._draw_frequency()
        self._draw_mode()
        self._draw_s_meter()
        self._draw_status()
        self._draw_footer()

    def _partial_update(self):
        """
        Perform a partial display update.

        Only updates sections that have changed.
        """
        freq_changed = self.cat.frequency != self.last_freq
        mode_changed = self.cat.mode_name != self.last_mode
        smeter_changed = self.cat.s_meter != self.last_s_meter
        tx_changed = self.cat.tx_active != self.last_tx

        if freq_changed:
            self._draw_frequency()
            self.last_freq = self.cat.frequency

        if mode_changed:
            self._draw_mode()
            self.last_mode = self.cat.mode_name

        if smeter_changed:
            self._draw_s_meter()
            self.last_s_meter = self.cat.s_meter

        if tx_changed or True:  # Always update status for now
            self._draw_status()
            self.last_tx = self.cat.tx_active

    def run(self):
        """Main application loop."""
        # Show splash screen
        self._draw_splash()

        # Clear and prepare main display
        self.display.fill(BG_COLOR)

        connection_attempts = 0
        max_attempts = 5

        while True:
            # Try to update from radio
            success = self.cat.update()

            if success:
                if not self.connected:
                    self.connected = True
                    self._full_update()
                    connection_attempts = 0
                else:
                    self._partial_update()
            else:
                connection_attempts += 1
                if connection_attempts >= max_attempts:
                    if self.connected:
                        self.connected = False
                        self._draw_no_connection()

            # Wait before next update
            time.sleep_ms(UPDATE_INTERVAL_MS)


def main():
    """Application entry point."""
    print("Starting FT8x7 CAT Display...")

    try:
        app = RadioDisplay()
        app.run()
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print("Error:", e)
        raise


if __name__ == "__main__":
    main()
