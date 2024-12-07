# BlackArch Conversion Toolkit

## Overview

The BlackArch Conversion Toolkit is a comprehensive Python utility designed to seamlessly convert an existing Arch Linux system into a security-focused BlackArch Linux environment. This tool provides an automated, configurable method to integrate BlackArch's extensive collection of cybersecurity and penetration testing tools.

## Author Information
- **Name:** b0urn3
- **GitHub:** [github.com/q4n0](https://github.com/q4n0)
- **Contact:** q4n0@proton.me

## Features

- 🔍 System Compatibility Checking
- 💾 Automatic System Backup
- 🛠 Intelligent Tool Recommendation
- 🔒 Security-Focused Tool Installation
- 🖥 Interactive and Non-Interactive Modes
- 📊 Detailed Logging

## Prerequisites

- Arch Linux system
- Root/sudo access
- Active internet connection
- Minimum 20GB free disk space
- Python 3.8+

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/blackutility.git

# Change directory
cd blackutility

# Ensure executable permissions
chmod +x blackarch_converter.py
```

## Usage

### Basic Usage
```bash
sudo python3 blackarch_converter.py
```

### Advanced Options
```bash
# Specify tool categories
sudo python3 blackarch_converter.py -c network exploitation

# Set optimization level (0-3)
sudo python3 blackarch_converter.py -l 2

# Dry run (simulation mode)
sudo python3 blackarch_converter.py --dry-run

# Non-interactive mode
sudo python3 blackarch_converter.py --non-interactive
```

### Command-Line Arguments
- `-c/--categories`: Select specific tool categories
- `-l/--level`: Set optimization level (default: 2)
- `--dry-run`: Simulate conversion without changes
- `--non-interactive`: Automatic tool installation

## Configuration

The script uses a `ConversionConfiguration` class with customizable parameters:
- `output_directory`: Logging destination
- `backup_directory`: System backup location
- `repositories`: BlackArch repositories to add
- `tool_categories`: Categories for tool recommendations
- `security_level`: Conversion security profile
- `optimization_level`: System optimization setting

## Logging

Conversion logs are stored in `/var/log/blackarch_conversion/` with timestamped log files for tracking and debugging.

## Safety Recommendations

⚠️ **IMPORTANT**: 
- Always backup your system before running
- Understand that this tool makes significant system modifications
- Recommended for advanced users familiar with Linux

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

See the LICENSE file for details. 

## Disclaimer

This tool is provided "as-is" without warranties. Use at your own risk. Always have a backup and understand the changes being made to your system.
