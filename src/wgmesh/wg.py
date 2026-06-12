from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


class WireGuardToolsError(RuntimeError):
    pass


class WireGuard:
    def __init__(self, executable: str | Path):
        self.executable = str(executable)

    def pubkey(self, private_key: str) -> str:
        return self._run(
            ["pubkey"],
            stdin=private_key.strip() + "\n",
            action="calculate WireGuard public key",
        )

    def genkey(self) -> str:
        return self._run(
            ["genkey"],
            action="generate WireGuard private key",
        )

    def genpsk(self) -> str:
        return self._run(
            ["genpsk"],
            action="generate WireGuard preshared key",
        )

    def _run(
        self,
        args: list[str],
        *,
        action: str,
        stdin: str | None = None,
    ) -> str:
        command = [self.executable, *args]

        try:
            proc = subprocess.run(
                command,
                input=stdin,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise WireGuardToolsError(_missing_wg_message()) from exc
        except PermissionError as exc:
            raise WireGuardToolsError(
                "WireGuard command exists but cannot be executed.\n"
                "\n"
                f"Command:\n  {self.executable}\n"
                "\n"
                "Check file permissions or install WireGuard tools again."
            ) from exc

        if proc.returncode != 0:
            stderr = proc.stderr.strip() or "no error output"
            raise WireGuardToolsError(
                f"Failed to {action}.\n"
                "\n"
                f"Command:\n  {' '.join(command)}\n"
                "\n"
                f"WireGuard output:\n{stderr}"
            )

        value = proc.stdout.strip()
        if not value:
            raise WireGuardToolsError(
                f"Failed to {action}.\n"
                "\n"
                f"Command returned empty output:\n  {' '.join(command)}"
            )

        return value


def get_wg() -> WireGuard:
    return WireGuard(_find_wg_executable())


def _find_wg_executable() -> str:
    env_path = os.environ.get("WG_EXECUTABLE")
    if env_path:
        return env_path

    path_wg = shutil.which("wg")
    if path_wg:
        return path_wg

    if platform.system().lower() == "windows":
        default_windows_path = Path("C:/Program Files/WireGuard/wg.exe")
        if default_windows_path.exists():
            return str(default_windows_path)

    raise WireGuardToolsError(_missing_wg_message())


def _missing_wg_message() -> str:
    return (
        "WireGuard command line tools are required but `wg` was not found.\n"
        "\n"
        "wgmesh uses `wg` for:\n"
        "  - wg pubkey\n"
        "  - wg genkey\n"
        "  - wg genpsk\n"
        "\n"
        "Install WireGuard tools:\n"
        "  Debian/Ubuntu: sudo apt install wireguard-tools\n"
        "  Alpine:       sudo apk add wireguard-tools\n"
        "  Arch Linux:   sudo pacman -S wireguard-tools\n"
        "  Fedora/RHEL:  sudo dnf install wireguard-tools\n"
        "  openSUSE:     sudo zypper install wireguard-tools\n"
        "\n"
        "Windows:\n"
        "  Install official WireGuard for Windows MSI.\n"
        "  The CLI tool is usually installed as:\n"
        "    C:/Program Files/WireGuard/wg.exe\n"
        "\n"
        "  Official MSI builds are available for amd64, arm64 and x86.\n"
        "\n"
        "Override path if needed:\n"
        "  WG_EXECUTABLE=/path/to/wg wgmesh build\n"
    )
