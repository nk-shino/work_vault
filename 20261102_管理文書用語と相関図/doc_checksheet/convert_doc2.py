# -*- coding: utf-8 -*-
"""2つの.docのうち未変換分をdocx化し、両docxを表構造保持のまま構造化テキストへ起こす。
出力はTEMPのみ。標準出力は数値のみ。"""
import os
import shutil
import time

SRC_DIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB"
NAMES = ["NR6010T0101.doc", "NR6010T0201.doc"]
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\doc_checksheet"

os.makedirs(TMP, exist_ok=True)


def copy_retry(src, dst, tries=6):
    last = None
    for i in range(tries):
        try:
            shutil.copy2(src, dst)
            return
        except PermissionError as exc:
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"copy failed (OneDrive lock?): {src}") from last


import win32com.client as wc  # noqa: E402
from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.table import Table  # noqa: E402
from docx.text.paragraph import Paragraph  # noqa: E402

# --- 1) 未変換の.docをdocxへ ---
word = wc.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    for name in NAMES:
        base = os.path.join(TMP, name[:-4])
        if os.path.exists(base + ".docx"):
            continue
        local = os.path.join(TMP, name)
        if not os.path.exists(local):
            copy_retry(os.path.join(SRC_DIR, name), local)
        doc = word.Documents.Open(local, False, True)
        doc.SaveAs2(base + ".docx", 12)
        doc.Close(False)
finally:
    word.Quit()

# 旧フラットtxt(文字化け源)を削除
for name in NAMES:
    stale = os.path.join(TMP, name[:-4] + ".txt")
    if os.path.exists(stale):
        os.remove(stale)


# --- 2) docxを構造化テキストへ ---
def walk_container(container, out, depth=0):
    n_par = n_tbl = 0
    for child in container.element.body.iterchildren() if hasattr(container, "element") else []:
        pass  # unused; kept for clarity
    return n_par, n_tbl


def iter_block_items(parent):
    """body内の段落と表を出現順に返す。"""
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield ("p", Paragraph(child, parent))
        elif child.tag == qn("w:tbl"):
            yield ("tbl", Table(child, parent))
        elif child.tag == qn("w:sdt"):
            # コンテンツコントロール配下の段落・表を展開
            for sub in child.iter():
                if sub.tag == qn("w:p"):
                    yield ("p", Paragraph(sub, parent))
                elif sub.tag == qn("w:tbl"):
                    yield ("tbl", Table(sub, parent))
        else:
            yield ("skip", child.tag.split("}")[-1])


def dump_docx(docx_path, out_path):
    doc = Document(docx_path)
    lines = []
    stats = {"par": 0, "tbl": 0, "chars": 0}
    # セクション情報(縦長確認用)
    for i, sec in enumerate(doc.sections, 1):
        pw = round(sec.page_width.cm, 1) if sec.page_width else None
        ph = round(sec.page_height.cm, 1) if sec.page_height else None
        lines.append(f"[SECTION {i}] {pw}cm x {ph}cm orientation={sec.orientation}")
        for label, part in (("HEADER", sec.header), ("FOOTER", sec.footer)):
            try:
                texts = [p.text for p in part.paragraphs if p.text.strip()]
                if texts:
                    lines.append(f"[{label} {i}] " + " / ".join(texts))
            except Exception:
                lines.append(f"[{label} {i}] <read error>")
    lines.append("--- BODY ---")
    for kind, item in iter_block_items(doc):
        if kind == "p":
            t = item.text
            if t.strip():
                lines.append("[P] " + t)
                stats["par"] += 1
                stats["chars"] += len(t)
        elif kind == "tbl":
            tbl = item
            nrows = len(tbl.rows)
            ncols = len(tbl.columns)
            stats["tbl"] += 1
            lines.append(f"[TABLE {stats['tbl']}] {nrows}rows x {ncols}cols")
            for r in tbl.rows:
                cells = []
                for c in r.cells:
                    cells.append(c.text.replace("\n", "\\n").replace("\r", "\\r"))
                row = " | ".join(cells)
                lines.append("  " + row)
                stats["chars"] += len(row)
        else:
            lines.append(f"[SKIP {item}]")
    with open(out_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
    return stats


results = {}
for name in NAMES:
    base = os.path.join(TMP, name[:-4])
    stats = dump_docx(base + ".docx", base + "_structured.txt")
    results[name] = stats

for name, s in results.items():
    print(f"{name}: paragraphs={s['par']} tables={s['tbl']} chars={s['chars']}")
