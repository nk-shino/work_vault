"""開発用コマンドの入口。make の代わり。

社用PCに make や Docker がある保証は無く、PowerShell 5.1 は BOM なし UTF-8 の .ps1 を
文字化けさせるので、Python 1本で回す。

    python tasks.py                  引数なし：初回は setup、そのあと起動してブラウザを開く（VS Code の実行ボタン用）
    python tasks.py setup            仮想環境を作り、依存を入れ、DB を最新にする
    python tasks.py setup --wheelhouse DIR   ネットに出られないPC向け。DIR の wheel だけで入れる
    python tasks.py wheelhouse DIR [--python-version 3.11]  ネットに出られるPCで wheel を集める
    python tasks.py preprocess       取得 → 除去 → マスキング（data/work/masked.jsonl）
    python tasks.py extract          候補語・共起ペアの CSV（data/out/）
    python tasks.py propose          モックLLMで提案を作り、提案キューへ積む
    python tasks.py import DIR [--limit N]  DIR 以下のメール・資料から候補を取り込む（上の3つをまとめて）
    python tasks.py revise [--limit N]  「修正が必要」の評価が付いた定義の改稿案を LLM に作らせ、提案キューへ積む
    python tasks.py demo             fixtures で上の3つを通し、一部を採用してデモ用 DB を作る
    python tasks.py serve [--db FILE] [--open]  http://127.0.0.1:8000 で起動（--open でブラウザも開く）
    python tasks.py test | lint | typecheck | check（3つまとめて）
    python tasks.py evaluate DIR     人手ラベル CSV から評価指標を出す
    python tasks.py fixtures         架空メール50通を作り直す
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
# 子プロセスの入出力は UTF-8 に固定する。社用PCの既定（cp932）で日本語が化けないように
CHILD_ENV = os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
FAR_PAST = datetime(1900, 1, 1)
FAR_FUTURE = datetime(2999, 1, 1)


def run(*cmd: str | Path) -> None:
    print("$", " ".join(str(c) for c in cmd), flush=True)
    code = subprocess.call([str(c) for c in cmd], cwd=ROOT, env=CHILD_ENV)
    if code:
        sys.exit(code)


def in_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV.resolve()


def reexec_in_venv() -> None:
    if in_venv():
        return
    if not VENV_PY.exists():
        sys.exit("仮想環境がありません。先に `python tasks.py setup` を実行してください")
    sys.exit(subprocess.call([str(VENV_PY), __file__, *sys.argv[1:]], cwd=ROOT, env=CHILD_ENV))


# ---- 環境づくり（仮想環境の外で動く） ----


def cmd_setup(args: argparse.Namespace) -> None:
    warn_synced_folder()
    # 社用PCの python が古い場合に、分かる言葉で止めるための確認（pyproject の下限とは別に要る）
    if sys.version_info < (3, 11):  # noqa: UP036
        sys.exit(f"Python 3.11 以上が必要です（今は {sys.version.split()[0]}）")
    if not VENV_PY.exists():
        run(sys.executable, "-m", "venv", VENV)
    pip = [VENV_PY, "-m", "pip", "install", "--disable-pip-version-check"]
    if args.wheelhouse:
        pip += ["--no-index", "--find-links", Path(args.wheelhouse).resolve()]
    run(*pip, "-e", ".[dev]")
    run(VENV_PY, __file__, "migrate")


def cmd_wheelhouse(args: argparse.Namespace) -> None:
    # 社用PCと同じ Python の版・Windows 64bit 向けの wheel を集める
    out = Path(args.dir).resolve()
    run(
        sys.executable, "-m", "pip", "download", "--dest", out,
        "--only-binary=:all:", "--platform", "win_amd64",
        "--python-version", args.python_version,
        "setuptools>=68", "wheel", "-r", ROOT / "requirements-lock.txt",
    )  # fmt: skip
    print(f"{out} を社用PCへ運び、`python tasks.py setup --wheelhouse {out.name}` を実行")


# ---- ここから下は仮想環境の中で動く ----


def _settings():  # type: ignore[no-untyped-def]
    sys.path.insert(0, str(ROOT / "src"))
    from glossary.settings import load_settings

    return load_settings()


def _migrate(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")


def _paths(s):  # type: ignore[no-untyped-def]
    return s.data_dir / "work" / "masked.jsonl", s.data_dir / "out"


def cmd_preprocess(_args: argparse.Namespace) -> None:
    s = _settings()
    from glossary.factory import make_source
    from glossary.preprocess.cleaner import Cleaner
    from glossary.preprocess.masking import Masker
    from glossary.preprocess.pipeline import preprocess, save_jsonl

    docs, counts = preprocess(
        make_source(s),
        Cleaner.from_yaml(s.config_dir / "cleaning_rules.yaml"),
        Masker.from_yaml(s.config_dir / "masking_rules.yaml"),
        FAR_PAST,
        FAR_FUTURE,
    )
    masked, _ = _paths(s)
    save_jsonl(docs, masked)
    print(f"{len(docs)} 通を前処理 → {masked}")
    print("マスキング件数:", dict(sorted(counts.items())))


def cmd_extract(_args: argparse.Namespace) -> None:
    s = _settings()
    from glossary.preprocess.pipeline import load_jsonl
    from glossary.stats.candidates import load_stopwords
    from glossary.stats.extract import analyze, write_candidates, write_pairs

    masked, out = _paths(s)
    rows, pairs = analyze(load_jsonl(masked), load_stopwords(s.config_dir / "stopwords.txt"))
    write_candidates(rows, out / "candidates.csv")
    write_pairs(pairs, out / "cooccurrence.csv")
    print(f"候補語 {len(rows)} 件 / 共起ペア {len(pairs)} 件 → {out}")
    for r in rows[:10]:
        print(f"  {r.surface}\tfreq={r.freq}\tdf={r.df}\ttfidf={r.tfidf}")


def cmd_propose(_args: argparse.Namespace) -> None:
    s = _settings()
    _migrate(s.database_url)
    from glossary.db.session import make_engine, make_session_factory
    from glossary.factory import make_llm
    from glossary.preprocess.pipeline import load_jsonl
    from glossary.propose import AdoptionRules, propose_and_adopt, propose_relations
    from glossary.stats.extract import read_csv

    masked, out = _paths(s)
    cands = read_csv(out / "candidates.csv")
    pairs = read_csv(out / "cooccurrence.csv")
    from glossary.preprocess.masking import Masker

    rules = AdoptionRules.from_yaml(s.config_dir / "adoption.yaml")
    send_masker = Masker.from_yaml(s.config_dir / "llm_send_masking.yaml")
    factory = make_session_factory(make_engine(s.database_url))
    with factory() as db:
        limit = getattr(_args, "limit", 20)
        o = propose_and_adopt(
            db, make_llm(s), cands, load_jsonl(masked), limit=limit, rules=rules,
            send_masker=send_masker,
        )  # fmt: skip
        heads = {c["surface"] for c in cands[:limit]}
        m = propose_relations(db, pairs, heads)
        db.commit()
    print(
        f"新しい語 {o.proposed} 件（自動採用 {o.auto_adopted} / 保留 {o.held}）"
        f" / 登録済みの語へ用例 {o.evidence_added} 件を追加 / 関係の提案 {m} 件"
    )
    print(f"（{s.database_url}）")


def cmd_import(args: argparse.Namespace) -> None:
    folder = Path(args.dir).resolve()
    if not folder.is_dir():
        sys.exit(f"フォルダが見つかりません: {folder}")
    os.environ["EXPORT_DIR"] = str(folder)
    cmd_preprocess(args)
    cmd_extract(args)
    cmd_propose(args)
    print("ブラウザの「提案キュー」で確認してください（python tasks.py serve --open）")


def cmd_revise(args: argparse.Namespace) -> None:
    s = _settings()
    _migrate(s.database_url)
    from glossary.db.session import make_engine, make_session_factory
    from glossary.factory import make_llm
    from glossary.preprocess.masking import Masker
    from glossary.propose import revise_flagged

    send_masker = Masker.from_yaml(s.config_dir / "llm_send_masking.yaml")
    factory = make_session_factory(make_engine(s.database_url))
    with factory() as db:
        made = revise_flagged(db, make_llm(s), limit=args.limit, send_masker=send_masker)
        db.commit()
    print(f"改稿案 {made} 件を提案キューに積みました")
    print(f"（{s.database_url}）")
    print("ブラウザの「提案キュー」で確認してください（python tasks.py serve --open）")


def cmd_demo(_args: argparse.Namespace) -> None:
    demo_dir = ROOT / "data" / "demo"
    db_file = demo_dir / "glossary-demo.db"
    if db_file.exists():
        # 前回のデモ DB は消さずに脇へ退ける
        db_file.rename(db_file.with_suffix(f".{datetime.now():%Y%m%d%H%M%S}.bak"))
    os.environ.update(
        SOURCE_BACKEND="export",
        LLM_BACKEND="mock",
        EXPORT_DIR=str(ROOT / "fixtures" / "mails"),
        GLOSSARY_DATA_DIR=str(demo_dir),
        DATABASE_URL=f"sqlite:///{db_file.as_posix()}",
    )
    ns = argparse.Namespace()
    cmd_preprocess(ns)
    cmd_extract(ns)
    cmd_propose(ns)
    _demo_review(os.environ["DATABASE_URL"])
    print("\nレビューUIを開くには:")
    print("  python tasks.py serve --db data/demo/glossary-demo.db")


def _demo_review(url: str) -> None:
    """人がレビューした後の画面も見られるよう、提案の一部を「デモ」名義で処理する。"""
    from sqlalchemy import select

    from glossary.db.models import Proposal, Sense, Term
    from glossary.db.session import make_engine, make_session_factory
    from glossary.domain import evaluations, proposals, review

    factory = make_session_factory(make_engine(url))
    with factory() as db:
        pending = db.scalars(
            select(Proposal).where(Proposal.status == "pending").order_by(Proposal.score.desc())
        ).all()
        # fixtures の架空用語は上位13件にちょうど収まる（竜舎はどのメールにも出るので13位）
        senses = [p for p in pending if p.proposal_type == "sense"][:13]
        for p in senses:
            proposals.accept(db, p.id, reviewer="デモ")
        # ここで確定させる。下の関係で失敗したときの rollback に、語義の採用まで巻き込まないように
        db.commit()
        for p in [p for p in pending if p.proposal_type == "relation"][:6]:
            try:
                proposals.accept(db, p.id, reviewer="デモ")
                db.commit()
            except Exception as e:  # 両端の語義が未採用のものは飛ばす
                print("  関係の採用を見送り:", e)
                db.rollback()
        # 同音異表記は統計から出す手段が無いので、人が気付いて足した想定の関係として入れる
        heads = set(db.scalars(select(Term.headword)).all())
        if {"竜舎", "竜車"} <= heads:
            proposals.add_proposal(
                db, proposal_type="relation",
                payload={"from_headword": "竜舎", "to_headword": "竜車",
                         "relation_type": "confused_with", "method": "human", "score": None},
                model_name="human", prompt_version="manual", score=None,
            )  # fmt: skip
            db.flush()
            last = db.scalars(select(Proposal).order_by(Proposal.created_at.desc())).first()
            assert last is not None
            proposals.accept(db, last.id, reviewer="デモ", reason="読みが同じで取り違えが起きたため")
        # 係争中の表示を確かめるため、1件だけ disputed にする
        first = db.scalars(select(Sense).order_by(Sense.created_at)).first()
        if first is not None:
            review.edit_sense(
                db, first.id, expected_revision=first.revision_number,
                changes={"status": "disputed"}, editor_name="デモ",
                change_reason="部署によって解釈が違うという指摘があった（デモ）",
            )  # fmt: skip
        # 「見直し」の画面に中身が出るよう、2件目に評価を付けておく
        second = db.scalars(select(Sense).order_by(Sense.created_at).offset(1)).first()
        if second is not None:
            evaluations.evaluate(
                db, second.id, seen_revision=second.revision_number, accuracy="needs_fix",
                comment="用例と定義が合っていない（デモ）",
            )  # fmt: skip
        db.commit()
    print(f"デモ用に語義 {len(senses)} 件を採用しました")


def cmd_serve(args: argparse.Namespace) -> None:
    s = _settings()
    url = f"sqlite:///{Path(args.db).resolve().as_posix()}" if args.db else s.database_url
    _migrate(url)
    import uvicorn

    from glossary.web.app import create_app

    if args.open:
        import threading
        import webbrowser

        # 起動を待ってから開く。先に開くと「接続できません」の画面が出る
        threading.Timer(2.0, webbrowser.open, [f"http://127.0.0.1:{args.port}/"]).start()
    # 社内ネットワークへは公開しない。自分の PC からだけ開ける
    uvicorn.run(create_app(url), host="127.0.0.1", port=args.port)


def cmd_migrate(_args: argparse.Namespace) -> None:
    _migrate(_settings().database_url)


def cmd_test(_args: argparse.Namespace) -> None:
    run(sys.executable, "-m", "pytest")


def cmd_lint(_args: argparse.Namespace) -> None:
    run(sys.executable, "-m", "ruff", "check", "src", "tests", "tasks.py", "scripts", "migrations")


def cmd_typecheck(_args: argparse.Namespace) -> None:
    run(sys.executable, "-m", "mypy")


def cmd_check(args: argparse.Namespace) -> None:
    cmd_lint(args)
    cmd_typecheck(args)
    cmd_test(args)


def cmd_evaluate(args: argparse.Namespace) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from glossary.evaluation.metrics import evaluate_dir

    print(json.dumps(evaluate_dir(Path(args.dir)), ensure_ascii=False, indent=2))


def cmd_fixtures(_args: argparse.Namespace) -> None:
    run(sys.executable, ROOT / "scripts" / "make_fixtures.py")


OUTSIDE_VENV = {"setup", "wheelhouse", "start"}


def warn_synced_folder() -> None:
    # OneDrive や Google Drive の同期フォルダに仮想環境（数千ファイル）を作ると、
    # 同期がファイルを掴んで pip が途中で失敗したり、同期の容量を食ったりする
    synced = ("onedrive", "google drive", "googledrive", "dropbox")
    if any(k in str(ROOT).lower() for k in synced):
        print("注意：このフォルダは同期フォルダの中にあります。")
        print("      仮想環境の作成や同期で失敗しやすいので、C:\\work のような同期されない場所へ")
        print("      フォルダごと移してから実行するのがおすすめです。このまま続けます。\n")


def cmd_start(args: argparse.Namespace) -> None:
    """引数なしで実行されたときの入口。初めてなら準備してから、起動してブラウザを開く。"""
    warn_synced_folder()
    if not VENV_PY.exists():
        print("初回の準備をします（数分かかります）")
        cmd_setup(argparse.Namespace(wheelhouse=args.wheelhouse))
    code = subprocess.call(
        [str(VENV_PY), __file__, "serve", "--open"], cwd=ROOT, env=CHILD_ENV
    )
    sys.exit(code)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # 表示できない文字で止まらないように
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("start").add_argument("--wheelhouse")
    sub.add_parser("setup").add_argument("--wheelhouse")
    wh = sub.add_parser("wheelhouse")
    wh.add_argument("dir")
    wh.add_argument("--python-version", default="3.11")
    for name in ("preprocess", "extract", "propose", "demo", "migrate", "test", "lint",
                 "typecheck", "check", "fixtures"):  # fmt: skip
        sub.add_parser(name)
    rev = sub.add_parser("revise")
    rev.add_argument("--limit", type=int, default=5, help="改稿案を作る語義の数")
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--db", help="SQLite ファイル（例: data/demo/glossary-demo.db）")
    serve.add_argument("--open", action="store_true", help="起動後にブラウザを開く")
    imp = sub.add_parser("import")
    imp.add_argument("dir")
    imp.add_argument("--limit", type=int, default=30, help="語義の提案を作る候補語の数")
    sub.add_parser("evaluate").add_argument("dir")
    args = p.parse_args()
    if args.cmd is None:
        # 引数なし（VS Code の実行ボタンやダブルクリック）は、使い方の表示で止めずに起動まで進める
        args = p.parse_args(["start"])
    if args.cmd not in OUTSIDE_VENV:
        reexec_in_venv()
    globals()[f"cmd_{args.cmd}"](args)


if __name__ == "__main__":
    main()
