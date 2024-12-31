# BlackUtility - Advanced Cybersecurity Arsenal for Arch

BlackUtility is a sophisticated command-line utility designed to streamline the installation and management of BlackArch penetration testing tools on Arch Linux systems. Built with modern terminal interfaces and robust error handling, it provides a seamless experience for cybersecurity professionals and enthusiasts.

## Features

- **Intelligent Package Management**: Automated installation of the complete BlackArch toolkit with smart retry mechanisms and timeout handling
- **Modern Terminal Interface**: Beautiful progress bars, spinners, and color-coded output for enhanced visibility
- **Resource Management**: Automatic system requirement verification and disk space management
- **Error Resilience**: Comprehensive error handling with automatic retries and detailed logging
- **Safe Operation**: Lock file implementation to prevent concurrent installations
- **User-Friendly**: Clear progress indicators and status messages throughout the installation process

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

1. Run the utility with root privileges:
```bash
sudo ./blackutility
```

2. The program will:
   - Verify system requirements
   - Display a warning message
   - Prompt for confirmation
   - Update system packages
   - Install BlackArch tools with progress indication

## Safety Features

- System requirement verification before installation
- Confirmation prompt before system modification
- Lock file mechanism to prevent multiple instances
- Timeout handling for stuck operations
- Automatic cleanup on interruption
- Detailed logging of all operations

## Logging

The program maintains detailed logs at:
- Main log: `/var/log/blackutility.log`
- Backup log: `/var/log/blackutility.log.bak`

Log entries include timestamps and severity levels for easy troubleshooting.

## Error Handling

The utility includes several error handling mechanisms:
- Multiple retry attempts for failed installations
- Timeout handling for hung operations
- Disk space verification
- Proper cleanup on interruption
- Detailed error logging

## Terminal Interface Features

- Progress bars with percentage completion
- Color-coded status messages
- Modern Unicode symbols for status indication
- Centered text boxes for important messages
- Smooth animations for long-running operations

## Contributing

1. Fork the repository
2. Create your feature branch
3. Implement your changes
4. Create a pull request

Please maintain the existing code style and add appropriate error handling for new features.

## Security Considerations

- The tool requires root privileges - use with caution
- All installed packages come from the official BlackArch repositories
- The program creates lock files to prevent concurrent modifications
- System state is verified before any modifications

## Troubleshooting

Common issues and solutions:

1. **Insufficient Permissions**
   - Ensure you're running with sudo or as root

2. **Installation Failures**
   - Check internet connectivity
   - Verify available disk space
   - Review logs at `/var/log/blackutility.log`

3. **Lock File Issues**
   - Delete `/var/lock/blackutility.lock` if no instance is running

## License

MIT License - see LICENSE file for details

## Acknowledgments

- BlackArch Linux team for maintaining the tool repositories
- Arch Linux community for package management tools
- Contributors to the terminal UI libraries

## Version History

- 0.1: Initial release
  - Basic installation functionality
  - Modern terminal interface
  - Error handling and logging

## Contact

For bugs, features, or questions:
- GitHub Issues: [Project Issues Page](https://github.com/0xb0rn3/blackutility/issues)
- Website: [https://github.com/0xb0rn3/blackutility](https://github.com/0xb0rn3/blackutility)

## Disclaimer

This tool is for educational and professional use in authorized environments only. Users are responsible for complying with applicable laws and regulations when using security tools.
