# -*- coding: utf-8 -*-
"""Phase 1: 範囲切替コーパス（保管庫 Work_Vault とワークスペース）の収集と前処理。

前回（デスクトップ data フォルダ）と同じパイプラインを再利用する。
- 抽出・キャップ: 本スクリプト（既存スクリプトは改変しない）
- クリーニング: glossary.preprocess.cleaner.Cleaner（config/cleaning_rules.yaml）
- マスキング: glossary.preprocess.masking.Masker（config/masking_rules.yaml）
  40,000バイト単位の分割は run_import.py と同じ方式（SudachiPy の入力上限対策）

処理の順序:
  1. ディレクトリ除外 → ファイル名除外 → 拡張子（.md/.txt）
  2. 読み込み（UTF-8 優先、失敗時 cp932）→ YAML フロントマター除去
  3. 45,000バイトでキャップ（UTF-8）→ ミラーへ書き出し
  4. クリーニング → マスキング（分割適用・マスキング漏れ例外は除外）
  5. 漏えいゲート: 7桁以上の連続数字を含む文書を除外。
     メールアドレス・電話番号様の残存も走査して件数を記録する（0件を確認）
  6. マスキング済み jsonl を出力し、件数だけを集計 JSON と標準出力へ出す

個人情報そのもの（氏名・番号等）は出力しない。集計は件数のみ。
98_Pass 配下と認証情報ファイルはディレクトリ／ファイル名の除外で開かない。
"""
import io
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

APP = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\06_Tools\用語集アプリ"
sys.path.insert(0, os.path.join(APP, "src"))
os.chdir(APP)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from glossary.preprocess.cleaner import Cleaner
from glossary.preprocess.masking import Masker, MaskingLeak
from glossary.preprocess.pipeline import MaskedDocument, save_jsonl

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault"
WORKSPACE = r"C:\Users\ss80751\kohden-code-workspace"
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code"
MIRROR = os.path.join(TMP, "glossary_import_scope2")
OUT_JSONL = os.path.join(TMP, "masked_scope2.jsonl")
STATS_JSON = os.path.join(TMP, "stats_scope2.json")

# 収集元ごとのディレクトリ除外（小文字で比較）
EXCLUDE_DIRS = {
    "vault": {"98_pass", ".obsidian", ".git", "data", ".venv", "node_modules"},
    "workspace": {"_archive", "workvault-sync", ".git", "node_modules", ".venv",
                  ".slim", "data", "20261106_用語集データ追加3"},
}
# ワークスペースのみ: scripts/logs 配下
WS_EXCLUDE_SUBPATH = ("scripts\\logs", "scripts/logs")

# ファイル名の部分一致除外（大小無視）
NAME_EXCLUDES = [
    "名簿", "診断書", "通院", "給与", "賞与", "保険", "控除", "源泉", "葬儀",
    "香典", "餞別", "面談", "経歴", "勤怠", "申出", "誓約", "委任", "個人情報",
    "パスワード", "認証", "秘匿", ".env", "id_rsa", ".pem", ".key",
]

MAX_BYTES = 45000      # 1文書の上限（UTF-8 バイト）
CHUNK_BYTES = 40000    # マスキングの分割単位（run_import.py と同じ）

FRONT = re.compile(r"\A---\r?\n.*?\r?\n---[ \t]*\r?\n", re.S)
DIGIT7 = re.compile(r"\d{7,}")
EMAIL_RESID = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RESID = re.compile(
    r"(?<![\d\-])(?:\+81[\-\s]?|0)\d{1,4}[\-\s(（]?\d{1,4}[\-\s)）]?\d{3,4}(?![\d\-])"
)


def iter_files(root: str, source: str):
    """ディレクトリ除外と拡張子で絞った (絶対パス, 相対パス) を返す。"""
    ex = EXCLUDE_DIRS[source]
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d.lower() not in ex)
        rel_dir = os.path.relpath(dp, root).replace(os.sep, "/").lower()
        if source == "workspace" and any(rel_dir == s or rel_dir.startswith(s + "/")
                                         for s in WS_EXCLUDE_SUBPATH):
            continue
        for n in sorted(fns):
            if os.path.splitext(n)[1].lower() not in (".md", ".txt"):
                continue
            full = os.path.join(dp, n)
            yield full, os.path.relpath(full, root)


def name_excluded(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in NAME_EXCLUDES)


def read_text(path: str):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(enc), None
        except UnicodeDecodeError:
            continue
    return None, "decode"


def cap_bytes(text: str, limit: int = MAX_BYTES):
    b = text.encode("utf-8")
    if len(b) <= limit:
        return text, False
    return b[:limit].decode("utf-8", errors="ignore"), True


