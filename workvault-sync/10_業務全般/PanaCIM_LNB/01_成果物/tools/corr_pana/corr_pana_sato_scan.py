# -*- coding: utf-8 -*-
"""§11(1) 佐藤(勇)引継ぎフォルダ照査: システム接続パス情報の抽出(読み取り専用)。
対象: pptx/docx/md/csv/txt のテキスト。キーワード(アンドン/フィーダ/接続/UNC/IP)で抜粋。
認証情報は伏字。出力: corr_pana_sato_scan.json + コンソール要約。
判定: E06(ノズル/リーダーデータ)/E09/E10(アンドン) を実線化できる証跡があるか。"""
import sys, io, os, re, json, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault/09_佐藤さん引継ぎ"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corr_pana_sato_scan.json")

# 判定に直結するキーワード(§11: アンドン・フィーダー情報のシステム所在/接続)
KW_CONN = ["アンドン", "andon", "Andon", "ANDON", "フィーダ", "Feeder", "feeder"]
KW_SYS  = ["PanaCIM", "パナCIM", "Pana-CIM", "DGS", "NPM", "LNB", "Eg-Pro", "EGPro", "Asprova",
           "Solder", "ソルダ", "目視", "実績", "計画データ", "連携", "接続", "サーバ"]
PAT_UNC = re.compile(r"\\\\[\w\-.・]+\\[\w\-.\\ 　（）()・ー]+")
PAT_IP  = re.compile(r"\b(?:192\.168|172\.2\d|10\.\d+)\.\d+\.\d+\b")
PAT_DRIVE = re.compile(r"\b[A-Za-z]:\\[\w\-.\\ 　（）()・ー]{2,110}")

def redact(s):
    return re.sub(r"(?i)(PWD|Password|パスワード)\s*[=:＝]\s*\S+", r"\1=[伏字]", s)

# 認証情報を含む恐れのある行/ファイルは丸ごと除外(Kohden Code 禁止情報対策)
DROP_FILE_PAT = re.compile(r"(ログイン|認証|アカウント|password|pass)", re.I)
DROP_LINE_PAT = re.compile(r"(パスワード|password|pwd|administrator|admin\b|アカウント|認証|ログイン)", re.I)

def safe_picks(picks):
    out = []
    for p in picks:
        if DROP_LINE_PAT.search(p):
            continue
        out.append(p)
    return out

def pptx_text(path):
    z = zipfile.ZipFile(path)
    out = []
    for n in sorted(z.namelist()):
        if re.match(r"ppt/slides/slide\d+\.xml$", n):
            xml = z.read(n).decode("utf-8", "ignore")
            ts = [t for t in re.findall(r"<a:t>([^<]*)</a:t>", xml) if t.strip()]
            out.append(f"-- {n.split('/')[-1]}: " + " | ".join(ts))
        if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", n):
            xml = z.read(n).decode("utf-8", "ignore")
            ts = [t for t in re.findall(r"<a:t>([^<]*)</a:t>", xml) if t.strip()]
            if ts:
                out.append(f"-- {n.split('/')[-1]}(notes): " + " | ".join(ts))
    z.close()
    return "\n".join(out)

def docx_text(path):
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8", "ignore")
    z.close()
    ts = [t for t in re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml) if t.strip()]
    return "\n".join(ts)

def xlsx_text(path):
    z = zipfile.ZipFile(path)
    out = []
    for n in z.namelist():
        if re.match(r"xl/(sharedStrings|worksheets/sheet\d+)\.xml$", n):
            xml = z.read(n).decode("utf-8", "ignore")
            ts = [t for t in re.findall(r"<t[^>]*>([^<]*)</t>", xml) if t.strip()]
            if ts:
                out.append(" | ".join(ts[:200]))
    z.close()
    return "\n".join(out)

results = []
for root, dirs, files in os.walk(BASE):
    if DROP_FILE_PAT.search(os.path.basename(root)):
        dirs[:] = []
        continue
    for fn in list(files):
        if DROP_FILE_PAT.search(fn):
            files.remove(fn)
            continue
        low = fn.lower()
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, BASE)
        text = None
        try:
            if low.endswith(".pptx"):
                text = pptx_text(p)
            elif low.endswith(".docx"):
                text = docx_text(p)
            elif low.endswith((".xlsx", ".xlsm")):
                text = xlsx_text(p)
            elif low.endswith((".md", ".txt", ".csv")):
                text = open(p, encoding="utf-8", errors="replace").read()
        except Exception as e:
            results.append({"file": rel, "error": str(e)})
            continue
        if not text:
            continue
        # 接続判定行の抜粋: アンドン/フィーダ行 + それに近いシステム・パス行
        lines = [redact(l.strip()) for l in text.replace("\r", "\n").split("\n") if l.strip()]
        picks = safe_picks([
            " ≪ ".join(lines[max(0, i - 1): i + 2])[:300]
            for i, l in enumerate(lines)
            if (any(k in l for k in KW_CONN) or PAT_UNC.search(l) or PAT_IP.search(l) or PAT_DRIVE.search(l))
        ])
        # システム語ヒット統計
        sys_hits = {k: sum(1 for l in lines if k in l) for k in KW_SYS if any(k in l for l in lines)}
        if picks or sys_hits:
            results.append({"file": rel, "sys_hits": sys_hits, "picks": picks[:25]})

# 重複行圧縮
seen = set()
uniq = []
for r in results:
    key = r.get("file", "") + str(r.get("picks", []))[:80]
    if key not in seen:
        seen.add(key); uniq.append(r)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(uniq, f, ensure_ascii=False, indent=1)

print(f"対象: {BASE}")
print(f"ヒットファイル: {len(uniq)}")
for r in uniq:
    print("=" * 70)
    print(r["file"], r.get("sys_hits", ""))
    for p in r.get("picks", [])[:12]:
        print("   *", p)
# アンドン判定サマリ
andon = [r for r in uniq if any(("アンドン" in p or "Andon" in p or "andon" in p) for p in r.get("picks", []))]
print("=" * 70)
print(f"アンドン言及ファイル: {[r['file'] for r in andon]}")
