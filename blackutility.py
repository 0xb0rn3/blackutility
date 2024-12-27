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
    """Enhanced BlackArch Linux utility manager with network optimization and visual improvements."""
    
    BANNER = '''
[cyan]
█▄▄ █░░ ▄▀█ █▀▀ █▄▀ █░█ ▀█▀ █ █░░ █ ▀█▀ █▄█
█▄█ █▄▄ █▀█ █▄▄ █░█ █▄█ ░█░ █ █▄▄ █ ░█░ ░█░
[/cyan]
[yellow]Advanced Cybersecurity Arsenal for Arch[/yellow]

Dev: 0xb0rn3 | Socials{IG}: @theehiv3
Repo: github.com/0xb0rn3/blackutility
Version: 0.1.0 ALFA

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
            'mirrors': [
                "https://mirrors.kernel.org/blackarch/$repo/os/$arch",
                "https://mirror.cyberbits.eu/blackarch/$repo/os/$arch",
                "https://mirrors.dotsrc.org/blackarch/$repo/os/$arch"
            ],
            'blackarch_key': "4345771566D76038C7FEB43863EC0ADBEA87E4E3",
            'known_hashes': [
                "8eccac81b4e967c9140923f66b13cfb1f318879df06e3f8e35c913d3c8e070a5"
            ]
        }

    def setup_logging(self):
        """Configure rotating log handler with detailed formatting."""
        log_dir = Path("/var/log/blackutility")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("BlackArchUtility")
        self.logger.setLevel(logging.INFO)
        
        handler = RotatingFileHandler(
            log_dir / f"blackutility_{datetime.now():%Y%m%d}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)

    async def create_session(self):
        """Create optimized aiohttp session with connection pooling."""
        conn = aiohttp.TCPConnector(
            limit=self.config['max_concurrent_downloads'],
            ttl_dns_cache=300,  # Cache DNS results for 5 minutes
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=conn,
            timeout=aiohttp.ClientTimeout(total=self.config['connection_timeout'])
        )

    async def close_session(self):
        """Safely close the aiohttp session."""
        if self.session:
            await self.session.close()

    async def download_with_resume(self, url: str, dest_path: Path, 
                                 progress: Progress) -> bool:
        """Download file with resume capability and progress tracking."""
        file_id = hashlib.md5(url.encode()).hexdigest()
        chunk_size = self.config['chunk_size']
        
        if file_id not in self.download_chunks:
            self.download_chunks[file_id] = []
        
        chunks = self.download_chunks[file_id]
        start_byte = len(b''.join(chunks))
        
        headers = {'Range': f'bytes={start_byte}-'}
        
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
                        
                    with open(dest_path, 'wb') as f:
                        f.write(b''.join(chunks))
                        
                    return True
                    
            except Exception as e:
                retry_count += 1
                self.logger.warning(
                    f"Download attempt {retry_count} failed: {str(e)}"
                )
                if retry_count < self.config['max_retries']:
                    await asyncio.sleep(self.config['retry_delay'])
                    
        return False

    async def verify_strap(self, content: bytes) -> bool:
        """Verify strap.sh integrity with retries."""
        sha256 = hashlib.sha256(content).hexdigest()
        return sha256 in self.config['known_hashes']

    async def test_mirror_speed(self, mirror: str) -> Tuple[str, float]:
        """Test mirror download speed with visual feedback."""
        try:
            url = f"{mirror.split('$')[0]}/strap.sh"
            start_time = datetime.now()
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    await response.read()
                    duration = (datetime.now() - start_time).total_seconds()
                    return mirror, duration
                    
        except Exception:
            pass
            
        return mirror, float('inf')

    async def get_fastest_mirror(self) -> str:
        """Find the fastest responding mirror with visual feedback."""
        tasks = [self.test_mirror_speed(mirror) 
                for mirror in self.config['mirrors']]
        results = await asyncio.gather(*tasks)
        
        sorted_mirrors = sorted(results, key=lambda x: x[1])
        return sorted_mirrors[0][0]

    async def install(self) -> bool:
        """Install BlackArch with enhanced visual feedback and progress tracking."""
        try:
            self.console.print(Panel(self.BANNER, border_style="cyan"))
            
            if os.geteuid() != 0:
                self.console.print("[red]Must run as root[/red]")
                return False
                
            await self.create_session()
            
            # Enhanced progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console,
                expand=True
            ) as progress:
                
                # Mirror testing with visual feedback
                mirror_task = progress.add_task(
                    "[yellow]Testing mirrors...[/yellow]",
                    total=len(self.config['mirrors'])
                )
                mirror = await self.get_fastest_mirror()
                progress.update(mirror_task, completed=True)
                
                # Download with enhanced progress
                strap_path = Path(tempfile.mkdtemp()) / "strap.sh"
                url = f"{mirror.split('$')[0]}/strap.sh"
                
                if not await self.download_with_resume(url, strap_path, progress):
                    self.console.print(Panel(
                        "[red]Download failed after retries[/red]",
                        border_style="red"
                    ))
                    return False
                    
                # Verification with spinner
                verify_task = progress.add_task(
                    "[cyan]Verifying integrity...[/cyan]",
                    total=1
                )
                content = strap_path.read_bytes()
                if not await self.verify_strap(content):
                    progress.update(verify_task, completed=True)
                    self.console.print(Panel(
                        "[red]Verification failed[/red]",
                        border_style="red"
                    ))
                    return False
                    
                progress.update(verify_task, completed=True)
                
                # Installation with detailed progress
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
                "[green]Installation completed successfully![/green]",
                border_style="green"
            ))
            return True
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Error: {str(e)}[/red]",
                border_style="red"
            ))
            return False
            
        finally:
            await self.close_session()

async def main():
    """Entry point with enhanced error handling and user feedback."""
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
        utility.console.print(Panel(
            f"[red]Fatal error: {str(e)}[/red]",
            border_style="red"
        ))
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
