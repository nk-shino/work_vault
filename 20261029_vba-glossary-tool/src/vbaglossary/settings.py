"""環境変数の読み取り。既定値はこのファイルに集める。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_url: str
    data_dir: Path
    config_dir: Path
    export_dir: Path

    @property
    def masking_rules_path(self) -> str:
        return str(self.config_dir / "masking_rules.yaml")

    @property
    def adoption_path(self) -> str:
        return str(self.config_dir / "adoption.yaml")


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("VBA_GLOSSARY_DATA_DIR", ROOT / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    export_dir = Path(os.environ.get("VBA_GLOSSARY_EXPORT_DIR", ROOT / "export"))
    export_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", f"sqlite:///{(data_dir / 'glossary.db').as_posix()}"
        ),
        data_dir=data_dir,
        config_dir=ROOT / "config",
        export_dir=export_dir,
    )
