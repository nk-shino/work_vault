"""レビューUI。Jinja2 テンプレートと素の JavaScript だけで作る。

定義や用例はプレーンテキストとして扱う。テンプレートの自動エスケープは切らず、|safe も使わない。

編集者の欄は置かない（2026-09-24 決定：誰でも誰の項目でも編集でき、今は誰が直したかを残す必要が無い）。
DB の editor_name / reviewed_by は将来ログインを入れるときのために残してあり、今は常に空。
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlencode, urlparse

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from glossary.adapters.llm.mock_adapter import MOCK_MODEL_NAME
from glossary.db.models import (
    PROPOSAL_STATUSES,
    RELATION_TYPES,
    SENSE_STATUSES,
    TERM_STATUSES,
    Proposal,
    Sense,
    Term,
)
from glossary.db.session import make_engine, make_session_factory
from glossary.domain import evaluations, proposals, queries, review
from glossary.domain.errors import ConflictError, DomainError, NotFound, ValidationFailed
from glossary.domain.proposals import SenseOverrides
from glossary.settings import load_settings

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=str(HERE / "templates"))

LABELS = {
    "draft": "草案",
    "active": "有効",
    "disputed": "係争中",
    "archived": "アーカイブ済み",
    "ai_draft": "AI草案",
    "needs_review": "要レビュー",
    "confirmed": "確定",
    "rejected": "却下",
    "pending": "未処理",
    "accepted": "採用済み",
    "related": "関連",
    "synonym": "同義",
    "abbrev_of": "略語の元",
    "broader": "上位概念",
    "narrower": "下位概念",
    "confused_with": "混同注意",
    "ai": "AI",
    "human": "人手",
    "sense": "語義",
    "relation": "関係",
    "evidence": "用例の追加",
    "term": "用語",
    "auto": "自動採用",
    "correct": "正しい",
    "needs_fix": "修正が必要",
    "unsure": "判断できない",
    "useful": "役に立つ",
    "not_useful": "役に立たない",
}
templates.env.globals["label"] = lambda key: LABELS.get(key, key)
JST = timezone(timedelta(hours=9))


def _jst(value: datetime | None) -> str:
    # DB には UTC で入っている。画面では利用者の時刻（日本時間）で見せる
    return value.astimezone(JST).strftime("%Y-%m-%d %H:%M") if value else "日時不明"


templates.env.filters["jst"] = _jst
# モックの定義文は中身の無い置き物。そのまま「確定」にさせないため、画面でも受理でも区別する
templates.env.globals["MOCK_MODEL_NAME"] = MOCK_MODEL_NAME
PROPOSALS_PER_PAGE = 20


def get_session(request: Request) -> Iterator[Session]:
    f: sessionmaker[Session] = request.app.state.factory
    with f() as session:
        yield session


# モジュールの直下に置く。関数の中に置くと、FastAPI が注釈を解決できずクエリ引数と取り違える
Db = Annotated[Session, Depends(get_session)]


def create_app(database_url: str | None = None) -> FastAPI:
    url = database_url or load_settings().database_url
    factory = make_session_factory(make_engine(url))
    app = FastAPI(title="社内用語集")
    app.state.factory = factory
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

    @app.middleware("http")
    async def reject_cross_site_posts(request: Request, call_next: Any) -> Response:
        # 127.0.0.1 で待ち受けていても、利用者が開いた別のサイトのページからは
        # このアプリへフォームを送れてしまう（CSRF）。書き込みは同じ画面から来たものだけ通す
        if request.method == "POST":
            origin = request.headers.get("origin") or request.headers.get("referer") or ""
            if origin and urlparse(origin).netloc != request.url.netloc:
                return PlainTextResponse("別のサイトからの送信は受け付けません", status_code=403)
        response: Response = await call_next(request)
        return response

    # 引数名を status にしないこと。テンプレートへ渡す絞り込みの status とぶつかる
    def render(request: Request, name: str, code: int = 200, **ctx: Any) -> HTMLResponse:
        return templates.TemplateResponse(request, name, ctx, status_code=code)

    @app.exception_handler(NotFound)
    async def _not_found(request: Request, exc: NotFound) -> Response:
        return render(request, "error.html", 404, message=str(exc))

    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> Response:
        return render(request, "error.html", 400, message=str(exc))

    @app.get("/")
    def index() -> RedirectResponse:
        return RedirectResponse("/terms", status_code=303)

    @app.get("/terms", response_class=HTMLResponse)
    def terms_list(
        request: Request, db: Db, q: str = "", tag: str = "", status: str = "", page: int = 1
    ) -> HTMLResponse:
        result = queries.list_terms(db, q=q.strip(), tag=tag, status=status, page=page)

        def page_url(n: int) -> str:
            # 検索条件は URL に全部載せる。リンクを共有すれば同じ一覧が開ける
            params = {k: v for k, v in {"q": q, "tag": tag, "status": status}.items() if v}
            return "/terms?" + urlencode(params | {"page": n})

        return render(
            request,
            "terms_list.html",
            result=result,
            q=q,
            tag=tag,
            status=status,
            tags=queries.context_tags(db),
            statuses=TERM_STATUSES,
            page_url=page_url,
        )

    @app.get("/terms/{term_id}", response_class=HTMLResponse)
    def term_detail(request: Request, db: Db, term_id: str) -> HTMLResponse:
        detail = queries.term_detail(db, term_id)
        if detail is None:
            raise NotFound("用語が見つからない")
        evals = evaluations.summaries(db, detail.senses)
        return render(request, "term_detail.html", d=detail, evals=evals)

    @app.post("/senses/{sense_id}/evaluate")
    def sense_evaluate(
        db: Db,
        sense_id: str,
        revision_number: Annotated[int, Form()],
        accuracy: Annotated[str, Form()] = "",
        usefulness: Annotated[str, Form()] = "",
        comment: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        ev = evaluations.evaluate(
            db, sense_id, seen_revision=revision_number, accuracy=accuracy or None,
            usefulness=usefulness or None, comment=comment,
        )  # fmt: skip
        db.commit()
        sense = db.get(Sense, ev.sense_id)
        assert sense is not None
        return RedirectResponse(f"/terms/{sense.term_id}#sense-{sense.id}", status_code=303)

    @app.get("/review", response_class=HTMLResponse)
    def review_page(request: Request, db: Db, kind: str = "needs_fix") -> HTMLResponse:
        items = evaluations.review_queue(db, kind)
        return render(
            request, "review.html", items=items, kind=kind, kinds=evaluations.REVIEW_KINDS,
            counts=evaluations.review_counts(db),
        )  # fmt: skip

    @app.post("/terms/{term_id}/archive")
    def term_archive(
        request: Request,
        db: Db,
        term_id: str,
        revision_number: Annotated[int, Form()],
        change_reason: Annotated[str, Form()] = "",
    ) -> Response:
        try:
            review.archive_term(
                db,
                term_id,
                expected_revision=revision_number,
                editor_name=None,
                change_reason=change_reason,
            )
            db.commit()
        except ConflictError as e:
            db.rollback()
            return render(request, "conflict.html", 409, e=e, back=f"/terms/{term_id}", diff=[])
        except ValueError as e:
            db.rollback()
            raise ValidationFailed(str(e)) from e
        return RedirectResponse(f"/terms/{term_id}", status_code=303)

    @app.get("/senses/{sense_id}/edit", response_class=HTMLResponse)
    def sense_edit_form(request: Request, db: Db, sense_id: str) -> HTMLResponse:
        sense = db.get(Sense, sense_id)
        if sense is None:
            raise NotFound("語義が見つからない")
        return render(request, "sense_edit.html", s=sense, statuses=SENSE_STATUSES, error=None)

    @app.post("/senses/{sense_id}/edit", response_class=HTMLResponse)
    def sense_edit(
        request: Request,
        db: Db,
        sense_id: str,
        revision_number: Annotated[int, Form()],
        definition: Annotated[str, Form()] = "",
        scope_note: Annotated[str, Form()] = "",
        context_tag: Annotated[str, Form()] = "",
        status: Annotated[str, Form()] = "",
        change_reason: Annotated[str, Form()] = "",
    ) -> Response:
        changes = {
            "definition": definition,
            "scope_note": scope_note or None,
            "context_tag": context_tag or None,
            "status": status,
        }
        try:
            sense = review.edit_sense(
                db,
                sense_id,
                expected_revision=revision_number,
                changes=changes,
                editor_name=None,
                change_reason=change_reason,
            )
            db.commit()
        except ConflictError as e:
            db.rollback()
            current = {k: e.current.get(k) for k in changes}
            diff = queries.diff_lines(current, changes)
            return render(
                request, "conflict.html", 409, e=e, back=f"/senses/{sense_id}/edit", diff=diff
            )
        except (ValidationFailed, ValueError) as e:
            db.rollback()
            s = db.get(Sense, sense_id)
            return render(
                request, "sense_edit.html", 400, s=s, statuses=SENSE_STATUSES, error=str(e),
                form=changes | {"change_reason": change_reason},
            )
        return RedirectResponse(f"/terms/{sense.term_id}", status_code=303)

    @app.get("/proposals", response_class=HTMLResponse)
    def proposals_list(
        request: Request, db: Db, status: str = "pending", page: int = 1
    ) -> HTMLResponse:
        stmt = select(Proposal)
        if status:
            stmt = stmt.where(Proposal.status == status)
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        pages = max(1, -(-total // PROPOSALS_PER_PAGE))
        page = min(max(1, page), pages)
        items = db.scalars(
            stmt.order_by(Proposal.score.desc(), Proposal.created_at)
            .offset((page - 1) * PROPOSALS_PER_PAGE)
            .limit(PROPOSALS_PER_PAGE)
        ).all()
        rows = [(p, json.loads(p.payload_json)) for p in items]
        return render(
            request, "proposals.html", rows=rows, status=status, statuses=PROPOSAL_STATUSES,
            page=page, pages=pages, total=total,
        )

    @app.post("/proposals/{pid}/accept")
    def proposal_accept(
        db: Db, pid: str
    ) -> RedirectResponse:
        p = db.get(Proposal, pid)
        if p is not None and p.proposal_type == "sense" and p.model_name == MOCK_MODEL_NAME:
            raise ValidationFailed(
                "モックの定義文はそのまま採用できない。「修正して採用」で定義を書いてください"
            )
        proposals.accept(db, pid, reviewer=None)
        db.commit()
        return RedirectResponse("/proposals", status_code=303)

    @app.post("/proposals/{pid}/reject")
    def proposal_reject(
        db: Db, pid: str
    ) -> RedirectResponse:
        proposals.reject(db, pid, reviewer=None)
        db.commit()
        return RedirectResponse("/proposals", status_code=303)

    @app.get("/proposals/{pid}/edit", response_class=HTMLResponse)
    def proposal_edit_form(request: Request, db: Db, pid: str) -> HTMLResponse:
        p = db.get(Proposal, pid)
        if p is None or p.proposal_type != "sense":
            raise NotFound("修正して採用できる語義の提案が無い")
        payload = json.loads(p.payload_json)
        if p.model_name == MOCK_MODEL_NAME:
            payload["definition"] = ""  # 置き物の文を書き換え忘れて確定させないよう、空で出す
        return render(request, "proposal_edit.html", p=p, payload=payload)

    @app.post("/proposals/{pid}/edit")
    def proposal_edit_accept(
        db: Db,
        pid: str,
        definition: Annotated[str, Form()] = "",
        context_tag: Annotated[str, Form()] = "",
        scope_note: Annotated[str, Form()] = "",
        change_reason: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        if not change_reason.strip():
            raise ValidationFailed("編集理由は必須")
        if not definition.strip():
            raise ValidationFailed("定義を書いてください")
        proposals.accept(
            db,
            pid,
            reviewer=None,
            overrides=SenseOverrides(definition or None, context_tag or None, scope_note or None),
            reason=change_reason,
        )
        db.commit()
        return RedirectResponse("/proposals", status_code=303)

    @app.get("/new", response_class=HTMLResponse)
    def term_new_form(request: Request, headword: str = "") -> HTMLResponse:
        return render(request, "term_new.html", f={"headword": headword}, error=None)

    @app.post("/new", response_class=HTMLResponse)
    def term_new(
        request: Request,
        db: Db,
        headword: Annotated[str, Form()] = "",
        definition: Annotated[str, Form()] = "",
        excerpt: Annotated[str, Form()] = "",
        source_ref: Annotated[str, Form()] = "",
        context_tag: Annotated[str, Form()] = "",
        scope_note: Annotated[str, Form()] = "",
        reading: Annotated[str, Form()] = "",
        english: Annotated[str, Form()] = "",
        abbreviation: Annotated[str, Form()] = "",
    ) -> Response:
        form = {
            "headword": headword, "definition": definition, "excerpt": excerpt,
            "source_ref": source_ref, "context_tag": context_tag, "scope_note": scope_note,
            "reading": reading, "english": english, "abbreviation": abbreviation,
        }  # fmt: skip
        try:
            proposals.register_manually(db, **form)
            db.commit()
        except ValidationFailed as e:
            db.rollback()
            return render(request, "term_new.html", 400, f=form, error=str(e))
        term = db.scalars(select(Term).where(Term.headword == headword.strip())).first()
        assert term is not None
        return RedirectResponse(f"/terms/{term.id}", status_code=303)

    @app.get("/terms/{term_id}/edit", response_class=HTMLResponse)
    def term_edit_form(request: Request, db: Db, term_id: str) -> HTMLResponse:
        term = db.get(Term, term_id)
        if term is None:
            raise NotFound("用語が見つからない")
        return render(request, "term_edit.html", t=term, f={}, error=None)

    @app.post("/terms/{term_id}/edit", response_class=HTMLResponse)
    def term_edit(
        request: Request,
        db: Db,
        term_id: str,
        revision_number: Annotated[int, Form()],
        headword: Annotated[str, Form()] = "",
        reading: Annotated[str, Form()] = "",
        english: Annotated[str, Form()] = "",
        abbreviation: Annotated[str, Form()] = "",
        status: Annotated[str, Form()] = "active",
        change_reason: Annotated[str, Form()] = "",
    ) -> Response:
        changes = {
            "headword": headword.strip(), "reading": reading or None, "english": english or None,
            "abbreviation": abbreviation or None, "status": status,
        }  # fmt: skip
        try:
            review.edit_term(
                db, term_id, expected_revision=revision_number, changes=changes,
                change_reason=change_reason,
            )  # fmt: skip
            db.commit()
        except ConflictError as e:
            db.rollback()
            diff = queries.diff_lines({k: e.current.get(k) for k in changes}, changes)
            return render(
                request, "conflict.html", 409, e=e, back=f"/terms/{term_id}/edit", diff=diff
            )
        except (ValidationFailed, ValueError) as e:
            db.rollback()
            t = db.get(Term, term_id)
            return render(
                request, "term_edit.html", 400, t=t, error=str(e),
                f=changes | {"change_reason": change_reason},
            )  # fmt: skip
        return RedirectResponse(f"/terms/{term_id}", status_code=303)

    @app.post("/terms/{term_id}/relations")
    def term_relate(
        db: Db,
        term_id: str,
        relation_type: Annotated[str, Form()] = "",
        other: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        term = db.get(Term, term_id)
        if term is None:
            raise NotFound("用語が見つからない")
        if relation_type not in RELATION_TYPES:
            raise ValidationFailed("関係の種類を選んでください")
        proposals.relate_manually(
            db, from_headword=term.headword, to_headword=other, relation_type=relation_type
        )
        db.commit()
        return RedirectResponse(f"/terms/{term_id}", status_code=303)

    @app.get("/export.csv")
    def export_csv(db: Db) -> Response:
        # BOM 付き UTF-8。社用PCの Excel でダブルクリックしても化けないように
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(queries.EXPORT_HEADER)
        writer.writerows(queries.export_rows(db))
        stamp = datetime.now(JST).strftime("%Y%m%d")
        return Response(
            "\ufeff" + buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="glossary-{stamp}.csv"'},
        )

    @app.get("/history/{target_type}/{target_id}", response_class=HTMLResponse)
    def history(request: Request, db: Db, target_type: str, target_id: str) -> HTMLResponse:
        if target_type not in ("term", "sense"):
            raise NotFound("履歴の対象は term か sense")
        entries = queries.history(db, target_type, target_id)
        owner = db.get(Term, target_id) if target_type == "term" else db.get(Sense, target_id)
        if owner is None:
            raise NotFound("対象が見つからない")
        return render(
            request, "history.html", entries=entries, target_type=target_type, owner=owner
        )

    return app
