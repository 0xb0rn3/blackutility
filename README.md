# 🔒 BlackUtility: Cybersecurity Tool Management System

## Overview

BlackUtility is an advanced, automated tool for managing and installing cybersecurity tools on Arch Linux systems. Designed for security professionals, researchers, and ethical hackers, this utility simplifies the process of setting up a comprehensive cybersecurity toolkit.

## 🌟 Key Features

### Comprehensive Tool Management
- Install tools across multiple cybersecurity domains
- Support for targeted category-based installations
- Robust error handling and retry mechanisms
- Parallel tool installation for efficiency

### Installation Categories
BlackUtility supports the following tool categories:
- Information Gathering
- Vulnerability Analysis
- Web Applications
- Exploitation
- Password Attacks
- Wireless Attacks
- Reverse Engineering
- Forensics

### Advanced Capabilities
- Internet connectivity verification
- Storage space validation
- Detailed logging
- Installation state tracking and resume functionality
- Comprehensive installation reporting

## 🛠 Prerequisites

- Arch Linux system
- Sudo privileges
- Active internet connection
- Minimum 10 GB of free storage space

## 📦 Installation

1. Clone the repository
```bash
git clone https://github.com/q4n0/blackutility.git
cd blackutility
```

2. Ensure script is executable
```bash
chmod +x blackutility.py
```

## 🚀 Usage

### Basic Usage
```bash
sudo python3 blackutility.py
```
This will install all available BlackArch tools.

### Advanced Usage Options

#### Install Specific Category
```bash
sudo python3 blackutility.py -c web-applications
```

#### Resume Interrupted Installation
```bash
sudo python3 blackutility.py -r
```

## 📋 Command-Line Arguments

- `-c, --category`: Specify tool category (default: all)
- `-r, --resume`: Resume a previously interrupted installation

## 🔍 How It Works

1. Verifies Arch Linux system
2. Adds BlackArch repository
3. Retrieves tool list for specified category
4. Performs parallel tool installation
5. Generates comprehensive installation report

## 📊 Installation Reporting

After installation, a detailed report is generated at:
`/var/log/blackarch_installation_report.json`

The report includes:
- Total tools processed
- Successfully installed tools
- Failed installations
- Overall success rate

## ⚠️ Important Notes

- Requires active internet connection
- Minimum 10 GB storage recommended
- Only works on Arch Linux systems
- Uses sudo for package management

## 🛡️ Ethical Use Statement

BlackUtility is designed for authorized cybersecurity research, penetration testing, and educational purposes. Users must comply with local laws and obtain proper authorization before using any included tools.

## 👤 Developer Information

- **Developer**: q4n0
- **Contact**:
  - Email: q4n0@proton.me
  - GitHub: github.com/q4n0
  - Instagram: @onlybyhive

## 📄 License

[Read the License.md file for License information]

## 🤝 Contributions

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 🚨 Disclaimer

This tool is for educational and authorized testing purposes only. Misuse of these tools can be illegal and unethical, Tool is provided as is with no warranties proceed with CAUTION!
