#!/usr/bin/env python3
import os
import sys
import subprocess
import hashlib
import tempfile
import logging
import shutil
from typing import Tuple, Optional
from pathlib import Path
import requests
from datetime import datetime
from urllib.parse import urlparse
from logging.handlers import RotatingFileHandler

class StrapInstallationError(Exception):
    """Custom exception for strap installation failures."""
    pass

class SecurityVerificationError(Exception):
    """Custom exception for security verification failures."""
    pass

class BlackArchInstaller:
    """Handles secure installation of BlackArch Linux tools."""
    
    def __init__(self, verbose: bool = False):
        # ASCII Art Banner
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
        
        # Configure logging
        self.logger = self._setup_logging(verbose)
        
        # Define trusted sources and verification data
        self.TRUSTED_MIRRORS = [
            'https://blackarch.org',
            'https://mirrors.tuna.tsinghua.edu.cn/blackarch',
            'https://mirror.cyberbits.eu/blackarch',
        ]
        
        # Known good SHA256 hashes of strap.sh (update these regularly)
        self.KNOWN_GOOD_HASHES = [
            "a1bce8278d5f0132c45d7f0a82e4293d8b361e640dfb197ed06c846d85787857",
            "f7b3f96c597d987111d3910ed86c224e03ee07f2c814a42046b56c82f856cc95"
        ]
        
        # GPG key for BlackArch verification
        self.BLACKARCH_GPG_KEY = '4345771566D76038C7FEB43863EC0ADBEA87E4E3'
        
        # Temporary directory for downloads
        self.temp_dir = Path(tempfile.mkdtemp(prefix='blackarch_'))
        
        # Path for the strap script
        self.strap_path = self.temp_dir / 'strap.sh'

    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """Configure detailed logging for the installation process."""
        logger = logging.getLogger('BlackArchInstaller')
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Set up log directory
        log_dir = Path('/var/log/blackutility')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        log_file = log_dir / f"blackutility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(message)s'  # Simpler format for console
        )
        
        # Configure handlers
        file_handler.setFormatter(file_formatter)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def print_banner(self):
        """Display the ASCII art banner."""
        print(self.banner)

    def display_status(self, message: str, status: bool = True):
        """Display a status message with appropriate emoji."""
        emoji = "✅" if status else "❌"
        print(f"{emoji} {message}")
    def download_strap(self) -> bool:
        """
        Download strap.sh with multiple fallback mirrors and security checks.
        
        Returns:
            bool: True if download successful and verified
        """
        for mirror in self.TRUSTED_MIRRORS:
            try:
                url = f"{mirror}/strap.sh"
                self.logger.info(f"Attempting download from: {url}")
                
                # Verify URL safety
                if not self._is_safe_url(url):
                    continue
                
                # Download with security headers
                response = requests.get(
                    url,
                    headers={
                        'User-Agent': 'BlackArch-Installer/1.0',
                        'Accept': 'text/plain,application/octet-stream'
                    },
                    timeout=30,
                    verify=True  # Enforce SSL verification
                )
                
                if response.status_code != 200:
                    raise StrapInstallationError(
                        f"Download failed with status: {response.status_code}"
                    )
                
                # Save to temporary location
                self.strap_path.write_bytes(response.content)
                
                # Verify downloaded content
                if self._verify_strap():
                    self.logger.info("Strap script downloaded and verified successfully")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Download failed from {mirror}: {str(e)}")
                continue
                
        raise StrapInstallationError("Failed to download strap.sh from all mirrors")

    def _is_safe_url(self, url: str) -> bool:
        """
        Verify URL safety and structure.
        
        Args:
            url: URL to verify
            
        Returns:
            bool: True if URL is considered safe
        """
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme in ('http', 'https'),
                parsed.netloc in [urlparse(mirror).netloc for mirror in self.TRUSTED_MIRRORS],
                parsed.path.endswith('/strap.sh'),
                not parsed.params,
                not parsed.query,
                not parsed.fragment
            ])
        except Exception:
            return False

    def _verify_strap(self) -> bool:
        """
        Perform multiple security checks on downloaded strap.sh.
        
        Returns:
            bool: True if all security checks pass
        """
        try:
            # Check file size (shouldn't be too small or too large)
            size = self.strap_path.stat().st_size
            if not 1024 <= size <= 1024*1024:  # Between 1KB and 1MB
                raise SecurityVerificationError("Suspicious file size")
            
            # Verify content structure
            content = self.strap_path.read_text()
            if not self._verify_content_structure(content):
                raise SecurityVerificationError("Invalid script structure")
            
            # Check SHA256 hash
            if not self._verify_hash():
                raise SecurityVerificationError("Hash verification failed")
            
            # Verify GPG signature if available
            if not self._verify_gpg():
                self.logger.warning("GPG verification failed, falling back to hash verification")
            
            # Set correct permissions
            self.strap_path.chmod(0o755)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Verification failed: {str(e)}")
            return False

    def _verify_content_structure(self, content: str) -> bool:
        """
        Verify the basic structure and content of the strap script.
        
        Args:
            content: Script content to verify
            
        Returns:
            bool: True if content structure is valid
        """
        required_elements = [
            '#!/bin/sh',
            'blackarch',
            'pacman',
            'check_priv',
            'make_tmp_dir'
        ]
        
        suspicious_patterns = [
            'rm -rf /',
            ':(){ :|:& };:',
            'mkfs',
            'dd if=',
            'mv /* ',
            '>/dev/sda'
        ]
        
        # Check for required elements
        if not all(element in content for element in required_elements):
            return False
            
        # Check for suspicious patterns
        if any(pattern in content for pattern in suspicious_patterns):
            return False
            
        return True

    def _verify_hash(self) -> bool:
        """
        Verify the SHA256 hash of strap.sh.
        
        Returns:
            bool: True if hash matches known good hashes
        """
        sha256_hash = hashlib.sha256()
        
        with open(self.strap_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest() in self.KNOWN_GOOD_HASHES

    def _verify_gpg(self) -> bool:
        """
        Verify GPG signature of strap.sh if available.
        
        Returns:
            bool: True if GPG verification succeeds
        """
        try:
            # Download signature
            sig_url = f"{self.TRUSTED_MIRRORS[0]}/strap.sh.sig"
            sig_path = self.temp_dir / 'strap.sh.sig'
            
            response = requests.get(sig_url, timeout=30)
            if response.status_code != 200:
                return False
                
            sig_path.write_bytes(response.content)
            
            # Import BlackArch GPG key
            subprocess.run(
                ['gpg', '--keyserver', 'keyserver.ubuntu.com',
                 '--recv-keys', self.BLACKARCH_GPG_KEY],
                check=True,
                capture_output=True
            )
            
            # Verify signature
            result = subprocess.run(
                ['gpg', '--verify', str(sig_path), str(self.strap_path)],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.warning(f"GPG verification error: {str(e)}")
            return False

    def install_strap(self) -> bool:
        """
        Execute strap.sh installation safely.
        
        Returns:
            bool: True if installation succeeds
        """
        try:
            # Check if running as root
            if os.geteuid() != 0:
                self.display_status("Must run as root", False)
                raise StrapInstallationError("Must run as root")
            
            self.display_status("Starting BlackArch strap installation...")
            
            # Execute strap script
            result = subprocess.run(
                [str(self.strap_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                self.display_status("Installation failed", False)
                raise StrapInstallationError(
                    f"Installation failed with code {result.returncode}: {result.stderr}"
                )
            
            # Verify installation success
            if not self._verify_installation():
                self.display_status("Post-installation verification failed", False)
                raise StrapInstallationError("Post-installation verification failed")
            
            self.display_status("BlackArch strap installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {str(e)}")
            return False
        finally:
            # Cleanup
            self._cleanup()

    def generate_report(self):
        """Generate an installation report."""
        report = f"""
{'='*60}
📊 BlackArch Installation Report
{'='*60}

🕒 Installation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 System Information:
   - OS: {self._get_os_info()}
   - Kernel: {self._get_kernel_version()}
   
💾 Installation Location:
   - Log file: {self.logger.handlers[0].baseFilename}
   
📝 Note: For detailed logs, check the log file above.
{'='*60}
"""
        print(report)

    def _get_os_info(self) -> str:
        """Get OS information."""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().strip('"')
        except Exception:
            return "Unknown"

    def _get_kernel_version(self) -> str:
        """Get kernel version."""
        try:
            return subprocess.check_output(['uname', '-r'], text=True).strip()
        except Exception:
            return "Unknown"


    def _verify_installation(self) -> bool:
        """
        Verify successful BlackArch installation.
        
        Returns:
            bool: True if installation appears successful
        """
        checks = [
            # Check BlackArch repository
            "grep -q '\\[blackarch\\]' /etc/pacman.conf",
            # Check pacman database
            "pacman -Sl blackarch >/dev/null",
            # Check keyring
            "pacman-key --list-keys | grep -q 'BlackArch'"
        ]
        
        for check in checks:
            try:
                subprocess.run(
                    check,
                    shell=True,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                return False
                
        return True

def main():
    """Main entry point for the BlackArch installation process."""
    installer = BlackArchInstaller(verbose=False)
    
    try:
        installer.print_banner()
        
        installer.display_status("Starting BlackArch installation process...")
        
        if installer.download_strap():
            if installer.install_strap():
                installer.generate_report()
                installer.display_status("BlackArch installation completed successfully!")
                return 0
        
        installer.display_status("Installation failed", False)
        return 1
        
    except Exception as e:
        installer.display_status(f"Fatal error: {str(e)}", False)
        return 1

if __name__ == "__main__":
    sys.exit(main())   
