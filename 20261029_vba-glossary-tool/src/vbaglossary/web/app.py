"""FastAPI の画面。書き込みはすべて domain を通る。

- 提案の受理・見送り: domain.proposals
- 語義の編集: domain.review（楽観ロック付き・理由必須）
- 評価: domain.evaluations（追記専用）

注意: このファイルは `from __future__ import annotations` を使わない。
依存の型（DbDep など）を FastAPI が実行時に解決する必要があるため。
"""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from vbaglossary.db.guards import register_guards
from vbaglossary.db.models import Module, Procedure, Proposal, Sense
from vbaglossary.db.session import make_engine, make_session_factory
from vbaglossary.domain import evaluations as evaluations_domain
from vbaglossary.domain import proposals as proposals_domain
from vbaglossary.domain import queries, review
from vbaglossary.domain.errors import ConflictError, ValidationFailed

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def _flash(request: Request) -> dict[str, str]:
    return {"msg": request.query_params.get("msg", ""), "err": request.query_params.get("err", "")}


def create_app(database_url: str) -> FastAPI:
    register_guards()
    factory = make_session_factory(make_engine(database_url))
    app = FastAPI(title="VBA 学習辞書", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    def db() -> Iterator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    DbDep = Annotated[Session, Depends(db)]

    def render(
        request: Request, db: Session, name: str, nav: str, **ctx: Any
    ) -> HTMLResponse:
        ctx.update(_flash(request))
        ctx["nav"] = nav
        ctx["open_proposals"] = (
            db.scalar(
                select(Proposal.id)
                .where(Proposal.decided_at.is_(None), Proposal.state != "hold")
                .limit(1)
            )
            is not None
        )
        return TEMPLATES.TemplateResponse(request, name, ctx)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, db: DbDep) -> HTMLResponse:
        return render(
            request,
            db,
            "index.html",
            "home",
            stats=queries.stats(db),
            recent=queries.list_proposals(db)[:8],
        )

    @app.get("/procedures", response_class=HTMLResponse)
    def procedure_list(
        request: Request,
        db: DbDep,
        q: str = "",
        kind: str = "",
        module: str = "",
        tag: str = "",
        learned: str = "",
    ) -> HTMLResponse:
        rows = queries.list_procedures(
            db, q=q, kind=kind, module_id=module, tag=tag, learned=learned
        )
        modules = db.scalars(select(Module).order_by(Module.name)).all()
        stats = queries.stats(db)
        return render(
            request,
            db,
            "procedures.html",
            "procedures",
            rows=rows,
            modules=modules,
            tag_counts=stats.tag_counts,
            filt={"q": q, "kind": kind, "module": module, "tag": tag, "learned": learned},
        )

    def _call_links(db: Session, p: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """呼び出し先・呼び出し元を名前とリンクに整理する。"""
        book_id = p["book_id"]
        book_procs = db.execute(
            select(Procedure, Module)
            .join(Module, Procedure.module_id == Module.id)
            .where(Module.book_id == book_id)
        ).all()
        by_lower = {proc.name.lower(): proc for proc, _m in book_procs}
        id_to_name = {proc.id: proc.name for proc, _m in book_procs}

        def link_for(name: str) -> dict[str, str]:
            target = by_lower.get(name.lower())
            if target is None:
                return {"name": name, "id": ""}
            return {"name": name, "id": target.id}

        calls = [link_for(name) for name in p["calls"]]
        called_by = [
            {"name": id_to_name.get(pid, pid), "id": pid} for pid in p["called_by"]
        ]
        return calls, called_by

    def _code_path(db: Session, p: dict[str, Any]) -> Path | None:
        from vbaglossary.settings import load_settings

        safe_book = re.sub(r'[\\/:*?"<>|]+', "_", p["book_name"])
        ext = ".cls" if p["module_kind"] == "class" else ".bas"
        path = Path(load_settings().export_dir) / safe_book / f"{p['file_name']}"
        if not path.exists():
            path = Path(load_settings().export_dir) / safe_book / f"{p['module_name']}{ext}"
        return path if path.exists() else None

    @app.get("/procedures/{proc_id}", response_class=HTMLResponse)
    def procedure_detail(proc_id: str, request: Request, db: DbDep) -> HTMLResponse:
        p = queries.get_procedure(db, proc_id)
        if p is None:
            raise HTTPException(status_code=404, detail="プロシージャが見つからない")
        calls, called_by = _call_links(db, p)
        histories = queries.history_for(db, "procedures", proc_id)
        return render(
            request,
            db,
            "procedure_detail.html",
            "procedures",
            p=p,
            calls=calls,
            called_by=called_by,
            histories=histories,
            code_path=_code_path(db, p),
        )

    @app.get("/procedures/{proc_id}/code", response_class=HTMLResponse)
    def procedure_code(proc_id: str, request: Request, db: DbDep) -> HTMLResponse:
        p = queries.get_procedure(db, proc_id)
        if p is None:
            raise HTTPException(status_code=404, detail="プロシージャが見つからない")
        path = _code_path(db, p)
        if path is None:
            raise HTTPException(status_code=404, detail="コードの書き出しが見つからない（再解析で作成される）")
        code = path.read_text(encoding="utf-8", errors="replace")
        return render(
            request, db, "code.html", "procedures", p=p, code=code, file_name=path.name
        )

    @app.get("/proposals", response_class=HTMLResponse)
    def proposal_queue(
        request: Request, db: DbDep, state: str = ""
    ) -> HTMLResponse:
        rows = queries.list_proposals(db, state=state)
        return render(
            request, db, "proposals.html", "proposals", rows=rows, state=state
        )

    @app.post("/proposals/{proposal_id}/accept")
    def accept_proposal(
        proposal_id: str,
        db: DbDep,
        text: Annotated[str, Form()],
        reason: Annotated[str, Form()] = "提案どおり受理",
    ) -> RedirectResponse:
        proposal = db.get(Proposal, proposal_id)
        if proposal is None:
            raise HTTPException(status_code=404, detail="提案が見つからない")
        back = f"/procedures/{proposal.procedure_id}"
        try:
            sense = proposals_domain.accept(db, proposal_id, text=text, reason=reason)
            db.commit()
        except ValidationFailed as exc:
            db.rollback()
            return RedirectResponse(f"{back}?err={_q(str(exc))}", status_code=303)
        return RedirectResponse(
            f"/procedures/{sense.procedure_id}?msg={_q('語義を受理しました')}",
            status_code=303,
        )

    @app.post("/proposals/{proposal_id}/reject")
    def reject_proposal(
        proposal_id: str, db: DbDep, reason: Annotated[str, Form()]
    ) -> RedirectResponse:
        proposal = db.get(Proposal, proposal_id)
        back = f"/procedures/{proposal.procedure_id}" if proposal else "/proposals"
        try:
            proposals_domain.reject(db, proposal_id, reason=reason)
            db.commit()
        except ValidationFailed as exc:
            db.rollback()
            return RedirectResponse(f"{back}?err={_q(str(exc))}", status_code=303)
        return RedirectResponse(f"{back}?msg={_q('提案を見送りました')}", status_code=303)

    @app.get("/review", response_class=HTMLResponse)
    def review_list(request: Request, db: DbDep) -> HTMLResponse:
        return render(
            request, db, "review.html", "review", rows=queries.review_list(db)
        )

    @app.post("/senses/{sense_id}/edit")
    def edit_sense(
        sense_id: str,
        db: DbDep,
        text: Annotated[str, Form()],
        reason: Annotated[str, Form()],
        expected_revision: Annotated[int, Form()],
    ) -> RedirectResponse:
        sense = db.get(Sense, sense_id)
        back = (
            f"/procedures/{sense.procedure_id}" if sense else "/review"
        )
        try:
            review.edit_sense(
                db, sense_id, expected_revision=expected_revision, text=text, reason=reason
            )
            db.commit()
        except ConflictError:
            db.rollback()
            msg = "他の操作が先に保存したため競合しました。最新の内容を確認してやり直してください"
            return RedirectResponse(f"{back}?err={_q(msg)}", status_code=303)
        except ValidationFailed as exc:
            db.rollback()
            return RedirectResponse(f"{back}?err={_q(str(exc))}", status_code=303)
        return RedirectResponse(f"{back}?msg={_q('語義を更新しました（履歴に記録）')}", status_code=303)

    @app.post("/senses/{sense_id}/evaluate")
    def evaluate_sense(
        sense_id: str,
        db: DbDep,
        accuracy: Annotated[str, Form()],
        usefulness: Annotated[str, Form()],
        seen_version: Annotated[int, Form()],
        reason: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        sense = db.get(Sense, sense_id)
        back = f"/procedures/{sense.procedure_id}" if sense else "/review"
        try:
            evaluations_domain.evaluate(
                db,
                sense_id,
                seen_version=seen_version,
                accuracy=accuracy,
                usefulness=usefulness,
                reason=reason,
            )
            db.commit()
        except ValidationFailed as exc:
            db.rollback()
            return RedirectResponse(f"{back}?err={_q(str(exc))}", status_code=303)
        return RedirectResponse(f"{back}?msg={_q('評価を記録しました')}", status_code=303)

    @app.get("/history/{entity}/{entity_id}", response_class=HTMLResponse)
    def history_view(
        entity: str, entity_id: str, request: Request, db: DbDep
    ) -> HTMLResponse:
        if entity not in ("procedures", "senses", "proposals"):
            raise HTTPException(status_code=404, detail="不明な対象")
        title = {"procedures": "プロシージャ", "senses": "語義", "proposals": "提案"}[entity]
        return render(
            request,
            db,
            "history.html",
            "procedures",
            entity=entity,
            entity_id=entity_id,
            title=title,
            rows=queries.history_for(db, entity, entity_id),
        )

    return app


def _q(text: str) -> str:
    from urllib.parse import quote

    return quote(text)
