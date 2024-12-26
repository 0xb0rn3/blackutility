#!/usr/bin/env python3

# Standard library imports for system operations and utilities
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
import hashlib
from pathlib import Path

# Third-party imports for enhanced functionality
from tqdm import tqdm  # For progress bars
import requests       # For downloading files

class BlackUtility:
    def handle_interrupt(self, signum, frame):
        """
        Handle interruption signals gracefully and save state.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.warning(f"Received interrupt signal {signum}")
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

    def __init__(self, category: str = 'all', resume: bool = False):
        """
        Initialize the BlackUtility installer with comprehensive security tool management.
        
        Args:
            category (str): Tool category to install (default: 'all')
            resume (bool): Whether to resume a previous installation
        """
        self.banner = r"""
██████╗ ██╗      █████╗  ██████╗██╗  ██╗██╗   ██╗████████╗██╗██╗     
██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██║   ██║╚══██╔══╝██║██║     
██████╔╝██║     ███████║██║     █████╔╝ ██║   ██║   ██║   ██║██║     
██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██║   ██║   ██║   ██║██║     
██████╔╝███████╗██║  ██║╚██████╗██║  ██╗╚██████╔╝   ██║   ██║███████╗
╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝╚══════╝
                                                                      
    [Advanced Cybersecurity Arsenal for Arch]
    
    Developer: 0xb0rn3
    Repository: github.com/0xb0rn3/blackutility
    
    Stay Ethical. Stay Secure. Enjoy!
        """
        
        print(self.banner)
        
        # Initialize logging configuration
        os.makedirs('/var/log', exist_ok=True)  # Ensure log directory exists
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='/var/log/blackutility.log',
            filemode='a'
        )
        self.logger = logging.getLogger(__name__)

        # State management configuration
        self.state_file = '/var/tmp/blackutility_state.pkl'
        self.category = category
        self.resume = resume
        self.completed_tools = []
        self.remaining_tools = []

        # Tool categories with their respective packages
        self.tool_categories = {
            'all': None,
            'information-gathering': ['nmap', 'maltego', 'dmitry', 'fierce'],
            'vulnerability-analysis': ['nmap', 'openvas', 'nikto', 'sqlmap'],
            'web-applications': ['burpsuite', 'sqlmap', 'zaproxy', 'wpscan'],
            'exploitation': ['metasploit', 'exploitdb', 'social-engineer-toolkit'],
            'password-attacks': ['john', 'hashcat', 'hydra', 'medusa'],
            'wireless-attacks': ['aircrack-ng', 'wireshark', 'reaver'],
            'reverse-engineering': ['radare2', 'ida-free', 'ghidra'],
            'forensics': ['volatility', 'autopsy', 'binwalk']
        }

        # Installation parameters
        self.max_retries = 3
        self.retry_delay = 10  # seconds
        self.min_storage_required = 10 * 1024 * 1024 * 1024  # 10 GB

        # Set up signal handlers for graceful interruption
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

def download_and_verify_strap(self) -> bool:
    """Download and verify the BlackArch strap script"""
    print("\n📥 Verifying BlackArch strap script...")
    
    strap_path = "./strap.sh"  # Look for strap.sh in current directory
    
    try:
        # Check if strap.sh exists in current directory
        if not os.path.exists(strap_path):
            print("❌ strap.sh not found in current directory")
            print("Please download it using: curl -O https://blackarch.org/strap.sh")
            return False
            
        # Read the local file
        with open(strap_path, "rb") as f:
            content = f.read()
            
        # Verify SHA1 sum
        sha1_calc = hashlib.sha1(content).hexdigest()
        
        # Get official SHA1 from BlackArch
        try:
            sha1_response = requests.get("https://blackarch.org/strap.sh.sha1sum", timeout=30)
            sha1_response.raise_for_status()
            sha1_official = sha1_response.text.strip().split()[0]
            
            if sha1_calc == sha1_official:
                print("✅ Strap script verified successfully")
                # Copy to /tmp for installation
                shutil.copy2(strap_path, "/tmp/strap.sh")
                os.chmod("/tmp/strap.sh", 0o755)
                return True
            else:
                print("❌ Strap script verification failed")
                print("SHA1 mismatch:")
                print(f"Expected: {sha1_official}")
                print(f"Got:      {sha1_calc}")
                return False
        except requests.exceptions.RequestException as e:
            print("⚠️ Could not fetch official SHA1 sum. Proceeding with caution...")
            # If we can't verify, we'll trust the local file
            shutil.copy2(strap_path, "/tmp/strap.sh")
            os.chmod("/tmp/strap.sh", 0o755)
            return True
                
    except Exception as e:
        self.logger.error(f"Error verifying strap script: {e}")
        print(f"❌ Failed to verify strap script: {e}")
        return False

    def install_strap(self) -> bool:
        """Install the BlackArch strap script"""
        try:
            result = subprocess.run(
                ['sudo', '/tmp/strap.sh'],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ BlackArch strap installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Strap installation failed: {e.stderr}")
            print(f"❌ Strap installation failed: {e.stderr}")
            return False

    def check_internet_connection(self) -> bool:
        """
        Check internet connectivity using multiple DNS servers.
        
        Returns:
            bool: True if connection is stable, False otherwise
        """
        try:
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
        Verify sufficient storage space is available.
        
        Returns:
            bool: True if enough space available, False otherwise
        """
        total, used, free = shutil.disk_usage('/')
        self.logger.info(f"Total Storage: {total / (1024*1024*1024):.2f} GB")
        self.logger.info(f"Free Storage: {free / (1024*1024*1024):.2f} GB")
        
        is_sufficient = free >= self.min_storage_required
        if not is_sufficient:
            self.logger.error(f"Insufficient storage. Requires at least {self.min_storage_required / (1024*1024*1024):.2f} GB")
        return is_sufficient

    def check_arch_system(self) -> bool:
        """
        Verify the system is running Arch Linux.
        
        Returns:
            bool: True if running on Arch Linux, False otherwise
        """
        try:
            with open('/etc/os-release', 'r') as f:
                return 'Arch Linux' in f.read()
        except FileNotFoundError:
            self.logger.error("Unable to verify Arch Linux system")
            return False

    def handle_interrupt(self, signum, frame):
        """
        Handle interruption signals gracefully and save state.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.warning(f"Received interrupt signal {signum}")
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

    def main(self):
        """
        Main installation workflow with comprehensive error handling.
        """
        try:
            # Check all requirements first
            if not self.check_requirements():
                print("❌ Requirements not met. Aborting installation.")
                sys.exit(1)

            # Add BlackArch repository
            if not self.add_blackarch_repository():
                print("❌ Failed to add BlackArch repository")
                sys.exit(1)

            # Get tools to install
            print("\n📋 Preparing tool list...")
            tools = self.get_tools_by_category(self.category)
            if not tools:
                print("❌ No tools found for the specified category")
                sys.exit(1)

            print(f"🔍 Found {len(tools)} tools to install in category '{self.category}'")
            
            # Install tools
            installation_results = self.install_tools(tools)
            
            # Generate report
            self.generate_install_report(installation_results)
            
            print("\n🎉 Installation process completed!")
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}", exc_info=True)
            print(f"\n❌ Fatal error: {e}")
            sys.exit(1)

    def check_requirements(self):
        """
        Comprehensive check of all requirements before proceeding with BlackArch installation.
        """
        requirements_status = {
            'root_access': False,
            'arch_system': False,
            'internet_connection': False,
            'storage_space': False,
            'ram_requirements': False,
            'strap_exists': False,
            'pacman_ready': False
        }
        
        print("\n🔍 Checking system requirements...")
        
        # Check for root/sudo access
        try:
            subprocess.run(['sudo', '-n', 'true'], check=True, capture_output=True)
            requirements_status['root_access'] = True
            print("✅ Root access available")
        except subprocess.CalledProcessError:
            print("❌ Root access not available")
            return False
            
        # Verify Arch Linux system
        if self.check_arch_system():
            requirements_status['arch_system'] = True
            print("✅ Running on Arch Linux")
        else:
            print("❌ Not running on Arch Linux")
            return False
            
        # Check internet connectivity
        if self.check_internet_connection():
            requirements_status['internet_connection'] = True
            print("✅ Internet connection stable")
        else:
            print("❌ Internet connection unstable")
            return False
            
        # Verify storage space
        if self.check_storage_availability():
            requirements_status['storage_space'] = True
            print("✅ Sufficient storage space available")
        else:
            print("❌ Insufficient storage space")
            return False
            
        # Check RAM requirements (minimum 2GB)
        total_ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        if total_ram >= 2 * 1024 ** 3:
            requirements_status['ram_requirements'] = True
            print("✅ Sufficient RAM available")
        else:
            print("❌ Insufficient RAM (minimum 2GB required)")
            return False

        return all(requirements_status.values())

    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Get list of tools for the specified category.
        
        Args:
            category (str): Tool category name
            
        Returns:
            List[str]: List of tool names
        """
        if category not in self.tool_categories:
            self.logger.error(f"Invalid category: {category}")
            return []

        if category == 'all':
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
        Install specified tools with retry mechanism and progress tracking.
        
        Args:
            tools (List[str]): List of tools to install
            
        Returns:
            Dict[str, bool]: Installation results for each tool
        """
        if not self.check_storage_availability():
            print("❌ Insufficient storage space. Aborting installation.")
            return {}

        # Load previous state if resuming
        previous_state = self.load_previous_state() if self.resume else None
        
        if previous_state:
            tools = previous_state.get('remaining_tools', tools)
            self.completed_tools = previous_state.get('completed_tools', [])
        
        self.remaining_tools = tools.copy()

        def install_tool(tool: str) -> tuple:
            """Install a single tool with retry mechanism."""
            if tool in self.completed_tools:
                return tool, True

            for attempt in range(self.max_retries):
                try:
                    if not self.check_internet_connection():
                        print(f"❌ Internet unstable. Pausing installation of {tool}")
                        return tool, False

                    subprocess.run(
                        ['sudo', 'pacman', '-S', '--noconfirm', tool],
                        check=True,
                        capture_output=True
                    )
                    
                    self.completed_tools.append(tool)
                    self.remaining_tools.remove(tool)
                    
                    return tool, True
                except subprocess.CalledProcessError:
                    self.logger.warning(f"Installation attempt {attempt+1} failed for {tool}")
                    time.sleep(self.retry_delay)
            return tool, False

        results = {}
        with tqdm(total=len(tools), desc="Installing BlackArch Tools", unit="tool") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_tool = {executor.submit(install_tool, tool): tool for tool in tools}
                for future in concurrent.futures.as_completed(future_to_tool):
                    tool = future_to_tool[future]
                    try:
                        tool, success = future.result()
                        results[tool] = success
                        pbar.update(1)
                    except Exception as e:
                        self.logger.error(f"Error installing {tool}: {e}")
                        results[tool] = False
                        pbar.update(1)

        # Clean up state file after successful completion
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

        return results

    def load_previous_state(self) -> Optional[Dict]:
        """
        Load previous installation state for resume functionality.
        
        Returns:
            Optional[Dict]: Previous state if available, None otherwise
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            self.logger.error(f"Error loading previous state: {e}")
        return None

    def add_blackarch_repository(self) -> bool:
        """
        Add BlackArch Linux repository to pacman configuration.
        
        Returns:
            bool: True if repository added successfully, False otherwise
        """
        if not self.check_internet_connection():
            print("❌ Internet connection is unstable. Please check your network.")
            return False

        try:
            # Update pacman
            print("📦 Updating pacman databases...")
            subprocess.run(['sudo', 'pacman', '-Sy', '--noconfirm'], 
                         check=True, capture_output=True)

            # Install keyring if needed
            print("🔑 Installing archlinux-keyring...")
            subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'archlinux-keyring'],
                         check=True, capture_output=True)

            print("✅ Repository configuration completed")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Repository configuration failed: {e.stderr}")
            print(f"❌ Repository configuration failed: {e.stderr}")
            return False

    def generate_install_report(self, results: Dict[str, bool]) -> None:
        """
        Generate and save detailed installation report.
        
        Args:
            results (Dict[str, bool]): Installation results for each tool
        """
        successful_tools = [tool for tool, status in results.items() if status]
        failed_tools = [tool for tool, status in results.items() if not status]

        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tools': len(results),
            'successful_tools': successful_tools,
            'failed_tools': failed_tools,
            'success_rate': len(successful_tools) / len(results) * 100 if results else 0,
            'category': self.category
        }

        # Create report directory if it doesn't exist
        os.makedirs('/var/log', exist_ok=True)
        
        # Save detailed report
        with open('/var/log/blackarch_installation_report.json', 'w') as f:
            json.dump(report, f, indent=4)

        # Print summary to console
        print("\n🔧 BlackArch Installation Report 🔧")
        print(f"Total Tools: {report['total_tools']}")
        print(f"✅ Successfully Installed: {len(successful_tools)}")
        print(f"❌ Failed to Install: {len(failed_tools)}")
        print(f"📊 Success Rate: {report['success_rate']:.2f}%")

        if failed_tools:
            print("\nFailed tools list:")
            for tool in failed_tools:
                print(f"  - {tool}")
            print("\nYou can try reinstalling failed tools later using:")
            print(f"sudo pacman -S [tool_name]")

        # Log report details
        self.logger.info(f"Installation completed - Success Rate: {report['success_rate']:.2f}%")
        self.logger.info(f"Total Tools: {report['total_tools']}")
        self.logger.info(f"Successful Tools: {len(successful_tools)}")
        self.logger.info(f"Failed Tools: {len(failed_tools)}")

    def main(self):
        """
        Main installation workflow with comprehensive error handling.
        """
        try:
            # Check all requirements first
            if not self.check_requirements():
                print("❌ Requirements not met. Aborting installation.")
                sys.exit(1)

            # Add BlackArch repository
            if not self.add_blackarch_repository():
                print("❌ Failed to add BlackArch repository")
                sys.exit(1)

            # Get tools to install
            print("\n📋 Preparing tool list...")
            tools = self.get_tools_by_category(self.category)
            if not tools:
                print("❌ No tools found for the specified category")
                sys.exit(1)

            print(f"🔍 Found {len(tools)} tools to install in category '{self.category}'")
            
            # Install tools
            installation_results = self.install_tools(tools)
            
            # Generate report
            self.generate_install_report(installation_results)
            
            print("\n🎉 Installation process completed!")
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}", exc_info=True)
            print(f"\n❌ Fatal error: {e}")
            sys.exit(1)

def parse_arguments():
    """
    Parse command-line arguments with comprehensive help information.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='BlackUtility - Advanced Cybersecurity Tool Management System',
        epilog='Developed by 0xb0rn3 | Secure Your Arsenal'
    )
    
    parser.add_argument(
        '-c', '--category',
        choices=['all', 'information-gathering', 'vulnerability-analysis',
                'web-applications', 'exploitation', 'password-attacks',
                'wireless-attacks', 'reverse-engineering', 'forensics'],
        default='all',
        help='Specify tool category to install (default: all available categories)'
    )
    
    parser.add_argument(
        '-r', '--resume',
        action='store_true',
        help='Resume a previously interrupted installation'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output for debugging'
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for the BlackUtility installer.
    """
    print("\n🔒 BlackUtility Cybersecurity Tool Installer 🔒")
    print("Preparing to enhance your security arsenal...\n")
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run installer
    try:
        installer = BlackUtility(
            category=args.category,
            resume=args.resume
        )
        installer.main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.error(f"Installation failed with error: {e}", exc_info=True)
        sys.exit(1)
if __name__ == '__main__':
    main()

# Developer Metadata
__author__ = "0xb0rn3"
__version__ = "0.0.3"
__repository__ = "github.com/0xb0rn3/blackutility"
