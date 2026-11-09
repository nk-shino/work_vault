# -*- coding: utf-8 -*-
"""件数のみの診断スクリプト（本文・語は出力しない）。前処理統計メモの集計根拠。
1. recon 実績（vault 715 / workspace 470）との差分がどのディレクトリ除外ルール由来か
2. 7桁以上の数字を含む文書の内訳（YYYYMMDD 形式の日付のみか、他の番号か）
3. クリーニングで本文が大きく削られた文書の有無

実行: glossary_venv の python で PYTHONIOENCODING=utf-8 を付けて実行する。
collect_scope2.py と同じディレクトリに置くか、sys.path に追加して実行する。
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect_scope2 as cs  # noqa: E402
from glossary.preprocess.cleaner import Cleaner  # noqa: E402
from glossary.preprocess.masking import Masker, MaskingLeak  # noqa: E402
from pathlib import Path  # noqa: E402

# ---- 1. ディレクトリ除外ルール別の件数 ----
CORE = {"98_pass", ".obsidian", ".git", ".venv", "node_modules"}  # recon 相当の最小除外


def count_with(source_root, source, ex_dirs, extra_subpath=()):
    n = 0
    for dp, dns, fns in os.walk(source_root):
        dns[:] = sorted(d for d in dns if d.lower() not in ex_dirs)
        rel_dir = os.path.relpath(dp, source_root).replace(os.sep, "/").lower()
        if extra_subpath and any(rel_dir == s or rel_dir.startswith(s + "/") for s in extra_subpath):
            continue
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in (".md", ".txt"):
                n += 1
    return n


for source, root in (("vault", cs.VAULT), ("workspace", cs.WORKSPACE)):
    core = count_with(root, source, CORE)
    with_data = count_with(root, source, CORE | {"data"})
    sub = cs.WS_EXCLUDE_SUBPATH if source == "workspace" else ()
    with_logs = count_with(root, source, CORE | {"data"}, sub)
    mine = count_with(root, source, cs.EXCLUDE_DIRS[source],
                      cs.WS_EXCLUDE_SUBPATH if source == "workspace" else ())
    print(f"[{source}] recon相当(最小除外)={core}  -data配下={with_data}  -scripts/logs={with_logs}  今回の実装={mine}")

# data 配下の内訳（参考）
def count_under_named(root, dirname):
    n = 0
    for dp, dns, fns in os.walk(root):
        if os.path.basename(dp).lower() == dirname:
            for fn in fns:
                if os.path.splitext(fn)[1].lower() in (".md", ".txt"):
                    n += 1
        dns[:] = [d for d in dns if d.lower() != dirname]
    return n

print(f"data配下(vault)={count_under_named(cs.VAULT, 'data')} data配下(workspace)={count_under_named(cs.WORKSPACE, 'data')}")

# ---- 2/3. 7桁数字の内訳とクリーニングの削られ幅（マスク済みテキストで判定） ----
cleaner = Cleaner.from_yaml(Path(cs.APP) / "config" / "cleaning_rules.yaml")
masker = Masker.from_yaml(Path(cs.APP) / "config" / "masking_rules.yaml")
DATE_LIKE = re.compile(r"(?:19|20)\d{6}")

cls = Counter()
severe_cut = 0
total = 0
for source, root in (("vault", cs.VAULT), ("workspace", cs.WORKSPACE)):
    for full, rel in cs.iter_files(root, source):
        if cs.name_excluded(os.path.basename(full)):
            continue
        try:
            text, err = cs.read_text(full)
        except OSError:
            continue
        if err:
            continue
        text = cs.FRONT.sub("", text)
        if not text.strip():
            continue
        text, _ = cs.cap_bytes(text)
        cleaned = cleaner.clean(text)
        if len(cleaned) < len(text) * 0.5:
            severe_cut += 1
        if not cleaned.strip():
            continue
        try:
            masked, _, _ = cs.mask_chunked(masker, cleaned)
        except MaskingLeak:
            continue
        total += 1
        runs = re.findall(r"\d{7,}", masked)
        if not runs:
            continue
        if all(DATE_LIKE.fullmatch(r) for r in runs):
            cls[f"{source}:日付形式のみ"] += 1
        elif any(DATE_LIKE.fullmatch(r) for r in runs):
            cls[f"{source}:日付を含む混合"] += 1
        else:
            cls[f"{source}:日付以外の番号"] += 1

print(f"mask+gate判定対象: {total}  7桁を含む文書の内訳: {dict(cls)}")
print(f"クリーニングで半分以下に削られた文書: {severe_cut}")
