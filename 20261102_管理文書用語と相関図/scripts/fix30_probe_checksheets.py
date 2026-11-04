# -*- coding: utf-8 -*-
"""fix30_probe_checksheets.py — 計画§9 G-pass(G6·G3)実装前の読み取り専用プローブ。

対象:
- Pana チェックシート(月次・異常時) / LNB チェックシート(日次) / LNB チェックシート(月次・異常時):
  結合範囲·列幅·行高·値(A..N)·罫線マップ·塗色·ページ設定(印刷範囲·改ページ·余白·FirstPageNumber·ヘッダー/フッター)
- LNB 申し送り(認証情報): ページ設定のみ(値は出力しない)
- LNB 引用と部品照合: 行1-4の様式(フォント·結合·塗色·罫線·行高)+ページ設定(G3複製元)
- LNB 目次: 行6-22の行高·結合·A/B/C/Jセルのフォント(G3目次挿入)
- 要確認事項一覧(両冊): 最終行の行高·罫線·フォント·配置(G5新規行複製元)
- 両冊のシート順序

出力: scripts/fix30_probe_checksheets_report.json + 標準出力サマリ。ファイルは保存しない。
"""
import os, sys, json, hashlib

sys.stdout.reconfigure(encoding="utf-8")

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
PANA = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
LNB  = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
REPORT = os.path.join(WORK, "scripts", "fix30_probe_checksheets_report.json")

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

NC = 14  # A..N


def col_widths(ws, upto=52):
    out = {}
    for i in range(1, upto + 1):
        L = get_column_letter(i)
        dim = ws.column_dimensions.get(L)
        if dim is not None:
            out[L] = {"width": dim.width, "hidden": bool(dim.hidden)}
    return out


def row_heights(ws, r1, r2):
    out = {}
    for r in range(r1, r2 + 1):
        dim = ws.row_dimensions.get(r)
        if dim is not None and dim.height is not None:
            out[r] = round(dim.height, 2)
    return out


def merge_map(ws):
    out = []
    for mr in ws.merged_cells.ranges:
        out.append(str(mr))
    return sorted(out, key=lambda s: (int("".join(c for c in s.split(":")[0] if c.isdigit())), s))


def value_grid(ws, r1, r2):
    out = []
    for r in range(r1, r2 + 1):
        for c in range(1, NC + 1):
            v = ws.cell(row=r, column=c).value
            if v is not None and str(v) != "":
                out.append({"cell": f"{get_column_letter(c)}{r}", "v": str(v)})
    return out


def border_grid(ws, r1, r2):
    out = []
    for r in range(r1, r2 + 1):
        for c in range(1, NC + 1):
            cell = ws.cell(row=r, column=c)
            b = cell.border
            sides = ""
            for ch, side in (("L", b.left), ("R", b.right), ("T", b.top), ("B", b.bottom)):
                if side is not None and side.style:
                    sides += ch
            if sides:
                out.append({"cell": f"{get_column_letter(c)}{r}", "s": sides})
    return out


def fill_grid(ws, cells):
    out = {}
    for addr in cells:
        cell = ws[addr]
        f = cell.fill
        if f is not None and f.fill_type:
            rgb = None
            try:
                rgb = f.start_color.rgb if f.start_color else None
            except Exception:
                pass
            out[addr] = {"type": f.fill_type, "rgb": rgb if isinstance(rgb, str) else str(rgb)}
    return out


def font_info(ws, addr):
    cell = ws[addr]
    f = cell.font
    return {"name": f.name, "size": f.size, "bold": f.bold, "color": (f.color.rgb if f.color and isinstance(f.color.rgb, str) else None)}


def align_info(ws, addr):
    cell = ws[addr]
    a = cell.alignment
    return {"h": a.horizontal, "v": a.vertical, "wrap": a.wrap_text}


def page_info(ws):
    ps = ws.page_setup
    m = ws.page_margins
    breaks = []
    try:
        for br in ws.row_breaks.brk:
            breaks.append(int(br.id))
    except Exception:
        pass
    hf = {}
    try:
        hf = {"oddHeader": str(ws.oddHeader.center.text) if ws.oddHeader and ws.oddHeader.center else None,
              "oddFooter": str(ws.oddFooter.center.text) if ws.oddFooter and ws.oddFooter.center else None}
    except Exception:
        pass
    try:
        fpn = ps.firstPageNumber
        use_fp = bool(ps.useFirstPageNumber)
    except Exception:
        fpn, use_fp = None, None
    return {
        "print_area": ws.print_area,
        "orientation": ps.orientation,
        "paperSize": ps.paperSize,
        "fitToWidth": ps.fitToWidth, "fitToHeight": ps.fitToHeight,
        "scale": ps.scale,
        "firstPageNumber": fpn if fpn else None, "useFirstPageNumber": use_fp,
        "margins_in": {"left": m.left, "right": m.right, "top": m.top, "bottom": m.bottom,
                       "header": m.header, "footer": m.footer},
        "row_breaks": breaks,
        "headerFooter": hf,
        "title_rows": ws.print_title_rows,
    }


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


