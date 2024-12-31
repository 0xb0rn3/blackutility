# BlackUtility - Advanced Cybersecurity Arsenal for Arch

BlackUtility is a high-performance command-line utility designed to streamline the installation and management of BlackArch penetration testing tools on Arch Linux systems. Originally written in Python, this project has been completely rewritten in C to provide significant performance improvements and enhanced system-level integration.

## About the Rewrite

The transition from Python to C brings several significant improvements:

- **Enhanced Performance**: Native C implementation provides faster execution and lower resource usage
- **System-Level Integration**: Direct interaction with system calls and terminal interfaces
- **Memory Efficiency**: Optimized memory management and resource utilization
- **Improved Error Handling**: Robust system-level error detection and recovery
- **Real-time Processing**: Enhanced progress monitoring and status updates
- **Reduced Dependencies**: Minimal external library requirements

## Core Features

The C implementation enhances the original Python version with:

- **Intelligent Package Management**: Automated installation with smart retry mechanisms and timeout handling
- **Advanced Terminal Interface**: Real-time progress bars, spinners, and color-coded output
- **Resource Management**: Proactive system requirement verification and disk space monitoring
- **Enhanced Security**: Lock file implementation and privilege verification
- **Comprehensive Logging**: Detailed operation logging with backup functionality
- **Graceful Error Recovery**: Automatic cleanup and state restoration on failures

## Prerequisites

- Arch Linux or Arch-based distribution
- Root privileges
- Minimum system requirements:
  - 10GB of free disk space
  - 2GB RAM
  - Active internet connection
  - Base development tools

## Installation

1. Clone the repository:
```bash
git clone https://github.com/0xb0rn3/blackutility.git
cd blackutility
```

2. Compile the program:
```bash
gcc -o blackutility main.c -lncurses
```

3. Make it executable:
```bash
chmod +x blackutility
```

## Usage

Execute with root privileges:
```bash
sudo ./blackutility
```

The program performs:
- System compatibility verification
- User confirmation for system modifications
- System package updates
- BlackArch tools installation with progress tracking

## Technical Improvements

The C rewrite introduces several technical enhancements:

- **Terminal Handling**: Direct terminal manipulation for smoother display updates
- **Process Management**: Improved control over child processes and system commands
- **Resource Monitoring**: Real-time system resource tracking
- **Signal Handling**: Graceful handling of system signals and interrupts
- **Unicode Support**: Enhanced display with modern Unicode characters
- **Color Management**: Advanced ANSI color support for better visibility

## Safety Features

- Comprehensive system requirement verification
- Explicit user confirmation for system changes
- Process isolation through lock file mechanisms
- Operation timeout management
- Automatic cleanup on interruption
- Detailed operation logging

## Logging System

Logs are maintained at:
- Primary log: `/var/log/blackutility.log`
- Backup log: `/var/log/blackutility.log.bak`

Each log entry includes:
- Precise timestamps
- Operation severity levels
- Detailed status information
- Error context when applicable

## Error Recovery

Enhanced error handling includes:
- Multiple installation retry attempts
- Timeout management for hung operations
- Disk space verification
- Proper cleanup procedures
- Comprehensive error logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement improvements
4. Submit a pull request

Please maintain:
- Existing code style
- Error handling patterns
- Documentation standards
- Performance optimizations

## Security Considerations

- Root privileges required - use with caution
- Official BlackArch repository integration
- Process isolation through lock files
- System state verification
- Secure package handling

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for complete details. The MIT License permits commercial use, modification, distribution, and private use while maintaining limited liability and providing no warranty.

## Maintenance and Support

BlackUtility is actively developed and maintained by [@0xb0rn3](https://github.com/0xb0rn3). For support:

- Submit issues through GitHub Issues
- Follow the project updates
- Contribute improvements
- Report security concerns

## Version History

- 0.3-ALFA: Initial C implementation
  - Complete Python to C rewrite
  - Enhanced terminal interface
  - Improved error handling
  - Performance optimizations
  - System-level integration

## Acknowledgments

- BlackArch Linux team
- Arch Linux community
- Original Python version contributors
- Terminal interface library developers

## Project Links

- GitHub: [https://github.com/0xb0rn3/blackutility](https://github.com/0xb0rn3/blackutility)
- Issues: [Project Issues Page](https://github.com/0xb0rn3/blackutility/issues)

## Disclaimer

This tool is intended for educational and professional use in authorized environments only. Users are responsible for ensuring compliance with applicable laws and regulations when using security tools.

---
Developed and maintained with ♥ by [@0xb0rn3](https://github.com/0xb0rn3)
