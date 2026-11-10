# -*- coding: utf-8 -*-
"""単語データ作成: 専門性×文書分散の採点と、合格語の提案キューへの登録（パラメータ化版）。

v3（2026-11-10・Gate 1 再レビュー attempt 2 対応）。v2 からの変更点:
- R1: DBへ保存する用例（抜粋）にも安全性検査を適用する。
      snippet に用例検査を重ね、番号・メール・電話・URL・パスの残存と、
      役割・敬称の直前にマスクトークン以外の人名らしい並びがある抜粋を除外する。
      安全な用例が1つも無い候補は登録しない。除外理由は件数のみ記録（値は出力しない）。
- R2: DB登録は同一トランザクション内で flush 後に件数検証をしてから commit する
      （pending増分・総数増分・提案数＝登録対象数・auto_adopted==0・evidence_added==0）。
      不一致は rollback して非ゼロ終了する。
- minor: summary に入力ファイル内容の SHA-256 を記録し、登録実行時に同一内容か照合する
      （不一致なら中止する）。
- ストップワード補足: ドライラン上位200語の点検に基づき、汎用的な操作・管理語を
      EXTRA_STOPWORDS に追加（正規化キーの完全一致でのみ除外・dfやスコアの新下限は設けない）。

v2 からの変更点（Gate 1 attempt 1 是正）:
- M5: 入力jsonl・CSV出力先・summary出力先・トピック名を引数で指定。上書きは --force 必須。
      summary に入力識別情報（パスの SHA-256 上位16桁）と文書数を記録。
- M3: 採点・出力より前にプライバシー検査を実施。疑わしい語は値を一切出力せず理由別件数のみ。
- M2: --commit 時は DB 登録の前に抜粋・出典（文書本文）の安全性走査を行う。
- 採点式（ストップワード定義・スコア・合格ゲート・カテゴリ）の計算式自体は変更しない。

使い方:
    python run_score2.py --input <jsonl> --csv-out <csv> --summary-out <json> \
        --topic-name <名前>            # 採点とCSV・集計まで（DB は書き換えない）
    python run_score2.py ... --commit  # 合格語（重複除く）を proposals へ pending で登録
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

APP = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\06_Tools\用語集アプリ"

sys.path.insert(0, os.path.join(APP, "src"))
os.chdir(APP)
# 標準出力を UTF-8 にする。既に UTF-8 のときはラップしない（二重ラップで閉じるのを防ぐ）
if (sys.stdout.encoding or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)

# 実行条件を前回バッチに合わせて固定する（アプリ側のコード・設定ファイルは変えない）
os.environ["LLM_BACKEND"] = "mock"
os.environ["GLOSSARY_DATA_DIR"] = os.path.join(APP, "data")

from sqlalchemy import text  # noqa: E402

from glossary.db.session import make_engine, make_session_factory  # noqa: E402
from glossary.factory import make_llm  # noqa: E402
from glossary.preprocess.masking import Masker  # noqa: E402
from glossary.preprocess.pipeline import load_jsonl  # noqa: E402
import glossary.propose as _gp  # noqa: E402
from glossary.propose import SNIPPET_LEN, AdoptionRules, Outcome, propose_and_adopt  # noqa: E402
from glossary.settings import load_settings  # noqa: E402
from glossary.stats.candidates import extract, load_stopwords  # noqa: E402
from glossary.stats.normalize import normalize_key  # noqa: E402

# ---------------------------------------------------------------- 採点仕様の定数

# ストップワード（確定リスト・2026-11-06 指示）
TASK_STOPWORDS = [
    "場合", "左記", "随時", "シート", "確認", "作業", "対応", "内容", "対象", "実施",
    "完了", "依頼", "連絡", "資料", "本日", "会社", "担当", "参考", "以下", "上記",
    "該当", "追加", "変更", "削除", "更新", "問題", "当方", "先方", "今日", "明日",
    "結果", "目的", "方法", "状況", "必要", "関係",
]
# 補足の一般語（ドライランで上位に並んだ語から確定。除外の内訳はレポートに載せる）
EXTRA_STOPWORDS = [
    "作業内容", "作業時間", "作業連絡", "確認事項", "対応方法", "対応内容",
    "実施内容", "実施結果", "対象製品", "対象装置", "対象部品", "連絡先",
    "連絡事項", "依頼内容", "報告書", "説明書", "チェック", "サンプル",
    "コメント", "メール", "ファイル", "フォルダ", "データ", "システム",
    "プログラム", "場合分け", "次ページ", "前ページ", "本ページ", "同様",
    "本年", "昨年", "来年", "今月", "先月", "来月", "午前", "午後", "自分",
    "皆様", "お願い", "宛先", "件名", "備考", "タイトル", "番号",
    # 以下はドライラン（2026-11-06）の合格上位から追加した一般語
    "管理番号", "製造番号", "コード", "担当者", "メーカー", "生産部生産",
    "リスト", "スケジュール", "ページ", "シリアル", "ヶ月", "フリー",
    "従来通り", "サイズ", "配布先", "セット", "判断", "エラー", "株式会社",
    "特記事項", "トラブル", "テーブル", "消費税", "社内", "運用", "コピー",
    "ボタン", "フロー", "プロセス",
    # v3補足（2026-11-10・ドライラン上位200語の点検に基づく）。理由は統計メモに記載。
    # 完全一致でのみ除外するため、複合語（セットアップレポート等）には影響しない
    "ユーザー", "利用者", "成果物", "テスト", "ツール", "リンク", "レビュー",
    "ステータス", "ルール", "グループ", "リスク", "アクション", "ケース",
    "ステップ", "モード", "レベル", "タイミング", "時点", "現時点", "具体的",
    "スタート", "ノート", "サイト", "メモ", "レポート", "ファイル名",
    "保存先", "参照先", "移動先", "対象外",
    "未確認", "未確定", "未実施", "未承認", "未検証", "確認済み", "確定済み",
    "要確認", "反映済み",
    "実施者", "確認者", "承認者",
    "実施日", "実行前", "注意点", "実データ",
    "パスワード", "認証情報",
]

# カテゴリ判定（キーワード部分一致・上に書いたものほど優先）
CATEGORY_RULES = [
    ("装置・設備", ["印刷機", "マウンター", "リフロー", "ストッカー", "コンベア",
                    "AOI", "炉", "検査機", "拡大鏡"]),
    ("工程", ["実装", "印刷", "洗浄", "梱包", "出荷", "SMT"]),
    ("品質・検査", ["不具合", "不良", "是正", "検査", "点検", "校正"]),
    ("部品・材料", ["基板", "部品", "フィーダー", "ノズル", "メタルマスク",
                    "はんだ", "フラックス"]),
    ("帳票・管理", ["伝票", "台帳", "申請", "承認", "見積", "チェックシート", "手順書"]),
    ("教育・研修", ["教育", "訓練", "研修", "講習"]),
]

MIN_DF = 3          # 文書分散の下限
MIN_LEN = 2         # 文字数の下限
BONUS = {"model": 3.0, "compound": 2.0, "katakana": 2.0}  # 重複時は最大値

_KATA = re.compile(r"[ァ-ヶー]")
# 型番・コードパターン: 英字1-4文字＋数字3桁以上（例: UR-4501）
_MODEL = re.compile(r"^[A-Za-z]{1,4}-?[0-9]{3,}$")

# ---------------------------------------------------------------- プライバシー検査（M3・R1）

# 候補語の疑わしい形。これに当たった語は値を出力せず、理由別件数だけを記録する
_PRIVACY_PATTERNS = [
    ("電話番号形", re.compile(r"(?<!\d)0\d{1,4}-\d{1,4}-\d{3,4}(?!\d)")),
    ("郵便番号形", re.compile(r"(?<!\d)\d{3}-\d{4}(?!\d)")),
    ("番号列", re.compile(r"(?<!\d)\d{7,}(?!\d)")),
    ("区切り番号列", re.compile(r"(?<!\d)\d{4}-\d{4}-\d{4}(?!\d)")),
    ("メールアドレス形", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("URL残存", re.compile(r"https?://|file://", re.I)),
    ("パス残存", re.compile(r"\\\\")),
    ("マスクトークン", re.compile(r"<[A-Z]+>")),
]
# 敬称と結合した語（人名の可能性が高い）
_HONORIFIC_TAIL = re.compile(
    r"(?:さん|さま|様|殿|くん|ちゃん|氏|部長|課長|係長|主任|社長|会長|理事|監査役)$"
)

# 文書本文（出典）の疑わしい形
_DOC_PRIVACY_PATTERNS = [
    ("番号列", re.compile(r"(?<!\d)\d{7,}(?!\d)")),
    ("メールアドレス形", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("電話番号形", re.compile(r"(?<![\d\-])(?:\+81[\-\s]?|0)\d{1,4}[\-\s(（]?\d{1,4}[\-\s)）]?\d{3,4}(?![\d\-])")),
    ("URL残存", re.compile(r"https?://|file://", re.I)),
    ("パス残存", re.compile(r"\\\\")),
]

# R1: 用例（抜粋）の人名疑い。役割・敬称の直前に、マスクトークン（<PERSON> など・
# 「>」で終わる）以外の人名らしい並びが続く抜粋は疑わしいとみなす（保守的）。
# 直前が一般語（お客様・皆様・ユーザー様など）の敬称は除外しない
_ROLE_WORDS = r"(?:さん|さま|様|殿|くん|氏|部長|課長|係長|主任|社長|会長|理事)"
_NON_PERSON_BEFORE = [
    "お客", "各位", "皆", "同", "多", "仕", "お得意", "ご担当", "当方", "先方",
    "ユーザ", "ユーザー", "利用者", "各", "元", "副", "現",
]
_ROLE_SUSPECT = re.compile(
    r"(?<!>)"
    + "".join(f"(?<!{w})" for w in _NON_PERSON_BEFORE)
    + r"(?:[一-龥々]{1,6}|[ァ-ヶー]{2,8}|[A-Za-z][A-Za-z\-]{1,15})"
    + r"(?=[ 　]?" + _ROLE_WORDS + r")"
)


def privacy_flag(term: str) -> str | None:
    """候補語がプライバシー検査に当たるか。当たった場合は理由名を返す（値は出力しない）。"""
    for name, pat in _PRIVACY_PATTERNS:
        if pat.search(term):
            return name
    if _HONORIFIC_TAIL.search(term):
        return "敬称結合"
    return None


def snippet_privacy_verdict(snip: str) -> str | None:
    """DBへ保存する用例（抜粋）の安全性検査（R1）。疑わしい場合は理由名を返す。"""
    for name, pat in _DOC_PRIVACY_PATTERNS:
        if pat.search(snip):
            return name
    if _ROLE_SUSPECT.search(snip):
        return "人名疑い(敬称・役割)"
    return None


def make_safe_snippet(orig_snippet, reasons: Counter | None = None):
    """元の snippet に用例検査を重ねた snippet 関数を作る（R1②・除外で対応）。

    疑わしい抜粋は値を返さない（None）。propose 側は用例が空の候補を登録しないため、
    安全な用例が1つも無い候補は自然に登録から漏れる（R1③）。
    """
    def _safe(text: str, word: str, width: int = SNIPPET_LEN):
        if word not in text:
            return None
        snip = orig_snippet(text, word, width)
        if snip is None:
            return None
        v = snippet_privacy_verdict(snip)
        if v is not None:
            if reasons is not None:
                reasons[v] += 1
            return None
        return snip
    return _safe


def safe_evidence_stats(term: str, docs) -> tuple[int, Counter]:
    """候補語ごとに、安全な用例を持つ文書数と、除外した抜粋の理由別件数を数える。"""
    n = 0
    reasons: Counter[str] = Counter()
    for d in docs:
        if term not in d.text:
            continue
        snip = _gp.snippet(d.text, term)
        if snip is None:
            continue
        v = snippet_privacy_verdict(snip)
        if v is not None:
            reasons[v] += 1
        else:
            n += 1
    return n, reasons


def scan_docs_privacy(docs) -> Counter:
    """DBへ渡す抜粋・出典（文書本文）の安全性走査。理由別件数のみを返す（M2）。"""
    hits: Counter[str] = Counter()
    for d in docs:
        for name, pat in _DOC_PRIVACY_PATTERNS:
            if pat.search(d.text):
                hits[name] += 1
    return hits


def content_sha256(path: str) -> str:
    """入力ファイル内容の SHA-256（minor）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def path_id(path: str) -> str:
    """入力識別情報。パスの SHA-256 上位16桁（内容の識別は content_sha256 で行う）。"""
    norm = os.path.normcase(os.path.abspath(path))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- 集計と採点


