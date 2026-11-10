# -*- coding: utf-8 -*-
"""Phase 1: 範囲切替コーパス（保管庫 Work_Vault とワークスペース）の収集と前処理。

v2（2026-11-10・Gate 1 是正後）。v1 からの変更点:
- M1: 未マスク本文ミラーを廃止。ディスクへ出すのは安全性検査通過後のマスク済み jsonl のみ
- M2: 今回専用のマスキング設定（%TEMP%・アプリの config は変更しない）
  ① 役割語と一緒に出る人名の keep を廃止（役割文脈の人名もマスク）
  ② URL・file://・UNC パスを <URL>/<PATH> としてマスク（protect で残さない）
  ③ thread_id / source_ref は元パスを含まない不透明ID（正規化パスの SHA-256 上位16桁・
     doc: 接頭辞・同一パスは同一ID・対応表は永続化しない）
- M4: 資料にメール用 Cleaner を適用しない（pipeline.py の設計に合わせる）
  「〜書きました」行や罫線で本文が打ち切られないようにする
- 7桁以上の連続数字の漏えいゲートは緩和せず維持
- 生成後、jsonl 全行を再読込して検証する（結果は件数のみ・値は出力しない）

処理の順序:
  1. ディレクトリ除外 → ファイル名除外 → 拡張子（.md/.txt）
  2. 読み込み（UTF-8 優先、失敗時 cp932）→ YAML フロントマター除去
  3. 45,000バイトでキャップ（UTF-8）→ マスキング（分割適用・マスキング漏れ例外は除外）
  4. 漏えいゲート: 7桁以上の連続数字・メール/電話/URL/パスの残存を含む文書を除外
  5. マスキング済み jsonl を出力し、全行検証の結果と件数だけを標準出力へ出す

個人情報そのもの（氏名・番号等）は出力しない。集計は件数のみ。
98_Pass 配下と認証情報ファイルはディレクトリ／ファイル名の除外で開かない。
"""
import hashlib
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

from glossary.preprocess.masking import Masker, MaskingLeak  # noqa: E402
from glossary.preprocess.pipeline import MaskedDocument, save_jsonl  # noqa: E402

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault"
WORKSPACE = r"C:\Users\ss80751\kohden-code-workspace"
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code"
MASK_CFG = os.path.join(TMP, "masking_rules_scope2.yaml")
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
URL_RESID = re.compile(r"https?://|file://", re.I)
UNC_RESID = re.compile(r"\\\\")

# ---------------------------------------------------------------- 今回専用マスキング設定

# アプリの config/masking_rules.yaml を基に、今回の収集用に上書きした設定。
# アプリ側のファイルは変更しない。この内容自体に個人情報は含まれない。
MASK_CONFIG_TEMPLATE = r"""# 今回専用のマスキング設定（v2・Gate 1 是正後）。
# アプリの config/masking_rules.yaml を基に collect_scope2.py が生成する。
# 変更点: protect 廃止（URL・file://・UNC を <URL>/<PATH> でマスク）、
#         役割語文脈の人名 keep（keep_before/keep_after）の廃止。
rules:
  - name: url
    type: regex
    pattern: '(?:https?|file)://[^\s<>"「」（）()]+'
    token: '<URL>'

  - name: unc_path
    type: regex
    pattern: '\\\\[^\s<>"「」（）()]+'
    token: '<PATH>'

  - name: email
    type: regex
    pattern: '[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}'
    token: '<EMAIL>'

  - name: serial
    type: regex
    pattern: '(?:(?:S/N|SN|シリアル(?:番号)?|製造番号)[:：\s]*[A-Za-z0-9][A-Za-z0-9\-]{3,})|\b(?=[A-Za-z0-9\-]*\d)(?=[A-Za-z0-9\-]*[A-Za-z])[A-Za-z0-9]{2,}(?:-[A-Za-z0-9]+){2,}\b'
    token: '<SERIAL>'

  - name: phone
    type: regex
    pattern: '(?<![\d\-])(?:\+81[\-\s]?|0)\d{1,4}[\-\s(（]?\d{1,4}[\-\s)）]?\d{3,4}(?![\d\-])'
    token: '<PHONE>'

  - name: money
    type: regex
    pattern: '[¥￥$]\s?[\d,，]+(?:\.\d+)?|[\d,，]+(?:\.\d+)?\s?(?:万|億|千)?円'
    token: '<MONEY>'

  - name: person_honorific
    type: regex
    pattern: '([一-龥々ァ-ヶー]{1,8}|(?<![ぁ-ん])[ぁ-ん]{2,4})(?=\s?(?:さん|さま|殿|くん|部長|課長|係長|主任|社長|様(?![々一-龥])|氏(?![一-龥])))'
    group: 1
    exclude: ['皆', 'みな', 'お客', '各位', 'お得意', 'ご担当者', '担当者', 'ご担当']
    exclude_suffix: ['仕', '同', '模', '多', '異', '一', '有', '左', '斯']
    token: '<PERSON>'

  - name: person_self_intro
    type: regex
    pattern: '\A[ 　]*([一-龥々ァ-ヶー]{1,8}(?:[ 　][一-龥々ぁ-んァ-ヶー]{1,8})?)(?=[ 　]*(?:です|と申します)[。．]?[ 　]*$)'
    group: 1
    flags: [MULTILINE]
    token: '<PERSON>'

  - name: person_pos
    type: pos
    pos: ['名詞', '固有名詞', '人名']
    token: '<PERSON>'
"""


