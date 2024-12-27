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
    """Enhanced BlackArch Linux utility manager with official repository support."""
    
    BANNER = '''
[cyan]
█▄▄ █░░ ▄▀█ █▀▀ █▄▀ █░█ ▀█▀ █ █░░ █ ▀█▀ █▄█
█▄█ █▄▄ █▀█ █▄▄ █░█ █▄█ ░█░ █ █▄▄ █ ░█░ ░█░
[/cyan]
[yellow]Advanced Cybersecurity Arsenal for Arch[/yellow]

Dev: 0xb0rn3 | Socials{IG}: @theehiv3
Repo: github.com/0xb0rn3/blackutility
Version: 1.0.0 BETA

[green]Stay Ethical. Stay Secure. Enjoy![/green]
'''
    
    def __init__(self):
        self.console = Console()
        self.config = self._load_config()
        self.session = None
        self.download_chunks: Dict[str, List[bytes]] = {}
        self.setup_logging()
        self.layout = self._setup_layout()
        
    def _setup_layout(self) -> Layout:
        """Initialize the rich layout for better visual organization."""
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        return layout
        
    def _create_status_table(self) -> Table:
        """Create a status table for displaying system and network information."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        return table

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with optimized network settings."""
        return {
            'chunk_size': 1024 * 1024,  # 1MB chunks for optimal network usage
            'max_concurrent_downloads': 3,
            'max_retries': 5,
            'retry_delay': 1,
            'connection_timeout': 30,
            'official_strap_url': "https://blackarch.org/strap.sh",  # Official BlackArch strap URL
            'blackarch_keyserver': "hkps://keyserver.ubuntu.com",
            'blackarch_key': "bbf0a0b838aed0ec05fff2d375dd17591cbdf8aa",
            'known_hashes': []  # We'll verify against the official source
        }

    def setup_logging(self):
        """Configure rotating log handler with detailed formatting."""
        log_dir = Path("/var/log/blackutility")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("BlackArchUtility")
        self.logger.setLevel(logging.DEBUG)  # Enhanced debugging
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logging
        file_handler = RotatingFileHandler(
            log_dir / f"blackutility_{datetime.now():%Y%m%d}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        )
        self.logger.addHandler(file_handler)

    async def create_session(self):
        """Create optimized aiohttp session with improved SSL handling."""
        conn = aiohttp.TCPConnector(
            limit=self.config['max_concurrent_downloads'],
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            ssl=True  # Ensure SSL verification
        )
        
        self.session = aiohttp.ClientSession(
            connector=conn,
            timeout=aiohttp.ClientTimeout(total=self.config['connection_timeout']),
            headers={
                'User-Agent': 'BlackArchUtility/1.0.0',
                'Accept': '*/*'
            }
        )

    async def close_session(self):
        """Safely close the aiohttp session."""
        if self.session:
            await self.session.close()

    async def download_with_resume(self, url: str, dest_path: Path, 
                                 progress: Progress) -> bool:
        """Download file with resume capability and enhanced error handling."""
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
                    self.logger.debug(f"Response status: {response.status}")
                    self.logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    if response.status == 416:
                        self.logger.info("File already completely downloaded")
                        return True
                        
                    if not response.status in (200, 206):
                        raise aiohttp.ClientError(
                            f"Bad status code: {response.status}"
                        )
                    
                    total = int(response.headers.get('Content-Length', 0))
                    progress.update(task_id, total=total + start_byte)
                    
                    async for chunk in response.content.iter_chunked(chunk_size):
                        chunks.append(chunk)
                        progress.update(task_id, advance=len(chunk))
                        
                    final_content = b''.join(chunks)
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
            except Exception as e:
                self.logger.error(f"Unexpected error during download: {str(e)}", 
                                exc_info=True)
                return False
                    
        self.logger.error("Download failed after all retries")
        return False

    async def verify_strap_signature(self, strap_path: Path) -> bool:
        """Verify the strap.sh signature using GnuPG."""
        try:
            # Download the signature file
            sig_url = f"{self.config['official_strap_url']}.sig"
            sig_path = strap_path.with_suffix('.sh.sig')
            
            async with self.session.get(sig_url) as response:
                if response.status != 200:
                    self.logger.error("Failed to download signature file")
                    return False
                    
                sig_content = await response.read()
                sig_path.write_bytes(sig_content)
            
            # Import BlackArch key if needed
            import_cmd = await asyncio.create_subprocess_exec(
                'gpg', '--keyserver', self.config['blackarch_keyserver'],
                '--recv-keys', self.config['blackarch_key'],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await import_cmd.communicate()
            
            # Verify signature
            verify_cmd = await asyncio.create_subprocess_exec(
                'gpg', '--verify', str(sig_path), str(strap_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await verify_cmd.communicate()
            return verify_cmd.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Signature verification failed: {str(e)}")
            return False

    async def install(self) -> bool:
        """Install BlackArch with enhanced security and progress tracking."""
        try:
            self.console.print(Panel(self.BANNER, border_style="cyan"))
            
            if os.geteuid() != 0:
                self.console.print("[red]Must run as root[/red]")
                return False
                
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
                
                # Download strap.sh from official source
                strap_path = Path(tempfile.mkdtemp()) / "strap.sh"
                download_task = progress.add_task(
                    "[cyan]Downloading strap.sh[/cyan]",
                    total=None
                )
                
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
                    
                progress.update(download_task, completed=True)
                
                # Verify signature
                verify_task = progress.add_task(
                    "[cyan]Verifying signature...[/cyan]",
                    total=1
                )
                
                if not await self.verify_strap_signature(strap_path):
                    progress.update(verify_task, completed=True)
                    self.console.print(Panel(
                        "[red]Signature verification failed[/red]",
                        border_style="red"
                    ))
                    return False
                    
                progress.update(verify_task, completed=True)
                
                # Install BlackArch
                install_task = progress.add_task(
                    "[green]Installing BlackArch...[/green]",
                    total=1
                )
                
                os.chmod(strap_path, 0o755)
                process = await asyncio.create_subprocess_exec(
                    str(strap_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    progress.update(install_task, completed=True)
                    self.console.print(Panel(
                        f"[red]Installation failed: {stderr.decode()}[/red]",
                        border_style="red"
                    ))
                    return False
                    
                progress.update(install_task, completed=True)
                
            self.console.print(Panel(
                "[green]BlackArch installation completed successfully![/green]",
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
            await self.close_session()

async def main():
    """Entry point with comprehensive error handling."""
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
