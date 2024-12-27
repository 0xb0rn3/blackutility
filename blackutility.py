#!/usr/bin/env python3 
import os
import sys
import asyncio
import aiohttp
import hashlib
import tempfile
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.style import Style
from rich.text import Text
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler

class BlackArchUtility:
    """
    An enhanced BlackArch Linux utility manager that combines secure installation
    with advanced features while maintaining strict adherence to official processes.
    """
    
    BANNER = '''
[cyan]
█▄▄ █░░ ▄▀█ █▀▀ █▄▀ █░█ ▀█▀ █ █░░ █ ▀█▀ █▄█
█▄█ █▄▄ █▀█ █▄▄ █░█ █▄█ ░█░ █ █▄▄ █ ░█░ ░█░
[/cyan]
[yellow]Advanced Cybersecurity Arsenal for Arch[/yellow]

Dev: 0xb0rn3 | Socials{IG}: @theehiv3
Repo: github.com/0xb0rn3/blackutility
Version: 1.0.1 STABLE

[green]Stay Ethical. Stay Secure. Enjoy![/green]
'''
    
    def __init__(self):
        """
        Initialize the utility with enhanced security features and visual improvements.
        Sets up logging, layout, and secure network configurations.
        """
        self.console = Console()
        self.config = self._load_config()
        self.session = None
        self.download_chunks: Dict[str, List[bytes]] = {}
        self.setup_logging()
        self.layout = self._setup_layout()
        
    def _setup_layout(self) -> Layout:
        """
        Initialize the rich layout for better visual organization and user feedback.
        Creates a three-section layout for header, main content, and footer.
        """
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        return layout
        
    def _create_status_table(self) -> Table:
        """
        Create a status table for real-time system and network information display.
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        return table

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration with security-focused settings and official URLs.
        """
        return {
            'chunk_size': 1024 * 1024,  # 1MB chunks for optimal network usage
            'max_concurrent_downloads': 3,
            'max_retries': 5,
            'retry_delay': 1,
            'connection_timeout': 30,
            'official_strap_url': "https://blackarch.org/strap.sh",
            'blackarch_keyserver': "hkps://keyserver.ubuntu.com",
            'official_sha1': "bbf0a0b838aed0ec05fff2d375dd17591cbdf8aa",
            'verify_ssl': True,
            'dns_cache_ttl': 300,
            'temp_dir': None  # Will be set during runtime
        }

    def setup_logging(self):
        """
        Configure comprehensive logging system for security audit and debugging.
        """
        log_dir = Path("/var/log/blackutility")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("BlackArchUtility")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with improved formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        self.logger.addHandler(console_handler)
        
        # File handler with detailed logging
        file_handler = RotatingFileHandler(
            log_dir / f"blackutility_{datetime.now():%Y%m%d}.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        )
        self.logger.addHandler(file_handler)

    async def create_session(self):
        """
        Create an optimized aiohttp session with enhanced security features.
        """
        conn = aiohttp.TCPConnector(
            limit=self.config['max_concurrent_downloads'],
            ttl_dns_cache=self.config['dns_cache_ttl'],
            enable_cleanup_closed=True,
            ssl=self.config['verify_ssl']
        )
        
        self.session = aiohttp.ClientSession(
            connector=conn,
            timeout=aiohttp.ClientTimeout(total=self.config['connection_timeout']),
            headers={
                'User-Agent': 'BlackArchUtility/1.0.1',
                'Accept': '*/*'
            }
        )

    async def close_session(self):
        """
        Safely close the HTTP session and cleanup resources.
        """
        if self.session:
            await self.session.close()

    async def download_with_resume(self, url: str, dest_path: Path, 
                                 progress: Progress) -> bool:
        """
        Download file with resume capability and enhanced error handling.
        """
        file_id = hashlib.md5(url.encode()).hexdigest()
        chunk_size = self.config['chunk_size']
        
        if file_id not in self.download_chunks:
            self.download_chunks[file_id] = []
        
        chunks = self.download_chunks[file_id]
        start_byte = len(b''.join(chunks))
        
        headers = {'Range': f'bytes={start_byte}-'}
        
        self.logger.info(f"Starting download from {url}")
        self.logger.debug(f"Request headers: {headers}")
        
        task_id = progress.add_task(
            f"[cyan]Downloading {dest_path.name}[/cyan]",
            total=None,
            start=start_byte
        )
        
        retry_count = 0
        while retry_count < self.config['max_retries']:
            try:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 416:
                        self.logger.info("File already completely downloaded")
                        return True
                        
                    if not response.status in (200, 206):
                        raise aiohttp.ClientError(
                            f"Bad status code: {response.status}"
                        )
                    
                    total = int(response.headers.get('Content-Length', 0))
                    if total == 0:
                        self.logger.warning("Content-Length header missing")
                    else:
                        progress.update(task_id, total=total + start_byte)
                    
                    async for chunk in response.content.iter_chunked(chunk_size):
                        chunks.append(chunk)
                        progress.update(task_id, advance=len(chunk))
                        
                    final_content = b''.join(chunks)
                    
                    # Verify the content is not empty
                    if len(final_content) == 0:
                        self.logger.error("Downloaded content is empty")
                        return False
                        
                    dest_path.write_bytes(final_content)
                    
                    self.logger.info(f"Successfully downloaded {len(final_content)} bytes")
                    return True
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                retry_count += 1
                self.logger.warning(
                    f"Download attempt {retry_count} failed: {str(e)}"
                )
                if retry_count < self.config['max_retries']:
                    await asyncio.sleep(self.config['retry_delay'])
                    
        return False

    def verify_sha1(self, file_path: Path) -> bool:
        """
        Verify the SHA1 hash of the downloaded file against the official hash.
        """
        sha1_hash = hashlib.sha1()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self.config['chunk_size']):
                    sha1_hash.update(chunk)
                    
            calculated_hash = sha1_hash.hexdigest()
            is_valid = calculated_hash == self.config['official_sha1']
            
            self.logger.info(f"SHA1 verification: calculated={calculated_hash}, "
                            f"expected={self.config['official_sha1']}")
                            
            return is_valid
        except IOError as e:
            self.logger.error(f"Failed to read file for SHA1 verification: {str(e)}")
            return False

    async def verify_strap_signature(self, strap_path: Path) -> bool:
        """
        Verify the strap.sh signature using GnuPG with enhanced error checking.
        """
        try:
            # BlackArch maintainer's signing key
            BLACKARCH_SIGNING_KEY = "4345771566D76038C7FEB43863EC0ADBEA87E4E3"
            
            # Create a clean GPG environment
            gpg_home = Path(tempfile.mkdtemp())
            self.config['temp_dir'] = gpg_home  # Store for cleanup
            os.environ['GNUPGHOME'] = str(gpg_home)
            
            # Download the signature file
            sig_url = f"{self.config['official_strap_url']}.sig"
            sig_path = strap_path.with_suffix('.sh.sig')
            
            self.logger.info(f"Downloading signature file from {sig_url}")
            async with self.session.get(sig_url) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to download signature file: Status {response.status}")
                    return False
                
                sig_content = await response.read()
                
                # Verify signature content
                if len(sig_content) < 100:  # Basic size validation
                    self.logger.error(f"Signature file too small: {len(sig_content)} bytes")
                    return False
                
                # Write signature file
                sig_path.write_bytes(sig_content)
                if not sig_path.exists() or sig_path.stat().st_size == 0:
                    self.logger.error("Failed to write signature file")
                    return False
                
                self.logger.info(f"Signature file saved to {sig_path}")
                self.logger.debug(f"Signature content first bytes: {sig_content[:20].hex()}")
            
            # Initialize GPG
            init_cmd = await asyncio.create_subprocess_exec(
                'gpg',
                '--batch',
                '--no-tty',
                '--yes',
                '--list-keys',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await init_cmd.communicate()
            
            # Import the BlackArch signing key
            self.logger.info("Importing BlackArch signing key...")
            import_cmd = await asyncio.create_subprocess_exec(
                'gpg',
                '--batch',
                '--no-tty',
                '--keyserver', self.config['blackarch_keyserver'],
                '--recv-keys', BLACKARCH_SIGNING_KEY,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await import_cmd.communicate()
            if import_cmd.returncode != 0:
                self.logger.error(f"Key import failed: {stderr.decode()}")
                return False
            
            # Verify the key was imported
            verify_key_cmd = await asyncio.create_subprocess_exec(
                'gpg',
                '--batch',
                '--no-tty',
                '--list-keys', BLACKARCH_SIGNING_KEY,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await verify_key_cmd.communicate()
            if verify_key_cmd.returncode != 0:
                self.logger.error("Failed to verify key import")
                return False
            
            # Verify the signature with detailed output
            self.logger.info("Verifying signature...")
            verify_cmd = await asyncio.create_subprocess_exec(
                'gpg',
                '--batch',
                '--no-tty',
                '--verbose',
                '--debug-all',
                '--verify',
                str(sig_path),
                str(strap_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await verify_cmd.communicate()
            verification_output = stderr.decode()
            
            if verify_cmd.returncode == 0:
                self.logger.info("Signature verification successful")
                return True
            else:
                self.logger.error(f"Signature verification failed with output:\n{verification_output}")
                return False
            
        except Exception as e:
            self.logger.error(f"Signature verification failed with exception: {str(e)}", exc_info=True)
            return False
            
        finally:
            # Clean up the temporary GPG home
            if self.config['temp_dir']:
                import shutil
                try:
                    shutil.rmtree(str(self.config['temp_dir']), ignore_errors=True)
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temp directory: {str(e)}")

    async def install(self) -> bool:
        """
        Execute the BlackArch installation process with enhanced security and monitoring.
        """
        try:
            self.console.print(Panel(self.BANNER, border_style="cyan"))
            
            # Check root privileges
            if os.geteuid() != 0:
                self.console.print("[red]Must run as root[/red]")
                return False
                
            # Create session for downloads
            await self.create_session()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console,
                expand=True
            ) as progress:
                
                # Download strap.sh
                strap_path = Path(tempfile.mkdtemp()) / "strap.sh"
                if not await self.download_with_resume(
                    self.config['official_strap_url'],
                    strap_path,
                    progress
                ):
                    self.console.print(Panel(
                        "[red]Failed to download strap.sh[/red]",
                        border_style="red"
                    ))
                    return False
                
                # Verify integrity
                verify_task = progress.add_task(
                    "[cyan]Verifying integrity...[/cyan]",
                    total=2
                )
                
                # SHA1 verification
                if not self.verify_sha1(strap_path):
                    progress.update(verify_task, completed=True)
                    self.console.print(Panel(
                        "[red]SHA1 verification failed[/red]",
                        border_style="red"
                    ))
                    return False
                    
                progress.update(verify_task, advance=1)
                
                # GPG signature verification
                if not await self.verify_strap_signature(strap_path):
                    progress.update(verify_task, completed=True)
                    self.console.print(Panel(
                        "[red]GPG signature verification failed[/red]",
                        border_style="red"
                    ))
                    return False
                    
                progress.update(verify_task, advance=1)
                
                # Execute installation
                install_task = progress.add_task(
                    "[green]Installing BlackArch...[/green]",
                    total=1
                )
                
                # Set executable permissions
                os.chmod(strap_path, 0o755)
                
                # Run installation script with detailed output capture
                process = await asyncio.create_subprocess_exec(
                    str(strap_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Monitor installation progress
                while True:
                    try:
                        stdout_line = await process.stdout.readline()
                        if not stdout_line:
                            break
                        self.logger.info(stdout_line.decode().strip())
                    except Exception as e:
                        self.logger.error(f"Error reading installation output: {str(e)}")
                
                # Wait for completion
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    progress.update(install_task, completed=True)
                    error_msg = stderr.decode().strip()
                    self.logger.error(f"Installation failed with error: {error_msg}")
                    self.console.print(Panel(
                        f"[red]Installation failed: {error_msg}[/red]",
                        border_style="red"
                    ))
                    return False
                    
                progress.update(install_task, completed=True)
                
                # Verify installation success
                verify_install_task = progress.add_task(
                    "[cyan]Verifying installation...[/cyan]",
                    total=1
                )
                
                # Check if pacman config was updated
                pacman_conf = Path("/etc/pacman.conf")
                try:
                    content = pacman_conf.read_text()
                    if "[blackarch]" not in content:
                        self.logger.error("BlackArch repository not found in pacman.conf")
                        progress.update(verify_install_task, completed=True)
                        self.console.print(Panel(
                            "[red]Installation verification failed: BlackArch repository not configured[/red]",
                            border_style="red"
                        ))
                        return False
                except Exception as e:
                    self.logger.error(f"Failed to verify pacman configuration: {str(e)}")
                    progress.update(verify_install_task, completed=True)
                    return False
                
                progress.update(verify_install_task, completed=True)
            
            # Display success message with next steps
            self.console.print(Panel(
                "[green]BlackArch installation completed successfully![/green]\n"
                "[yellow]Next steps:[/yellow]\n"
                "1. Run 'sudo pacman -Syu' to sync the repositories\n"
                "2. Install tools using 'sudo pacman -S <package-name>'\n"
                "3. View available tools at https://blackarch.org/tools.html",
                border_style="green"
            ))
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {str(e)}", exc_info=True)
            self.console.print(Panel(
                f"[red]Error: {str(e)}[/red]",
                border_style="red"
            ))
            return False
            
        finally:
            # Ensure proper cleanup
            await self.close_session()
            if hasattr(self, 'temp_dir') and self.config['temp_dir']:
                import shutil
                try:
                    shutil.rmtree(str(self.config['temp_dir']), ignore_errors=True)
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temporary files: {str(e)}")

async def main():
    """
    Main entry point with comprehensive error handling and user feedback.
    """
    utility = BlackArchUtility()
    try:
        success = await utility.install()
        return 0 if success else 1
    except KeyboardInterrupt:
        utility.console.print(Panel(
            "\n[yellow]Operation cancelled by user[/yellow]",
            border_style="yellow"
        ))
        return 1
    except Exception as e:
        utility.logger.error("Fatal error", exc_info=True)
        utility.console.print(Panel(
            f"[red]Fatal error: {str(e)}[/red]",
            border_style="red"
        ))
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
