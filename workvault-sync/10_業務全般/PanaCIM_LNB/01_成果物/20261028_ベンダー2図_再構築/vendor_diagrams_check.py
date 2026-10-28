# -*- coding: utf-8 -*-
"""vendor_diagrams_check.py — 保存済み vendor_diagrams_panaEE.xlsx の独立検証(読み取り専用で再オープン)。
検証項目:
  1) シート名·図形数(作成時記録と突合)
  2) 箱同士のbbox重なり(許容1pt·設計上の包含は白名帯で除外)
  3) 文字溢れ(BoundHeight <= Height-2·空文字/線は除外)
  4) 印刷設定(A4横·1頁fit·余白8mm·印刷範囲)
  5) 線の矢頭/破線仕様(確定線=塗り三角·例示線=破線無矢)
結果: vendor_diagrams_check_result.json
"""
import json, os, sys, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, "vendor_diagrams_panaEE.xlsx")
BUILD_JSON = os.path.join(HERE, "vendor_diagrams_build_result.json")
RESULT = os.path.join(HERE, "vendor_diagrams_check_result.json")

TOL = 1.0  # bbox重なり無視許容(pt) — 接触は重なりとみなさない

# 設計上の包含/跨りを許すペア(名前·順序不定)
WL = [
    # Sheet1: コンテナと子モジュール(外部I/Fは右枠に跨る)
    ("s1_container", "s1_mod_zairyo"), ("s1_container", "s1_mod_trace"),
    ("s1_container", "s1_mod_kado"), ("s1_container", "s1_mod_shogo"),
    ("s1_container", "s1_extif"),
    # Sheet1: 凡例パネルと子
    ("s1_leg_panel", "s1_leg_title"), ("s1_leg_panel", "s1_leg_sw1"),
    ("s1_leg_panel", "s1_leg_sw1_tx"), ("s1_leg_panel", "s1_leg_sw2"),
    ("s1_leg_panel", "s1_leg_sw2_tx"), ("s1_leg_panel", "s1_leg_sw3"),
    ("s1_leg_panel", "s1_leg_sw3_tx"), ("s1_leg_panel", "s1_leg_sw4"),
    ("s1_leg_panel", "s1_leg_sw4_tx"), ("s1_leg_panel", "s1_leg_sw5_ln"),
    ("s1_leg_panel", "s1_leg_sw5_tx"),
    # Sheet2: 帯と見出し·帯とノード(レーン配置)·凡例パネルと子
    ("s2_zone1", "s2_zone1_head"), ("s2_zone2", "s2_zone2_head"),
    ("s2_zone3", "s2_zone3_head"), ("s2_zone4", "s2_zone4_head"),
    ("s2_zone1", "s2_ilnb"), ("s2_zone2", "s2_ilnb"), ("s2_zone3", "s2_ilnb"),
    ("s2_zone1", "s2_note1"),
    ("s2_zone2", "s2_npmdgs"), ("s2_zone2", "s2_lnb"), ("s2_zone2", "s2_panasv"),
    ("s2_zone3", "s2_nip"), ("s2_zone4", "s2_plcpc"),
    ("s2_aux", "s2_auxlbl"), ("s2_aux", "s2_shuri"),
    ("s2_zone3", "s2_lbl_stub"), ("s2_zone4", "s2_lbl_stub"),  # 例示ラベルは帯境界に跨る
    # Sheet2: 内部網の帯(ユーザー決定2026-10-28) — 帯は上位網レーン枠と線を共有し、
    # LNBを包含(NPM-DGSは帯下端に跨り·iLNB·レーン見出しは背面で通過する設計)
    ("s2_band_naibu", "s2_zone2"), ("s2_band_naibu", "s2_zone2_head"),
    ("s2_band_naibu", "s2_ilnb"), ("s2_band_naibu", "s2_npmdgs"),
    ("s2_band_naibu", "s2_lnb"),     ("s2_band_naibu", "s2_band_naibu_lbl"), ("s2_band_naibu_lbl", "s2_zone2"),
    ("s2_leg_panel", "s2_leg_title"),
    ("s2_leg_panel", "s2_leg_n1_sw"), ("s2_leg_panel", "s2_leg_n1_tx"),
    ("s2_leg_panel", "s2_leg_n2_sw"), ("s2_leg_panel", "s2_leg_n2_tx"),
    ("s2_leg_panel", "s2_leg_n3_sw"), ("s2_leg_panel", "s2_leg_n3_tx"),
    ("s2_leg_panel", "s2_leg_n4_sw"), ("s2_leg_panel", "s2_leg_n4_tx"),
    ("s2_leg_panel", "s2_leg_n5_sw"), ("s2_leg_panel", "s2_leg_n5_tx"),
    ("s2_leg_panel", "s2_leg_key"),
]

# 線の期待仕様: name -> (arrow_style 期待値, dash 期待値 1=実線 4=破線)
LINES_S1 = {
    "s1_ln_data": (2, 1), "s1_ln_musen": (2, 1), "s1_ln_web": (2, 1),
    "s1_ln_fan1": (2, 1), "s1_ln_fan2": (2, 1), "s1_ln_fan3": (2, 1),
    "s1_leg_sw5_ln": (None, 1),
}
LINES_S2 = {"s2_ln_stub": (None, 4)}
EXP_COUNT = {"外部インターフェース構成": 60, "ネットワーク構成例": 38}  # 記録54+線6 / 記録37+線1(内部網帯+ラベル追加)

out = {"ok": False, "checks": [], "overlaps": [], "overflow": [], "lines": {}, "print": {}, "errors": []}

