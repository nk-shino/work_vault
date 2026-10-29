"""開発用コマンドの入口。make の代わり。

    python tasks.py                  引数なし：初回は setup、そのあと起動してブラウザを開く
    python tasks.py setup            仮想環境を作り、依存を入れ、DB を最新にする
    python tasks.py analyze BOOK     ブックの VBA を解析して提案キューへ積む
    python tasks.py demo             fixtures で 解析→提案→一部受理 を通しデモ DB を作る
    python tasks.py serve [--db FILE] [--open]  http://127.0.0.1:8000 で起動
    python tasks.py test | lint | typecheck | check（3つまとめて）
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
CHILD_ENV = os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


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


def warn_synced_folder() -> None:
    synced = ("onedrive", "google drive", "googledrive", "dropbox")
    if any(k in str(ROOT).lower() for k in synced):
        print("注意：このフォルダは同期フォルダの中にあります。")
        print("      仮想環境の作成や同期で失敗しやすいので、C:\\work のような同期されない場所へ")
        print("      フォルダごと移してから実行するのがおすすめです。このまま続けます。\n")


def cmd_setup(args: argparse.Namespace) -> None:
    warn_synced_folder()
    if sys.version_info < (3, 11):  # noqa: UP036
        sys.exit(f"Python 3.11 以上が必要です（今は {sys.version.split()[0]}）")
    if not VENV_PY.exists():
        run(sys.executable, "-m", "venv", VENV)
    run(VENV_PY, "-m", "pip", "install", "--disable-pip-version-check", "-e", ".[dev]")
    run(VENV_PY, __file__, "migrate")


def _settings():  # type: ignore[no-untyped-def]
    sys.path.insert(0, str(ROOT / "src"))
    from vbaglossary.settings import load_settings

    return load_settings()


def _migrate(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    if url.startswith("sqlite:///"):
        Path(url[len("sqlite:///"):]).parent.mkdir(parents=True, exist_ok=True)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")


def cmd_migrate(_args: argparse.Namespace) -> None:
    _migrate(_settings().database_url)


def cmd_test(_args: argparse.Namespace) -> None:
    run(sys.executable, "-m", "pytest")


def cmd_lint(_args: argparse.Namespace) -> None:
    run(sys.executable, "-m", "ruff", "check", "src", "tests", "tasks.py", "migrations/env.py")


def cmd_typecheck(_args: argparse.Namespace) -> None:
    run(sys.executable, "-m", "mypy")


def cmd_check(args: argparse.Namespace) -> None:
    cmd_lint(args)
    cmd_typecheck(args)
    cmd_test(args)


def cmd_serve(args: argparse.Namespace) -> None:
    s = _settings()
    url = f"sqlite:///{Path(args.db).resolve().as_posix()}" if args.db else s.database_url
    _migrate(url)
    import uvicorn

    from vbaglossary.web.app import create_app

    if args.open:
        import threading
        import webbrowser

        threading.Timer(2.0, webbrowser.open, [f"http://127.0.0.1:{args.port}/"]).start()
    uvicorn.run(create_app(url), host="127.0.0.1", port=args.port)


def _analyze(url: str, source: Path) -> None:

    from vbaglossary.db.guards import register_guards
    from vbaglossary.db.session import make_engine, make_session_factory
    from vbaglossary.vba.analyzer import analyze

    register_guards()
    session = make_session_factory(make_engine(url))()
    result = analyze(session, source)
    session.close()
    print(f"ブック: {result.book_name} (sha {result.sha256[:12]})")
    print(
        f"モジュール {result.modules} / プロシージャ {result.procedures}"
        f"（新規 {result.new_procedures}・更新 {result.updated_procedures}）"
    )
    print(
        f"提案: 新規 {result.proposals_added}・差し替え {result.proposals_updated}"
        f"・保留 {result.proposals_held}"
    )
    for w in result.warnings:
        print(f"警告: {w}")
    print("ブラウザで確認: python tasks.py serve --open")


def cmd_analyze(args: argparse.Namespace) -> None:
    s = _settings()
    url = f"sqlite:///{Path(args.db).resolve().as_posix()}" if args.db else s.database_url
    _migrate(url)
    source = Path(args.source)
    if not source.exists():
        sys.exit(f"解析対象が見つからない: {source}")
    _analyze(url, source)


def cmd_demo(_args: argparse.Namespace) -> None:
    """fixtures で 解析→提案→一部受理→評価 まで通したデモ DB を作る。"""
    s = _settings()
    demo_db = Path(args_demo_db(s))
    if demo_db.exists():
        demo_db.unlink()
    url = f"sqlite:///{demo_db.resolve().as_posix()}"
    _migrate(url)

    from sqlalchemy import select

    from vbaglossary.db.guards import register_guards
    from vbaglossary.db.models import Proposal
    from vbaglossary.db.session import make_engine, make_session_factory
    from vbaglossary.domain import evaluations as ev
    from vbaglossary.domain import proposals as pr
    from vbaglossary.vba.analyzer import analyze

    register_guards()
    session = make_session_factory(make_engine(url))()
    result = analyze(session, ROOT / "fixtures" / "vba", book_name="demo_計画.xlsm")
    open_proposals = session.scalars(
        select(Proposal).where(Proposal.decided_at.is_(None), Proposal.state != "hold")
    ).all()
    for i, proposal in enumerate(open_proposals):
        if i % 3 == 2:
            pr.reject(session, proposal.id, reason="デモ用に見送り")
            continue
        sense = pr.accept(session, proposal.id, reason="デモ用に受理")
        if i % 3 == 0:
            ev.evaluate(session, sense.id, seen_version=sense.version, accuracy="needs_fix", usefulness="useful", reason="デモ用の見直し対象")
        else:
            ev.evaluate(session, sense.id, seen_version=sense.version, accuracy="correct", usefulness="useful")
    session.commit()
    session.close()
    print(f"デモ DB を作成: {demo_db}")
    print(f"解析結果: プロシージャ {result.procedures} / 提案 新規 {result.proposals_added}・保留 {result.proposals_held}")
    print("起動: python tasks.py serve --db " + str(demo_db) + " --open")


def args_demo_db(s) -> Path:  # type: ignore[no-untyped-def]
    return s.data_dir / "demo" / "glossary-demo.db"


def cmd_start(args: argparse.Namespace) -> None:
    warn_synced_folder()
    if not VENV_PY.exists():
        print("初回の準備をします（数分かかります）")
        cmd_setup(argparse.Namespace(wheelhouse=None))
    code = subprocess.call([str(VENV_PY), __file__, "serve", "--open"], cwd=ROOT, env=CHILD_ENV)
    sys.exit(code)


OUTSIDE_VENV = {"setup", "start"}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("start")
    sub.add_parser("setup")
    for name in ("migrate", "test", "lint", "typecheck", "check"):
        sub.add_parser(name)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--db", help="SQLite ファイル（例: data/demo/glossary-demo.db）")
    serve.add_argument("--open", action="store_true", help="起動後にブラウザを開く")
    an = sub.add_parser("analyze", help="ブック（.xlsm 等）またはフォルダ（.bas 群）を解析する")
    an.add_argument("source", help="解析対象のパス")
    an.add_argument("--db", help="SQLite ファイル（省略時は data/glossary.db）")
    sub.add_parser("demo", help="fixtures でデモ DB を作る")
    args = p.parse_args()
    if args.cmd is None:
        args = p.parse_args(["start"])
    if args.cmd not in OUTSIDE_VENV:
        reexec_in_venv()
    globals()[f"cmd_{args.cmd}"](args)


if __name__ == "__main__":
    main()
