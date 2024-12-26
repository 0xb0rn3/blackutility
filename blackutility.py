#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
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
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Third-party imports
from tqdm import tqdm
import requests

class BlackUtility:
    """
    Advanced cybersecurity tool management system for Arch Linux.
    Handles installation, verification, and management of BlackArch tools.
    """
    
    def __init__(self, category: str = 'all', resume: bool = False, verbose: bool = False):
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
        
        # Enhanced logging configuration
        log_dir = '/var/log/blackutility'
        os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler
        log_file = f"{log_dir}/blackutility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Configuration parameters
        self.state_file = '/var/tmp/blackutility_state.pkl'
        self.category = category
        self.resume = resume
        self.completed_tools = []
        self.remaining_tools = []
        self.verbose = verbose

        # System requirements
        self.min_storage_required = 20 * 1024 * 1024 * 1024  # 20 GB
        self.min_ram_required = 2 * 1024 * 1024 * 1024      # 2 GB
        self.min_cpu_cores = 2
        
        # Installation parameters
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.timeout = 300    # 5 minutes timeout for operations
        self.pacman_lock_file = '/var/lib/pacman/db.lck'
        
        # Tool categories with dependencies
        self.tool_categories = {
            'all': None,  # Dynamically populated
            'information-gathering': [
                'nmap', 'maltego', 'dmitry', 'fierce', 'recon-ng', 
                'spiderfoot', 'theHarvester'
            ],
            'vulnerability-analysis': [
                'nmap', 'openvas', 'nikto', 'sqlmap', 'metasploit',
                'nessus', 'burpsuite'
            ],
            'web-applications': [
                'burpsuite', 'sqlmap', 'zaproxy', 'wpscan', 'dirb',
                'dirbuster', 'commix'
            ],
            'exploitation': [
                'metasploit', 'exploitdb', 'social-engineer-toolkit',
                'beef', 'armitage'
            ],
            'password-attacks': [
                'john', 'hashcat', 'hydra', 'medusa', 'crunch',
                'wordlists', 'rainbowcrack'
            ],
            'wireless-attacks': [
                'aircrack-ng', 'wireshark', 'reaver', 'kismet',
                'wifite', 'pixiewps'
            ],
            'reverse-engineering': [
                'radare2', 'ghidra', 'ida-free', 'gdb', 'hopper',
                'binary-ninja'
            ],
            'forensics': [
                'volatility', 'autopsy', 'binwalk', 'foremost',
                'sleuthkit', 'bulk-extractor'
            ]
        }

        # Set up signal handlers
        self._setup_signal_handlers()
        
        self.logger.info(f"BlackUtility initialized with category: {category}, resume: {resume}")

    def _setup_signal_handlers(self) -> None:
        """Configure signal handlers for graceful interruption."""
        signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]
        for sig in signals:
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle interruption signals and save state."""
        signal_names = {
            signal.SIGINT: 'SIGINT',
            signal.SIGTERM: 'SIGTERM',
            signal.SIGHUP: 'SIGHUP'
        }
        
        self.logger.warning(f"Received {signal_names.get(signum, 'UNKNOWN')} signal")
        self._save_state()
        print("\n\n⚠️ Installation interrupted. Use --resume to continue later.")
        sys.exit(1)

    def _save_state(self) -> None:
        """Save current installation state."""
        try:
            state_dir = os.path.dirname(self.state_file)
            os.makedirs(state_dir, exist_ok=True)
            
            state = {
                'timestamp': datetime.now().isoformat(),
                'category': self.category,
                'completed_tools': self.completed_tools,
                'remaining_tools': self.remaining_tools
            }
            
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
            
            self.logger.info("Installation state saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save installation state: {e}")
            print("\n⚠️ Warning: Could not save installation state")

    def check_requirements(self) -> Tuple[bool, List[str]]:
        """
        Comprehensive system requirements verification.
        
        Returns:
            Tuple[bool, List[str]]: (requirements_met, error_messages)
        """
        errors = []
        
        # Check for root/sudo access
        if os.geteuid() != 0:
            errors.append("Root access required")
            return False, errors

        # Verify Arch Linux
        if not self._is_arch_linux():
            errors.append("Not running on Arch Linux")
            return False, errors

        # Check internet connectivity
        if not self._check_internet():
            errors.append("No stable internet connection")
        
        # Verify system resources
        storage = self._check_storage()
        if not storage[0]:
            errors.append(storage[1])
            
        ram = self._check_ram()
        if not ram[0]:
            errors.append(ram[1])
            
        cpu = self._check_cpu()
        if not cpu[0]:
            errors.append(cpu[1])

        # Check package manager
        if not self._check_pacman():
            errors.append("Package manager is locked or unavailable")

        return len(errors) == 0, errors

    def _is_arch_linux(self) -> bool:
        """Verify system is running Arch Linux."""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                return 'arch linux' in content
        except Exception as e:
            self.logger.error(f"Failed to verify Arch Linux: {e}")
            return False

    def _check_internet(self) -> bool:
        """Verify internet connectivity using multiple methods."""
        test_hosts = [
            ('8.8.8.8', 53),    # Google DNS
            ('1.1.1.1', 53),    # Cloudflare DNS
            ('9.9.9.9', 53),    # Quad9 DNS
            ('208.67.222.222', 53)  # OpenDNS
        ]
        
        for host, port in test_hosts:
            try:
                socket.setdefaulttimeout(3)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                return True
            except (socket.error, socket.timeout):
                continue
                
        return False

    def _check_storage(self) -> Tuple[bool, str]:
        """Verify sufficient storage space."""
        try:
            total, used, free = shutil.disk_usage('/')
            if free < self.min_storage_required:
                return False, f"Insufficient storage. Need {self.min_storage_required/(1024**3):.1f}GB, have {free/(1024**3):.1f}GB"
            return True, ""
        except Exception as e:
            return False, f"Storage check failed: {e}"

    def _check_ram(self) -> Tuple[bool, str]:
        """Verify sufficient RAM."""
        try:
            total_ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
            if total_ram < self.min_ram_required:
                return False, f"Insufficient RAM. Need {self.min_ram_required/(1024**3):.1f}GB, have {total_ram/(1024**3):.1f}GB"
            return True, ""
        except Exception as e:
            return False, f"RAM check failed: {e}"

    def _check_cpu(self) -> Tuple[bool, str]:
        """Verify CPU capabilities."""
        try:
            cpu_count = os.cpu_count() or 0
            if cpu_count < self.min_cpu_cores:
                return False, f"Insufficient CPU cores. Need {self.min_cpu_cores}, have {cpu_count}"
            return True, ""
        except Exception as e:
            return False, f"CPU check failed: {e}"

    def _check_pacman(self) -> bool:
        """Verify package manager availability."""
        return not os.path.exists(self.pacman_lock_file)

    def download_and_verify_strap(self) -> bool:
        """Download and verify the BlackArch strap script."""
        strap_url = "https://blackarch.org/strap.sh"
        strap_path = "/tmp/strap.sh"
        
        try:
            # Configure session with retry strategy
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(
                max_retries=3,
                pool_connections=10,
                pool_maxsize=10
            ))
            
            # Download strap script
            response = session.get(strap_url, timeout=30)
            response.raise_for_status()
            
            # Save script
            with open(strap_path, "wb") as f:
                f.write(response.content)
            
            # Set permissions
            os.chmod(strap_path, 0o755)
            
            # Verify checksum
            sha1_calc = hashlib.sha1(response.content).hexdigest()
            sha1_response = session.get(f"{strap_url}.sha1sum", timeout=30)
            sha1_response.raise_for_status()
            sha1_official = sha1_response.text.strip().split()[0]
            
            if sha1_calc != sha1_official:
                raise ValueError("Checksum verification failed")
                
            self.logger.info("Strap script downloaded and verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Strap script download/verification failed: {e}")
            if os.path.exists(strap_path):
                os.remove(strap_path)
            return False

    def install_strap(self) -> bool:
        """Install the BlackArch strap script."""
        try:
            result = subprocess.run(
                ['sudo', '/tmp/strap.sh'],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            self.logger.info("BlackArch strap installed successfully")
            return True
            
        except subprocess.SubprocessError as e:
            self.logger.error(f"Strap installation failed: {str(e)}")
            return False

    def configure_blackarch(self) -> bool:
        """Configure BlackArch repository and update system."""
        try:
            # Update package databases
            subprocess.run(
                ['sudo', 'pacman', '-Sy', '--noconfirm'],
                check=True,
                capture_output=True,
                timeout=self.timeout
            )
            
            # Install/update keyrings
            subprocess.run(
                ['sudo', 'pacman', '-S', '--noconfirm', 'archlinux-keyring', 'blackarch-keyring'],
                check=True,
                capture_output=True,
                timeout=self.timeout
            )
            
            self.logger.info("BlackArch configuration completed successfully")
            return True
            
        except subprocess.SubprocessError as e:
            self.logger.error(f"BlackArch configuration failed: {str(e)}")
            return False

    def get_tools(self) -> List[str]:
        """Get list of tools based on selected category."""
        if self.category not in self.tool_categories:
            self.logger.error(f"Invalid category: {self.category}")
            return []

        if self.category == 'all':
            try:
                result = subprocess.run(
                    ['pacman', '-Slq', 'blackarch'],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout
                )
                return result.stdout.splitlines()
            except subprocess.SubprocessError as e:
                self.logger.error(f"Failed to retrieve tool list: {str(e)}")
                return []

        return self.tool_categories[self.category]

    def install_tools(self, tools: List[str]) -> Dict[str, bool]:
        """Install specified tools with parallel processing and progress tracking."""
        if not tools:
            self.logger.warning("No tools provided for installation")
            return {}

        # Resume from previous state if applicable
        if self.resume:
            previous_state = self._load_state()
            if previous_state:
                tools = previous_state.get('remaining_tools', tools)
                self.completed_tools = previous_state.get('completed_tools', [])
                self.logger.info(f"Resumed installation: {len(tools)} tools remaining")

        self.remaining_tools = tools.copy()
        results = {}
        
        # Calculate optimal number of workers based on system resources
        max_workers = min(os.cpu_count() or 2, 4)  # Limit to 4 parallel installations
        
        print(f"\n🔧 Installing {len(tools)} tools using {max_workers} parallel workers...")
        
        with tqdm(total=len(tools), desc="Installing Tools", unit="tool") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit installation jobs
                future_to_tool = {
                    executor.submit(self._install_tool, tool): tool 
                    for tool in tools
                }
                
                # Process completed installations
                for future in concurrent.futures.as_completed(future_to_tool):
                    tool = future_to_tool[future]
                    try:
                        success = future.result()
                        results[tool] = success
                        
                        if success:
                            self.completed_tools.append(tool)
                            self.remaining_tools.remove(tool)
                            self._save_state()  # Save progress after each successful installation
                        
                        pbar.update(1)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to install {tool}: {str(e)}")
                        results[tool] = False
                        pbar.update(1)

        # Cleanup state file if installation completed
        if not self.remaining_tools and os.path.exists(self.state_file):
            os.remove(self.state_file)
            self.logger.info("Installation completed, removed state file")

        return results

    def _install_tool(self, tool: str) -> bool:
        """
        Install a single tool with retry mechanism and dependency handling.
        
        Args:
            tool (str): Name of the tool to install
            
        Returns:
            bool: True if installation successful, False otherwise
        """
        if tool in self.completed_tools:
            self.logger.debug(f"Tool {tool} already installed, skipping")
            return True

        for attempt in range(self.max_retries):
            try:
                # Verify internet connection before attempt
                if not self._check_internet():
                    self.logger.warning(f"Internet connection unstable, retrying {tool}")
                    time.sleep(self.retry_delay)
                    continue

                # Clear package manager locks if they exist
                self._clear_pacman_locks()

                # Install tool with dependencies
                cmd = ['sudo', 'pacman', '-S', '--noconfirm', '--needed', tool]
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                # Verify installation
                if self._verify_installation(tool):
                    self.logger.info(f"Successfully installed {tool}")
                    return True
                
                raise subprocess.SubprocessError("Installation verification failed")

            except subprocess.SubprocessError as e:
                self.logger.warning(f"Installation attempt {attempt + 1} failed for {tool}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error installing {tool}: {str(e)}")
                return False

        self.logger.error(f"Failed to install {tool} after {self.max_retries} attempts")
        return False

    def _verify_installation(self, tool: str) -> bool:
        """
        Verify tool installation success.
        
        Args:
            tool (str): Name of the tool to verify
            
        Returns:
            bool: True if tool is properly installed
        """
        try:
            result = subprocess.run(
                ['pacman', '-Qi', tool],
                check=True,
                capture_output=True,
                text=True
            )
            return "Install Date" in result.stdout
        except subprocess.SubprocessError:
            return False

    def _clear_pacman_locks(self) -> None:
        """Safely remove pacman lock files if they exist."""
        try:
            if os.path.exists(self.pacman_lock_file):
                os.remove(self.pacman_lock_file)
                self.logger.info("Cleared pacman lock file")
        except Exception as e:
            self.logger.warning(f"Failed to clear pacman lock: {str(e)}")

    def _load_state(self) -> Optional[Dict]:
        """
        Load previous installation state.
        
        Returns:
            Optional[Dict]: Previous state if available and valid
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)
                
                # Validate state data
                required_keys = {'timestamp', 'category', 'completed_tools', 'remaining_tools'}
                if not all(key in state for key in required_keys):
                    raise ValueError("Invalid state file format")
                    
                # Check if state is too old (>24 hours)
                timestamp = datetime.fromisoformat(state['timestamp'])
                if (datetime.now() - timestamp).total_seconds() > 86400:
                    self.logger.warning("State file too old, starting fresh installation")
                    return None
                    
                return state
        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
        return None

    def generate_report(self, results: Dict[str, bool]) -> None:
        """
        Generate comprehensive installation report.
        
        Args:
            results (Dict[str, bool]): Installation results for each tool
        """
        successful = [tool for tool, status in results.items() if status]
        failed = [tool for tool, status in results.items() if not status]
        
        # Calculate statistics
        total = len(results)
        success_count = len(successful)
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # Gather system information
        system_info = {
            'os': self._get_os_info(),
            'kernel': self._get_kernel_version(),
            'cpu': self._get_cpu_info(),
            'ram': self._get_ram_info(),
            'storage': self._get_storage_info()
        }
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'category': self.category,
            'statistics': {
                'total_tools': total,
                'successful': success_count,
                'failed': len(failed),
                'success_rate': round(success_rate, 2)
            },
            'successful_tools': successful,
            'failed_tools': failed,
            'system_info': system_info,
            'installation_time': time.time() - self.start_time
        }
        
        # Save detailed report
        report_file = f'/var/log/blackutility/report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=4)
            
        self._print_report_summary(report)
        
        self.logger.info(f"Installation report saved to {report_file}")

    def _print_report_summary(self, report: Dict) -> None:
        """Print formatted installation report summary."""
        print("\n" + "="*60)
        print("📊 BlackArch Installation Report")
        print("="*60)
        
        stats = report['statistics']
        print(f"\nCategory: {report['category']}")
        print(f"Installation Time: {report['installation_time']/60:.1f} minutes")
        print(f"\nTotal Tools: {stats['total_tools']}")
        print(f"✅ Successfully Installed: {stats['successful']}")
        print(f"❌ Failed to Install: {stats['failed']}")
        print(f"📈 Success Rate: {stats['success_rate']}%")
        
        if report['failed_tools']:
            print("\n❌ Failed Tools:")
            for tool in report['failed_tools']:
                print(f"  - {tool}")
            print("\n💡 Try reinstalling failed tools manually:")
            print("   sudo pacman -S [tool_name]")
            
        print(f"\n📝 Detailed report saved to: {report_file}")
        print("="*60 + "\n")

    def main(self) -> int:
        """
        Main installation workflow.
        
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        self.start_time = time.time()
        
        try:
            # Check requirements
            requirements_met, errors = self.check_requirements()
            if not requirements_met:
                for error in errors:
                    print(f"❌ {error}")
                return 1

            # Download and verify strap script
            if not self.download_and_verify_strap():
                print("❌ Failed to verify strap script")
                return 1

            # Install strap script
            if not self.install_strap():
                print("❌ Failed to install strap script")
                return 1

            # Configure BlackArch
            if not self.configure_blackarch():
                print("❌ Failed to configure BlackArch")
                return 1

            # Get tools list
            tools = self.get_tools()
            if not tools:
                print("❌ No tools found for the specified category")
                return 1

            # Install tools
            results = self.install_tools(tools)
            
            # Generate report
            self.generate_report(results)
            
            # Return success if all tools installed
            return 0 if all(results.values()) else 1
            
        except Exception as e:
            self.logger.error(f"Installation failed: {str(e)}", exc_info=True)
            print(f"\n❌ Fatal error: {str(e)}")
            return 1

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='BlackUtility - Advanced Cybersecurity Tool Management System',
        epilog='Developed by 0xb0rn3 | Stay Ethical. Stay Secure.'
    )
    
    parser.add_argument(
        '-c', '--category',
        choices=['all'] + list(BlackUtility().tool_categories.keys())[1:],
        default='all',
        help='Tool category to install (default: all)'
    )
    
    parser.add_argument(
        '-r', '--resume',
        action='store_true',
        help='Resume interrupted installation'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_arguments()
        
        installer = BlackUtility(
            category=args.category,
            resume=args.resume,
            verbose=args.verbose
        )
        
        sys.exit(installer.main())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        logging.error(f"Installation failed: {str(e)}", exc_info=True)
        sys.exit(1)