def chk(name, cond, detail=""):
    out["checks"].append({"name": name, "pass": bool(cond), "detail": detail})
    return bool(cond)

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", pid, flush=True)

try:
    wb = xl.Workbooks.Open(XLSX, 0, True)  # ReadOnly
    with open(BUILD_JSON, "r", encoding="utf-8") as f:
        build = json.load(f)

    for sname in ("外部インターフェース構成", "ネットワーク構成例"):
        ws = wb.Worksheets(sname)
        n = ws.Shapes.Count
        chk("count_" + sname, n == EXP_COUNT[sname], "live=%d expect=%d" % (n, EXP_COUNT[sname]))

        boxes = {}
        lines = {}
        for i in range(1, n + 1):
            shp = ws.Shapes(i)
            nm = shp.Name
            geo = {"l": round(shp.Left, 1), "t": round(shp.Top, 1),
                   "w": round(shp.Width, 1), "h": round(shp.Height, 1)}
            txt = ""
            try:
                txt = shp.TextFrame2.TextRange.Text
            except Exception:
                pass
            geo["text"] = txt
            is_line = False
            try:
                is_line = (int(shp.Type) == 9)  # msoLine
            except Exception:
                pass
            if is_line or abs(geo["h"]) < 0.5 or abs(geo["w"]) < 0.5:
                lines[nm] = geo
            else:
                boxes[nm] = geo

        # 作成時の記録に全キーが存在するか(欠落=保存時に失われた)
        rec_keys = set(build["sheets"][sname].keys())
        live_keys = set(boxes.keys()) | set(lines.keys())
        missing = sorted(rec_keys - live_keys)
        chk("names_" + sname, not missing, "missing=" + ",".join(missing))

        # 文字溢れ(空文字·線は除外)
        for nm, g in boxes.items():
            if not g["text"].strip():
                continue
            try:
                bh = ws.Shapes(nm).TextFrame2.TextRange.BoundHeight
            except Exception:
                continue
            if bh > g["h"] - 2:
                out["overflow"].append({"name": nm, "bound_h": round(bh, 1), "box_h": g["h"]})

        # 箱同士の重なり(白名帯除外)
        names = sorted(boxes.keys())
        for a_i in range(len(names)):
            for b_i in range(a_i + 1, len(names)):
                a, b = names[a_i], names[b_i]
                ga, gb = boxes[a], boxes[b]
                ox = min(ga["l"] + ga["w"], gb["l"] + gb["w"]) - max(ga["l"], gb["l"])
                oy = min(ga["t"] + ga["h"], gb["t"] + gb["h"]) - max(ga["t"], gb["t"])
                if ox > TOL and oy > TOL:
                    if (a, b) in WL or (b, a) in WL:
                        continue
                    out["overlaps"].append({"a": a, "b": b, "ox": round(ox, 1), "oy": round(oy, 1)})

        # 線の仕様
        exp = LINES_S1 if sname == "外部インターフェース構成" else LINES_S2
        for nm, (arrow, dash) in exp.items():
            g = lines.get(nm)
            if g is None:
                out["lines"][nm] = {"present": False}
                continue
            shp = ws.Shapes(nm)
            try:
                ast = shp.Line.EndArrowheadStyle
            except Exception:
                ast = None
            try:
                ds = shp.Line.DashStyle
            except Exception:
                ds = None
            okl = (arrow is None or int(ast) == arrow) and int(ds) == dash
            out["lines"][nm] = {"present": True, "arrow": ast, "dash": ds, "pass": bool(okl)}
            chk("line_" + nm, okl, "arrow=%s(expect %s) dash=%s(expect %s)" % (ast, arrow, ds, dash))

        # 印刷設定
        ps = ws.PageSetup
        m = 8 / 25.4 * 72.0
        pr = {"orientation": ps.Orientation, "paper": ps.PaperSize, "zoom": bool(ps.Zoom),
              "fit_w": ps.FitToPagesWide, "fit_h": ps.FitToPagesTall,
              "left": round(ps.LeftMargin, 1), "top": round(ps.TopMargin, 1),
              "print_area": ps.PrintArea}
        out["print"][sname] = pr
        okp = (int(pr["orientation"]) == 2 and int(pr["paper"]) == 9 and pr["zoom"] is False
               and int(pr["fit_w"]) == 1 and int(pr["fit_h"]) == 1
               and abs(pr["left"] - round(m, 1)) <= 0.2)
        chk("print_" + sname, okp, json.dumps(pr, ensure_ascii=False))

    chk("no_overlap", not out["overlaps"], "%d conflicts" % len(out["overlaps"]))
    chk("no_overflow", not out["overflow"], "%d boxes" % len(out["overflow"]))
    wb.Close(False)
    out["ok"] = all(c["pass"] for c in out["checks"])

finally:
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append("quit:" + repr(e)[:120])
    time.sleep(2)
    try:
        c2 = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in c2.stdout.upper():
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Stop-Process -Id %d -Force" % pid], capture_output=True)
            out["errors"].append("stopped residual EXCEL PID %d (Stop-Process -Id)" % pid)
    except Exception as e:
        out["errors"].append("cleanup:" + repr(e)[:120])

with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
for c in out["checks"]:
    print(("PASS" if c["pass"] else "FAIL"), c["name"], c["detail"][:100])
if out["overlaps"]:
    print("overlaps:", out["overlaps"])
if out["overflow"]:
    print("overflow:", out["overflow"])
print("errors:", out["errors"])
