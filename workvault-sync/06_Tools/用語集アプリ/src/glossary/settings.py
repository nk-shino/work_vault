"""環境変数の読み取りをここに集める。

既定値はすべて「外に出ない」側に倒す。値が空でも Phase 0 はモックで動く。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_BACKENDS = ("export", "knowledge_api")
LLM_BACKENDS = ("mock", "litellm", "local")


@dataclass(frozen=True)
class Settings:
    source_backend: str
    llm_backend: str
    export_dir: Path
    database_url: str
    data_dir: Path
    config_dir: Path


def _env(name: str, default: str) -> str:
    # 空文字は「未設定」と同じに扱う。.env.example を写しただけの状態でも既定で動かすため
    value = os.environ.get(name, "").strip()
    return value or default


def load_settings() -> Settings:
    data_dir = Path(_env("GLOSSARY_DATA_DIR", str(PROJECT_ROOT / "data")))
    source = _env("SOURCE_BACKEND", "export")
    llm = _env("LLM_BACKEND", "mock")
    if source not in SOURCE_BACKENDS:
        raise ValueError(f"SOURCE_BACKEND は {SOURCE_BACKENDS} のいずれか: {source!r}")
    if llm not in LLM_BACKENDS:
        raise ValueError(f"LLM_BACKEND は {LLM_BACKENDS} のいずれか: {llm!r}")
    return Settings(
        source_backend=source,
        llm_backend=llm,
        export_dir=Path(_env("EXPORT_DIR", str(PROJECT_ROOT / "fixtures" / "mails"))),
        database_url=_env("DATABASE_URL", f"sqlite:///{(data_dir / 'glossary.db').as_posix()}"),
        data_dir=data_dir,
        config_dir=PROJECT_ROOT / "config",
    )
