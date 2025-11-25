# Copilot Instructions for FT8x7Cat Display with Pi-pico

## Project Overview

This is an open-source project for an FT8x7 CAT (Computer Aided Transceiver) display system using a Raspberry Pi Pico microcontroller with LCD. The project is designed for amateur radio enthusiasts who want to create a display interface for Yaesu FT-817, FT-818, or similar transceivers.

## Tech Stack

- **Microcontroller**: Raspberry Pi Pico (RP2040)
- **Programming**: MicroPython or C/C++ with Pico SDK
- **Display**: LCD module compatible with Pi Pico
- **Protocol**: CAT (Computer Aided Transceiver) serial communication

## Coding Guidelines

- Follow the existing code style in the repository
- Use clear and descriptive variable and function names
- Add comments for complex logic, especially for CAT protocol handling
- Keep functions focused and modular
- Handle serial communication errors gracefully

## Hardware Considerations

- Ensure pin assignments are clearly documented
- Consider power consumption for portable operation
- Account for different LCD module configurations
- Document any hardware modifications required

## Testing

- Test CAT commands with actual transceiver hardware when possible
- Verify LCD display output for different frequency ranges and modes
- Test edge cases for frequency and mode parsing

## Documentation

- Update README.md when adding new features
- Document pin connections and wiring diagrams
- Include setup and installation instructions
- Provide troubleshooting guidance for common issues

## License

This project is licensed under GPL-3.0. Ensure all contributions comply with this license.
