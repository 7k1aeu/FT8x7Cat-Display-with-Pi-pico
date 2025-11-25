"""
FT8x7 CAT Protocol Library for MicroPython

This module implements the CAT (Computer Aided Transceiver) protocol
for Yaesu FT-817/FT-818/FT-857/FT-897 radios.

The CAT protocol uses serial communication at 4800 or 9600 baud with
8 data bits, no parity, and 2 stop bits.
"""

from machine import UART, Pin
import time


class FT8x7CAT:
    """
    CAT Protocol handler for FT-817/818/857/897 radios.

    This class provides methods to communicate with Yaesu radios
    using the CAT protocol over UART.
    """

    # Operating Modes
    MODE_LSB = 0x00
    MODE_USB = 0x01
    MODE_CW = 0x02
    MODE_CWR = 0x03
    MODE_AM = 0x04
    MODE_FM = 0x08
    MODE_DIG = 0x0A
    MODE_PKT = 0x0C
    MODE_NFM = 0x88
    MODE_WFM = 0x06

    # Mode names for display
    MODE_NAMES = {
        0x00: "LSB",
        0x01: "USB",
        0x02: "CW",
        0x03: "CW-R",
        0x04: "AM",
        0x08: "FM",
        0x0A: "DIG",
        0x0C: "PKT",
        0x88: "NFM",
        0x06: "WFM",
    }

    # CAT Commands
    CMD_LOCK_ON = bytes([0x00, 0x00, 0x00, 0x00, 0x00])
    CMD_LOCK_OFF = bytes([0x00, 0x00, 0x00, 0x00, 0x80])
    CMD_PTT_ON = bytes([0x00, 0x00, 0x00, 0x00, 0x08])
    CMD_PTT_OFF = bytes([0x00, 0x00, 0x00, 0x00, 0x88])
    CMD_READ_FREQ = bytes([0x00, 0x00, 0x00, 0x00, 0x03])
    CMD_READ_RX_STATUS = bytes([0x00, 0x00, 0x00, 0x00, 0xE7])
    CMD_READ_TX_STATUS = bytes([0x00, 0x00, 0x00, 0x00, 0xF7])

    def __init__(self, uart_id=0, tx_pin=0, rx_pin=1,
                 baudrate=4800, bits=8, parity=None, stop=2):
        """
        Initialize the CAT interface.

        Args:
            uart_id: UART peripheral ID (0 or 1)
            tx_pin: TX GPIO pin number
            rx_pin: RX GPIO pin number
            baudrate: Serial baud rate (4800 or 9600)
            bits: Data bits
            parity: Parity (None for no parity)
            stop: Stop bits
        """
        self.uart = UART(
            uart_id,
            baudrate=baudrate,
            bits=bits,
            parity=parity,
            stop=stop,
            tx=Pin(tx_pin),
            rx=Pin(rx_pin)
        )

        # Current radio state
        self.frequency = 0
        self.mode = 0
        self.mode_name = ""
        self.squelch_open = False
        self.s_meter = 0
        self.tx_active = False
        self.po_meter = 0
        self.swr_high = False
        self.split_active = False

        # Communication timeout
        self.timeout_ms = 200

    def _send_command(self, cmd):
        """
        Send a CAT command and read the response.

        Args:
            cmd: 5-byte command to send

        Returns:
            bytes: Response data or None on timeout
        """
        # Clear input buffer
        while self.uart.any():
            self.uart.read()

        # Send command
        self.uart.write(cmd)

        # Wait for response
        start = time.ticks_ms()
        while not self.uart.any():
            if time.ticks_diff(time.ticks_ms(), start) > self.timeout_ms:
                return None
            time.sleep_ms(5)

        # Read response
        time.sleep_ms(20)  # Wait for complete response
        response = self.uart.read()

        return response

    def set_frequency(self, freq_hz):
        """
        Set the operating frequency.

        Args:
            freq_hz: Frequency in Hz

        Returns:
            bool: True if successful
        """
        # Convert frequency to BCD format
        # Frequency is stored as 4 bytes in BCD, representing 0.1 MHz to 0.01 Hz
        freq_10hz = freq_hz // 10

        bcd = bytearray(4)
        for i in range(4):
            bcd[3 - i] = ((freq_10hz // (10 ** (i * 2 + 1))) % 10) << 4
            bcd[3 - i] |= (freq_10hz // (10 ** (i * 2))) % 10

        cmd = bytes(bcd) + bytes([0x01])
        response = self._send_command(cmd)

        return response == bytes([0x00])

    def get_frequency_and_mode(self):
        """
        Read the current frequency and mode from the radio.

        Returns:
            tuple: (frequency_hz, mode) or (None, None) on error
        """
        response = self._send_command(self.CMD_READ_FREQ)

        if response is None or len(response) < 5:
            return (None, None)

        # Parse BCD frequency
        freq_10hz = 0
        for i in range(4):
            high = (response[i] >> 4) & 0x0F
            low = response[i] & 0x0F
            freq_10hz = freq_10hz * 100 + high * 10 + low

        freq_hz = freq_10hz * 10

        # Parse mode
        mode = response[4]

        # Update internal state
        self.frequency = freq_hz
        self.mode = mode
        self.mode_name = self.MODE_NAMES.get(mode, "???")

        return (freq_hz, mode)

    def get_rx_status(self):
        """
        Read the RX status from the radio.

        Returns:
            dict: RX status information or None on error
        """
        response = self._send_command(self.CMD_READ_RX_STATUS)

        if response is None or len(response) < 1:
            return None

        status_byte = response[0]

        # Parse status byte
        self.squelch_open = not bool(status_byte & 0x80)
        self.s_meter = status_byte & 0x0F

        # Check discriminator center (for FM)
        disc_center = not bool(status_byte & 0x40)

        return {
            'squelch_open': self.squelch_open,
            's_meter': self.s_meter,
            'disc_center': disc_center,
            'ctcss_match': not bool(status_byte & 0x20)
        }

    def get_tx_status(self):
        """
        Read the TX status from the radio.

        Returns:
            dict: TX status information or None on error
        """
        response = self._send_command(self.CMD_READ_TX_STATUS)

        if response is None or len(response) < 1:
            return None

        status_byte = response[0]

        # Parse status byte
        self.tx_active = not bool(status_byte & 0x80)
        self.swr_high = bool(status_byte & 0x40)
        self.split_active = bool(status_byte & 0x20)
        self.po_meter = status_byte & 0x0F

        return {
            'tx_active': self.tx_active,
            'swr_high': self.swr_high,
            'split_active': self.split_active,
            'po_meter': self.po_meter
        }

    def set_mode(self, mode):
        """
        Set the operating mode.

        Args:
            mode: Mode constant (MODE_LSB, MODE_USB, etc.)

        Returns:
            bool: True if successful
        """
        cmd = bytes([mode, 0x00, 0x00, 0x00, 0x07])
        response = self._send_command(cmd)
        return response == bytes([0x00])

    def set_ptt(self, on):
        """
        Toggle PTT (Push-To-Talk).

        Args:
            on: True to activate TX, False to deactivate

        Returns:
            bool: True if successful
        """
        if on:
            response = self._send_command(self.CMD_PTT_ON)
        else:
            response = self._send_command(self.CMD_PTT_OFF)

        return response is not None

    def lock(self, on):
        """
        Toggle dial lock.

        Args:
            on: True to lock, False to unlock

        Returns:
            bool: True if successful
        """
        if on:
            response = self._send_command(self.CMD_LOCK_ON)
        else:
            response = self._send_command(self.CMD_LOCK_OFF)

        return response == bytes([0x00])

    def get_vfo(self):
        """
        Get current VFO selection.

        Returns:
            str: 'A' or 'B', or None on error
        """
        cmd = bytes([0x00, 0x00, 0x00, 0x00, 0x03])
        response = self._send_command(cmd)

        if response is None or len(response) < 1:
            return None

        # This command doesn't directly return VFO info
        # The frequency/mode read is for the current VFO
        return 'A'  # Default assumption

    def toggle_vfo(self):
        """
        Toggle between VFO A and VFO B.

        Returns:
            bool: True if successful
        """
        cmd = bytes([0x00, 0x00, 0x00, 0x00, 0x81])
        response = self._send_command(cmd)
        return response == bytes([0x00])

    def set_clar(self, on, offset_hz=0):
        """
        Set clarifier (RIT/XIT) on or off.

        Args:
            on: True to enable clarifier
            offset_hz: Clarifier offset in Hz (-9999 to +9999)

        Returns:
            bool: True if successful
        """
        if on:
            cmd = bytes([0x00, 0x00, 0x00, 0x00, 0x05])
        else:
            cmd = bytes([0x00, 0x00, 0x00, 0x00, 0x85])

        response = self._send_command(cmd)
        return response == bytes([0x00])

    def format_frequency(self, freq_hz=None):
        """
        Format frequency for display.

        Args:
            freq_hz: Frequency in Hz (uses internal state if None)

        Returns:
            str: Formatted frequency string (e.g., "14.074.000")
        """
        if freq_hz is None:
            freq_hz = self.frequency

        if freq_hz == 0:
            return "----.---"

        mhz = freq_hz // 1000000
        khz = (freq_hz % 1000000) // 1000
        hz = freq_hz % 1000

        return "{:4d}.{:03d}.{:03d}".format(mhz, khz, hz)

    def get_band(self, freq_hz=None):
        """
        Get the amateur band name for a frequency.

        Args:
            freq_hz: Frequency in Hz (uses internal state if None)

        Returns:
            str: Band name (e.g., "20m", "2m")
        """
        if freq_hz is None:
            freq_hz = self.frequency

        # Define band edges (in Hz)
        bands = [
            (1800000, 2000000, "160m"),
            (3500000, 4000000, "80m"),
            (5330500, 5405500, "60m"),
            (7000000, 7300000, "40m"),
            (10100000, 10150000, "30m"),
            (14000000, 14350000, "20m"),
            (18068000, 18168000, "17m"),
            (21000000, 21450000, "15m"),
            (24890000, 24990000, "12m"),
            (28000000, 29700000, "10m"),
            (50000000, 54000000, "6m"),
            (144000000, 148000000, "2m"),
            (420000000, 450000000, "70cm"),
        ]

        for low, high, name in bands:
            if low <= freq_hz <= high:
                return name

        return "---"

    def update(self):
        """
        Update all radio status information.

        This method reads frequency, mode, RX status, and TX status
        from the radio.

        Returns:
            bool: True if all reads were successful
        """
        freq_result = self.get_frequency_and_mode()
        rx_result = self.get_rx_status()
        tx_result = self.get_tx_status()

        return all([
            freq_result[0] is not None,
            rx_result is not None,
            tx_result is not None
        ])
