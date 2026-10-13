"""エクスポートファイル（.eml / CSV / JSONL）と資料（.md / .txt）を取得元として読む。

メールナレッジ化AI に接続できるかは未確認なので、手元に書き出したファイルからでも
同じ RawDocument を作れるようにしておく。こちらは Phase 0 で完結させる側。

.md / .txt は引継ぎ資料のようなメモを想定している。用語集が一番要るのは、
前任者の資料を読むときだから。サブフォルダもたどる（資料はフォルダで分けて置かれるため）。

本文はここで読んでメモリ上に置くだけで、どこにも書き出さない。
"""

from __future__ import annotations

import csv
import email
import email.policy
import io
import json
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from glossary.ports import RawDocument

# 時差の無い日時は日本時間とみなす。社内メールのエクスポートを想定しているため
DEFAULT_TZ = timezone(timedelta(hours=9))

# CSV / JSONL で必須にする列。名前を固定しておけば、エクスポート側で列名を合わせるだけで済む
REQUIRED_FIELDS = ("body", "thread_id", "occurred_at", "source_ref")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=DEFAULT_TZ)


def _parse_iso(value: str) -> datetime:
    return _aware(datetime.fromisoformat(value.strip()))


def _read_text(path: Path) -> str:
    # Excel が書き出す CSV は BOM 付き UTF-8 か cp932 のどちらかであることが多い
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"文字コードを判定できない: {path.name}")


def _eml_body(msg: EmailMessage) -> str:
    part = msg.get_body(preferencelist=("plain",))
    if part is None:
        return ""
    content = part.get_content()
    return content if isinstance(content, str) else ""


def _eml_thread_id(msg: EmailMessage) -> str:
    # 返信の連なりは References の先頭（最初のメール）で束ねる。無ければ自分が起点
    refs = str(msg.get("References", "")).split()
    if refs:
        return refs[0]
    reply_to = str(msg.get("In-Reply-To", "")).strip()
    if reply_to:
        return reply_to
    return str(msg.get("Message-ID", "")).strip()


def _parse_eml(path: Path) -> RawDocument:
    with path.open("rb") as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    assert isinstance(msg, EmailMessage)
    date_header = msg.get("Date")
    if date_header is None:
        raise ValueError(f"Date ヘッダが無い: {path.name}")
    message_id = str(msg.get("Message-ID", "")).strip()
    return RawDocument(
        body=_eml_body(msg),
        thread_id=_eml_thread_id(msg) or f"eml:{path.name}",
        occurred_at=_aware(parsedate_to_datetime(str(date_header))),
        source_ref=f"eml:{path.name}#{message_id}" if message_id else f"eml:{path.name}",
    )


def _from_record(record: dict[str, Any], where: str) -> RawDocument:
    missing = [k for k in REQUIRED_FIELDS if not str(record.get(k, "")).strip()]
    if missing:
        raise ValueError(f"{where}: 必須項目が空 {missing}")
    return RawDocument(
        body=str(record["body"]),
        thread_id=str(record["thread_id"]),
        occurred_at=_parse_iso(str(record["occurred_at"])),
        source_ref=str(record["source_ref"]),
    )


def _parse_csv(path: Path) -> Iterator[RawDocument]:
    reader = csv.DictReader(io.StringIO(_read_text(path), newline=""))
    for i, row in enumerate(reader, start=2):
        yield _from_record(row, f"{path.name}:{i}")


def _parse_note(path: Path, root: Path) -> RawDocument:
    rel = path.relative_to(root).as_posix()
    # 資料には送信日時が無いので、最後に更新された日時を出典日時にする
    return RawDocument(
        body=_read_text(path),
        thread_id=f"doc:{rel}",
        occurred_at=datetime.fromtimestamp(path.stat().st_mtime, tz=DEFAULT_TZ),
        source_ref=f"doc:{rel}",
    )


def _parse_jsonl(path: Path) -> Iterator[RawDocument]:
    for i, line in enumerate(_read_text(path).splitlines(), start=1):
        if line.strip():
            yield _from_record(json.loads(line), f"{path.name}:{i}")


class ExportFileAdapter:
    """フォルダ以下の .eml / .csv / .jsonl / .md / .txt を読む SourcePort 実装。"""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _iter_all(self) -> Iterator[RawDocument]:
        if not self.directory.is_dir():
            raise FileNotFoundError(f"エクスポートフォルダが無い: {self.directory}")
        for path in sorted(self.directory.rglob("*")):
            # .obsidian や .git のような隠しフォルダの中は資料ではない
            if not path.is_file() or any(
                part.startswith(".") for part in path.relative_to(self.directory).parts
            ):
                continue
            suffix = path.suffix.lower()
            if suffix == ".eml":
                yield _parse_eml(path)
            elif suffix == ".csv":
                yield from _parse_csv(path)
            elif suffix == ".jsonl":
                yield from _parse_jsonl(path)
            elif suffix in (".md", ".txt"):
                yield _parse_note(path, self.directory)

    def fetch_documents(self, since: datetime, until: datetime) -> Iterable[RawDocument]:
        lo, hi = _aware(since), _aware(until)
        return [d for d in self._iter_all() if lo <= d.occurred_at < hi]
