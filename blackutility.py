#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from typing import List, Dict, Optional
import time
import json
import concurrent.futures
import socket
import shutil
import signal
import pickle
import argparse
from tqdm import tqdm  # Enhanced progress bar

class BlackUtility:
    def __init__(self, category: str = 'all', resume: bool = False):
        """
        BlackUtility - Advanced Cybersecurity Tool Installer
        
        A comprehensive tool for managing cybersecurity toolsets
        with robust installation and management capabilities.
        """
        # Colorful ASCII Banner with Contact Information
        self.banner = r"""
 ▄▄▄▄    ██▓    ▄▄▄       ▄████▄   ██░ ██  █    ██ ▄▄▄█████▓ ██▓ ██▓    ██▓▄▄▄█████▓▓██   ██▓
▓█████▄ ▓██▒   ▒████▄    ▒██▀ ▀█  ▓██░ ██▓▒██  ▓██▒▓  ██▒ ▓▒▓██▒▓██▒   ▓██▒▓  ██▒ ▓▒ ▒██  ██▒
▒██▒ ▄██▒██░   ▒██  ▀█▄  ▒▓█    ▄ ▒██▀▀██▓░ ▓██ ▒██░▒ ▓██░ ▒░▒██▒▒██░   ▒██▒▒ ▓██░ ▒░  ▒██ ██░
▒██░█▀  ▒██░   ░██▄▄▄▄██ ▒▓▓▄ ▄██▒░▓█ ░██ ░ ▓▓█  ░██░░ ▓██▓ ░ ░██░▒██░   ░██░░ ▓██▓ ░   ░ ▐██▓░
░▓█  ▀█▓░██████▒▓█   ▓██▒▒ ▓███▀ ░░▓█▒░██▓  ▒ ▓██▓ ░   ▒██▒ ░ ░██████▒░██████▒▒██▒ ░   ░ ██▒▓░
░▒▓███▀▒░ ▒░▓  ░▒▒   ▓▒█░░ ░▒ ▒  ░ ▒ ░░▒░▒  ▒ ▒▓██  ░   ▒ ░░   ░ ▒░▓  ░░ ▒░▓  ░▒ ░░      ██▒▒▒ 
▒░▒   ░ ░ ░ ▒  ░ ▒   ▒▒ ░  ░  ▒    ▒ ░▒░ ░  ░ ▒▓▒   ░     ░    ░ ░ ▒  ░░ ░ ▒  ░  ░      ▓██ ░▒░ 
 ░    ░   ░ ░    ░   ▒   ░         ░  ░░ ░    ▒ ░    ░          ░ ░      ░ ░           ▒ ▒ ░░  
 ░          ░  ░     ░  ░░ ░       ░  ░  ░    ░                   ░  ░    ░  ░          ▒ ░   
      ░                  ░                                                              ░     

    [Cybersecurity Tool Installer]

    Developer: q4n0
    Contact:  
    • Email:    q4n0@proton.me
    • GitHub:  github.com/q4n0
    • IG:      @onlybyhive

    Stay Ethical. Stay Secure.
        """
        
        # Print banner
        print(self.banner)
        
        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='/var/log/blackutility.log',
            filemode='a'
        )
        self.logger = logging.getLogger(__name__)

        # Remaining initialization stays the same as in previous script
        self.state_file = '/var/tmp/blackutility_state.pkl'
        self.category = category
        self.resume = resume
        """
        Initialize BlackArch Linux tool installer with comprehensive logging, configuration, and resume capabilities
        
        Args:
            category (str): Tool category to install
            resume (bool): Whether to resume a previous installation
        """
        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='/var/log/blackarch_installer.log',
            filemode='a'
        )
        self.logger = logging.getLogger(__name__)

        # State tracking
        self.state_file = '/var/tmp/blackarch_installer_state.pkl'
        self.category = category
        self.resume = resume

        # Configuration for tool categories and installation strategies
        self.tool_categories = {
            'all': None,  # Special case for all tools
            'information-gathering': ['nmap', 'maltego', 'dmitry', 'fierce'],
            'vulnerability-analysis': ['nmap', 'openvas', 'nikto', 'sqlmap'],
            'web-applications': ['burpsuite', 'sqlmap', 'zaproxy', 'wpscan'],
            'exploitation': ['metasploit', 'exploitdb', 'social-engineer-toolkit'],
            'password-attacks': ['john', 'hashcat', 'hydra', 'medusa'],
            'wireless-attacks': ['aircrack-ng', 'wireshark', 'reaver'],
            'reverse-engineering': ['radare2', 'ida-free', 'ghidra'],
            'forensics': ['volatility', 'autopsy', 'binwalk']
        }

        # Installation configuration
        self.max_retries = 3
        self.retry_delay = 10  # seconds between retries
        self.min_storage_required = 10 * 1024 * 1024 * 1024  # 10 GB minimum

        # Signal handling for graceful interruption
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def check_internet_connection(self) -> bool:
        """
        Check internet connectivity with multiple attempts and timeout
        
        Returns:
            bool: True if internet is stable, False otherwise
        """
        try:
            # Try to connect to multiple reliable endpoints
            test_hosts = [
                ('8.8.8.8', 53),  # Google DNS
                ('1.1.1.1', 53),  # Cloudflare DNS
                ('9.9.9.9', 53)   # Quad9 DNS
            ]
            
            for host, port in test_hosts:
                socket.setdefaulttimeout(3)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.error, socket.timeout):
            self.logger.warning("Internet connection is unstable")
            return False

    def check_storage_availability(self) -> bool:
        """
        Check available storage space
        
        Returns:
            bool: True if sufficient storage is available, False otherwise
        """
        total, used, free = shutil.disk_usage('/')
        
        # Log storage details
        self.logger.info(f"Total Storage: {total / (1024*1024*1024):.2f} GB")
        self.logger.info(f"Free Storage: {free / (1024*1024*1024):.2f} GB")
        
        # Check if free space meets minimum requirement
        is_sufficient = free >= self.min_storage_required
        
        if not is_sufficient:
            self.logger.error(f"Insufficient storage. Requires at least {self.min_storage_required / (1024*1024*1024):.2f} GB")
        
        return is_sufficient

    def handle_interrupt(self, signum, frame):
        """
        Handle interruption signals to allow pausing/resuming
        
        Args:
            signum (int): Signal number
            frame (frame): Current stack frame
        """
        self.logger.warning(f"Received interrupt signal {signum}")
        
        # Save current state
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump({
                    'category': self.category,
                    'completed_tools': self.completed_tools,
                    'remaining_tools': self.remaining_tools
                }, f)
            print("\nInstallation paused. Use --resume to continue later.")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
        
        sys.exit(0)

    def load_previous_state(self) -> Optional[Dict]:
        """
        Load previous installation state if resuming
        
        Returns:
            Optional[Dict]: Saved state or None
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            self.logger.error(f"Error loading previous state: {e}")
        return None

    def check_arch_system(self) -> bool:
        """
        Verify the system is running Arch Linux
        
        Returns:
            bool: True if running Arch Linux, False otherwise
        """
        try:
            with open('/etc/os-release', 'r') as f:
                return 'Arch Linux' in f.read()
        except FileNotFoundError:
            self.logger.error("Unable to verify Arch Linux system")
            return False

    def add_blackarch_repository(self) -> bool:
        """
        Add BlackArch Linux repository with comprehensive error handling
        
        Returns:
            bool: True if repository added successfully, False otherwise
        """
        if not self.check_internet_connection():
            print("❌ Internet connection is unstable. Please check your network.")
            return False

        commands = [
            ['pacman', '-Sy', '--noconfirm'],
            ['curl', '-O', 'https://blackarch.org/strap.sh'],
            ['chmod', '+x', 'strap.sh'],
            ['sudo', './strap.sh']
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    capture_output=True, 
                    text=True
                )
                print(f"✅ Successfully executed: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Command failed: {' '.join(cmd)}")
                self.logger.error(f"Error output: {e.stderr}")
                return False
        return True

    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Retrieve tools for a specific category with error handling
        
        Args:
            category (str): Tool category to retrieve
        
        Returns:
            List[str]: List of tools in the specified category
        """
        if category not in self.tool_categories:
            self.logger.error(f"Invalid category: {category}")
            return []

        if category == 'all':
            # Generate full tool list from BlackArch repository
            try:
                result = subprocess.run(
                    ['pacman', '-Sql', 'blackarch'], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                return result.stdout.splitlines()
            except subprocess.CalledProcessError:
                self.logger.error("Failed to retrieve tools list")
                return []

        return self.tool_categories.get(category, [])

    def install_tools(self, tools: List[str]) -> Dict[str, bool]:
        """
        Install tools with advanced retry, parallel processing, and progress tracking
        
        Args:
            tools (List[str]): List of tools to install
        
        Returns:
            Dict[str, bool]: Installation results for each tool
        """
        # Check storage before starting
        if not self.check_storage_availability():
            print("❌ Insufficient storage space. Aborting installation.")
            return {}

        # Resume previous state if applicable
        previous_state = self.load_previous_state() if self.resume else None
        
        if previous_state:
            tools = previous_state.get('remaining_tools', tools)
            self.completed_tools = previous_state.get('completed_tools', [])
        else:
            self.completed_tools = []
        
        self.remaining_tools = tools.copy()

        def install_tool(tool):
            # Skip already installed tools
            if tool in self.completed_tools:
                return tool, True

            for attempt in range(self.max_retries):
                try:
                    # Check internet before each installation attempt
                    if not self.check_internet_connection():
                        print(f"❌ Internet unstable. Pausing installation of {tool}")
                        return tool, False

                    subprocess.run(
                        ['sudo', 'pacman', '-S', tool, '--noconfirm'], 
                        check=True, 
                        capture_output=True
                    )
                    
                    # Update tracking
                    self.completed_tools.append(tool)
                    self.remaining_tools.remove(tool)
                    
                    return tool, True
                except subprocess.CalledProcessError:
                    self.logger.warning(f"Installation attempt {attempt+1} failed for {tool}")
                    time.sleep(self.retry_delay)
            return tool, False

        # Use progress bar with tqdm
        results = {}
        with tqdm(total=len(tools), desc="Installing BlackArch Tools", unit="tool") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                for tool, success in executor.map(install_tool, self.remaining_tools):
                    results[tool] = success
                    pbar.update(1)
                    
                    # Remove state file after successful completion
                    if os.path.exists(self.state_file):
                        os.remove(self.state_file)

        return results

    def generate_install_report(self, results: Dict[str, bool]) -> None:
        """
        Generate comprehensive installation report
        
        Args:
            results (Dict[str, bool]): Installation results for each tool
        """
        successful_tools = [tool for tool, status in results.items() if status]
        failed_tools = [tool for tool, status in results.items() if not status]

        report = {
            'total_tools': len(results),
            'successful_tools': successful_tools,
            'failed_tools': failed_tools,
            'success_rate': len(successful_tools) / len(results) * 100 if results else 0
        }

        with open('/var/log/blackarch_installation_report.json', 'w') as f:
            json.dump(report, f, indent=4)

        # Print colorful terminal report
        print("\n🔧 BlackArch Installation Report 🔧")
        print(f"Total Tools: {report['total_tools']}")
        print(f"✅ Successful Tools: {len(successful_tools)}")
        print(f"❌ Failed Tools: {len(failed_tools)}")
        print(f"📊 Success Rate: {report['success_rate']:.2f}%")

        # Detailed logging
        self.logger.info(f"Total Tools: {report['total_tools']}")
        self.logger.info(f"Successful Tools: {len(successful_tools)}")
        self.logger.info(f"Failed Tools: {len(failed_tools)}")
        self.logger.info(f"Success Rate: {report['success_rate']:.2f}%")

    def main(self):
        """
        Main installation workflow
        """
        # Validate Arch Linux system
        if not self.check_arch_system():
            print("❌ Not an Arch Linux system. Aborting.")
            sys.exit(1)

        # Add BlackArch repository
        if not self.add_blackarch_repository():
            print("❌ Failed to add BlackArch repository")
            sys.exit(1)

        # Get tools to install
        tools = self.get_tools_by_category(self.category)
        
        # Install tools
        installation_results = self.install_tools(tools)
        
        # Generate report
        self.generate_install_report(installation_results)

def parse_arguments():
    """
    Parse command-line arguments with enhanced description
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='BlackUtility - Advanced Cybersecurity Tool Management System',
        epilog='Developed by q4n0 | Secure Your Arsenal'
    )
    parser.add_argument(
        '-c', '--category', 
        default='all', 
        help='Specify tool category to install (default: all available categories)'
    )
    parser.add_argument(
        '-r', '--resume', 
        action='store_true', 
        help='Resume a previously interrupted installation'
    )
    return parser.parse_args()

if __name__ == '__main__':
    # Add a startup message
    print("🔒 BlackUtility Cybersecurity Tool Installer 🔒")
    print("Preparing to manage your cybersecurity toolkit...\n")
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Create and run installer
    try:
        installer = BlackUtility(
            category=args.category, 
            resume=args.resume
        )
        installer.main()
    except Exception as e:
        print(f"❌ Installation encountered an error: {e}")
        sys.exit(1)

# Developer Metadata
__author__ = "q4n0"
__contact__ = {
    "email": "q4n0@proton.me",
    "github": "github.com/q4n0",
    "instagram": "@onlybyhive"
}
