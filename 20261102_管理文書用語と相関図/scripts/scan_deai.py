# -*- coding: utf-8 -*-
"""DeAI事前スキャン: 改修後ダンプ(text_*.md)を解析し、AI生成文のサインを集計する。
deai-writing スキル §1·§2 の指標に基づく(文長リズム·対比·冒頭·構造宣言·接続詞·評価語)。
併せて G5(括弧内相互参照·未確認)と G6(チェックシートの日時欄)の対象箇所を抽出する。
読み取り専用。"""
import os, re, json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = {
    "Pana": os.path.join(BASE, "xlsx_dump_after_pana"),
    "LNB": os.path.join(BASE, "xlsx_dump_after_lnb"),
}
CHECK_SHEETS = ("チェックシート",)
LINE_RE = re.compile(r"^[-*]\s+([A-Z]{1,2}[0-9]{1,3}):\s?(.*)$")
HDR_RE = re.compile(r"^##\s+行\s+\d+")

def sentences(text):
    parts = re.split(r"(?<=[。！？])", text)
    return [p.strip() for p in parts if p.strip()]

def noun_end(s):
    """体言止め推定: 末尾が用言活用·助詞で終わらない(粗い推定)"""
    tail = re.sub(r"[」』）)」』]+$", "", s)
    if not tail:
        return False
    ng = ("です", "ます", "である", "だ", "ない", "した", "する", "れる", "られる",
          "いる", "きた", "くる", "こと", "もの", "ため", "られ", "ませ", "くださ",
          "いただ", "へ", "に", "を", "が", "は", "と", "より", "による", "での")
    return not tail.endswith(ng)

def scan_book(name, folder):
    out = {"sheets": defaultdict(lambda: defaultdict(int)), "hits": []}
    for fn in sorted(os.listdir(folder)):
        if not (fn.startswith("text_") and fn.endswith(".md")):
            continue
        sheet = re.sub(r"^text_.+?_(.+)\.md$", r"\1", fn)
        cells = []  # (cellref, value)
        for line in open(os.path.join(folder, fn), encoding="utf-8"):
            line = line.rstrip("\n")
            if HDR_RE.match(line) or line.startswith(("#", "- 抽出", "- シート", "- 使用", "- 実測", "- 値セル", "- 方針", "  数式", "  セル内")):
                continue
            m = LINE_RE.match(line)
            if m:
                cells.append((m.group(1), m.group(2)))
        st = out["sheets"][sheet]
        prose = [v for _, v in cells if len(v) >= 30]
        st["cells"] = len(cells)
        st["prose_cells"] = len(prose)
        for ref, v in cells:
            ss = sentences(v)
            lens = [len(s) for s in ss]
            # 対比構文
            for pat, key in (("ではなく", "taihis"), ("わけではない", "taihis")):
                n = v.count(pat)
                if n:
                    st[key] += n
                    if n >= 2:
                        out["hits"].append(f"[{name}/{sheet}!{ref}] 対比×{n}: {v[:60]}…")
            # 構造宣言
            if re.search(r"以下に|以下のとおり|以下の通り|ポイントを示し|概要を述べ", v):
                st["decl"] += 1
                out["hits"].append(f"[{name}/{sheet}!{ref}] 構造宣言: {v[:50]}…")
            # 汎用接続詞(文頭)
            for s in ss:
                if re.match(r"^(また|さらに|なお|そして|加えて)[、,]", s):
                    st["conn"] += 1
            # 評価語
            for w in ("重要", "不可欠", "効果的", "適切に", "有効活用"):
                if w in v:
                    st["hyoka"] += 1
                    break
            # 装飾記号
            if re.search(r"[★◆■●▲▶✔✓]", v):
                st["decor"] += 1
                out["hits"].append(f"[{name}/{sheet}!{ref}] 装飾記号: {v[:40]}…")
            # 3点パターン(・による列挙3以上)
            if v.count("・") >= 2 and len(v) < 80:
                st["triple"] += 1
            # G5: 括弧内相互参照
            for mm in re.finditer(r"（?第?[0-9０-９]+章[^（）]{0,12}?[0-9０-９.\-]+[^（）]{0,10}?）", v):
                st["xref"] += 1
                out["hits"].append(f"[{name}/{sheet}!{ref}] 括弧内相互参照: {mm.group(0)}")
            if re.search(r"[(（](相関図|第[0-9０-９]+章)", v):
                st["xref"] += 1
            # G5: 未確認·要確認
            if re.search(r"未確認|要確認", v):
                st["mikaku"] += 1
                out["hits"].append(f"[{name}/{sheet}!{ref}] 未確認·要確認: {v[:70]}…")
            # 文長リズム: 長文のみで均質なセル
            if len(lens) >= 3 and min(lens) >= 40 and (max(lens) - min(lens)) <= 25:
                st["uniform"] += 1
            st["short"] += sum(1 for L in lens if 0 < L <= 10)
            st["sent"] += len(lens)
            st["nounend"] += sum(1 for s in ss if noun_end(s))
        # G6: チェックシートの日時欄
        if any(k in sheet for k in CHECK_SHEETS):
            for ref, v in cells:
                if re.search(r"日時|実施日|実施年月日|日付|時刻", v):
                    out["hits"].append(f"[{name}/{sheet}!{ref}] 日時欄候補: {v[:50]}…")
    return out

report = []
for name, folder in BOOKS.items():
    if not os.path.isdir(folder):
        report.append(f"# {name}: ダンプ無し({folder})")
        continue
    res = scan_book(name, folder)
    report.append(f"\n# {name}\n")
    report.append("| シート | 値セル | 散文セル | 対比 | 構造宣言 | 文頭接続詞 | 評価語 | 装飾 | 3点 | 相互参照 | 未確認 | 均質長文 | 超短文(全文) | 体言止め推定 |")
    report.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for sheet, st in res["sheets"].items():
        report.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            sheet, st["cells"], st["prose_cells"], st["taihis"], st["decl"], st["conn"],
            st["hyoka"], st["decor"], st["triple"], st["xref"], st["mikaku"],
            st["uniform"], st["short"], st["nounend"]))
    report.append("\n## 指摘ヒット(抜粋·最大60件)\n")
    for h in res["hits"][:60]:
        report.append(f"- {h}")
    report.append(f"(全{len(res['hits'])}件)")

outpath = os.path.join(BASE, "点検_DeAI事前スキャン_20261104.md")
open(outpath, "w", encoding="utf-8").write("\n".join(report))
print("\n".join(report[:0]) or "", end="")
print("レポート出力:", outpath)
print("\n".join(report))