REP = {"pana": {}, "lnb": {}, "sha": {}}
PANA_CHECK = "チェックシート(月次・異常時)"
LNB_CHECKS = ["チェックシート(日次)", "チェックシート(月次・異常時)"]

print("[probe] SHA-256 計算中 ...", flush=True)
REP["sha"]["pana"] = sha256(PANA)
REP["sha"]["lnb"] = sha256(LNB)
print(f"  pana = {REP['sha']['pana'][:16]}...  lnb = {REP['sha']['lnb'][:16]}...", flush=True)

# ---------- Pana ----------
wbp = load_workbook(PANA, data_only=False)
REP["pana"]["sheetnames"] = wbp.sheetnames
ws = wbp[PANA_CHECK]
REP["pana"]["checksheet"] = {
    "merges": merge_map(ws),
    "col_widths": col_widths(ws),
    "row_heights": row_heights(ws, 1, 46),
    "values": value_grid(ws, 1, 46),
    "borders": border_grid(ws, 1, 46),
    "fills": fill_grid(ws, ["A6", "A11", "A21", "A36", "A42", "A7", "C7", "A12", "A23", "A37", "A43"]),
    "page": page_info(ws),
}
# 要確認事項一覧 最終行(複製元)
ws = wbp["要確認事項一覧"]
REP["pana"]["list_lastrow"] = {
    "row_heights": row_heights(ws, 33, 38),
    "borders_r36": border_grid(ws, 36, 36),
    "font_C36": font_info(ws, "C36"), "align_C36": align_info(ws, "C36"),
    "merges_r36": merge_map(ws),
    "page": page_info(ws),
}
del wbp
print("[probe] Pana 完了", flush=True)

# ---------- LNB ----------
wbl = load_workbook(LNB, data_only=False)
REP["lnb"]["sheetnames"] = wbl.sheetnames
for name in LNB_CHECKS:
    ws = wbl[name]
    REP["lnb"][name] = {
        "merges": merge_map(ws),
        "col_widths": col_widths(ws),
        "row_heights": row_heights(ws, 1, 32),
        "values": value_grid(ws, 1, 32),
        "borders": border_grid(ws, 1, 32),
        "fills": fill_grid(ws, ["A6", "A13", "A18", "A8", "A13", "A19", "A26", "A8", "A21"]),
        "page": page_info(ws),
    }
ws = wbl["申し送り(認証情報)"]
REP["lnb"]["cred_page"] = page_info(ws)          # 値は出力しない
ws = wbl["引用と部品照合"]
REP["lnb"]["quote_style"] = {
    "merges": merge_map(ws),
    "row_heights": row_heights(ws, 1, 6),
    "font_A1": font_info(ws, "A1"), "font_A2": font_info(ws, "W2"), "font_A3": font_info(ws, "A3"),
    "font_A4": font_info(ws, "A4"), "font_G4": font_info(ws, "G4"),
    "align_A1": align_info(ws, "A1"), "align_G4": align_info(ws, "G4"),
    "fills": fill_grid(ws, ["A1", "A2", "A3", "A4", "G4", "W2", "AU2", "W3", "AC3"]),
    "borders": border_grid(ws, 1, 4),
    "page": page_info(ws),
}
ws = wbl["目次"]
REP["lnb"]["toc"] = {
    "merges": merge_map(ws),
    "row_heights": row_heights(ws, 6, 22),
    "values": value_grid(ws, 6, 22),
    "fonts": {a: font_info(ws, a) for a in ["A19", "B19", "C19", "A20", "B20", "C20", "J19"]},
    "page": page_info(ws),
}
ws = wbl["要確認事項一覧"]
REP["lnb"]["list_lastrow"] = {
    "row_heights": row_heights(ws, 44, 48),
    "borders_r47": border_grid(ws, 47, 47),
    "font_C47": font_info(ws, "C47"), "align_C47": align_info(ws, "C47"),
    "merges_r47": merge_map(ws),
    "page": page_info(ws),
}
del wbl
print("[probe] LNB 完了", flush=True)

with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(REP, fh, ensure_ascii=False, indent=1)
print(f"[probe] 報告書出力: {REPORT}", flush=True)

# ---------- 標準出力サマリ ----------
print("\n=== サマリ ===", flush=True)
print("Pana sheets:", " / ".join(REP["pana"]["sheetnames"]), flush=True)
print("LNB  sheets:", " / ".join(REP["lnb"]["sheetnames"]), flush=True)
for key, rep in (("Pana", REP["pana"]["checksheet"]),) + tuple((n, REP["lnb"][n]) for n in LNB_CHECKS):
    print(f"\n-- {key} チェックシート --", flush=True)
    print(" page:", json.dumps(rep["page"], ensure_ascii=False), flush=True)
    print(" merges:", rep["merges"], flush=True)
    print(" row_heights:", rep["row_heights"], flush=True)
