"""Configuração lida de variáveis de ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).parent
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "rpgtools"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    port: int = 8000
    public_url: str | None = None

    @property
    def db_path(self) -> Path:
        return self.data_dir / "rpgtools.db"

    @property
    def assets_dir(self) -> Path:
        return self.data_dir / "assets"


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("RPG_DATA_DIR") or DEFAULT_DATA_DIR).expanduser()
    port = int(os.environ.get("RPG_PORT") or 8000)
    public_url = (os.environ.get("RPG_PUBLIC_URL") or "").rstrip("/") or None
    return Settings(data_dir=data_dir, port=port, public_url=public_url)
