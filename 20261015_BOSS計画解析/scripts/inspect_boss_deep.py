# -*- coding: utf-8 -*-
"""BOSSシート詳細: ZP21分析・日付分布・祝日網羅チェック・サイクルタイム重複詳細"""
import zipfile, sys, io, re, datetime
from xml.etree import ElementTree as ET
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題\BOSS計画.xlsm"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
z = zipfile.ZipFile(SRC)
ss = []
sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in sst:
    ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))

def col_idx(s):
    n = 0
    for ch in s: n = n * 26 + (ord(ch) - 64)
    return n

def load_rows(idx):
    ws = ET.fromstring(z.read(f"xl/worksheets/sheet{idx}.xml"))
    rows = {}
    for row in ws.iter("{%s}row" % NS["m"]):
        r = int(row.get("r"))
        d = {}
        for c in row:
            m = re.match(r"([A-Z]+)", c.get("r"))
            col = col_idx(m.group(1))
            v = c.find("m:v", NS); is_el = c.find("m:is", NS)
            val = None
            if v is not None:
                val = ss[int(v.text)] if c.get("t") == "s" else v.text
            elif is_el is not None:
                val = "".join(x.text or "" for x in is_el.iter("{%s}t" % NS["m"]))
            d[col] = val
        rows[r] = d
    return rows

def num(v):
    if v is None: return None
    try: return float(v)
    except: return None

rows = load_rows(14)
n = max(rows)
epoch = datetime.date(1899, 12, 30)

# ZP21の実態: 指図番号プレフィックス・品目・日付
zp = [r for r in range(2, n + 1) if rows[r].get(4) == "ZP21"]
la = [r for r in range(2, n + 1) if rows[r].get(4) == "LA"]
print(f"ZP21: {len(zp)} / LA: {len(la)}")
# 指図番号のプレフィックス分布
pref = Counter(rows[r].get(1, "")[:2] for r in zp)
print(f"ZP21指図番号プレフィックス: {dict(pref.most_common())}")
pref_la = Counter(rows[r].get(1, "")[:2] for r in la)
print(f"LA指図番号プレフィックス: {dict(pref_la.most_common())}")

# 日付分布(年毎)
years = Counter()
for r in range(2, n + 1):
    d = num(rows[r].get(14))
    if d: years[datetime.datetime.fromtimestamp(0) .fromordinal(int(d) + 693594).year] += 1
print(f"基準開始日の年分布: {dict(sorted(years.items()))}")

# Main のフィルタ(<=now-730 or >=now+730 で削除)を再現: 残るデータの範囲
now = datetime.date(2026, 10, 15)
lo = now - datetime.timedelta(days=730)
hi = now + datetime.timedelta(days=730)
print(f"フィルタ閾値: {lo} より古い or {hi} より新しい行は削除対象")
old = sum(1 for r in range(2, n + 1) if num(rows[r].get(14)) and epoch + datetime.timedelta(days=num(rows[r].get(14))) < lo)
future = sum(1 for r in range(2, n + 1) if num(rows[r].get(14)) and epoch + datetime.timedelta(days=num(rows[r].get(14))) > hi)
print(f"削除対象: 過去側={old} 未来側={future}")

# ZP21に '000000000' 的な自動追加行の痕跡: 指図番号が数値じゃない/9桁0
zero = [r for r in range(2, n + 1) if rows[r].get(1) == "000000000"]
print(f"指図='000000000'の行: {len(zero)}")

# サイクルタイム重複の詳細
rows18 = load_rows(18)
ids = Counter(rows18[r].get(1) for r in range(2, max(rows18) + 1) if rows18.get(r, {}).get(1))
dups = [k for k, v in ids.items() if v > 1]
print(f"\nサイクルタイム重複typeID: {dups}")
for k in dups:
    for r in range(2, max(rows18) + 1):
        if rows18.get(r, {}).get(1) == k:
            print(f"  r{r}: A={rows18[r].get(1)} D={rows18[r].get(4)}")

# 組取り数の typeID型: 数値に見えるID
rows19 = load_rows(19)
numeric_ids = sum(1 for r in range(2, max(rows19) + 1) if rows19.get(r, {}).get(1) and re.fullmatch(r"\d+", str(rows19[r].get(1))))
print(f"\n組取り数: 数値のみtypeID={numeric_ids}/{max(rows19)-1}")

# 祝日の年度網羅: 2026-10-16以降の祝日が無いと警告
rows15 = load_rows(15)
hol = sorted(num(rows15[r].get(1)) for r in rows15 if num(rows15[r].get(1)))
print(f"\n祝日: 最後={epoch + datetime.timedelta(days=hol[-1])}")
future_hol = [h for h in hol if epoch + datetime.timedelta(days=h) >= now]
print(f"今日以降の祝日: {len(future_hol)}")

# BOSS列O(基準終了日)とN列の整合
bad = 0
for r in range(2, n + 1):
    ns, ne = num(rows[r].get(14)), num(rows[r].get(15))
    if ns and ne and ne < ns: bad += 1
print(f"基準終了日<開始日: {bad}")
