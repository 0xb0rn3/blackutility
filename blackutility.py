#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import time
import json
import concurrent.futures
import socket
import shutil
import signal
import pickle
import argparse
import hashlib
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
from urllib.parse import urlparse

# Third-party imports
from tqdm import tqdm
import requests

class DownloadError(Exception):
    """Custom exception for download-related errors.
    
    This exception is raised when there are issues during the download process,
    such as network failures, invalid responses, or timeout issues.
    """
    pass

class VerificationError(Exception):
    """Custom exception for verification-related errors.
    
    This exception is raised when there are issues during the verification process,
    such as checksum mismatches or suspicious content detection.
    """
    pass
class BlackUtility:
    def __init__(self, category: str = 'all', resume: bool = False, verbose: bool = False):
        # Banner remains the same
        self.banner = r"""
██████╗ ██╗      █████╗  ██████╗██╗  ██╗██╗   ██╗████████╗██╗██╗     
██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██║   ██║╚══██╔══╝██║██║     
██████╔╝██║     ███████║██║     █████╔╝ ██║   ██║   ██║   ██║██║     
██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██║   ██║   ██║   ██║██║     
██████╔╝███████╗██║  ██║╚██████╗██║  ██╗╚██████╔╝   ██║   ██║███████╗
╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝╚══════╝
                                                                      
    [Advanced Cybersecurity Arsenal for Arch]
    
    Dev: 0xb0rn3 | Socials{IG}: @theehiv3
    Repo: github.com/0xb0rn3/blackutility
           Version: 0.0.2 BETA
    
    Stay Ethical. Stay Secure. Enjoy!
        """
        
        # Enhanced logging configuration with rotation
        log_dir = '/var/log/blackutility'
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = f"{log_dir}/blackutility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Extended configuration parameters
        self.state_file = '/var/tmp/blackutility_state.pkl'
        self.category = category
        self.resume = resume
        self.completed_tools = []
        self.remaining_tools = []
        self.verbose = verbose
        self.start_time = None

        # Enhanced system requirements
        self.min_storage_required = 20 * 1024 * 1024 * 1024  # 20 GB
        self.min_ram_required = 2 * 1024 * 1024 * 1024      # 2 GB
        self.min_cpu_cores = 2
        
        # Enhanced installation parameters
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.timeout = 300    # 5 minutes timeout for operations
        self.pacman_lock_file = '/var/lib/pacman/db.lck'
        
        # Mirror configuration
        self.mirrors = [
            'https://blackarch.org',
            'https://mirrors.tuna.tsinghua.edu.cn/blackarch',
            'https://mirror.cyberbits.eu/blackarch',
            'https://ftp.halifax.rwth-aachen.de/blackarch'
        ]
        
        # Download verification settings
        self.chunk_size = 8192
        self.download_timeout = 30
        self.temp_dir = tempfile.gettempdir()
        
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
        """
        Enhanced download and verification of the BlackArch strap script with multiple
        fallback mechanisms and comprehensive error handling.
        """
        for mirror in self.mirrors:
            strap_url = f"{mirror}/strap.sh"
            strap_path = os.path.join(self.temp_dir, "strap.sh")
            
            try:
                # Try different download methods
                if not self._try_download_methods(strap_url, strap_path):
                    continue
                
                # Verify downloaded content
                if not self._verify_strap_content(strap_path):
                    continue
                
                # Try multiple verification methods
                if self._verify_strap_integrity(strap_url, strap_path):
                    return True
                
            except Exception as e:
                self.logger.warning(f"Failed to download from {mirror}: {str(e)}")
                continue
            
        self.logger.error("All download attempts failed")
        return False
    def _try_download_methods(self, url: str, output_path: str) -> bool:
        """Try multiple download methods in sequence."""
        methods = [
            self._download_with_requests,
            self._download_with_urllib,
            self._download_with_wget,
            self._download_with_curl
        ]
        
        for method in methods:
            try:
                if method(url, output_path):
                    return True
            except Exception as e:
                self.logger.debug(f"Download method {method.__name__} failed: {str(e)}")
                continue
        
        return False

    def _download_with_requests(self, url: str, output_path: str) -> bool:
        """Download using requests library with enhanced error handling."""
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        ))
        
        headers = {
            'User-Agent': 'Mozilla/5.0 BlackUtility/0.0.4',
            'Accept': 'text/plain,application/octet-stream'
        }
        
        response = session.get(url, headers=headers, stream=True, timeout=self.download_timeout)
        
        if response.status_code != 200:
            raise DownloadError(f"HTTP {response.status_code}")
            
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type.lower():
            raise DownloadError("Received HTML response")
            
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)
                    
        return True

    def _download_with_urllib(self, url: str, output_path: str) -> bool:
        """Fallback download method using urllib."""
        import urllib.request
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 BlackUtility/0.0.4'}
        )
        
        with urllib.request.urlopen(request, timeout=self.download_timeout) as response:
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(self.chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    
        return True

    def _download_with_wget(self, url: str, output_path: str) -> bool:
        """Fallback download method using wget."""
        try:
            result = subprocess.run(
                ['wget', '--quiet', '--tries=3', '--timeout=30',
                 '--user-agent=BlackUtility/0.0.4',
                 '-O', output_path, url],
                check=True,
                timeout=self.download_timeout
            )
            return True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            return False

    def _download_with_curl(self, url: str, output_path: str) -> bool:
        """Fallback download method using curl."""
        try:
            result = subprocess.run(
                ['curl', '--silent', '--retry', '3',
                 '--retry-delay', '5',
                 '-A', 'BlackUtility/0.0.4',
                 '-o', output_path, url],
                check=True,
                timeout=self.download_timeout
            )
            return True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            return False

    def _verify_strap_content(self, strap_path: str) -> bool:
        """Verify basic strap script content validity."""
        try:
            with open(strap_path, 'r') as f:
                content = f.read()
                
            # Check for essential strap script markers
            required_markers = [
                '#!/bin/sh',
                'blackarch',
                'pacman'
            ]
            
            if not all(marker in content for marker in required_markers):
                self.logger.warning("Missing required content markers in strap script")
                return False
                
            # Check for suspicious content
            suspicious_patterns = [
                'rm -rf /',
                'mkfs',
                ':(){:|:&};:',
                'sudo rm'
            ]
            
            if any(pattern in content for pattern in suspicious_patterns):
                self.logger.warning("Detected potentially malicious content in strap script")
                return False
                
            # Check file size constraints
            min_size = 1024  # 1 KB
            max_size = 1024 * 1024  # 1 MB
            
            file_size = os.path.getsize(strap_path)
            if not min_size <= file_size <= max_size:
                self.logger.warning(f"Suspicious file size: {file_size} bytes")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Content verification failed: {str(e)}")
            return False

    def _verify_strap_integrity(self, strap_url: str, strap_path: str) -> bool:
        """Verify strap script integrity using multiple methods."""
        verification_methods = [
            self._verify_with_sha1sum,
            self._verify_with_gpg,
            self._verify_with_known_hashes
        ]
        
        for method in verification_methods:
            try:
                if method(strap_url, strap_path):
                    self.logger.info(f"Verification successful using {method.__name__}")
                    return True
            except Exception as e:
                self.logger.debug(f"Verification method {method.__name__} failed: {str(e)}")
                continue
                
        return False

    def _verify_with_sha1sum(self, strap_url: str, strap_path: str) -> bool:
        """Verify using SHA1 checksum."""
        checksum_url = f"{strap_url}.sha1sum"
        checksum_path = f"{strap_path}.sha1sum"
        
        try:
            # Download checksum file
            if not self._try_download_methods(checksum_url, checksum_path):
                return False
                
            # Read expected checksum
            with open(checksum_path, 'r') as f:
                expected_sha1 = f.read().strip().split()[0]
                
            # Calculate actual checksum
            with open(strap_path, 'rb') as f:
                actual_sha1 = hashlib.sha1(f.read()).hexdigest()
                
            return expected_sha1 == actual_sha1
            
        except Exception as e:
            self.logger.debug(f"SHA1 verification failed: {str(e)}")
            return False

    def _verify_with_gpg(self, strap_url: str, strap_path: str) -> bool:
        """Verify using GPG signature if available."""
        sig_url = f"{strap_url}.sig"
        sig_path = f"{strap_path}.sig"
        
        try:
            # Download signature
            if not self._try_download_methods(sig_url, sig_path):
                return False
                
            # Import BlackArch GPG key if needed
            subprocess.run(
                ['gpg', '--keyserver', 'keyserver.ubuntu.com',
                 '--recv-keys', '4345771566D76038C7FEB43863EC0ADBEA87E4E3'],
                check=True,
                capture_output=True
            )
            
            # Verify signature
            result = subprocess.run(
                ['gpg', '--verify', sig_path, strap_path],
                check=True,
                capture_output=True
            )
            
            return True
            
        except Exception as e:
            self.logger.debug(f"GPG verification failed: {str(e)}")
            return False

    def _verify_with_known_hashes(self, strap_url: str, strap_path: str) -> bool:
        """
        Verify against a list of known good hashes.
        This is a last resort verification method.
        """
        known_hashes = [
            "dd00d3c8c53ddb6f8f243ae84871a6f2602ef34d",
            "7eb79b43e6c79acaa776e714305fc9890ccc5d80",
            # Add more known good hashes here
        ]
        
        try:
            with open(strap_path, 'rb') as f:
                file_hash = hashlib.sha1(f.read()).hexdigest()
                
            return file_hash in known_hashes
            
        except Exception as e:
            self.logger.debug(f"Known hash verification failed: {str(e)}")
            return False
    def install_strap(self) -> bool:
        """Install the BlackArch strap script."""
        strap_path = "/tmp/strap.sh"
        
        if not os.path.exists(strap_path):
            self.logger.error("Strap script not found")
            return False
            
        try:
            self.logger.info("Installing strap script...")
            result = subprocess.run(
                [strap_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if "error" in result.stderr.lower() or "error" in result.stdout.lower():
                raise subprocess.SubprocessError(f"Installation error: {result.stderr}")
            
            self.logger.info("BlackArch strap installed successfully")
            return True
            
        except subprocess.SubprocessError as e:
            self.logger.error(f"Strap installation failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during strap installation: {str(e)}")
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
        Enhanced main installation workflow with better error handling
        and user feedback.
        
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        self.start_time = time.time()
        
        print(self.banner)
        
        try:
            # Check requirements
            requirements_met, errors = self.check_requirements()
            if not requirements_met:
                for error in errors:
                    print(f"❌ {error}")
                return 1

            # Download and verify strap script
            print("\n📥 Downloading and verifying strap script...")
            if not self.download_and_verify_strap():
                print("❌ Failed to verify strap script")
                return 1

            # Install strap script
            print("\n🔧 Installing strap script...")
            if not self.install_strap():
                print("❌ Failed to install strap script")
                return 1

            # Configure BlackArch
            print("\n⚙️ Configuring BlackArch...")
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
    
    # Create a temporary instance just to get categories
    utility = BlackUtility()
    categories = list(utility.tool_categories.keys())
    
    parser.add_argument(
        '-c', '--category',
        choices=['all'] + [cat for cat in categories if cat != 'all'],
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
