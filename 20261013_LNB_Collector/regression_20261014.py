import sys, os, re, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')

V = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB"
DOCS = os.path.join(V, "01_成果物")
fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)

lnb = open(os.path.join(DOCS, "LNB管理書.md"), encoding='utf-8').read()
pana = open(os.path.join(DOCS, "管理書.md"), encoding='utf-8').read()

# ===== 1. 回帰: 前回の全検証項目 =====
fm_lnb = lnb.split('---')[1]
check("LNB: front matter 版0.9", "版: 0.9" in fm_lnb)
check("LNB: 履歴に0.9", "| 0.9 | 2026-10-14 |" in lnb)
fm_pana = pana.split('---')[1]
check("PANA: front matter 版0.11", "版: 0.11" in fm_pana)
check("PANA: 履歴に0.11", "| 0.11 | 2026-10-14 |" in pana)
for k in ["LNB再起動", "LNB-PC電源OFF", "LNB-PCリブート", "172.25.253.10", "SP70-1",
          "L1NPM-1", "設定情報リストア", "認証ID", "192.168.20.23"]:
    check("LNB書: 含む " + k, k in lnb)
check("LNB書: 旧表現なし", "再起動（2種に分かれている）" not in lnb)
check("LNB書: DGS行崩れ修正済み", "と同じ扱い）- **アンドン**" not in lnb)
check("LNB書: 対応付け推定明示", "対応付けはボタン名からの推定" in lnb)
check("PANA書: DGS上位システム", "上位システム" in pana and "172.25.253.10" in pana)
check("PANA書: 旧表現なし", "LNB のバックアップ経路に現れる系。本書での位置づけは要確認 |" not in pana)

for f in [os.path.join(V, "01_成果物", "LNB_確実構成図.drawio"), os.path.join(V, "01_成果物", "PanaCIM_LNB_確実構成図.drawio")]:
    dx = open(f, encoding='utf-8').read()
    tree = ET.fromstring(dx)
    ids = {c.get('id') for c in tree.iter('mxCell')}
    texts = "\n".join((c.get('value') or '') for c in tree.iter('mxCell'))
    check(f + ": XMLパース", True)
    orph = [c.get('id') for c in tree.iter('mxCell') if c.get('parent') and c.get('parent') not in ids and c.get('parent') != '0']
    check(f + ": 孤立ノードなし", not orph)
    broken = [c.get('id') for c in tree.iter('mxCell') if c.get('edge') == '1'
              for ref in (c.get('source'), c.get('target')) if ref and ref not in ids]
    check(f + ": エッジ接続先存在", not broken)
    check(f + ": 認証情報を含まない", "password" not in texts.lower() and "パスワード=" not in texts)

check("drawio(LNB): DGS IP記載", "172.25.253.10" in open(os.path.join(V, "01_成果物", "LNB_確実構成図.drawio"), encoding='utf-8').read())

# ===== 2. 相対リンク切れ検査 =====
def check_links(path, text):
    base = os.path.dirname(path)
    links = re.findall(r'\]\(([^)]+)\)', text)
    for lk in links:
        if lk.startswith(('http', '#')):
            continue
        target = os.path.normpath(os.path.join(base, lk.split('#')[0]))
        check(f"リンク存在: {os.path.basename(path)} -> {lk}", os.path.exists(target))

check_links(os.path.join(DOCS, "LNB管理書.md"), lnb)
check_links(os.path.join(DOCS, "管理書.md"), pana)

# ===== 3. 認証情報の漏えい検査（§15 運用の確認）=====
secret_pat = re.compile(r'(id=|pass(word)?=|user=)[^\s&]+', re.I)
for name, t in [("LNB管理書", lnb), ("管理書", pana)]:
    hits = [m.group(0) for m in secret_pat.finditer(t)]
    check(f"{name}: 認証情報らしき値なし", not hits)

print()
print("FAIL:", len(fails))
sys.exit(1 if fails else 0)
