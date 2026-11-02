#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx 全文インベントリ抽出ツール(読み取り専用)

- Excel COM 不使用。zipfile + XML 解析が本体。
- openpyxl は read_only=True の読み取り検証のみに使用(save は一切呼ばない)。
- 冊(xlsx)自体はいかなる場合も変更しない。
- シート名に「認証情報」を含むシートは、シート名・表示状態・印刷設定等の
  メタデータのみ記録し、セル内容は一切出力しない。

出力(xlsx_dump 配下):
  sheets_<冊名>.md            シート一覧表
  text_<冊名>_<シート名>.md   シートごとの全文テキスト
  summary_<冊名>.json         統計
  検証サンプル_<冊名>.md      目視点検用サンプル(各冊10シート)
"""

import argparse
import hashlib
import json
import os
import posixpath
import re
import sys
from collections import Counter
from datetime import datetime

import zipfile
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- 基礎関数

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

SHAPE_TAGS = ("sp", "pic", "grpSp", "cxnSp", "graphicFrame", "contentPart")
SHAPE_JA = {
    "sp": "図形(テキスト/オートシェイプ)",
    "pic": "画像",
    "grpSp": "グループ",
    "cxnSp": "コネクタ",
    "graphicFrame": "チャート/表",
    "contentPart": "その他パート",
}

PAPER = {1: "Letter", 5: "Legal", 8: "A3", 9: "A4", 11: "A5", 12: "B4(JIS)", 13: "B5(JIS)"}


def local(el):
    return el.tag.rsplit("}", 1)[-1]


def find_child(el, name):
    if el is None:
        return None
    for ch in el:
        if local(ch) == name:
            return ch
    return None


def findall_deep(el, name):
    if el is None:
        return []
    return [e for e in el.iter() if local(e) == name]


def col_to_num(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n


def num_to_col(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def parse_ref(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref or "")
    if not m:
        return None, None
    return int(m.group(2)), col_to_num(m.group(1))


def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", s).strip().strip(".")
    return s or "unnamed"


def resolve_target(base_dir, target):
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(base_dir, target))


# ---------------------------------------------------------------- sharedStrings

def parse_shared_strings(data):
    root = ET.fromstring(data)
    out = []
    for si in findall_deep(root, "si"):
        parts = []

        def walk(el):
            if local(el) == "rPh":  # ふりがな(ルビ)は本文から除外
                return
            if local(el) == "t":
                parts.append(el.text or "")
            for ch in el:
                walk(ch)

        walk(si)
        out.append("".join(parts))
    return out


# ---------------------------------------------------------------- 図形カウント

def drawing_counts(data):
    root = ET.fromstring(data)
    allc = Counter()
    for el in root.iter():
        t = local(el)
        if t in SHAPE_TAGS:
            allc[t] += 1
    top = Counter()
    for anchor in root:
        if local(anchor) in ("twoCellAnchor", "oneCellAnchor", "absoluteAnchor"):
            for child in anchor:
                t = local(child)
                if t in SHAPE_TAGS:
                    top[t] += 1
    return top, allc


# ---------------------------------------------------------------- 数式(共有数式の展開つき)

_REF_RE = re.compile(r"(\$?)([A-Z]{1,3})(\$?)(\d+)")


def translate_shared_formula(fml, d_row, d_col):
    """共有数式の基準式をセルオフセット分だけ平行移動する。
    文字列リテラル("...")内部は対象外。関数名(直後に括弧)は対象外。"""
    parts = re.split(r'("(?:[^"]|"")*")', fml)
    out = []
    for i, seg in enumerate(parts):
        if i % 2 == 1:  # クォート内部
            out.append(seg)
            continue

        def repl(m):
            d1, c1, d2, r1 = m.groups()
            if m.end() < len(seg) and seg[m.end()] == "(":
                return m.group(0)  # 関数名
            col = col_to_num(c1) if d1 == "$" else col_to_num(c1) + d_col
            row = int(r1) if d2 == "$" else int(r1) + d_row
            if col < 1 or row < 1:
                return "#REF!"
            return ("%s%s%s%d" % (d1, num_to_col(col), d2, row))

        out.append(_REF_RE.sub(repl, seg))
    return "".join(out)


# ---------------------------------------------------------------- シート解析

def parse_worksheet(data, shared, rel_drawing_targets, rel_vml_targets):
    """1シート分のセル内容とメタデータを抽出する。
    rel_drawing_targets / rel_vml_targets: シートrels由来のパスリスト(数は呼び出し側で保持)"""
    root = ET.fromstring(data)
    info = {}
    dim_el = find_child(root, "dimension")
    info["dimension"] = dim_el.get("ref") if dim_el is not None else None

    # ページ設定
    sheet_pr = find_child(root, "sheetPr")
    fit_to_page = None
    if sheet_pr is not None:
        psp = find_child(sheet_pr, "pageSetUpPr")
        if psp is not None:
            fit_to_page = psp.get("fitToPage")
    info["fit_to_page"] = (fit_to_page in ("1", "true"))

    pm = find_child(root, "pageMargins")
    info["margins"] = None
    if pm is not None:
        info["margins"] = {k: pm.get(k) for k in ("left", "right", "top", "bottom", "header", "footer") if pm.get(k) is not None}

    ps = find_child(root, "pageSetup")
    info["page_setup"] = None
    if ps is not None:
        info["page_setup"] = dict(ps.attrib)

    info["print_options"] = dict(find_child(root, "printOptions").attrib) if find_child(root, "printOptions") is not None else None
    info["header_footer"] = find_child(root, "headerFooter") is not None

    # 結合セル
    mc = find_child(root, "mergeCells")
    info["merge_count"] = int(mc.get("count")) if mc is not None else 0

    # セル
    rows = {}
    max_row = 0
    max_col = 0
    n_value_cells = 0
    n_formula_cells = 0
    n_empty_str = 0
    shared_map = {}  # si -> (base_ref, formula_text, ftype, ref_attr)

    sheet_data = find_child(root, "sheetData")
    if sheet_data is not None:
        for row_el in sheet_data.findall(NS_MAIN + "row"):
            for c in row_el:
                if local(c) != "c":
                    continue
                ref = c.get("r") or ""
                row, col = parse_ref(ref)
                if row is None:
                    continue
                if row > max_row:
                    max_row = row
                if col > max_col:
                    max_col = col

                f_el = find_child(c, "f")
                if f_el is not None:
                    n_formula_cells += 1
                    ftype = f_el.get("t")
                    ftext = f_el.text or ""
                    si = f_el.get("si")
                    fref = f_el.get("ref")
                    if ftext:
                        if ftype == "shared" and si is not None:
                            shared_map[si] = (ref, ftext, ftype, fref)
                        rows.setdefault(row, {})[col] = ("F", ftext, ref)
                    else:
                        if si is not None and si in shared_map:
                            base_ref, base_text, btype, _ = shared_map[si]
                            b_row, b_col = parse_ref(base_ref)
                            if btype == "array":
                                rows.setdefault(row, {})[col] = (
                                    "F", "[配列数式 si=%s の一部] 基準 %s" % (si, fref or base_ref), ref)
                            else:
                                d_row = row - b_row
                                d_col = col - b_col
                                rows.setdefault(row, {})[col] = (
                                    "F", translate_shared_formula(base_text, d_row, d_col), ref)
                        else:
                            rows.setdefault(row, {})[col] = ("F", "[空の数式定義]" if not fref else "[配列数式 %s の一部]" % fref, ref)
                    continue

                t = c.get("t")
                v_el = find_child(c, "v")
                is_el = find_child(c, "is")
                text = None
                if is_el is not None:
                    parts = [e.text or "" for e in is_el.iter() if local(e) == "t"]
                    text = "".join(parts)
                elif v_el is not None:
                    raw = v_el.text if v_el.text is not None else ""
                    if t == "s":
                        try:
                            text = shared[int(raw)]
                        except (ValueError, IndexError):
                            text = "[共有文字列取得失敗 index=%s]" % raw
                    elif t == "b":
                        text = "TRUE" if raw == "1" else "FALSE"
                    elif t in ("str", "e", "d"):
                        text = raw
                    else:
                        text = raw
                if text is None:
                    continue  # 書式のみのセル
                n_value_cells += 1
                if text == "":
                    n_empty_str += 1
                    continue  # 空文字列は出力しない(集計には数える)
                rows.setdefault(row, {})[col] = ("V", text, ref)

    info["rows"] = rows
    info["max_row"] = max_row
    info["max_col"] = max_col
    info["n_value_cells"] = n_value_cells
    info["n_formula_cells"] = n_formula_cells
    info["n_empty_str"] = n_empty_str
    info["n_used_cells"] = n_value_cells + n_formula_cells
    return info


# ---------------------------------------------------------------- 分類推定

def classify_sheet(name, n_val_cells, shape_total):
    if "認証情報" in name:
        return "除外(認証情報)"
    if "表紙" in name:
        base = "表紙"
    elif re.search(r"目次|一覧|リスト|用語", name):
        base = "リスト"
    elif re.search(r"相関図|構成図|フロー|図解", name):
        base = "図解"
    elif shape_total >= 3 and n_val_cells < 30 and shape_total >= n_val_cells:
        base = "図解"
    elif re.search(r"手順|様式|管理|点検|起動|停止|バックアップ|復旧|異常|構成|体制|チェック|付録|引用|照合|対応|サービス", name):
        base = "本文様式"
    else:
        base = "その他"
    suffix = ""
    low = name.lower()
    if "_old" in low or "旧版" in name:
        suffix = "(旧版)"
    elif re.search(r"仮|一時|ドラフト", name):
        suffix = "(暫定)"
    return base + suffix


# ---------------------------------------------------------------- 出力生成

def fmt_margins(m):
    if not m:
        return "なし"
    def g(k):
        try:
            return "%.2f" % float(m[k])
        except (KeyError, TypeError, ValueError):
            return "?"
    return "L%s/R%s/T%s/B%s" % (g("left"), g("right"), g("top"), g("bottom"))


def fmt_fit(info):
    ps = info.get("page_setup") or {}
    if info.get("fit_to_page"):
        fw = ps.get("fitToWidth", "1")
        fh = ps.get("fitToHeight", "1")
        return "Fit %sx%s" % (fw, fh)
    if ps.get("scale"):
        return "スケール%s%%" % ps["scale"]
    return "なし(既定100%)"


def fmt_orientation(info):
    ps = info.get("page_setup") or {}
    o = ps.get("orientation")
    if o == "landscape":
        return "横"
    if o == "portrait":
        return "縦"
    return "なし(規定値:縦)"


def build_text_md(book, sheet_name, state_ja, src_path, generated_at, info):
    lines = []
    lines.append("# text: %s / %s" % (book, sheet_name))
    lines.append("")
    lines.append("- 抽出元: %s" % src_path)
    lines.append("- 抽出日時: %s" % generated_at)
    lines.append("- シート状態: %s" % state_ja)
    lines.append("- 使用範囲(XML dimension属性): %s" % (info["dimension"] or "なし"))
    lines.append("- 実測(セル要素ベース): %d行 x %d列" % (info["max_row"], info["max_col"]))
    lines.append("- 値セル: %d(うち空文字列%d) / 数式セル: %d / 結合範囲: %d"
                 % (info["n_value_cells"], info["n_empty_str"], info["n_formula_cells"], info["merge_count"]))
    lines.append("- 方針: 値と数式文字列をそのまま列挙。書式のみのセルは省略。結合セルは左上の値のみ。")
    lines.append("  数式は「F: 」接頭で式の文字列のみ(結果値は出力しない)。セル内改行は改行文字のまま保持。")
    lines.append("")
    for row in sorted(info["rows"]):
        lines.append("## 行 %d" % row)
        for col in sorted(info["rows"][row]):
            kind, text, ref = info["rows"][row][col]
            if kind == "F":
                lines.append("- %s: F: %s" % (ref, text))
            else:
                lines.append("- %s: %s" % (ref, text))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- メイン

def process(xlsx_path, out_dir, sample_path):
    xlsx_path = os.path.abspath(xlsx_path)
    book = os.path.splitext(os.path.basename(xlsx_path))[0]
    generated_at = datetime.now().isoformat(timespec="seconds")

    with open(xlsx_path, "rb") as f:
        raw = f.read()
    sha256 = hashlib.sha256(raw).hexdigest()

    z = zipfile.ZipFile(xlsx_path)
    names = set(z.namelist())

    # ---- workbook.xml
    wb_root = ET.fromstring(z.read("xl/workbook.xml"))
    sheets_el = find_child(wb_root, "sheets")
    sheet_entries = []
    for s in sheets_el:
        sheet_entries.append({
            "name": s.get("name"),
            "state": s.get("state") or "visible",
            "rid": s.get(NS_R + "id"),
        })

    # ---- workbook rels
    rels_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {}
    for rel in rels_root:
        rid_to_target[rel.get("Id")] = rel.get("Target")

    # ---- defined names
    print_area = {}
    print_titles = {}
    for dn in findall_deep(wb_root, "definedName"):
        nm = dn.get("name")
        lsid = dn.get("localSheetId")
        if lsid is None:
            continue
        text = (dn.text or "").strip()
        if nm == "_xlnm.Print_Area":
            print_area.setdefault(int(lsid), []).append(text)
        elif nm == "_xlnm.Print_Titles":
            print_titles.setdefault(int(lsid), []).append(text)

    # ---- sharedStrings
    shared = parse_shared_strings(z.read("xl/sharedStrings.xml")) if "xl/sharedStrings.xml" in names else []

    # ---- media / printerSettings / vml(冊単位)
    media_files = sorted(n for n in names if n.startswith("xl/media/"))
    printer_files = sorted(n for n in names if n.startswith("xl/printerSettings/"))
    vml_files = sorted(n for n in names if "vmlDrawing" in n)

    results = []
    used_text_names = set()

    for idx, entry in enumerate(sheet_entries):
        name = entry["name"]
        state = entry["state"]
        state_ja = "表示" if state in ("visible",) else ("非表示(%s)" % state)
        target = rid_to_target.get(entry["rid"])
        ws_path = resolve_target("xl", target)
        excluded = "認証情報" in name

        # シート rels
        sheet_rels_path = posixpath.join(posixpath.dirname(ws_path), "_rels", posixpath.basename(ws_path) + ".rels")
        drawing_paths, vml_paths = [], []
        if sheet_rels_path in names:
            sr = ET.fromstring(z.read(sheet_rels_path))
            for rel in sr:
                t = rel.get("Type", "")
                tgt = rel.get("Target", "")
                base = posixpath.dirname(ws_path)
                if t.endswith("/drawing"):
                    drawing_paths.append(resolve_target(base, tgt))
                elif t.endswith("/vmlDrawing"):
                    vml_paths.append(resolve_target(base, tgt))

        info = None
        top_shapes, all_shapes = Counter(), Counter()
        if not excluded:
            info = parse_worksheet(z.read(ws_path), shared, drawing_paths, vml_paths)
        for dp in drawing_paths:
            if dp in names:
                top_s, all_s = drawing_counts(z.read(dp))
                top_shapes.update(top_s)
                all_shapes.update(all_s)

        shape_total_top = sum(top_shapes[t] for t in SHAPE_TAGS)
        pic_total = all_shapes["pic"]

        cls = classify_sheet(name, info["n_value_cells"] if info else 0, shape_total_top)

        pa = print_area.get(idx) or []
        pt = print_titles.get(idx) or []

        results.append({
            "index": idx,
            "name": name,
            "state": state,
            "state_ja": state_ja,
            "worksheet_part": ws_path,
            "excluded": excluded,
            "info": info,
            "top_shapes": top_shapes,
            "all_shapes": all_shapes,
            "shape_total_top": shape_total_top,
            "pic_total": pic_total,
            "category": cls,
            "print_area": pa,
            "print_titles": pt,
            "drawing_parts": drawing_paths,
            "vml_parts": vml_paths,
        })

    os.makedirs(out_dir, exist_ok=True)

    # ---- sheets_<冊名>.md
    md = []
    md.append("# sheets: %s" % book)
    md.append("")
    md.append("- 抽出元: %s" % xlsx_path)
    md.append("- SHA-256: %s" % sha256)
    md.append("- 抽出日時: %s" % generated_at)
    md.append("- シート数: %d(表示%d / 非表示%d)" % (
        len(results),
        sum(1 for r in results if r["state"] == "visible"),
        sum(1 for r in results if r["state"] != "visible"),
    ))
    md.append("- 項目が見つからない場合は「なし」と明記。")
    md.append("- 使用行数·使用列数: セル要素(書式のみを含む)の実測最大行·最大列。")
    md.append("- 図形数: シートに紐づく描画XMLのトップレベル描画オブジェクト数(グループは1個と数える)。")
    md.append("- 画像数: 描画XML内の全階層の画像(pic)数。冊全体のメディアファイル数は summary を参照。")
    md.append("- シート名に「認証情報」を含むシートは内容(セル·テキスト)を出力しないため、セル系統計は「除外」。")
    md.append("")
    md.append("| # | シート名 | 表示/非表示 | 使用行数 | 使用列数 | 値セル数 | 向き | FitToPages/スケール | 印刷範囲 | タイトル行 | 余白(インチ L/R/T/B) | 図形数 | 画像数 | 分類推定 |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        info = r["info"]
        if info is None:
            rows_s = cols_s = vals_s = "除外"
            dim = "(除外)"
            fit = "除外"
            ori = "除外"
        else:
            rows_s = str(info["max_row"])
            cols_s = str(info["max_col"])
            vals_s = str(info["n_value_cells"])
            dim = info["dimension"] or "なし"
            fit = fmt_fit(info)
            ori = fmt_orientation(info)
        pa = ", ".join(r["print_area"]) if r["print_area"] else "なし"
        pt = ", ".join(r["print_titles"]) if r["print_titles"] else "なし"
        margins = fmt_margins((info or {}).get("margins")) if info else "除外"
        md.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d | %d | %s |" % (
            r["index"] + 1, r["name"], r["state_ja"], rows_s, cols_s, vals_s,
            ori, fit, pa, pt, margins, r["shape_total_top"], r["pic_total"], r["category"],
        ))
    sheets_md_path = os.path.join(out_dir, "sheets_%s.md" % book)
    with open(sheets_md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")

    # ---- text_<冊名>_<シート名>.md
    for r in results:
        if r["excluded"]:
            continue
        base = safe_name(r["name"])
        fname = "text_%s_%s.md" % (book, base)
        k = 2
        while fname in used_text_names:
            fname = "text_%s_%s_%d.md" % (book, base, k)
            k += 1
        used_text_names.add(fname)
        r["text_file"] = fname
        content = build_text_md(book, r["name"], r["state_ja"], xlsx_path, generated_at, r["info"])
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    # ---- summary_<冊名>.json
    cat_counts = Counter(r["category"] for r in results)
    ori_counts = Counter()
    fit_cnt = scale_cnt = none_fit_cnt = 0
    area_cnt = titles_cnt = margins_cnt = 0
    for r in results:
        if r["excluded"]:
            continue
        ps = (r["info"].get("page_setup") or {})
        o = ps.get("orientation")
        ori_counts["横" if o == "landscape" else ("縦" if o == "portrait" else "明記なし(規定:縦)")] += 1
        f = fmt_fit(r["info"])
        if f.startswith("Fit"):
            fit_cnt += 1
        elif f.startswith("スケール"):
            scale_cnt += 1
        else:
            none_fit_cnt += 1
        if r["print_area"]:
            area_cnt += 1
        if r["print_titles"]:
            titles_cnt += 1
        if r["info"].get("margins"):
            margins_cnt += 1

    sheets_json = []
    for r in results:
        info = r["info"]
        item = {
            "index": r["index"],
            "name": r["name"],
            "visibility": r["state"],
            "category_estimate": r["category"],
            "excluded_credentials": r["excluded"],
            "worksheet_part": r["worksheet_part"],
            "print_area": r["print_area"] or None,
            "print_titles": r["print_titles"] or None,
            "drawing_parts": r["drawing_parts"],
            "vml_parts": r["vml_parts"],
            "shapes_top_level": {SHAPE_JA[k]: r["top_shapes"][k] for k in SHAPE_TAGS if r["top_shapes"][k]},
            "shapes_top_level_total": r["shape_total_top"],
            "pic_count_all_levels": r["pic_total"],
        }
        if info is not None:
            ps = info.get("page_setup") or {}
            item.update({
                "dimension_attr": info["dimension"],
                "used_rows_max": info["max_row"],
                "used_cols_max": info["max_col"],
                "value_cells": info["n_value_cells"],
                "empty_string_cells": info["n_empty_str"],
                "formula_cells": info["n_formula_cells"],
                "merged_ranges": info["merge_count"],
                "print": {
                    "orientation": ps.get("orientation") or None,
                    "paper_size": (PAPER.get(int(ps["paperSize"]), ps["paperSize"]) if ps.get("paperSize") else None),
                    "fit_to_page": info["fit_to_page"],
                    "fit_to_width": ps.get("fitToWidth"),
                    "fit_to_height": ps.get("fitToHeight"),
                    "scale": ps.get("scale"),
                    "margins_inch": info["margins"],
                    "header_footer_present": info["header_footer"],
                    "print_options": info["print_options"],
                },
                "text_file": r.get("text_file"),
            })
        else:
            item.update({
                "dimension_attr": None, "used_rows_max": None, "used_cols_max": None,
                "value_cells": None, "empty_string_cells": None, "formula_cells": None,
                "merged_ranges": None, "print": None, "text_file": None,
                "note": "セル内容·セル統計は認証情報シートのため出力·集計対象外",
            })
        sheets_json.append(item)

    summary = {
        "book": book,
        "source_file": xlsx_path,
        "source_size_bytes": len(raw),
        "source_sha256": sha256,
        "generated_at": generated_at,
        "tool": "extract_xlsx_inventory.py (zipfile+XML解析 / openpyxl read_only による検証, 保存なし)",
        "sheet_count": len(results),
        "visible_sheet_count": sum(1 for r in results if r["state"] == "visible"),
        "hidden_sheet_count": sum(1 for r in results if r["state"] != "visible"),
        "category_counts": dict(cat_counts),
        "totals": {
            "value_cells": sum(r["info"]["n_value_cells"] for r in results if r["info"]),
            "empty_string_cells": sum(r["info"]["n_empty_str"] for r in results if r["info"]),
            "formula_cells": sum(r["info"]["n_formula_cells"] for r in results if r["info"]),
            "merged_ranges": sum(r["info"]["merge_count"] for r in results if r["info"]),
            "shapes_top_level_total": sum(r["shape_total_top"] for r in results),
            "shapes_by_type_all_levels": {SHAPE_JA[k]: sum(r["all_shapes"][k] for r in results) for k in SHAPE_TAGS},
            "pic_count_all_levels_total": sum(r["pic_total"] for r in results),
            "media_files": len(media_files),
            "vml_files": len(vml_files),
            "printer_settings_files": len(printer_files),
        },
        "print_settings_distribution": {
            "orientation": dict(ori_counts),
            "fit_to_pages_sheets": fit_cnt,
            "scale_sheets": scale_cnt,
            "no_fit_no_scale_sheets": none_fit_cnt,
            "print_area_sheets": area_cnt,
            "print_titles_sheets": titles_cnt,
            "margins_present_sheets": margins_cnt,
            "note": "認証情報シートは集計対象外。該当なしなら 0。",
        },
        "credentials_sheet_policy": "シート名に「認証情報」を含むシートはセル内容を一切出力しない(シート名·表示状態·印刷設定等のメタデータのみ記録)",
        "sheets": sheets_json,
    }
    summary_path = os.path.join(out_dir, "summary_%s.json" % book)
    with open(summary_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # ---- openpyxl read_only によるクロスチェック(保存は絶対にしない)
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path, read_only=True, data_only=False, keep_vba=False, rich_text=False)
    wb_names = list(wb.sheetnames)
    xlsx_names = [r["name"] for r in results]
    check_names = (wb_names == xlsx_names)
    openpyxl_counts = {}
    dim_check = []
    for ws in wb.worksheets:
        n = 0
        for row in ws.iter_rows(values_only=True):
            for v in row:
                if v is not None:
                    n += 1
        openpyxl_counts[ws.title] = n
        try:
            dim_check.append((ws.title, ws.calculate_dimension()))
        except Exception:
            dim_check.append((ws.title, "計算不能"))
    wb.close()

    xml_counts = {}
    for r in results:
        if r["info"]:
            xml_counts[r["name"]] = r["info"]["n_value_cells"] + r["info"]["n_formula_cells"]
        else:
            xml_counts[r["name"]] = None
    diff_sheets = []
    for nm in xlsx_names:
        if xml_counts.get(nm) is None:
            continue  # 認証情報シートは内容比較の対象外
        a, b = xml_counts.get(nm, 0), openpyxl_counts.get(nm, 0)
        if a != b:
            diff_sheets.append((nm, a, b))

    # ---- 検証サンプル(各冊10シート, 均等抽出)
    cand = [r for r in results if not r["excluded"]]
    n = len(cand)
    k = min(10, n)
    picked = [cand[round(i * (n - 1) / (k - 1))] for i in range(k)] if k > 1 else cand
    smp = []
    smp.append("# 検証サンプル(文字化け目視点検用): %s" % book)
    smp.append("")
    smp.append("- 抽出元: %s" % xlsx_path)
    smp.append("- 対象: 全%dシート(認証情報シート除く)から均等抽出した%dシート" % (n, k))
    smp.append("- 各シートの先頭60行分(またはテキスト全体)を転載")
    smp.append("")
    for r in picked:
        smp.append("## %s(%s)" % (r["name"], r["text_file"]))
        smp.append("")
        body = build_text_md(book, r["name"], r["state_ja"], xlsx_path, generated_at, r["info"]).splitlines()
        if len(body) > 70:
            smp.extend(body[:70])
            smp.append("...(後略: 全文は text ファイルを参照)")
        else:
            smp.extend(body)
        smp.append("")
    sample_file = os.path.join(out_dir, "検証サンプル_%s.md" % book)
    with open(sample_file, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(smp) + "\n")

    # ---- コンソール報告(認証情報シートの内容は一切出力しない)
    print("=" * 60)
    print("book: %s" % book)
    print("  sheets: %d (visible %d / hidden %d)" % (
        len(results), summary["visible_sheet_count"], summary["hidden_sheet_count"]))
    print("  value_cells(non-empty)=%d + empty_str=%d + formulas=%d" % (
        summary["totals"]["value_cells"], summary["totals"]["empty_string_cells"], summary["totals"]["formula_cells"]))
    print("  categories: %s" % json.dumps(summary["category_counts"], ensure_ascii=False))
    print("  shapes(top-level total)=%d  pic(all levels)=%d  media=%d  vml=%d" % (
        summary["totals"]["shapes_top_level_total"], summary["totals"]["pic_count_all_levels_total"],
        summary["totals"]["media_files"], summary["totals"]["vml_files"]))
    print("  print: area=%d sheets, titles=%d sheets, fit=%d, scale=%d, none=%d" % (
        area_cnt, titles_cnt, fit_cnt, scale_cnt, none_fit_cnt))
    print("  openpyxl sheet-name check: %s" % ("OK" if check_names else "NG"))
    print("  cell-count diff (XML vs openpyxl): %s" % ("none" if not diff_sheets else diff_sheets))
    print("  outputs: %s" % sheets_md_path)
    print("            %s" % summary_path)
    print("            text files: %d" % len(used_text_names))
    print("            sample: %s" % sample_file)
    z.close()

    return {
        "book": book,
        "xlsx_path": xlsx_path,
        "sheets_md": sheets_md_path,
        "summary": summary_path,
        "text_files": sorted(used_text_names),
        "sample": sample_file,
        "diff_sheets": diff_sheets,
        "check_names": check_names,
        "summary_json": summary,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = process(args.xlsx, args.out, None)
    print("DONE %s" % res["book"])


if __name__ == "__main__":
    main()
