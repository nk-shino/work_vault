# -*- coding: utf-8 -*-
"""適用後検証: ①メンバー完全差分 ②用語シート再ダンプ ③sharedStrings接頭辞一致 ④COM開帳·図形数。"""
import zipfile, hashlib, os, json
import xml.etree.ElementTree as ET

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\20261102_terms"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

FILES = [
    ("pana", VAULT + r"\Pana-CIM管理手順書案_未承認.xlsx"),
    ("lnb", VAULT + r"\LNB管理手順書案_未承認.xlsx"),
]

def sha(b): return hashlib.sha256(b).hexdigest()

out = []
for tag, path in FILES:
    bak = os.path.join(TMP, os.path.basename(path) + ".pre_20261102.xlsx")
    zb = zipfile.ZipFile(bak)
    zn = zipfile.ZipFile(path)
    b_names = zb.namelist(); n_names = zn.namelist()
    res = {"tag": tag}
    res["member_list_identical"] = b_names == n_names
    diffs, same = [], 0
    for nm in b_names:
        if zb.read(nm) == zn.read(nm): same += 1
        else: diffs.append(nm)
    res["byte_identical_members"] = same
    res["changed_members"] = sorted(diffs)
    res["drawings_identical"] = all(zb.read(nm) == zn.read(nm) for nm in b_names if nm.startswith("xl/drawings/"))

    # 用語シート再ダンプ(sheet3·ET解析)
    root = ET.fromstring(zn.read("xl/worksheets/sheet3.xml"))
    sst = ET.fromstring(zn.read("xl/sharedStrings.xml"))
    sst_items = sst.findall(NS + "si")
    strs = []
    for t in sst_items:
        texts = [e.text or "" for e in t.iter(NS + "t")]
        strs.append("".join(texts))
    res["sst_count_attr"] = sst.get("count"); res["sst_uniqueCount_attr"] = sst.get("uniqueCount")
    res["sst_si_count"] = len(sst_items)
    # 用語シートのC列エントリ(行7以降)
    entries = []
    for row in root.iter(NS + "row"):
        r = int(row.get("r"))
        if r < 7: continue
        for c in row.iter(NS + "c"):
            ref = c.get("r")
            if ref and ref[0] == "C" and c.get("t") == "s":
                v = c.find(NS + "v")
                if v is not None:
                    entries.append((r, ref, c.get("s"), strs[int(v.text)]))
    res["term_entries"] = entries

    # 旧バックアップ側の用語エントリ(接頭辞一致確認)
    root_b = ET.fromstring(zb.read("xl/worksheets/sheet3.xml"))
    sst_b = ET.fromstring(zb.read("xl/sharedStrings.xml"))
    strs_b = ["".join(e.text or "" for e in t.iter(NS + "t")) for t in sst_b.findall(NS + "si")]
    entries_b = []
    for row in root_b.iter(NS + "row"):
        r = int(row.get("r"))
        if r < 7: continue
        for c in row.iter(NS + "c"):
            ref = c.get("r")
            if ref and ref[0] == "C" and c.get("t") == "s":
                v = c.find(NS + "v")
                if v is not None:
                    entries_b.append((r, ref, c.get("s"), strs_b[int(v.text)]))
    k = len(entries_b)
    res["old_entries_preserved"] = entries[:k] == entries_b
    res["old_sst_prefix_preserved"] = strs[:len(strs_b)] == strs_b
    res["new_entries"] = entries[k:]
    out.append(res)
    zb.close(); zn.close()

with open(os.path.join(TMP, "verify_dump.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("VERIFY PARSE OK")
for r in out:
    print(r["tag"], "| members:", r["member_list_identical"], "| same:", r["byte_identical_members"],
          "| changed:", r["changed_members"], "| drawings:", r["drawings_identical"],
          "| sst:", r["sst_count_attr"], r["sst_uniqueCount_attr"], r["sst_si_count"],
          "| old_kept:", r["old_entries_preserved"], r["old_sst_prefix_preserved"], "| new:", len(r["new_entries"]))
