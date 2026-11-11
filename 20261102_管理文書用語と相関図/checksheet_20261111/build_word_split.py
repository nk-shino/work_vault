# -*- coding: utf-8 -*-
"""Split the LNB checksheet into cycle-specific single-page files.

Word/COM handles text entry and paragraph formatting; python-docx removes the
unused item rows and the continuation page at XML level (Word's object model
cannot delete rows in this vertically merged table).
"""
from pathlib import Path

import fitz
import win32com.client as win32
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
SRC = HERE / "word" / "NR6010T0101_work.doc"
OUT = HERE / "word" / "split"
OUT.mkdir(parents=True, exist_ok=True)

WEEKLY = [
    "【週次】日次記録の週次集計を確認した",
    "【週次】バックアップ成否を確認した",
    "【週次】LWS PC のディスク空き容量・ログを確認した",
    "【週次】接続状態の傾向を確認した",
    "【週次】エラーログを確認した",
    "【週次】変更・3Hの記録を確認した",
    "【週次】物理ランプを確認した",
    "【週次】自動監視の稼働を確認した",
]

NOTE_TEXTS = [
    "判定基準はLNB管理書§6-2を参照。",
    "判定基準は LNB管理書 §6-2 を参照。",
    "判定基準はLNB管理書§6-2を参照",
]

ITEM_FIRST = 10          # 1-based first item row in table1
SPARE_FIRST = 30         # 1-based first spare row (5 rows: 30..34)


def find_replace(doc, find_text, replace_text, wildcards=False):
    rng = doc.Content
    f = rng.Find
    f.ClearFormatting()
    f.Replacement.ClearFormatting()
    return bool(
        f.Execute(
            find_text, False, False, wildcards, False, False, True, 0, False,
            replace_text, 2,
        )
    )


def remove_note(doc):
    for txt in NOTE_TEXTS:
        if find_replace(doc, txt, ""):
            return True
    return find_replace(doc, "判定基準は*参照。", "", wildcards=True)


def set_cycle(doc, label):
    rng = doc.Content
    f = rng.Find
    f.ClearFormatting()
    if not f.Execute("月次・年次", False, False, False, False, False, True, 0, False):
        return False
    try:
        rng.Cells(1).Range.Text = label
        return True
    except Exception:
        return False


def left_align(doc, first, count):
    t = doc.Tables(1)
    for r in range(first, first + count):
        pf = t.Cell(r, 2).Range.ParagraphFormat
        pf.Alignment = 0
        pf.LeftIndent = 0
        pf.FirstLineIndent = 0
        pf.RightIndent = 0
        pf.SpaceBefore = 0
        pf.SpaceAfter = 0
        pf.LineSpacingRule = 0


def word_prepare(name, kind):
    """Copy the work doc, apply text/format edits in Word, save as .docx."""
    target = OUT / f"NR6010T0101_{name}.docx"
    src_copy = OUT / f"_base_{name}.doc"
    src_copy.write_bytes(SRC.read_bytes())
    for p in OUT.glob(f"NR6010T0101_{name}.*"):
        p.unlink()

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = word.Documents.Open(str(src_copy), False, False, False)
    try:
        remove_note(doc)
        if kind == "weekly":
            t = doc.Tables(1)
            for i, text in enumerate(WEEKLY):
                t.Cell(ITEM_FIRST + i, 2).Range.Text = text
            count = len(WEEKLY)
            left_align(doc, ITEM_FIRST, count)
        elif kind == "annual":
            count = 10
            left_align(doc, 20, count)
        else:
            count = 10
            left_align(doc, ITEM_FIRST, count)
        set_cycle(doc, name)
        doc.SaveAs2(str(target), 12)
    finally:
        doc.Close(False)
        word.Quit()
        src_copy.unlink(missing_ok=True)
    return target


def delete_rows(tbl, first_0, last_0):
    trs = tbl.findall(qn("w:tr"))
    for tr in trs[first_0:last_0 + 1]:
        tbl.remove(tr)


def docx_structure(path, kind):
    d = Document(str(path))
    tbl1 = d.tables[0]._tbl

    if kind == "monthly":
        delete_rows(tbl1, 19, 28)      # annual 10 rows (1-based 20..29)
    elif kind == "annual":
        delete_rows(tbl1, 9, 18)       # monthly 10 rows (1-based 10..19)
    else:
        delete_rows(tbl1, 17, 28)      # leftover rows (1-based 18..29)

    body = d.element.body
    sect = body.find(qn("w:sectPr"))
    children = list(body)
    after = False
    for child in children:
        if child is tbl1:
            after = True
            continue
        if after and child is not sect:
            body.remove(child)

    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    spacing.set(qn("w:line"), "240")
    spacing.set(qn("w:lineRule"), "auto")
    pPr.append(spacing)
    p.append(pPr)
    sect.addprevious(p)
    d.save(str(path))


def finalize(name, count):
    docx = OUT / f"NR6010T0101_{name}.docx"
    doc = OUT / f"NR6010T0101_{name}.doc"
    pdf = OUT / f"NR6010T0101_{name}.pdf"

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    wd = word.Documents.Open(str(docx), False, False, False)
    try:
        t = wd.Tables(1)
        for i in range(count):
            t.Cell(ITEM_FIRST + i, 1).Range.Text = str(i + 1)
        wd.SaveAs2(str(doc), 0)
        wd.ExportAsFixedFormat(str(pdf), 17)
    finally:
        wd.Close(False)
        word.Quit()

    d = fitz.open(str(pdf))
    for i, page in enumerate(d, 1):
        pix = page.get_pixmap(dpi=150)
        pix.save(str(pdf.with_name(f"{pdf.stem}_p{i}.png")))
    print(f"{name}: pdf_pages={len(d)}")


COUNTS = {"monthly": 10, "annual": 10, "weekly": len(WEEKLY)}

for name, kind in (("月次", "monthly"), ("年次", "annual"), ("週次", "weekly")):
    path = word_prepare(name, kind)
    docx_structure(path, kind)
    finalize(name, COUNTS[kind])
