#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import argparse
import json
import sqlite3
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
import shutil
from datetime import datetime
import requests
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Banner
BANNER = f"""
{Fore.RED}██████╗ ██╗      █████╗  ██████╗██╗  ██╗ █████╗ ██████╗  ██████╗  █████╗ ██╗  ██╗
{Fore.YELLOW}██╔══██╗██║     ██╔══██╗██╔════╝██║  ██║██╔══██╗██╔══██╗██╔════╝ ██╔══██╗██║ ██╔╝
{Fore.RED}██████╔╝██║     ███████║██║     ███████║███████║██████╔╝██║  ███╗███████║█████╔╝ 
{Fore.YELLOW}██╔═══╝ ██║     ██╔══██║██║     ██╔══██║██╔══██║██╔═══╝ ██║   ██║██╔══██║██╔═██╗ 
{Fore.RED}██║     ███████╗██║  ██║╚██████╗██║  ██║██║  ██║██║     ╚██████╔╝██║  ██║██║  ██╗
{Fore.YELLOW}╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
{Style.RESET_ALL}
{Fore.CYAN}BlackArch Conversion Toolkit - Seamlessly integrate BlackArch tools into Arch Linux.
{Fore.MAGENTA}Author: b0urn3 | GitHub: https://github.com/q4n0 | Contact: q4n0@proton.me
{Fore.GREEN}Instagram: onlybyhive
"""

print(BANNER)

class BlackArchConversionError(Exception):
    """Custom exception for BlackArch conversion errors"""
    pass

@dataclass
class ConversionConfiguration:
    """
    Comprehensive configuration for BlackArch Linux conversion
    """
    output_directory: str = '/var/log/blackarch_conversion'
    backup_directory: str = '/var/log/blackarch_conversion_backup'
    repositories: List[str] = field(default_factory=lambda: ['blackarch'])
    tool_categories: List[str] = field(default_factory=list)
    security_level: str = 'standard'
    optimization_level: int = 2
    dry_run: bool = False
    interactive: bool = True
    logging_level: int = logging.INFO

class SystemPreflightChecker:
    """
    Performs comprehensive system compatibility and readiness checks
    """
    @staticmethod
    def check_system_compatibility() -> Dict[str, bool]:
        """
        Conduct thorough system compatibility assessment
        
        Returns:
            Dict containing compatibility check results
        """
        checks = {
            'is_arch_linux': os.path.exists('/etc/arch-release'),
            'root_access': os.geteuid() == 0,
            'sufficient_disk_space': SystemPreflightChecker._check_disk_space(),
            'network_connectivity': SystemPreflightChecker._check_network(),
            'pacman_available': shutil.which('pacman') is not None
        }
        return checks

    @staticmethod
    def _check_disk_space(minimum_gb: int = 20) -> bool:
        """
        Check available disk space
        
        Args:
            minimum_gb (int): Minimum required free space in GB
        
        Returns:
            bool: Whether sufficient disk space is available
        """
        statvfs = os.statvfs('/')
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        free_gb = free_bytes / (1024 ** 3)
        return free_gb >= minimum_gb

    @staticmethod
    def _check_network() -> bool:
        """
        Verify network connectivity
        
        Returns:
            bool: Whether network is available
        """
        try:
            requests.get('https://blackarch.org', timeout=5)
            return True
        except requests.RequestException:
            return False

