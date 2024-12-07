# BlackUtility: Advanced Linux Security Transformation Toolkit

## 🚀 Overview

BlackUtility is an advanced, interactive Linux security transformation toolkit designed to simplify and streamline the process of converting your Linux system into a robust security-focused environment. Built with flexibility, user experience, and comprehensive system management in mind, BlackUtility provides a powerful yet intuitive interface for security professionals and enthusiasts.

## ✨ Key Features

### 1. Intelligent System Compatibility
- Comprehensive pre-flight system checks
- Verifies system readiness before conversion
- Provides detailed compatibility reports

### 2. Interactive Tool Ecosystem
- Dynamic tool recommendation engine
- Customizable tool category selection
- Interactive installation process with detailed insights

### 3. Enhanced User Experience
- **Colorful Console Output**: Visually engaging terminal interface
- **Detailed Error Reporting**: Clear, actionable error messages
- **Flexible Configuration**: Multiple runtime options

### 4. Robust System Management
- Full system backup before modifications
- Granular optimization levels
- Secure repository management

## 🛠 Installation

### Prerequisites
- Python 3.8+
- `sudo` privileges
- Arch Linux base system
- Active internet connection

### Quick Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/blackutility.git

# Change directory
cd blackutility

# Install required dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x blackutility.py
```

## 🖥 Usage

### Basic Execution
```bash
# Run with default settings
sudo python3 blackutility.py
```

### Advanced Configuration Options

#### Specify Tool Categories
```bash
# Install tools from specific security domains
sudo python3 blackutility.py -c network exploitation
```

#### Dry Run Mode
```bash
# Simulate conversion without making system changes
sudo python3 blackutility.py --dry-run
```

#### Non-Interactive Installation
```bash
# Automated tool installation without prompts
sudo python3 blackutility.py --non-interactive
```

## 🎛 Configuration Parameters

### Command-Line Arguments
| Argument | Description | Default | Options |
|----------|-------------|---------|---------|
| `-c, --categories` | Specify tool installation categories | `['network', 'exploitation']` | Any BlackArch tool category |
| `-l, --level` | System optimization intensity | `2` | `0-3` |
| `--dry-run` | Simulate conversion | `False` | Flag |
| `--non-interactive` | Disable interactive mode | Interactive | Flag |

### Optimization Levels
- **Level 0**: Minimal system changes
- **Level 1**: Basic performance tuning
- **Level 2**: Balanced optimization (Recommended)
- **Level 3**: Aggressive performance and security hardening

## 🔒 Security Considerations
- Requires careful consideration before execution
- Designed for experienced users
- Always backup critical data
- Understand potential system modifications

## 📋 Logging
- Detailed conversion logs stored in `/var/log/blackarch_conversion/`
- Comprehensive error tracking
- Timestamped log files for easy reference

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## ⚠️ Disclaimer
BlackUtility is provided "as-is" without warranties. Users are responsible for understanding and managing system-level changes. Always have a recovery plan and backup important data.

## 📞 Support
- Open GitHub Issues for bug reports
- Community support via GitHub Discussions
- Professional support: [ q4n0@proton.me ]


---

**Happy Securing! 🛡️**
