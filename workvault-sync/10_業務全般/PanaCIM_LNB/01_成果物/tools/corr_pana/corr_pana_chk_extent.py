# -*- coding: utf-8 -*-
"""Read-only check: does the built diagram fit within column AZ?
Parses the xlsx zip directly (no COM, no Excel start):
  1. column grid -> cumulative right edge (pt) per column
  2. drawing anchors (exact col/colOff of every shape) -> max right edge
  3. marks where key design x-values (650/656/664/687.5/750pt) fall
Assumption: MDW=7px (Calibri-11-like default); anchors are exact regardless.
"""
import zipfile, sys, io
from xml.etree import ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana.xlsx"
NSM   = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NSR   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSXDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
MDW = 7.0
EMU_PER_PX = 9525.0

def col_letter(idx1):
    s = ""
    while idx1 > 0:
        idx1, r = divmod(idx1 - 1, 26)
        s = chr(65 + r) + s
    return s

def col_index(letter):
    n = 0
    for ch in letter.upper():
        n = n * 26 + (ord(ch) - 64)
    return n

def px_of_width(w):
    if w < 1:
        return 12
    return int(round(w * MDW)) + 5

def resolve(base_dir, target):
    parts = (base_dir + "/" + target).split("/")
    out = []
    for p in parts:
        if p == "..":
            if out:
                out.pop()
        elif p in ("", "."):
            pass
        else:
            out.append(p)
    return "/".join(out)

z = zipfile.ZipFile(PATH)
wb = ET.fromstring(z.read("xl/workbook.xml"))
rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
relmap = {r.get("Id"): r.get("Target") for r in rels}

print("== defined names ==")
for dn in wb.iter("{%s}definedName" % NSM):
    print("  %s = %s" % (dn.get("name"), dn.text))

sheets = []
for sh in wb.iter("{%s}sheet" % NSM):
    rid = sh.get("{%s}id" % NSR)
    t = relmap[rid].lstrip("/")
    if not t.startswith("xl/"):
        t = "xl/" + t
    sheets.append((sh.get("name"), t))
print("sheets:", [n for n, _ in sheets])

AZ = col_index("AZ")
AY = col_index("AY")

for name, sheet_path in sheets:
    print("=" * 72)
    print("SHEET: %s  (%s)" % (name, sheet_path))
    sx = ET.fromstring(z.read(sheet_path))
    fmt = sx.find("{%s}sheetFormatPr" % NSM)
    defw = 8.43
    if fmt is not None and fmt.get("defaultColWidth"):
        defw = float(fmt.get("defaultColWidth"))
    print("  defaultColWidth=%s" % defw)

    widths = {}
    hidden = []
    for c in sx.iter("{%s}col" % NSM):
        mn, mx = int(c.get("min")), int(c.get("max"))
        w = float(c.get("width")) if c.get("width") is not None else defw
        for i in range(mn, min(mx, 70) + 1):
            widths[i] = w
            if c.get("hidden") == "1":
                hidden.append(col_letter(i))
    if hidden:
        print("  hidden columns: %s" % ",".join(hidden))

    B = [0.0]
    for i in range(1, 71):
        w = widths.get(i, defw)
        B.append(B[-1] + px_of_width(w) * 0.75)

    print("  column right edges (pt):")
    for i in list(range(1, 15)) + list(range(34, 58)):
        print("    %-3s %8.2f" % (col_letter(i), B[i]), end="")
        if (i % 4) == 0:
            print()
    print()
    print("  AY right edge = %.2f pt / AZ right edge = %.2f pt" % (B[AY], B[AZ]))

    marks = [(0, "canvas L"), (220, "n08.R"), (390, "container.R"), (430, "n09.L"),
             (650, "n09.R"), (656, "E03 descent x"), (664, "E09 descent x"),
             (685, "E17 label R"), (687.5, "E17 lane R"), (750, "canvas R")]
    print("  key x-values -> column:")
    for x, label in marks:
        c = 1
        while c < 70 and B[c] < x:
            c += 1
        print("    %7.1f pt (%s) -> col %s" % (x, label, col_letter(c)))

    ps = sx.find("{%s}pageSetup" % NSM)
    if ps is not None:
        print("  pageSetup:", dict(ps.attrib))
    pm = sx.find("{%s}pageMargins" % NSM)
    if pm is not None:
        print("  pageMargins:", dict(pm.attrib))
    sp = sx.find("{%s}sheetPr" % NSM)
    if sp is not None:
        psp = sp.find("{%s}pageSetUpPr" % NSM)
        if psp is not None:
            print("  pageSetUpPr:", dict(psp.attrib))

    base_dir = sheet_path.rsplit("/", 1)[0]
    rels_path = base_dir + "/_rels/" + sheet_path.rsplit("/", 1)[1] + ".rels"
    try:
        srels = ET.fromstring(z.read(rels_path))
    except KeyError:
        print("  (no drawing)")
        continue
    dpaths = [resolve(base_dir, r.get("Target")) for r in srels
              if r.get("Type", "").endswith("/drawing")]
    if not dpaths:
        print("  (no drawing)")
        continue
    for dpath in dpaths:
        print("  DRAWING: %s" % dpath)
        dx = ET.fromstring(z.read(dpath))
        shapes = []
        for anchor in dx:
            frm = anchor.find("{%s}from" % NSXDR)
            if frm is None:
                continue
            to = anchor.find("{%s}to" % NSXDR)
            def cell(el):
                return (int(el.find("{%s}col" % NSXDR).text),
                        int(el.find("{%s}colOff" % NSXDR).text),
                        int(el.find("{%s}row" % NSXDR).text),
                        int(el.find("{%s}rowOff" % NSXDR).text))
            fc, fco, fr, fro = cell(frm)
            tc, tco, tr, tro = cell(to) if to is not None else (fc, fco, fr, fro)
            x0 = B[fc] + fco / EMU_PER_PX * 0.75
            x1 = B[tc] + tco / EMU_PER_PX * 0.75
            nm = [n.get("name") for n in anchor.iter("{%s}cNvPr" % NSXDR)]
            shapes.append((nm[0] if nm else "?", fc, tc, x0, x1, fr, tr))
        print("    shapes: %d" % len(shapes))
        shapes.sort(key=lambda s: -s[4])
        for s in shapes[:12]:
            print("      right=%8.2f pt  col %s..%s  x %7.1f..%7.1f  rows %2d..%2d  %s"
                  % (s[4], col_letter(s[1] + 1), col_letter(s[2] + 1), s[3], s[4], s[5] + 1, s[6] + 1, s[0]))
        maxrow = max(s[6] + 1 for s in shapes)
        print("    max row used by shapes: %d" % maxrow)
        if shapes:
            mx = max(s[4] for s in shapes)
            c = 1
            while c < 70 and B[c] < mx:
                c += 1
            verdict = "OK (within AZ)" if c <= AZ else "** EXCEEDS AZ **"
            print("    MAX shape right edge = %.2f pt -> column %s  -> %s" % (mx, col_letter(c), verdict))
print("done")