def mask_chunked(masker: Masker, body: str):
    """run_import.py と同じ分割方式。戻り値は (text, counts, 超長行の除外数)。"""
    if len(body.encode("utf-8")) <= CHUNK_BYTES:
        r = masker.mask(body)
        return r.text, r.counts, 0
    lines = body.splitlines(keepends=True)
    chunks, cur, dropped = [], "", 0
    for ln in lines:
        if len((cur + ln).encode("utf-8")) > CHUNK_BYTES and cur:
            chunks.append(cur)
            cur = ""
        if len(ln.encode("utf-8")) > CHUNK_BYTES:
            dropped += 1
            continue
        cur += ln
    if cur:
        chunks.append(cur)
    texts, total = [], Counter()
    for ch in chunks:
        r = masker.mask(ch)
        texts.append(r.text)
        total.update(r.counts)
    text = "\n".join(texts)
    masker.assert_clean(text)
    return text, total, dropped


def main() -> None:
    cleaner = Cleaner.from_yaml(Path(APP) / "config" / "cleaning_rules.yaml")
    masker = Masker.from_yaml(Path(APP) / "config" / "masking_rules.yaml")

    stats = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sources": {},
        "mask_counts": {},
        "total_masked_docs": 0,
    }
    mask_counts: Counter[str] = Counter()
    docs: list[MaskedDocument] = []
    residual_email = 0
    residual_phone = 0
    residual_docs = 0
    digit7_docs = 0
    masking_leak_docs = 0
    long_line_dropped = 0
    cleaned_chars_before = 0
    cleaned_chars_after = 0

    for source, root in (("vault", VAULT), ("workspace", WORKSPACE)):
        st = Counter()
        for full, rel in iter_files(root, source):
            st["dir_filtered"] += 1  # ディレクトリ除外後の収集対象（recon と比較する件数）
            if name_excluded(os.path.basename(full)):
                st["excluded_filename"] += 1
                continue
            try:
                text, err = read_text(full)
            except OSError:
                st["read_error"] += 1
                continue
            if err:
                st["decode_error"] += 1
                continue
            text = FRONT.sub("", text)
            if not text.strip():
                st["empty"] += 1
                continue
            text, capped = cap_bytes(text)
            if capped:
                st["capped"] += 1
            # ミラー（フロントマター除去・キャップ後）
            dst = os.path.join(MIRROR, source, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            # クリーニング → マスキング
            cleaned = cleaner.clean(text)
            if len(cleaned) < len(text):
                st["cleaned_shorter"] += 1
            cleaned_chars_before += len(text)
            cleaned_chars_after += len(cleaned)
            if not cleaned.strip():
                st["empty_after_clean"] += 1
                continue
            try:
                masked, counts, dropped = mask_chunked(masker, cleaned)
            except MaskingLeak:
                st["leak_masking_exception"] += 1
                masking_leak_docs += 1
                continue
            long_line_dropped += dropped
            # 漏えいゲート
            if DIGIT7.search(masked):
                st["leak_digit7"] += 1
                digit7_docs += 1
                continue
            e = len(EMAIL_RESID.findall(masked))
            p = len(PHONE_RESID.findall(masked))
            residual_email += e
            residual_phone += p
            if e or p:
                st["leak_residual"] += 1
                residual_docs += 1
                continue
            mask_counts.update(counts)
            rel_posix = rel.replace(os.sep, "/")
            docs.append(MaskedDocument(
                thread_id=f"{source}:{rel_posix}",
                occurred_at=datetime.fromtimestamp(os.path.getmtime(full), tz=timezone.utc),
                source_ref=f"{source}/{rel_posix}",
                text=masked,
            ))
            st["masked"] += 1
        stats["sources"][source] = dict(st)

    save_jsonl(docs, Path(OUT_JSONL))
    stats["mask_counts"] = dict(sorted(mask_counts.items()))
    stats["total_masked_docs"] = len(docs)
    stats["leak_gate"] = {
        "masking_exception_docs": masking_leak_docs,
        "digit7_docs": digit7_docs,
        "residual_email_occurrences": residual_email,
        "residual_phone_occurrences": residual_phone,
        "residual_docs": residual_docs,
    }
    stats["cleaning"] = {
        "chars_before": cleaned_chars_before,
        "chars_after": cleaned_chars_after,
        "long_lines_dropped": long_line_dropped,
    }
    stats["outputs"] = {"jsonl": OUT_JSONL, "mirror": MIRROR}
    with open(STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # 標準出力は件数のみ（本文・氏名・番号は出さない）
    for source in ("vault", "workspace"):
        print(f"[{source}] {stats['sources'][source]}")
    print(f"masked docs: {len(docs)}")
    print(f"mask counts: {dict(sorted(mask_counts.items()))}")
    print(f"leak gate: {stats['leak_gate']}")
    print(f"cleaning: {stats['cleaning']}")
    print(f"jsonl: {OUT_JSONL}")


if __name__ == "__main__":
    main()
