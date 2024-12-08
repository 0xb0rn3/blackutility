#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import argparse
import json
import shutil
from typing import List, Dict, Optional
from dataclasses import dataclass
import platform
from datetime import datetime

# Color formatting
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # Fallback if colorama is not installed
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ''
    class Style:
        RESET_ALL = ''
        BRIGHT = ''

# Utility Constants
BLACKARCH_REPO_URL = "https://blackarch.org/blackarch-repo.html"
SUPPORTED_DESKTOP_ENVIRONMENTS = [
    'gnome', 'kde', 'xfce', 'mate', 'cinnamon', 'lxde', 'lxqt'
]

class BlackUtilityError(Exception):
    """Custom exception for BlackUtility operations"""
    def __init__(self, message: str, error_code: int = 1):
        super().__init__(message)
        self.error_code = error_code

@dataclass
class SystemInfo:
    """Comprehensive system information class"""
    distribution: str
    desktop_environment: str
    arch: str
    kernel: str

class BlackUtility:
    """Main BlackUtility class for system management and tool installation"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize BlackUtility with logging and system detection
        
        Args:
            verbose (bool): Enable verbose logging
        """
        # Setup logging
        self.logger = self._setup_logging(verbose)
        
        # Detect system information
        self.system_info = self._detect_system_info()
        
        # Validate system compatibility
        self._validate_system()
    
    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """
        Configure logging with console and file handlers
        
        Args:
            verbose (bool): Enable debug logging
        
        Returns:
            logging.Logger: Configured logger
        """
        # Create log directory
        log_dir = os.path.expanduser('~/.local/share/blackutility/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger('BlackUtility')
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_console_formatter = logging.Formatter(
            f'{Fore.CYAN}%(levelname)s{Style.RESET_ALL}: %(message)s'
        )
        console_handler.setFormatter(console_console_formatter)
        
        # File handler
        log_file = os.path.join(log_dir, f'blackutility_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _detect_system_info(self) -> SystemInfo:
        """
        Detect comprehensive system information
        
        Returns:
            SystemInfo: Detailed system information
        """
        # Detect distribution
        dist = self._detect_distribution()
        
        # Detect desktop environment
        desktop = self._detect_desktop_environment()
        
        return SystemInfo(
            distribution=dist,
            desktop_environment=desktop,
            arch=platform.machine(),
            kernel=platform.release()
        )
    
    def _detect_distribution(self) -> str:
        """
        Detect the specific Linux distribution
        
        Returns:
            str: Distribution name
        """
        try:
            # Try reading from os-release
            with open('/etc/os-release', 'r') as f:
                os_info = dict(line.strip().split('=') for line in f if '=' in line)
            
            # Prioritize ID over NAME
            return (os_info.get('ID', os_info.get('NAME', 'unknown')).lower().replace('"', ''))
        except FileNotFoundError:
            # Fallback methods
            try:
                # Use lsb_release if available
                dist = subprocess.check_output(['lsb_release', '-i'], 
                                               universal_newlines=True).split(':')[1].strip().lower()
                return dist
            except (subprocess.CalledProcessError, FileNotFoundError):
                return 'unknown'
    
    def _detect_desktop_environment(self) -> str:
        """
        Detect the current desktop environment
        
        Returns:
            str: Desktop environment name (lowercase)
        """
        # Check XDG_CURRENT_DESKTOP
        desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if desktop_env:
            return desktop_env
        
        # Check DESKTOP_SESSION
        desktop_session = os.environ.get('DESKTOP_SESSION', '').lower()
        if desktop_session:
            return desktop_session
        
        return 'unknown'
    
    def _validate_system(self):
        """
        Validate system compatibility for BlackArch tools
        
        Raises:
            BlackUtilityError: If system is incompatible
        """
        # Check if system is Arch-based
        arch_based_distros = ['arch', 'manjaro', 'endeavouros', 'garuda']
        if self.system_info.distribution not in arch_based_distros:
            self.logger.warning(f"Detected {self.system_info.distribution}, which is not a primary Arch-based distribution.")
        
        # Check package manager
        try:
            subprocess.run(['pacman', '--version'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL, 
                           check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise BlackUtilityError("Pacman package manager not found. This tool requires an Arch-based system.")
    
    def add_blackarch_repository(self):
        """
        Add BlackArch repository to system's package sources
        """
        self.logger.info("Adding BlackArch repository...")
        
        try:
            # Download and run BlackArch repository setup script
            subprocess.run([
                'curl', '-O', 'https://blackarch.org/strap.sh'
            ], check=True)
            
            # Make script executable
            subprocess.run(['chmod', '+x', 'strap.sh'], check=True)
            
            # Run repository setup (requires sudo)
            subprocess.run(['sudo', './strap.sh'], check=True)
            
            # Clean up setup script
            os.remove('strap.sh')
            
            self.logger.info("BlackArch repository added successfully!")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to add BlackArch repository: {e}")
            raise BlackUtilityError("Repository setup failed")
    
    def install_tools(self, tools: Optional[List[str]] = None, mode: str = 'minimal'):
        """
        Install BlackArch hacking tools
        
        Args:
            tools (Optional[List[str]]): Specific tools to install
            mode (str): Installation mode ('minimal', 'full', 'custom')
        """
        self.logger.info(f"Starting tool installation in {mode} mode")
        
        # Ensure BlackArch repository is added
        self.add_blackarch_repository()
        
        # Determine tool list based on mode
        if mode == 'full':
            # Install all BlackArch tools
            install_command = ['sudo', 'pacman', '-Syu', 'blackarch']
        elif mode == 'minimal':
            # Install essential tools
            minimal_tools = [
                'nmap', 'wireshark', 'metasploit', 'aircrack-ng', 
                'burpsuite', 'hydra', 'sqlmap'
            ]
            install_command = ['sudo', 'pacman', '-S'] + minimal_tools
        elif mode == 'custom' and tools:
            # Install specified tools
            install_command = ['sudo', 'pacman', '-S'] + tools
        else:
            raise BlackUtilityError("Invalid installation mode or no tools specified")
        
        try:
            # Execute installation
            subprocess.run(install_command, check=True)
            self.logger.info("Tool installation completed successfully!")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Tool installation failed: {e}")
            raise BlackUtilityError("Tool installation encountered an error")
    
    def generate_desktop_menus(self):
        """
        Generate desktop menu entries for installed tools
        Supports multiple desktop environments
        """
        self.logger.info(f"Generating menu entries for {self.system_info.desktop_environment}")
        
        # Desktop-specific menu generation logic
        if self.system_info.desktop_environment in SUPPORTED_DESKTOP_ENVIRONMENTS:
            try:
                # Placeholder for desktop-specific menu generation
                # This would involve creating .desktop files in appropriate directories
                # Example for GNOME/XDG compliant desktops
                menu_dir = os.path.expanduser('~/.local/share/applications')
                os.makedirs(menu_dir, exist_ok=True)
                
                # Example tool menu entry generation
                tools_to_menu = [
                    ('Nmap', 'nmap', 'Network Scanner'),
                    ('Wireshark', 'wireshark', 'Network Protocol Analyzer'),
                    ('Metasploit', 'msfconsole', 'Penetration Testing Framework')
                ]
                
                for name, executable, comment in tools_to_menu:
                    desktop_entry = f'''[Desktop Entry]
Name={name}
Exec={executable}
Type=Application
Comment={comment}
Categories=Network;Security;
'''
                    
                    with open(os.path.join(menu_dir, f'{executable}.desktop'), 'w') as f:
                        f.write(desktop_entry)
                
                self.logger.info("Desktop menu entries generated successfully!")
            except Exception as e:
                self.logger.error(f"Failed to generate menu entries: {e}")
        else:
            self.logger.warning(f"Unsupported desktop environment: {self.system_info.desktop_environment}")

def main():
    """
    Main entry point for BlackUtility
    """
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='BlackUtility - Comprehensive Hacking Tools Installer',
        epilog='Simplify BlackArch tools installation across Arch-based distributions.'
    )
    
    parser.add_argument('-m', '--mode', 
                        choices=['minimal', 'full', 'custom'], 
                        default='minimal',
                        help='Installation mode for BlackArch tools')
    parser.add_argument('-t', '--tools', 
                        nargs='+', 
                        help='Specific tools to install in custom mode')
    parser.add_argument('-v', '--verbose', 
                        action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Initialize BlackUtility
        black_utility = BlackUtility(verbose=args.verbose)
        
        # Display system information
        print(f"{Fore.CYAN}System Information:{Style.RESET_ALL}")
        print(json.dumps(black_utility.system_info.__dict__, indent=2))
        
        # Install tools based on mode
        black_utility.install_tools(
            tools=args.tools, 
            mode=args.mode
        )
        
        # Generate desktop menus
        black_utility.generate_desktop_menus()
        
        print(f"{Fore.GREEN}BlackUtility completed successfully!{Style.RESET_ALL}")
    
    except BlackUtilityError as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(e.error_code)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == '__main__':
    main()