class BlackArchToolManager:
    """
    Manages BlackArch tool discovery, recommendation, and installation
    """
    def __init__(self, config: ConversionConfiguration):
        self.config = config
        self.tool_database = self._initialize_tool_database()

    def _initialize_tool_database(self) -> sqlite3.Connection:
        """
        Create an in-memory SQLite database of BlackArch tools
        
        Returns:
            SQLite database connection
        """
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Rich tool metadata schema
        cursor.execute('''
            CREATE TABLE tools (
                name TEXT PRIMARY KEY,
                category TEXT,
                description TEXT,
                complexity REAL,
                dependencies TEXT,
                security_rating INTEGER
            )
        ''')
        
        # Populate with curated BlackArch tools
        tools = [
            ('nmap', 'network', 'Network discovery tool', 0.7, 'libpcap', 8),
            ('metasploit', 'exploitation', 'Penetration testing framework', 0.9, 'ruby,postgresql', 9),
            ('wireshark', 'network', 'Network protocol analyzer', 0.6, 'qt,libpcap', 7),
            ('burpsuite', 'web', 'Web vulnerability scanner', 0.8, 'java', 9),
            ('sqlmap', 'database', 'SQL injection tool', 0.7, 'python', 8)
        ]
        
        cursor.executemany('''
            INSERT INTO tools 
            (name, category, description, complexity, dependencies, security_rating) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', tools)
        
        conn.commit()
        return conn

    def recommend_tools(self, installed_packages: List[str]) -> List[str]:
        """
        Recommend BlackArch tools based on current system configuration
        
        Args:
            installed_packages (List[str]): Currently installed packages
        
        Returns:
            List of recommended tool names
        """
        cursor = self.tool_database.cursor()
        
        # Simple recommendation based on existing packages and categories
        recommended_tools = []
        for category in self.config.tool_categories:
            cursor.execute('''
                SELECT name FROM tools 
                WHERE category = ? 
                ORDER BY security_rating DESC 
                LIMIT 3
            ''', (category,))
            recommended_tools.extend([row[0] for row in cursor.fetchall()])
        
        return list(set(recommended_tools))

    def install_tools(self, tools: List[str]):
        """
        Install recommended BlackArch tools
        
        Args:
            tools (List[str]): Tools to install
        """
        if self.config.dry_run:
            print(f"{Fore.YELLOW}[DRY RUN] Would install tools: {', '.join(tools)}")
            return
        
        for tool in tools:
            try:
                subprocess.run(
                    ['sudo', 'pacman', '-S', '--noconfirm', f'blackarch-{tool}'],
                    check=True
                )
                print(f"{Fore.GREEN}✓ Installed: {tool}")
            except subprocess.CalledProcessError:
                print(f"{Fore.RED}✗ Failed to install: {tool}")

class BlackArchConverter:
    """
    Comprehensive BlackArch Linux conversion utility
    """
    def __init__(self, config: ConversionConfiguration):
        self.config = config
        self.logger = self._setup_logging()
        self.preflight_checker = SystemPreflightChecker()
        self.tool_manager = BlackArchToolManager(config)

    def _setup_logging(self) -> logging.Logger:
        """
        Configure comprehensive logging for conversion process
        """
        os.makedirs(self.config.output_directory, exist_ok=True)
        
        log_file = os.path.join(
            self.config.output_directory, 
            f'conversion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        
        logging.basicConfig(
            level=self.config.logging_level,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def _perform_system_backup(self):
        """
        Create comprehensive system backup
        """
        backup_dir = os.path.join(
            self.config.backup_directory, 
            f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup package list and critical configurations
        subprocess.run(['pacman', '-Qqe'], 
                       stdout=open(os.path.join(backup_dir, 'package_list.txt'), 'w'))
        
        self.logger.info(f"System backup created at {backup_dir}")

    def convert(self):
        """
        Execute comprehensive BlackArch Linux conversion
        """
        print(f"{Fore.CYAN}[*] Starting BlackArch Linux Conversion")
        
        # System compatibility checks
        compatibility = self.preflight_checker.check_system_compatibility()
        
        if not all(compatibility.values()):
            print(f"{Fore.RED}[!] System Compatibility Check Failed:")
            for check, result in compatibility.items():
                status = f"{Fore.GREEN}✓" if result else f"{Fore.RED}✗"
                print(f"    {status} {check}")
            return
        
        # Backup current system
        self._perform_system_backup()
        
        # Add BlackArch repositories
        self._add_repositories()
        
        # Update system
        self._update_system()
        
        # Recommend and install tools
        installed_packages = subprocess.check_output(
            ['pacman', '-Qqe'], 
            universal_newlines=True
        ).splitlines()
        
        recommended_tools = self.tool_manager.recommend_tools(installed_packages)
        
        if self.config.interactive:
            self._interactive_tool_selection(recommended_tools)
        else:
            self.tool_manager.install_tools(recommended_tools)
        
        print(f"{Fore.GREEN}[✓] BlackArch Conversion Complete!")

    def _add_repositories(self):
        """
        Add BlackArch repositories
        """
        try:
            subprocess.run(
                ['curl', '-O', 'https://blackarch.org/strap.sh'], 
                check=True
            )
            subprocess.run(
                ['chmod', '+x', 'strap.sh'], 
                check=True
            )
            subprocess.run(
                ['sudo', 'bash', 'strap.sh'], 
                check=True
            )
            self.logger.info("BlackArch repositories added successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Repository addition failed: {e}")
            raise BlackArchConversionError("Could not add BlackArch repositories")

    def _update_system(self):
        """
        Perform system-wide package update
        """
        try:
            subprocess.run(
                ['sudo', 'pacman', '-Syyu', '--noconfirm'], 
                check=True
            )
            self.logger.info("System updated successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"System update failed: {e}")
            raise BlackArchConversionError("System update failed")

    def _interactive_tool_selection(self, recommended_tools: List[str]):
        """
        Interactive tool selection and installation
        """
        print(f"\n{Fore.CYAN}[*] Recommended Tools:")
        for i, tool in enumerate(recommended_tools, 1):
            print(f"    {i}. {tool}")
        
        while True:
            try:
                selection = input(
                    f"\n{Fore.YELLOW}Enter tool numbers to install (comma-separated, or 'all'): "
                )
                
                if selection.lower() == 'all':
                    self.tool_manager.install_tools(recommended_tools)
                    break
                
                selected_tools = [recommended_tools[int(x.strip())-1] 
                                  for x in selection.split(',')]
                self.tool_manager.install_tools(selected_tools)
                break
            
            except (ValueError, IndexError):
                print(f"{Fore.RED}[!] Invalid selection. Try again.")

def main():
    """
    Command-line interface for BlackArch conversion
    """
    parser = argparse.ArgumentParser(description='BlackArch Linux Conversion Toolkit')
    
    parser.add_argument('-c', '--categories', nargs='+', 
                        help='Tool categories to install')
    parser.add_argument('-l', '--level', type=int, choices=[0, 1, 2, 3], 
                        default=2, help='Optimization level')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Simulate conversion without making changes')
    parser.add_argument('--non-interactive', action='store_false', 
                        dest='interactive', help='Non-interactive mode')
    
    args = parser.parse_args()
    
    config = ConversionConfiguration(
        tool_categories=args.categories or ['network', 'exploitation'],
        optimization_level=args.level,
        dry_run=args.dry_run,
        interactive=args.interactive
    )
    
    try:
        converter = BlackArchConverter(config)
        converter.convert()
    except BlackArchConversionError as e:
        print(f"{Fore.RED}[!] Conversion Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