def kata_ratio(s: str) -> float:
    if not s:
        return 0.0
    return sum(1 for c in s if _KATA.match(c)) / len(s)


def is_ascii_only(s: str) -> bool:
    return all(ord(c) < 128 for c in s)


def score_of(df: int, freq: int, flags: list[str]) -> float:
    bonus = max((BONUS[f] for f in flags), default=0.0)
    return round(2 * math.log2(df) + bonus + min(math.log2(freq), 3), 2)


def categorize(surface: str) -> str:
    for cat, keys in CATEGORY_RULES:
        for k in keys:
            if k in surface:
                return cat
    return "未分類"


def load_existing_headwords(db_path: str) -> tuple[set[str], set[str]]:
    """proposals（全状態）の payload 内の見出し語と terms の見出し語を集める。"""
    heads: set[str] = set()
    con = sqlite3.connect(db_path)
    try:
        for (pj,) in con.execute("SELECT payload_json FROM proposals"):
            try:
                p = json.loads(pj)
            except Exception:
                continue
            h = p.get("headword")
            if h:
                heads.add(str(h))
        for (h,) in con.execute("SELECT headword FROM terms"):
            heads.add(str(h))
    finally:
        con.close()
    return heads, {normalize_key(h) for h in heads}


def refuse_overwrite(path: str, force: bool) -> None:
    if os.path.exists(path) and not force:
        sys.exit(f"出力先が既に存在します（上書きするには --force を付ける）: {path}")


