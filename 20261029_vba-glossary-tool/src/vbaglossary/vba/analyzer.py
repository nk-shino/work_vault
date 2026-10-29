"""解析の入口。ブックからモジュール・プロシージャを登録し、提案を積むまで。

- 語義はここでは書かない。受理は人の仕事（domain.proposals.accept）
- 再解析に強い: 同じ内容（sha256）なら提案の重複を作らず、手で直した語義には
  触れない。プロシージャの定義が変わったら理由付きで更新する
- コメントに概要が書いてあればそれを語義ドラフトにする（draft_source=comment）。
  無ければ定型文（draft_source=auto）
- 禁止情報を検知したらその提案は保留にし、用例はマスキングした断片だけ残す
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from vbaglossary.db.guards import change_reason
from vbaglossary.db.models import EXCERPT_MAX_LEN, Book, Module, Procedure, Proposal, new_id
from vbaglossary.domain import proposals as proposals_domain
from vbaglossary.settings import load_settings
from vbaglossary.vba.extract import RawModule, extract_modules
from vbaglossary.vba.mask import mask, scan
from vbaglossary.vba.parse import ParsedProc, parse_module

NO_DRAFT_TEMPLATE = "{name}（{kind}）の説明が未記入"


@dataclass
class AnalyzeResult:
    book_id: str
    book_name: str
    sha256: str
    modules: int = 0
    procedures: int = 0
    new_procedures: int = 0
    updated_procedures: int = 0
    proposals_added: int = 0
    proposals_updated: int = 0
    proposals_held: int = 0
    warnings: list[str] = field(default_factory=list)


def _sha_of(source: Path, modules: list[RawModule]) -> str:
    if source.is_file():
        return hashlib.sha256(source.read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for mod in modules:
        digest.update(mod.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(mod.code.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _export_code(export_root: Path, book_name: str, mod: RawModule) -> Path:
    safe_book = re.sub(r'[\\/:*?"<>|]+', "_", book_name)
    target_dir = export_root / safe_book
    target_dir.mkdir(parents=True, exist_ok=True)
    ext = {("standard"): ".bas", ("class"): ".cls"}.get(mod.kind, ".bas")
    path = target_dir / f"{mod.name}{ext}"
    path.write_text(mod.code, encoding="utf-8")
    return path


def _source_key(book_name: str, module_name: str, proc: ParsedProc, duplicates: set[str]) -> str:
    slug = re.sub(r"[^\w.-]+", "_", book_name)
    key = f"{slug}:{module_name}:{proc.name}"
    if proc.name in duplicates:
        key += ":" + proc.kind.replace(" ", "-").lower()
    return key


def _excerpt(proc: ParsedProc) -> str:
    body = proc.body_code
    text = body if body.strip() else proc.signature
    return text[:EXCERPT_MAX_LEN]


def analyze(session: Session, source: Path, *, book_name: str | None = None) -> AnalyzeResult:
    settings = load_settings()
    modules_raw = extract_modules(source)
    sha = _sha_of(source, modules_raw)
    name = book_name or source.name

    # ブックは名前を正とする。同名の再解析は同じ行を更新し、履歴に差分を残す
    book = session.scalar(select(Book).where(Book.name == name))
    if book is None:
        book = Book(
            id=new_id("b"),
            name=name,
            path=str(source.resolve()),
            sha256=sha,
            analyzed_at=datetime.now(),
        )
        session.add(book)
        session.flush()
    else:
        book.sha256 = sha
        book.analyzed_at = datetime.now()
        book.path = str(source.resolve())

    result = AnalyzeResult(book_id=book.id, book_name=book.name, sha256=sha)

    parsed_by_module: list[tuple[RawModule, list[ParsedProc]]] = []
    for mod in modules_raw:
        parsed_by_module.append((mod, parse_module(mod)))
        _export_code(Path(settings.export_dir), book.name, mod)

    for mod, procs in parsed_by_module:
        dup_names = {p.name for p in procs if sum(1 for q in procs if q.name == p.name) > 1}
        module = session.scalar(
            select(Module).where(Module.book_id == book.id, Module.name == mod.name)
        )
        if module is None:
            module = Module(
                id=new_id("m"),
                book_id=book.id,
                name=mod.name,
                kind=mod.kind,
                file_name=mod.name + (".cls" if mod.kind == "class" else ".bas"),
            )
            session.add(module)
            session.flush()
        else:
            module.kind = mod.kind
        result.modules += 1

        for proc in procs:
            source_key = _source_key(book.name, mod.name, proc, dup_names)
            existing = session.scalar(
                select(Procedure).where(Procedure.source_key == source_key)
            )
            calls_json = json.dumps(sorted(proc.calls), ensure_ascii=False)
            if existing is None:
                procedure = Procedure(
                    id=new_id("p"),
                    module_id=module.id,
                    name=proc.name,
                    kind=proc.kind,
                    access=proc.access,
                    signature=proc.signature,
                    params_json=json.dumps(
                        [
                            {
                                "name": prm.name,
                                "type": prm.type,
                                "modifier": prm.modifier,
                                "optional": prm.optional,
                                "default": prm.default,
                            }
                            for prm in proc.params
                        ],
                        ensure_ascii=False,
                    ),
                    returns=proc.returns,
                    start_line=proc.start_line,
                    end_line=proc.end_line,
                    line_count=proc.line_count,
                    calls_json=calls_json,
                    called_by_json="[]",
                    tags_json=json.dumps(proc.tags, ensure_ascii=False),
                    source_key=source_key,
                )
                session.add(procedure)
                session.flush()
                result.new_procedures += 1
            else:
                procedure = existing
                if (
                    procedure.signature != proc.signature
                    or procedure.start_line != proc.start_line
                    or procedure.end_line != proc.end_line
                    or procedure.calls_json != calls_json
                    or procedure.tags_json != json.dumps(proc.tags, ensure_ascii=False)
                ):
                    with change_reason("再解析により定義を更新"):
                        procedure.signature = proc.signature
                        procedure.start_line = proc.start_line
                        procedure.end_line = proc.end_line
                        procedure.line_count = proc.line_count
                        procedure.calls_json = calls_json
                        procedure.tags_json = json.dumps(proc.tags, ensure_ascii=False)
                        session.flush()
                    result.updated_procedures += 1
            result.procedures += 1

            _queue_proposal(
                session, procedure, proc, result, settings.masking_rules_path
            )

    _fill_called_by(session, book.id)
    session.commit()
    return result


def _queue_proposal(
    session: Session,
    procedure: Procedure,
    proc: ParsedProc,
    result: AnalyzeResult,
    masking_rules_path: str,
) -> None:
    open_ids = set(
        session.scalars(
            select(Proposal.id).where(
                Proposal.procedure_id == procedure.id, Proposal.decided_at.is_(None)
            )
        )
    )
    if proc.comment_text:
        draft = proc.comment_text
        draft_source = "comment"
    else:
        draft = NO_DRAFT_TEMPLATE.format(name=proc.name, kind=proc.kind)
        draft_source = "auto"
    excerpt = _excerpt(proc)

    matched = scan(draft + "\n" + excerpt, masking_rules_path)
    reason: str | None
    if matched:
        draft = mask(draft, masking_rules_path)
        excerpt = mask(excerpt, masking_rules_path)
        state = "hold"
        reason = "禁止情報（" + ", ".join(matched) + "）を検知したため自動採用せず保留"
        result.proposals_held += 1
    else:
        state = "new"
        reason = None if draft_source == "comment" else "コメント未検出のため定型ドラフト"

    added = proposals_domain.add_proposal(
        session,
        procedure,
        state=state,
        draft_text=draft,
        excerpt=excerpt,
        draft_source=draft_source,
        reason=reason,
    )
    session.flush()
    if added is None:
        return
    if added.id in open_ids:
        result.proposals_updated += 1
    else:
        result.proposals_added += 1


def _fill_called_by(session: Session, book_id: str) -> None:
    procs = session.scalars(
        select(Procedure).join(Module, Procedure.module_id == Module.id).where(
            Module.book_id == book_id
        )
    ).all()
    by_lower: dict[str, list[str]] = {}
    for proc in procs:
        by_lower.setdefault(proc.name.lower(), []).append(proc.id)
    for proc in procs:
        callers = sorted(
            {
                caller.id
                for caller in procs
                if caller.id != proc.id
                and proc.name.lower()
                in {c.lower() for c in json.loads(caller.calls_json)}
            }
        )
        called_by = json.dumps(callers, ensure_ascii=False)
        if proc.called_by_json != called_by:
            with change_reason("再解析により呼び出し元を更新"):
                proc.called_by_json = called_by
                session.flush()