def ensure_mask_config() -> str:
    """今回専用のマスキング設定を %TEMP% に生成してパスを返す（毎回上書き）。"""
    os.makedirs(TMP, exist_ok=True)
    with open(MASK_CFG, "w", encoding="utf-8", newline="\n") as f:
        f.write(MASK_CONFIG_TEMPLATE)
    return MASK_CFG


# ---------------------------------------------------------------- 収集と前処理


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


def opaque_id(path: str) -> str:
    """元パスを含まない安定した不透明ID。正規化パスの SHA-256 上位16桁・doc: 接頭辞。"""
    norm = os.path.normcase(os.path.abspath(path))
    return "doc:" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


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


def process_document(text: str, masker: Masker):
    """1文書を処理する。戻り値は (マスク後本文 or None, 除外理由 or None, meta)。

    Cleaner は適用しない（M4）。meta は capped / chars / counts / long_lines_dropped。
    """
    body, capped = cap_bytes(text)
    meta = {"capped": capped, "chars": len(body), "counts": Counter(),
            "long_lines_dropped": 0}
    if not body.strip():
        return None, "empty_after_cap", meta
    try:
        masked, counts, dropped = mask_chunked(masker, body)
    except MaskingLeak:
        return None, "masking_exception", meta
    meta["counts"] = counts
    meta["long_lines_dropped"] = dropped
    if DIGIT7.search(masked):
        return None, "digit7", meta
    if EMAIL_RESID.search(masked):
        return None, "residual_email", meta
    if PHONE_RESID.search(masked):
        return None, "residual_phone", meta
    if URL_RESID.search(masked) or UNC_RESID.search(masked):
        return None, "residual_url_or_path", meta
    return masked, None, meta


def verify_jsonl(path: str) -> dict:
    """生成後の jsonl 全行を検証する。値は出力せず、件数とbooleanのみを返す。"""
    res = Counter()
    seen: set[str] = set()
    schema_ok = True
    id_re = re.compile(r"\Adoc:[0-9a-f]{16}\Z")
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            res["rows"] += 1
            if set(r.keys()) != {"thread_id", "occurred_at", "source_ref", "text"}:
                schema_ok = False
            t = r.get("text", "")
            if not isinstance(t, str) or not t.strip():
                res["empty_text"] += 1
            ref = r.get("source_ref", "")
            if ref in seen:
                res["dup_source_ref"] += 1
            seen.add(ref)
            if not id_re.match(str(r.get("thread_id", ""))) or not id_re.match(ref):
                res["bad_id_format"] += 1
            if DIGIT7.search(t):
                res["digit7"] += 1
            if EMAIL_RESID.search(t):
                res["email"] += 1
            if PHONE_RESID.search(t):
                res["phone"] += 1
            if URL_RESID.search(t):
                res["url"] += 1
            if UNC_RESID.search(t):
                res["unc_path"] += 1
    res["schema_ok"] = int(schema_ok)
    res["unique_source_ref"] = len(seen)
    return dict(res)


def main() -> None:
    masker = Masker.from_yaml(Path(ensure_mask_config()))

    stats = {
        "version": "v2",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sources": {},
        "mask_counts": {},
        "total_masked_docs": 0,
    }
    mask_counts: Counter[str] = Counter()
    docs: list[MaskedDocument] = []
    gate_totals: Counter[str] = Counter()
    chars_total = 0
    long_line_dropped = 0

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
            masked, reason, meta = process_document(text, masker)
            if meta["capped"]:
                st["capped"] += 1
            chars_total += meta["chars"]
            long_line_dropped += meta["long_lines_dropped"]
            if reason is not None:
                st[f"gate_{reason}"] += 1
                gate_totals[reason] += 1
                continue
            mask_counts.update(meta["counts"])
            oid = opaque_id(full)
            docs.append(MaskedDocument(
                thread_id=oid,
                occurred_at=datetime.fromtimestamp(os.path.getmtime(full), tz=timezone.utc),
                source_ref=oid,
                text=masked,
            ))
            st["masked"] += 1
        stats["sources"][source] = dict(st)

    save_jsonl(docs, Path(OUT_JSONL))
    stats["mask_counts"] = dict(sorted(mask_counts.items()))
    stats["total_masked_docs"] = len(docs)
    stats["leak_gate"] = dict(gate_totals)
    stats["corpus"] = {"chars_after_cap": chars_total,
                       "long_lines_dropped": long_line_dropped}
    stats["outputs"] = {"jsonl": OUT_JSONL}
    stats["verification"] = verify_jsonl(OUT_JSONL)
    with open(STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # 標準出力は件数のみ（本文・氏名・番号は出さない）
    for source in ("vault", "workspace"):
        print(f"[{source}] {stats['sources'][source]}")
    print(f"masked docs: {len(docs)}")
    print(f"mask counts: {dict(sorted(mask_counts.items()))}")
    print(f"leak gate: {stats['leak_gate']}")
    print(f"corpus: {stats['corpus']}")
    print(f"verification: {stats['verification']}")
    print(f"jsonl: {OUT_JSONL}")


if __name__ == "__main__":
    main()
