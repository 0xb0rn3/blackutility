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
from tqdm import tqdm

class BlackUtility:
    def __init__(self, category: str = 'all', resume: bool = False):
        """
        BlackUtility - Advanced Cybersecurity Tool Installer
        
        A comprehensive tool for managing cybersecurity toolsets
        with robust installation and management capabilities.
        """
        # Updated ASCII Banner
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

        # State tracking
        self.state_file = '/var/tmp/blackutility_state.pkl'
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
        self.retry_delay = 10  # seconds
        self.min_storage_required = 10 * 1024 * 1024 * 1024  # 10 GB

        # Signal handling
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def check_requirements(self) -> bool:
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
            self.logger.error("Root access check failed")
            
        # Verify Arch Linux system
        if self.check_arch_system():
            requirements_status['arch_system'] = True
            print("✅ Running on Arch Linux")
        else:
            print("❌ Not running on Arch Linux")
            
        # Check internet connectivity
        if self.check_internet_connection():
            requirements_status['internet_connection'] = True
            print("✅ Internet connection stable")
        else:
            print("❌ Internet connection unstable")
            
        # Verify storage space
        if self.check_storage_availability():
            requirements_status['storage_space'] = True
            print("✅ Sufficient storage space available")
        else:
            print("❌ Insufficient storage space")
            
        # Check RAM requirements (minimum 2GB)
        total_ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        if total_ram >= 2 * 1024 ** 3:
            requirements_status['ram_requirements'] = True
            print("✅ Sufficient RAM available")
        else:
            print("❌ Insufficient RAM (minimum 2GB required)")
            
        # Check if BlackArch strap exists and is valid
        strap_path = '/usr/bin/blackarch-strap'
        if os.path.exists(strap_path):
            try:
                strap_sha1 = subprocess.run(
                    ['sha1sum', strap_path],
                    capture_output=True,
                    text=True,
                    check=True
                ).stdout.split()[0]
                
                requirements_status['strap_exists'] = True
                print("✅ BlackArch strap is present and valid")
            except subprocess.CalledProcessError:
                print("❌ BlackArch strap validation failed")
        else:
            print("❌ BlackArch strap not found")
            
        # Check pacman configuration
        try:
            subprocess.run(['pacman', '-Sy'], check=True, capture_output=True)
            requirements_status['pacman_ready'] = True
            print("✅ Pacman is properly configured")
        except subprocess.CalledProcessError:
            print("❌ Pacman is not properly configured")
            
        # Generate detailed report
        print("\n📋 Requirements Summary:")
        all_requirements_met = all(requirements_status.values())
        for requirement, status in requirements_status.items():
            status_symbol = "✅" if status else "❌"
            print(f"{status_symbol} {requirement.replace('_', ' ').title()}")
            
        if all_requirements_met:
            print("\n✨ All requirements satisfied! Proceeding with installation...")
        else:
            print("\n❌ Some requirements not met. Please address the issues above.")
            self.logger.error("Requirements check failed")
            
        return all_requirements_met

    def check_internet_connection(self) -> bool:
        """Check internet connectivity with multiple attempts and timeout"""
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
        """Check available storage space"""
        total, used, free = shutil.disk_usage('/')
        self.logger.info(f"Total Storage: {total / (1024*1024*1024):.2f} GB")
        self.logger.info(f"Free Storage: {free / (1024*1024*1024):.2f} GB")
        
        is_sufficient = free >= self.min_storage_required
        if not is_sufficient:
            self.logger.error(f"Insufficient storage. Requires at least {self.min_storage_required / (1024*1024*1024):.2f} GB")
        return is_sufficient

    def handle_interrupt(self, signum, frame):
        """Handle interruption signals gracefully"""
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

    def load_previous_state(self) -> Optional[Dict]:
        """Load previous installation state if resuming"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            self.logger.error(f"Error loading previous state: {e}")
        return None

    def check_arch_system(self) -> bool:
        """Verify the system is running Arch Linux"""
        try:
            with open('/etc/os-release', 'r') as f:
                return 'Arch Linux' in f.read()
        except FileNotFoundError:
            self.logger.error("Unable to verify Arch Linux system")
            return False

    def add_blackarch_repository(self) -> bool:
        """Add BlackArch Linux repository with error handling"""
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
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ Successfully executed: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Command failed: {' '.join(cmd)}")
                self.logger.error(f"Error output: {e.stderr}")
                return False
        return True

    def get_tools_by_category(self, category: str) -> List[str]:
        """Retrieve tools for a specific category"""
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
        """Install tools with retry mechanism and progress tracking"""
        if not self.check_storage_availability():
            print("❌ Insufficient storage space. Aborting installation.")
            return {}

        previous_state = self.load_previous_state() if self.resume else None
        
        if previous_state:
            tools = previous_state.get('remaining_tools', tools)
            self.completed_tools = previous_state.get('completed_tools', [])
        else:
            self.completed_tools = []
        
        self.remaining_tools = tools.copy()

        def install_tool(tool):
            if tool in self.completed_tools:
                return tool, True

            for attempt in range(self.max_retries):
                try:
                    if not self.check_internet_connection():
                        print(f"❌ Internet unstable. Pausing installation of {tool}")
                        return tool, False

                    subprocess.run(
                        ['sudo', 'pacman', '-S', tool, '--noconfirm'], 
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
                for tool, success in executor.map(install_tool, self.remaining_tools):
                    results[tool] = success
                    pbar.update(1)
                    
                    if os.path.exists(self.state_file):
                        os.remove(self.state_file)

        return results

    def generate_install_report(self, results: Dict[str, bool]) -> None:
        """Generate detailed installation report"""
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

        print("\n🔧 BlackArch Installation Report 🔧")
        print(f"Total Tools: {report['total_tools']}")
        print(f"✅ Successful Tools: {len(successful_tools)}")
        print(f"❌ Failed Tools: {len(failed_tools)}")
        print(f"📊 Success Rate: {report['success_rate']:.2f}%")

        self.logger.info(f"Total Tools: {report['total_tools']}")
        self.logger.info(f"Successful Tools: {len(successful_tools)}")
        self.logger.info(f"Failed Tools: {len(failed_tools)}")
        self.logger.info(f"Success Rate: {report['success_rate']:.2f}%")

    def main(self):
        """
        Main installation workflow with comprehensive requirement checking
        """
        # Check all requirements first
        if not self.check_requirements():
            print("❌ Requirements not met. Aborting installation.")
            sys.exit(1)
            
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
        if not tools:
            print("❌ No tools found for the specified category")
            sys.exit(1)
            
        # Install tools
        installation_results = self.install_tools(tools)
        
        # Generate report
        self.generate_install_report(installation_results)
        
        print("\n🎉 Installation process completed!")

def parse_arguments():
    """
    Parse command-line arguments with comprehensive help information
    
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

if __name__ == '__main__':
    # Add startup message with ASCII art
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

# Developer Metadata
__author__ = "0xb0rn3"
__version__ = "0.0.2"
__repository__ = "github.com/0xb0rn3/blackutility"
