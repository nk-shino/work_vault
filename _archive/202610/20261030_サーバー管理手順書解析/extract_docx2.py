# -*- coding: utf-8 -*-
"""サーバー管理手順書.docx の再帰構造抽出(様式テーブル・テキストボックス内部まで・読み取り専用)"""
import io, zipfile, re
from collections import Counter
import xml.etree.ElementTree as ET

SRC = r"C:\Users\ss80751\OneDrive - NK\デスクトップ\サーバー管理手順書.docx"
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261030_サーバー管理手順書解析\_structure2.txt"
WNS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"

with zipfile.ZipFile(SRC) as z:
    styles_xml = z.read("word/styles.xml").decode("utf-8", "ignore")
    num_xml = z.read("word/numbering.xml").decode("utf-8", "ignore")
    doc_xml = z.read("word/document.xml")

# style id -> name
id2name = {}
for m in re.finditer(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>', styles_xml, re.S):
    sid, sbody = m.group(1), m.group(2)
    nm = re.search(r'<w:name w:val="([^"]+)"', sbody)
    id2name[sid] = nm.group(1) if nm else sid

buf = io.StringIO()
w = buf.write
counts = Counter()

def runs_info(p):
    """text + 最大サイズ + bold有無 + 画像数(直接の子孫のみ)"""
    texts = []
    maxsz = 0
    bold = False
    nimg = 0
    for r in p.iter():
        tag = r.tag
        if tag == WNS + "t":
            texts.append(r.text or "")
        elif tag == WNS + "sz":
            try:
                maxsz = max(maxsz, int(r.get(WNS + "val")) / 2)
            except (TypeError, ValueError):
                pass
        elif tag == WNS + "b":
            bold = True
        elif tag in (WNS + "drawing", WNS + "pict"):
            nimg += 1
    return "".join(texts).strip(), maxsz, bold, nimg

def walk(el, depth):
    for child in el:
        tag = child.tag
        if tag in (WNS + "drawing", WNS + "pict"):
            txb = child.find(".//" + WNS + "txbxContent")
            if txb is not None:
                w(f"{'  ' * depth}[TXBX]\n")
                walk(txb, depth + 1)
            continue
        if tag == WNS + "p":
            counts["p"] += 1
            pPr = child.find(WNS + "pPr")
            style = "-"
            num = ""
            if pPr is not None:
                ps = pPr.find(WNS + "pStyle")
                if ps is not None:
                    style = id2name.get(ps.get(WNS + "val"), ps.get(WNS + "val"))
                np_ = pPr.find(WNS + "numPr")
                if np_ is not None and np_.find(WNS + "numId") is not None:
                    nid = np_.find(WNS + "numId").get(WNS + "val")
                    ilvl = np_.find(WNS + "ilvl")
                    il = ilvl.get(WNS + "val") if ilvl is not None else "0"
                    num = f"L{il}#{nid}"
            text, sz, bold, nimg = runs_info(child)
            if text or nimg:
                flags = []
                if bold and text:
                    flags.append("B")
                if sz:
                    flags.append(f"{sz:g}pt")
                if nimg:
                    flags.append(f"IMGx{nimg}")
                ind = "  " * depth
                w(f"{ind}[{style}{'|' + num if num else ''}{'|' + ','.join(flags) if flags else ''}] {text[:150]}\n")
            # 段落内(インライン)の図形テキストボックスへも降りる
            for txb in child.findall(".//" + WNS + "txbxContent"):
                w(f"{'  ' * depth}[TXBX in p]\n")
                walk(txb, depth + 1)
        elif tag == WNS + "tbl":
            counts["tbl"] += 1
            rows = child.findall(WNS + "tr")
            ncols = len(rows[0].findall(WNS + "tc")) if rows else 0
            ind = "  " * depth
            w(f"{ind}<TBL{counts['tbl']} d{depth} {len(rows)}x{ncols}>\n")
            for tr in rows:
                for tc in tr.findall(WNS + "tc"):
                    tcw = tc.find(WNS + "tcPr/" + WNS + "tcW")
                    wid = tcw.get(WNS + "w") if tcw is not None else "?"
                    celltxt = "".join(t.text or "" for t in tc.iter(WNS + "t")).strip()
                    nested = len(tc.findall(".//" + WNS + "tbl"))
                    head = f"{ind}  cell(w={wid}"
                    if nested:
                        head += f",ntbl={nested}"
                    w(f"{head}) {celltxt[:80]}\n")
                    walk(tc, depth + 1)
        elif tag == WNS + "sectPr":
            pass

tree = ET.fromstring(doc_xml)

# mc:Fallback(DrawingMLのVML複製)を除去して二重カウントを防ぐ
def strip_fallback(el):
    for fb in list(el):
        if fb.tag == MC + "Fallback":
            el.remove(fb)
        else:
            strip_fallback(fb)
strip_fallback(tree)

body = tree.find(WNS + "body")
w("=== recursive dump (depth = table nesting, TXBX = textbox content) ===\n")
walk(body, 0)
w(f"\ncounts: {dict(counts)}\n")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print(f"written, {len(buf.getvalue())} chars, {dict(counts)}")
