# BlackUtility: Advanced BlackArch Linux Tools Management Utility

## Overview

BlackUtility is a sophisticated Python-based tool designed to streamline and enhance the management of BlackArch Linux security and penetration testing tools. This utility provides a comprehensive solution for discovering, installing, and maintaining a robust collection of cybersecurity tools.

## Key Features

### 🚀 Intelligent Tool Management
- Automated discovery of BlackArch Linux tools
- Parallel tool installation with dynamic throttling
- Comprehensive installation tracking and history

### 🔒 Advanced Security Measures
- Network stability checks before tool installation
- Integrity verification for installed tools
- Detailed logging and error handling

### 📊 Robust Tracking and Reporting
- Persistent state tracking using SQLite database
- Detailed installation history
- Configurable tool categories and installation parameters

## Prerequisites

- Python 3.8+
- Arch Linux or BlackArch Linux
- sudo privileges

## Installation

1. Clone the repository:
```bash
git clone https://github.com/q4n0/blackutility.git
cd blackutility
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x blackutility.py
```

## Usage

Run the tool with sudo privileges:
```bash
sudo python3 blackutility.py
```

### Interactive Menu Options

1. **Install All Tools**: Discovers and installs all available BlackArch tools
2. **Install by Category**: Allows selecting specific tool categories
3. **View Installation History**: Displays detailed tool installation records
4. **System Integrity Check**: Performs comprehensive system verification
5. **Configuration**: Manage and modify utility settings

## Configuration

The utility uses a flexible JSON configuration system with the following default settings:

```json
{
    "categories": ["penetration-testing", "vulnerability-assessment"],
    "max_parallel_downloads": 8,
    "network_timeout": 45,
    "retry_attempts": 5,
    "integrity_check": true,
    "auto_update": false,
    "security_level": "standard"
}
```

You can customize these settings by modifying the `blackutility_config.json` file.

## Logging

BlackUtility generates detailed log files in `~/.cache/blackutility/logs/` for comprehensive tracking and troubleshooting.

## Security Considerations

- Requires sudo privileges for package management
- Implements multiple network and integrity checks
- Provides granular logging for audit trails

## Contribution

Contributions are welcome! Please submit pull requests or open issues on the project's GitHub repository.


## Disclaimer

This tool is intended for authorized and legal security testing and research. Always ensure you have proper authorization before using security tools.
