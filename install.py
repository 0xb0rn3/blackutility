#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from typing import List, Dict, Optional
import time
import json
import concurrent.futures

class BlackArchInstaller:
    def __init__(self):
        """
        Initialize BlackArch Linux tool installer with comprehensive logging and configuration
        """
        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='/var/log/blackarch_installer.log',
            filemode='a'
        )
        self.logger = logging.getLogger(__name__)

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

    def check_arch_system(self) -> bool:
        """
        Verify the system is running Arch Linux
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
        """
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
                self.logger.info(f"Successfully executed: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Command failed: {' '.join(cmd)}")
                self.logger.error(f"Error output: {e.stderr}")
                return False
        return True

    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Retrieve tools for a specific category with error handling
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
        Install tools with advanced retry and parallel processing mechanism
        """
        def install_tool(tool):
            for attempt in range(self.max_retries):
                try:
                    subprocess.run(
                        ['sudo', 'pacman', '-S', tool, '--noconfirm'], 
                        check=True, 
                        capture_output=True
                    )
                    return tool, True
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"Installation attempt {attempt+1} failed for {tool}")
                    time.sleep(self.retry_delay)
            return tool, False

        # Use concurrent processing for faster installation
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(install_tool, tools))

        return dict(results)

    def generate_install_report(self, results: Dict[str, bool]) -> None:
        """
        Generate comprehensive installation report
        """
        successful_tools = [tool for tool, status in results.items() if status]
        failed_tools = [tool for tool, status in results.items() if not status]

        report = {
            'total_tools': len(results),
            'successful_tools': successful_tools,
            'failed_tools': failed_tools,
            'success_rate': len(successful_tools) / len(results) * 100
        }

        with open('/var/log/blackarch_installation_report.json', 'w') as f:
            json.dump(report, f, indent=4)

        # Log report details
        self.logger.info(f"Total Tools: {report['total_tools']}")
        self.logger.info(f"Successful Tools: {len(successful_tools)}")
        self.logger.info(f"Failed Tools: {len(failed_tools)}")
        self.logger.info(f"Success Rate: {report['success_rate']:.2f}%")

    def main(self, category: str = 'all'):
        """
        Main installation workflow
        """
        if not self.check_arch_system():
            self.logger.error("Not an Arch Linux system. Aborting.")
            sys.exit(1)

        if not self.add_blackarch_repository():
            self.logger.error("Failed to add BlackArch repository")
            sys.exit(1)

        tools = self.get_tools_by_category(category)
        installation_results = self.install_tools(tools)
        self.generate_install_report(installation_results)

if __name__ == '__main__':
    # Allow category specification via command line
    category = sys.argv[1] if len(sys.argv) > 1 else 'all'
    installer = BlackArchInstaller()
    installer.main(category)