# ---------------------------------------------------------------- DB登録（R2）


def register_with_verification(db, propose_fn, cands, docs, *, rules, send_masker, llm):
    """提案の登録を同一トランザクション内で検証してから commit する（R2）。

    propose_fn(db, llm, cands, docs, limit=..., rules=..., send_masker=...) -> Outcome
    検証: pending増分・総数増分・提案数＝登録対象数・auto_adopted==0・evidence_added==0。
    不一致のときは rollback して (False, エラー一覧, 件数) を返す。DB は変更されない。
    """
    before_total = db.execute(text("SELECT count(*) FROM proposals")).scalar()
    before_pending = db.execute(
        text("SELECT count(*) FROM proposals WHERE status='pending'")
    ).scalar()
    o = propose_fn(db, llm, cands, docs, limit=len(cands), rules=rules,
                   send_masker=send_masker)
    db.flush()
    after_total = db.execute(text("SELECT count(*) FROM proposals")).scalar()
    after_pending = db.execute(
        text("SELECT count(*) FROM proposals WHERE status='pending'")
    ).scalar()
    errs = []
    if o.proposed != len(cands):
        errs.append(f"提案数が登録対象数と不一致（{o.proposed}≠{len(cands)}）")
    if after_total - before_total != o.proposed:
        errs.append(f"proposals総数の増分が提案数と不一致（{after_total - before_total}≠{o.proposed}）")
    if after_pending - before_pending != o.proposed:
        errs.append(f"pendingの増分が提案数と不一致（{after_pending - before_pending}≠{o.proposed}）")
    if o.auto_adopted != 0:
        errs.append(f"自動採用が発生した（{o.auto_adopted}）")
    if o.evidence_added != 0:
        errs.append(f"既存語への用例追加が発生した（{o.evidence_added}）")
    counts = {
        "before_total": before_total, "before_pending": before_pending,
        "after_total": after_total, "after_pending": after_pending,
        "proposed": o.proposed, "auto_adopted": o.auto_adopted,
        "held": o.held, "evidence_added": o.evidence_added,
    }
    if errs:
        db.rollback()
        return False, errs, counts
    db.commit()
    return True, errs, counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="入力 jsonl（マスキング済み）")
    ap.add_argument("--csv-out", required=True, help="採点結果 CSV の出力先")
    ap.add_argument("--summary-out", required=True, help="summary JSON の出力先")
    ap.add_argument("--topic-name", default="", help="トピック名（summary に記録）")
    ap.add_argument("--force", action="store_true", help="既存出力の上書きを許可する")
    ap.add_argument("--commit", action="store_true", help="合格語を proposals に登録する")
    args = ap.parse_args()

    refuse_overwrite(args.csv_out, args.force)
    refuse_overwrite(args.summary_out, args.force)

    s = load_settings()
    src = args.input
    docs = load_jsonl(Path(src))
    print(f"入力: {src}（{len(docs)}文書）", flush=True)

    # ---- 抽出（前回と同じ条件） ----
    app_stop = load_stopwords(s.config_dir / "stopwords.txt")
    freq: Counter[str] = Counter()
    df_docs: defaultdict[str, set[int]] = defaultdict(set)
    surfaces: defaultdict[str, Counter[str]] = defaultdict(Counter)
    kinds: defaultdict[str, set[str]] = defaultdict(set)
    for i, d in enumerate(docs, 1):
        for c in extract(d.text, app_stop):
            freq[c.key] += 1
            df_docs[c.key].add(i)
            surfaces[c.key][c.surface] += 1
            kinds[c.key].add(c.kind)
        if i % 200 == 0:
            print(f"  抽出 {i}/{len(docs)} 文書", flush=True)
    print(f"候補キー {len(freq)}種 / 総出現 {sum(freq.values())}", flush=True)

    # ---- ストップワード（正規化キーで照合） ----
    stop_words = TASK_STOPWORDS + EXTRA_STOPWORDS
    stop_key_of = {normalize_key(w): w for w in stop_words}

    # ---- 既存語（重複排除用・proposals 全状態＋terms。読み取りのみ） ----
    db_path = s.database_url.removeprefix("sqlite:///")
    existing, existing_keys = load_existing_headwords(db_path)

    # ---- 採点 ----
    rows = []
    for key in freq:
        surface = surfaces[key].most_common(1)[0][0]
        df = len(df_docs[key])
        flags = []
        if "compound" in kinds[key]:
            flags.append("compound")
        if kata_ratio(surface) >= 0.5:
            flags.append("katakana")
        if _MODEL.match(surface):
            flags.append("model")
        rows.append({
            "key": key,
            "term": surface,
            "freq": freq[key],
            "df": df,
            "kinds": kinds[key],
            "flags": flags,
            "category": categorize(surface),
        })

    # ---- プライバシー検査（M3: 出力より前に実施。当たった語の値は出力しない） ----
    priv_counts: Counter[str] = Counter()
    for r in rows:
        priv = privacy_flag(r["term"])
        if priv:
            r["suppressed"] = True
            r["reason"] = f"プライバシー疑い({priv})"
            priv_counts[priv] += 1

    # ---- ゲート（最初に落としたゲートを除外理由にする） ----
    funnel = Counter()
    stop_hit: Counter[str] = Counter()
    for r in rows:
        if r.get("suppressed"):
            continue  # 件数は priv_counts に記録済み。値は出力しない
        if len(r["term"]) < MIN_LEN:
            r["reason"] = "2文字未満"
            funnel["2文字未満"] += 1
        elif r["key"] in stop_key_of:
            r["reason"] = "ストップワード"
            funnel["ストップワード"] += 1
            stop_hit[stop_key_of[r["key"]]] += 1
        elif r["df"] < MIN_DF:
            r["reason"] = "df<3"
            funnel["df<3"] += 1
        elif not r["flags"] or (is_ascii_only(r["term"]) and "model" not in r["flags"]):
            # 専門性フラグなし。ASCII のみで型番でない語は仕様④で除外する
            if is_ascii_only(r["term"]) and "model" not in r["flags"]:
                r["reason"] = "専門性フラグなし(ASCIIのみ・型番以外)"
                funnel["専門性フラグなし(ASCIIのみ)"] += 1
            else:
                r["reason"] = "専門性フラグなし"
                funnel["専門性フラグなし"] += 1
        else:
            r["reason"] = None
            funnel["合格"] += 1
            r["score"] = score_of(r["df"], r["freq"], r["flags"])
            r["flags_ja"] = "+".join(
                {"compound": "複合", "katakana": "カタカナ", "model": "型番"}[f]
                for f in r["flags"]
            )

    qualified = [r for r in rows if r["reason"] is None]
    qualified.sort(key=lambda r: (-r["score"], r["term"]))

    # ---- 重複排除（提案済み・採用済み） ----
    to_insert = []
    duplicates = []
    for r in qualified:
        if r["term"] in existing or r["key"] in existing_keys:
            r["dup"] = True
            duplicates.append(r["term"])
        else:
            r["dup"] = False
            to_insert.append(r)

    # ---- 前回上位200との比較 ----
    prev = set()
    con = sqlite3.connect(db_path)
    try:
        for (pj,) in con.execute(
            "SELECT payload_json FROM proposals WHERE proposal_type='sense'"
        ):
            p = json.loads(pj)
            if p.get("headword"):
                prev.add(str(p["headword"]))
    finally:
        con.close()
    row_by_term = {r["term"]: r for r in rows}
    row_by_key = {r["key"]: r for r in rows}
    prev_requal, prev_excl = [], []
    prev_reasons = Counter()
    prev_privacy = 0
    for w in sorted(prev):
        if privacy_flag(w):
            prev_privacy += 1
            prev_reasons["プライバシー疑い"] += 1
            continue
        r = row_by_term.get(w) or row_by_key.get(normalize_key(w))
        if r is not None and r["reason"] is None:
            prev_requal.append(w)
        elif r is not None:
            prev_excl.append((w, r["reason"]))
            prev_reasons[r["reason"]] += 1
        else:
            prev_excl.append((w, "候補に現れず"))
            prev_reasons["候補に現れず"] += 1

    # ---- 用例検査（R1③のドライラン計測。DB は書き換えない） ----
    # 登録候補それぞれについて、安全な用例を持つ文書数を数える。
    # 安全な用例が1つも無い候補は、登録時に propose 側で用例空のため除外される。
    evidence_reasons: Counter[str] = Counter()
    evidence_drop = 0
    registered_rows = []
    for r in to_insert:
        n, rs = safe_evidence_stats(r["term"], docs)
        evidence_reasons.update(rs)
        if n == 0:
            evidence_drop += 1
        else:
            registered_rows.append(r)
    print(f"用例検査: 安全な用例なし {evidence_drop} 件を登録対象から除く"
          f"（理由別: {dict(evidence_reasons)}）", flush=True)

    # ---- CSV（BOM 付き UTF-8・Excel でそのまま開ける）。疑わしい語の行は書かない ----
    def sort_key(r):
        return (0 if r["reason"] is None else 1, -r.get("score", 0.0), r["term"])

    rows_sorted = sorted(rows, key=sort_key)
    csv_rows_written = 0
    os.makedirs(os.path.dirname(os.path.abspath(args.csv_out)), exist_ok=True)
    with open(args.csv_out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["term", "freq", "df", "flags", "category", "score", "qualified"])
        for r in rows_sorted:
            if r.get("suppressed"):
                continue  # 値は一切書かない（件数は summary へ）
            w.writerow([
                r["term"], r["freq"], r["df"],
                r.get("flags_ja", ""), r["category"],
                r.get("score", ""), 0 if r["reason"] is not None else 1,
            ])
            csv_rows_written += 1
    print(f"CSV: {args.csv_out}（{csv_rows_written}行・合格 {len(qualified)}）", flush=True)

    # ---- カテゴリ・フラグ分布 ----
    cat_dist = Counter(r["category"] for r in qualified)
    flag_dist = Counter(r["flags_ja"] for r in qualified)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "version": "v3",
        "topic_name": args.topic_name,
        "input_path": src,
        "input_id": path_id(src),
        "input_content_sha256": content_sha256(src),
        "doc_count": len(docs),
        "occurrence_total": sum(freq.values()),
        "distinct_keys": len(rows),
        "funnel": dict(funnel),
        "privacy_exclusion_counts": dict(priv_counts),
        "privacy_exclusion_total": sum(priv_counts.values()),
        "evidence_check": {
            "dropped_no_safe_evidence": evidence_drop,
            "excluded_snippet_reasons": dict(evidence_reasons),
            "registered_after_check": len(registered_rows),
        },
        "ascii_only_non_model_excluded": funnel.get("専門性フラグなし(ASCIIのみ)", 0),
        "stopword_list": {
            "task": TASK_STOPWORDS,
            "extra": EXTRA_STOPWORDS,
        },
        "stopword_exclusion_counts": sorted(stop_hit.items(), key=lambda x: -x[1]),
        "qualified_count": len(qualified),
        "qualified": [
            {"term": r["term"], "category": r["category"], "df": r["df"],
             "freq": r["freq"], "flags": r["flags_ja"], "score": r["score"]}
            for r in qualified
        ],
        "category_distribution": dict(cat_dist),
        "flag_distribution": dict(flag_dist),
        "duplicates": {"count": len(duplicates), "terms": duplicates},
        "insert_candidates_count": len(registered_rows),
        "prev200": {
            "total": len(prev),
            "requalified_count": len(prev_requal),
            "requalified_terms": prev_requal,
            "excluded_count": len(prev_excl),
            "excluded_reasons": dict(prev_reasons),
            "excluded_examples": [{"term": w, "reason": rs} for w, rs in prev_excl],
            "privacy_suppressed": prev_privacy,
        },
        "db": None,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.summary_out)), exist_ok=True)
    with open(args.summary_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f"集計: {args.summary_out}", flush=True)

    print(f"合格 {len(qualified)} / 重複除外 {len(duplicates)} / 登録候補 {len(registered_rows)}"
          f" / プライバシー除外 {sum(priv_counts.values())} / 用例検査除外 {evidence_drop}")
    for r in qualified[:10]:
        print(f"  {r['term']}\t{r['category']}\tdf={r['df']}\tfreq={r['freq']}"
              f"\t{r['flags_ja']}\tscore={r['score']}")

    if not args.commit:
        print("--commit を付けないため DB は書き換えません", flush=True)
        return

    # ---- minor: 入力内容が summary 記録時と同一か照合する ----
    with open(args.summary_out, encoding="utf-8") as f:
        recorded = json.load(f)
    if recorded.get("input_content_sha256") != content_sha256(src):
        sys.exit("入力ファイルの内容が summary 記録時と一致しません（中止）")

    # ---- M2: DB登録前に抜粋・出典（文書本文）の安全性走査。1件でも疑わしければ中止 ----
    doc_hits = scan_docs_privacy(docs)
    if doc_hits:
        print(f"安全性走査で疑わしい文書を検出したため DB は書き換えません: {dict(doc_hits)}")
        return

    # ---- R1: 用例検査を通った候補だけを登録する。snippet は検査つきに差し替える ----
    cands = [{"surface": r["term"], "tfidf": r["score"]} for r in registered_rows]
    snippet_reasons: Counter[str] = Counter()
    _gp.snippet = make_safe_snippet(_gp.snippet, snippet_reasons)

    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.attributes["database_url"] = s.database_url
    command.upgrade(cfg, "head")
    factory = make_session_factory(make_engine(s.database_url))
    with factory() as db:
        ok, errs, counts = register_with_verification(
            db, propose_and_adopt, cands, docs,
            rules=AdoptionRules.from_yaml(s.config_dir / "adoption.yaml"),
            send_masker=Masker.from_yaml(s.config_dir / "llm_send_masking.yaml"),
            llm=make_llm(s),
        )
    if not ok:
        print("件数検証が不一致のため rollback しました（DB は変更されていません）")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)
    print(f"検証 OK: 提案 {counts['proposed']}（保留 {counts['held']}）/ "
          f"proposals {counts['before_total']} -> {counts['after_total']}（total）, "
          f"{counts['before_pending']} -> {counts['after_pending']}（pending）")
    print(f"用例検査で除外した抜粋: {dict(snippet_reasons)}")

    summary["db"] = {**counts, "verified": True,
                     "excluded_snippet_reasons": dict(snippet_reasons)}
    with open(args.summary_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
