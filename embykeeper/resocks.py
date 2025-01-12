import platform
import subprocess
import requests
import tarfile
import zipfile
from pathlib import Path
import stat
from typing import Optional


class Resocks:
    BASE_URL = "https://github.com/RedTeamPentesting/resocks/releases/download/v0.1.1"

    PLATFORM_MAPPING = {
        "Linux": {
            "x86_64": "Linux_x86_64.tar.gz",
            "aarch64": "Linux_arm64.tar.gz",
            "armv7l": "Linux_arm.tar.gz",
        },
        "Darwin": {
            "x86_64": "Darwin_x86_64.tar.gz",
            "arm64": "Darwin_arm64.tar.gz",
        },
        "Windows": {
            "AMD64": "Windows_x86_64.zip",
        },
    }

    def __init__(self, basedir: Path):
        """Initialize Resocks handler

        Args:
            cache_dir: Directory to store downloaded files. Defaults to ~/.cache/embykeeper
        """
        self.system = platform.system()
        self.machine = platform.machine()
        self.basedir = basedir
        self.basedir.mkdir(parents=True, exist_ok=True)
        self.process: Optional[subprocess.Popen] = None

    @property
    def executable_path(self) -> Path:
        """Get path to the executable"""
        exe_name = "resocks.exe" if self.system == "Windows" else "resocks"
        return self.basedir / exe_name

    def get_download_url(self) -> str:
        """Generate download URL based on current platform"""
        try:
            filename = f"resocks_{self.PLATFORM_MAPPING[self.system][self.machine]}"
            return f"{self.BASE_URL}/{filename}"
        except KeyError:
            raise RuntimeError(f"Unsupported platform: {self.system} {self.machine}")

    def download(self) -> None:
        """Download and extract resocks binary"""
        url = self.get_download_url()
        archive_path = self.basedir / url.split("/")[-1]

        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(archive_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Extract file
        if url.endswith(".tar.gz"):
            with tarfile.open(archive_path) as tar:
                tar.extract("resocks", self.basedir)
        else:  # .zip
            with zipfile.ZipFile(archive_path) as zip_ref:
                zip_ref.extract("resocks.exe", self.basedir)

        # Set executable permission on Unix
        if self.system != "Windows":
            self.executable_path.chmod(self.executable_path.stat().st_mode | stat.S_IEXEC)

        # Clean up
        archive_path.unlink()

    def ensure_binary(self) -> None:
        """Ensure binary exists and download if necessary"""
        if not self.executable_path.exists():
            self.download()

    def execute(self, *args) -> subprocess.Popen:
        """Execute resocks with given arguments and return Popen object"""
        self.ensure_binary()
        return subprocess.Popen(
            [str(self.executable_path), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def start(self, host: str, key: str) -> None:
        """Start resocks listen server

        Args:
            host: Server address with port
            key: Authentication key
        """
        if self.process and self.process.poll() is None:
            raise RuntimeError("Resocks is already running")

        self.process = self.execute("listen", str(host), "-k", key)

    def stop(self) -> None:
        """Stop resocks server if running"""
        if self.process:
            if self.process.poll() is None:  # Process is still running
                self.process.terminate()  # Try graceful shutdown first
                try:
                    self.process.wait(timeout=5)  # Wait up to 5 seconds
                except subprocess.TimeoutExpired:
                    self.process.kill()  # Force kill if not terminated
            self.process = None
