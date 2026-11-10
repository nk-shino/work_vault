# -*- coding: utf-8 -*-
"""件数のみの診断スクリプト（本文・語は出力しない）。前処理統計メモ v2 の集計根拠。

1. recon 実績（vault 715 / workspace 470）との差分がどのディレクトリ除外ルール由来か
2. 除外ディレクトリ配下の件数内訳（data 配下は相対パスの構成要素で判定する・修正済み）
3. 7桁以上の数字を含む文書の内訳（YYYYMMDD 形式の日付のみか、他の番号か）
   （v2 は Cleaner を適用しないため、キャップ後に直接マスキングして判定する）

実行: glossary_venv の python で PYTHONIOENCODING=utf-8 を付けて実行する。
collect_scope2.py と同じディレクトリに置くか、sys.path に追加して実行する。
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect_scope2 as cs  # noqa: E402
from glossary.preprocess.masking import Masker, MaskingLeak  # noqa: E402
from pathlib import Path  # noqa: E402

# ---- 1. ディレクトリ除外ルール別の件数 ----
CORE = {"98_pass", ".obsidian", ".git", ".venv", "node_modules"}  # recon 相当の最小除外


def count_with(source_root, ex_dirs):
    n = 0
    for dp, dns, fns in os.walk(source_root):
        dns[:] = sorted(d for d in dns if d.lower() not in ex_dirs)
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in (".md", ".txt"):
                n += 1
    return n


for source, root in (("vault", cs.VAULT), ("workspace", cs.WORKSPACE)):
    core = count_with(root, CORE)
    mine = count_with(root, cs.EXCLUDE_DIRS[source])
    print(f"[{source}] recon相当(最小除外)={core}  今回の実装={mine}")

# ---- 2. 除外ディレクトリ配下の内訳（相対パスの構成要素で判定・data の多階層対応） ----


def count_under_component(root, comp, pruned):
    n = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d.lower() not in pruned)
        rel = os.path.relpath(dp, root).lower().split(os.sep)
        if comp in rel:
            n += sum(1 for fn in fns if os.path.splitext(fn)[1].lower() in (".md", ".txt"))
    return n


ALL_PRUNED = cs.EXCLUDE_DIRS["vault"] | cs.EXCLUDE_DIRS["workspace"] - {"data"}
for comp in ("data", ".venv", "98_pass"):
    v = count_under_component(cs.VAULT, comp, ALL_PRUNED - {comp})
    w = count_under_component(cs.WORKSPACE, comp, ALL_PRUNED - {comp})
    print(f"{comp}配下: vault={v} workspace={w}")

# ---- 3. 7桁数字の内訳（マスク済みテキストで判定・Cleaner なし） ----
masker = Masker.from_yaml(Path(cs.ensure_mask_config()))
DATE_LIKE = re.compile(r"(?:19|20)\d{6}")

cls = Counter()
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
        try:
            masked, _counts, _dropped = cs.mask_chunked(masker, cs.cap_bytes(text)[0])
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

print(f"mask判定対象: {total}  7桁を含む文書の内訳: {dict(cls)}")
