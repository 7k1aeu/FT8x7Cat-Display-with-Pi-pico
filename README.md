# FT8x7 CAT Display with Raspberry Pi Pico

FT8x7 CAT Display - A hardware project to display information from Yaesu FT-817/FT-818/FT-857/FT-897 radios using a Raspberry Pi Pico and a 1.3" LCD display.

![FT8x7 CAT Display](docs/images/display_preview.png)

## Features

- **Real-time Frequency Display**: Shows current operating frequency with band indicator
- **Mode Display**: Shows operating mode (LSB, USB, CW, FM, AM, etc.)
- **S-Meter**: Graphical S-meter display with color-coded signal strength
- **Status Indicators**: TX/RX, Squelch, Split, SWR indicators
- **Automatic Connection Detection**: Detects radio connection status

## Hardware Requirements

### Components

| Component | Description | Link Example |
|-----------|-------------|--------------|
| CPU | Raspberry Pi Pico | [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/) |
| Display | 1.3" 240x240 LCD with ST7789 controller | [AliExpress LCD](https://ja.aliexpress.com/item/1005008766561044.html) |
| Cable | CAT cable for FT8x7 radio | 3.5mm TRS to GPIO wiring |
| Power | USB power supply or radio power | 5V USB or 3.3V regulated |

### Pin Connections

#### Display (ST7789 SPI)

| LCD Pin | Pico GPIO | Description |
|---------|-----------|-------------|
| VCC | 3V3 (Pin 36) | Power 3.3V |
| GND | GND (Pin 38) | Ground |
| SCL/SCK | GP18 (Pin 24) | SPI Clock |
| SDA/MOSI | GP19 (Pin 25) | SPI Data |
| DC | GP16 (Pin 21) | Data/Command |
| RST | GP17 (Pin 22) | Reset |
| CS | GP20 (Pin 26) | Chip Select |
| BL | GP21 (Pin 27) | Backlight |

#### CAT Serial (UART)

| CAT Pin | Pico GPIO | Description |
|---------|-----------|-------------|
| TXD (to radio) | GP0 (Pin 1) | UART TX |
| RXD (from radio) | GP1 (Pin 2) | UART RX |
| GND | GND (Pin 3) | Ground |

### Wiring Diagram

```
Raspberry Pi Pico                    ST7789 LCD
┌─────────────────┐                  ┌─────────┐
│            3V3  ├──────────────────┤ VCC     │
│            GND  ├──────────────────┤ GND     │
│           GP18  ├──────────────────┤ SCL     │
│           GP19  ├──────────────────┤ SDA     │
│           GP16  ├──────────────────┤ DC      │
│           GP17  ├──────────────────┤ RST     │
│           GP20  ├──────────────────┤ CS      │
│           GP21  ├──────────────────┤ BL      │
│                 │                  └─────────┘
│            GP0  ├─────┐
│            GP1  ├────┐│            FT8x7 Radio
│            GND  ├───┐││            ┌─────────┐
└─────────────────┘   │││            │ DATA    │
                      │││            │ ┌─────┐ │
                      ││└────────────┤►│ RXD │ │
                      │└─────────────┤◄│ TXD │ │
                      └──────────────┤ │ GND │ │
                                     │ └─────┘ │
                                     └─────────┘
```

## Software Setup

### Prerequisites

1. Install MicroPython on your Raspberry Pi Pico
   - Download from: https://micropython.org/download/rp2-pico/
   - Hold BOOTSEL button, connect USB, copy .uf2 file

2. Install Thonny IDE (recommended for file transfer)
   - Download from: https://thonny.org/

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/FT8x7Cat-Display-with-Pi-pico.git
   ```

2. Copy all files from `src/` directory to your Pico:
   - `main.py` - Main application
   - `config.py` - Configuration settings
   - `st7789.py` - LCD display driver
   - `font.py` - Bitmap font for display
   - `ft8x7_cat.py` - CAT protocol library

3. Configure settings in `config.py`:
   ```python
   # Adjust baud rate if needed (4800 or 9600)
   CAT_BAUDRATE = 4800
   
   # Select radio model
   RADIO_MODEL = 0  # 0=FT-817/818, 1=FT-857, 2=FT-897
   ```

4. Reset the Pico or power cycle to start

## Configuration

### config.py Options

```python
# Display rotation (0, 90, 180, 270)
DISPLAY_ROTATION = 0

# CAT baud rate (match your radio settings)
CAT_BAUDRATE = 4800  # or 9600

# Update interval (milliseconds)
UPDATE_INTERVAL_MS = 200

# Display colors (RGB565 format)
FREQ_COLOR = COLOR_GREEN
MODE_COLOR = COLOR_YELLOW
```

## Radio Setup

### FT-817/FT-818

1. Set CAT baud rate in menu:
   - Menu → #14 CAT RATE → Select 4800 or 9600

2. Connect CAT cable to DATA port (3.5mm jack)

### FT-857

1. Set CAT baud rate in menu:
   - Menu → #019 CAT RATE → Select 4800 or 9600

2. Connect to ACC port

### FT-897

1. Set CAT baud rate in menu:
   - Menu → #019 CAT RATE → Select 4800 or 9600

2. Connect to CAT port

## Display Layout

```
┌────────────────────────────────────────┐
│        FT8x7 CAT Display               │  Header
├────────────────────────────────────────┤
│                                        │
│         14.074.000                     │  Frequency
│           MHz  [20m]                   │
│                                        │
│  MODE: USB                             │  Mode
│                                        │
│  S: [████████████░░░░░░░░] S9+10      │  S-Meter
│                                        │
│  [TX] [SQ] [SPL] [SWR]                │  Status
│                                        │
├────────────────────────────────────────┤
│           Connected                    │  Footer
└────────────────────────────────────────┘
```

## Troubleshooting

### No Connection to Radio

1. Check CAT cable wiring (TX/RX may need to be swapped)
2. Verify baud rate matches radio settings
3. Ensure radio is powered on
4. Check ground connection

### Display Not Working

1. Verify SPI wiring connections
2. Check power connections (3.3V and GND)
3. Try adjusting display rotation in config

### Garbled Data

1. Check baud rate setting
2. Verify stop bits (should be 2)
3. Try shielded cable for CAT connection

## Project Structure

```
FT8x7Cat-Display-with-Pi-pico/
├── src/
│   ├── main.py          # Main application
│   ├── config.py        # Configuration settings
│   ├── st7789.py        # LCD display driver
│   ├── font.py          # Bitmap font
│   └── ft8x7_cat.py     # CAT protocol library
├── docs/
│   └── images/          # Documentation images
├── README.md            # This file
└── LICENSE              # GPL-3.0 License
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Yaesu for the FT8x7 CAT protocol documentation
- MicroPython community for the excellent firmware
- Contributors to ST7789 display drivers

## References

- [FT-817 Operating Manual](https://www.yaesu.com/indexVS.cfm?cmd=DisplayProducts&ProdCatID=102&encProdID=06014CD0AFA0702B25B12AB4DC9C0D27)
- [Raspberry Pi Pico Documentation](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [MicroPython Documentation](https://docs.micropython.org/en/latest/)
