# -*- coding: utf-8 -*-
"""corr_lnb_17_add_icons.py(v2) — icon_map.md 標準配置での機器アイコン統合。

標準配置: ノード左端の内側 8pt·垂直中央·14pt 正方(Tier 1)。テキストはアイコンの右 6pt から
(=TextFrame2.MarginLeft を 2→28 へ変更)。ノードテキストは 2 段落(ラベル 11pt+備考 8pt)で
密度が高いため、インデントによる再折返しで BoundHeight が形高-2pt を超えた場合は段階的に
フォールバックする(Pana-CIM Stage 5 の N17 ラベル 10pt フォールバックと同じ先行例):
  Tier 1 (14pt·余白28): 行送り 0.75→0.6 → 備考 7.5pt → ラベル 10pt → ラベル 9.5pt
  Tier 2 (12pt·余白22): 行送り 0.6 → 備考 7.5pt → ラベル 10pt → ラベル 9.5pt → 備考 7.0pt
(Tier 2 は実測に基づく: h26 ノード n08·n19 は 14pt+28余白では備考 8pt が 1 行に入らず、
 ラベル維持を優先してアイコンを 12pt へ下げる。備考 7.0pt の最終段は n19 のみで到達
 (備考が約 205pt 超·高 26pt で、余白 18 まで下げるとアイコンと文字が重なるため)。
 アイコン左端内側 8pt は Tier 間で共通)
全段失敗時はそのノードを「アイコンなし」で退避し(MarginLeft 2·元サイズ·行送り 0.75→0.6 の
構築時状態を再現)、skipped_fit に記録する。図形の矩形(幾何)は一切変更しない。
アイコンは validator のモデル外のため、追加後はレンダでの目視点検を行う。

個別ルール(icons_manifest.json):
  mode=head : n01_esxi(容器·テキスト上端·内部に N02〜N04 を収める)は垂直中央だと N02 と
              衝突するため、見出し行の左 (x+8, y+1) に配置する。
  skipped   : band_*_head は #404040 塗りのため同色アイコンが視認不可(単色規定)。
              n05_note は注記ボックス。状態バッジは適用中ノードなし(任意)。

使い方: python corr_lnb_17_add_icons.py <対象.xlsx> [--result 出力json]
注意: 対象シートに icon_* 図形が既にある場合は停止(再実行保護)。画像は埋め込み
(AddPicture LinkToFile=False·SaveWithDocument=True)。グリッド(行高·列幅)は変更しない。
"""
import json
import os
import sys
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANIFEST = os.path.join(HERE, "icons_manifest.json")
SHEET = "相関図"
SIZE = 14.0
INSET = 8.0
INDENT = 28.0  # INSET(8) + SIZE(14) + テキスト間隔(6)

OUT_DEFAULT = os.path.join(HERE, "corr_lnb_17_icons_result.json")


def main():
    target = os.path.abspath(sys.argv[1])
    result_path = OUT_DEFAULT
    if "--result" in sys.argv:
        result_path = sys.argv[sys.argv.index("--result") + 1]
    man = json.load(open(MANIFEST, encoding="utf-8"))
    icons_dir = man["icons_dir"]
    out = {"ok": False, "target": target, "pid": None, "anchor": None,
           "nodes": {}, "skipped_fit": [], "pre": {},
           "assert_fails": [], "errors": []}

    import win32com.client
    import win32process
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
    print("EXCEL PID", out["pid"], flush=True)

    def quit_and_cleanup():
        try:
            xl.Quit()
        except Exception as e:
            out["errors"].append(("quit: %r" % e)[:80])
        time.sleep(2)
        try:
            chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]],
                                 capture_output=True, text=True)
            if "EXCEL" in chk.stdout.upper():
                subprocess.run(["taskkill", "/PID", str(out["pid"]), "/F"], capture_output=True)
                out["cleanup"] = "killed residual %d" % out["pid"]
        except Exception as e:
            out["errors"].append(("cleanup: %r" % e)[:80])

    try:
        wb = xl.Workbooks.Open(target)
        try:
            wb.AutoSaveOn = False  # OneDrive 配下で中途状態が勝手に保存されるのを防ぐ(ERR-20261102-001)
        except Exception:
            pass
        ws = wb.Worksheets(SHEET)
        X0 = float(ws.Range("B11").Left)
        Y0 = float(ws.Range("B11").Top)
        out["anchor"] = [round(X0, 1), round(Y0, 1)]

        names = [ws.Shapes.Item(i).Name for i in range(1, ws.Shapes.Count + 1)]
        if any(n.startswith("icon_") for n in names):
            out["assert_fails"].append("icon_* shapes already exist (re-run guard)")
            raise RuntimeError("re-run guard")
        out["base_shape_count"] = ws.Shapes.Count

        for node, spec in man["nodes"].items():
            try:
                shp = ws.Shapes(node)
            except Exception:
                out["assert_fails"].append("node shape missing: %s" % node)
                continue
            h = float(shp.Height)
            w = float(shp.Width)
            tf2 = shp.TextFrame2

            # --- 事前状態の記録と検査 ---
            ml = float(tf2.MarginLeft)
            # win32com は段落分離を \n (LF) として返す(構築時の \r とは異なる)ため正規化する。
            # Characters の文字位置は内部テキスト_stream 基準で、構築時と同じく段落=1文字の分離。
            raw = str(tf2.TextRange.Text).replace("\r\n", "\n").replace("\r", "\n")
            paras = [p for p in raw.split("\n")]
            while paras and paras[-1] == "":
                paras.pop()
            if len(paras) != 2:
                out["assert_fails"].append("%s: paragraph count %d != 2" % (node, len(paras)))
                continue
            tfo = shp.TextFrame
            pos = 1
            sizes = []
            for pt in paras:
                sizes.append(float(tfo.Characters(pos, len(pt)).Font.Size))
                pos += len(pt) + 1
            bh0 = float(tf2.TextRange.BoundHeight)
            pre_ok = (abs(ml - 2.0) <= 0.3) and (bh0 <= h - 2.0 + 0.01)
            out["pre"][node] = {"margin": round(ml, 2), "sizes": sizes,
                                "bound": round(bh0, 2), "pre_fit_ok": pre_ok}
            if not pre_ok:
                out["assert_fails"].append("%s: unexpected pre state (margin %.2f, bound %.2f/%.1f)"
                                           % (node, ml, bh0, h - 2))
                continue

            # --- フォールバック連鎖(余白·サイズは各段で絶対値を明示) ---
            def bound():
                return float(tf2.TextRange.BoundHeight)

            def set_space(sp):
                tf2.TextRange.ParagraphFormat.SpaceWithin = sp

            def set_sizes(ls, ns):
                p = 1
                for pt, s in zip(paras, (ls, ns)):
                    tfo.Characters(p, len(pt)).Font.Size = s
                    p += len(pt) + 1

            sL, sN = sizes
            l10 = min(sL, 10.0)
            # Tier1 (14pt·余白28): 0.75 → 0.6 → 備考7.5 → ラベル10+備考7.5 → 9.5+7.5
            # Tier2 (12pt·余白22): ラベル維持を優先して再試行
            #   (実測: h26ノード n08·n19 は 14pt+28余白では備考8ptが1行に入らない)
            steps = [
                (1, 28.0, sL, sN, 0.75),
                (1, 28.0, sL, sN, 0.6),
                (1, 28.0, sL, 7.5, 0.6),
                (1, 28.0, l10, 7.5, 0.6),
                (1, 28.0, 9.5, 7.5, 0.6),
                (2, 22.0, sL, sN, 0.6),
                (2, 22.0, sL, 7.5, 0.6),
                (2, 22.0, l10, 7.5, 0.6),
                (2, 22.0, 9.5, 7.5, 0.6),
                (2, 22.0, sL, 7.0, 0.6),
            ]
            final = None
            tried = []
            for tier, margin, ls, ns, sp in steps:
                tf2.MarginLeft = margin
                set_sizes(ls, ns)
                set_space(sp)
                bh = bound()
                tried.append({"tier": tier, "margin": margin, "label_pt": ls,
                              "note_pt": ns, "space": sp, "bound": round(bh, 2)})
                if bh <= h - 2.0 + 0.01:
                    final = (tier, margin, ls, ns, sp, bh)
                    break

            if final is not None:
                tier, margin, ls, ns, sp, bh = final
                icon_size = SIZE if tier == 1 else 12.0
                tf2.MarginLeft = margin
                png = os.path.join(icons_dir, spec["png"])
                if not os.path.exists(png):
                    out["assert_fails"].append("png missing: %s" % png)
                    # テキスト状態を構築時へ戻してから次へ
                    tf2.MarginLeft = 2.0
                    set_sizes(sL, sN)
                    set_space(0.75 if bh0 <= h - 2.0 + 0.01 else 0.6)
                    continue
                mode = spec.get("mode", "std")
                left = float(shp.Left) + INSET
                top = float(shp.Top) + 1.0 if mode == "head" else float(shp.Top) + (h - icon_size) / 2.0
                pic = ws.Shapes.AddPicture(png, 0, -1, left, top, icon_size, icon_size)
                pic.Name = "icon_" + node
                il, it = float(pic.Left), float(pic.Top)
                iw, ih = float(pic.Width), float(pic.Height)
                if (il < float(shp.Left) - 0.1 or it < float(shp.Top) - 0.1
                        or il + iw > float(shp.Left) + w + 0.1
                        or it + ih > float(shp.Top) + h + 0.1):
                    out["assert_fails"].append("icon out of node bbox: %s" % node)
                out["nodes"][node] = {
                    "tier": tier, "mode": mode, "png": spec["png"],
                    "margin": margin, "icon_size": icon_size,
                    "label_pt": ls, "note_pt": ns,
                    "space": sp, "bound": round(bh, 2),
                    "icon_rel": [round(il - X0, 1), round(it - Y0, 1)],
                    "icon_size": [round(iw, 1), round(ih, 1)],
                    "tried": tried,
                }
            else:
                # 全段失敗 → 構築時状態へ復元してアイコンなしで退避
                tf2.MarginLeft = 2.0
                set_sizes(sL, sN)
                set_space(0.75)
                bh = bound()
                if bh > h - 2.0 + 0.01:
                    set_space(0.6)
                    bh = bound()
                revert_ok = bh <= h - 2.0 + 0.01
                out["skipped_fit"].append({"node": node, "reverted_bound": round(bh, 2),
                                           "revert_ok": revert_ok, "tried": tried})
                if not revert_ok:
                    out["assert_fails"].append("revert failed for %s (bound %.2f > %.1f)"
                                               % (node, bh, h - 2))

        out["icons_added"] = len(out["nodes"])
        out["icons_expected"] = len(man["nodes"])
        if out["icons_added"] != out["icons_expected"]:
            out["notes"] = ("icons added %d/%d — skipped_fit を確認し報告に記載すること"
                            % (out["icons_added"], out["icons_expected"]))

        wb.Save()
        wb.Close(False)
        print("saved.", flush=True)
    except Exception as e:
        out["errors"].append(("EXC %r" % (e,))[:200])
    finally:
        quit_and_cleanup()

    out["ok"] = not out["assert_fails"] and not out["errors"]
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("ok:", out["ok"])
    print("icons: %d/%d" % (out.get("icons_added", 0), out.get("icons_expected", 0)))
    print("skipped_fit:", json.dumps(out["skipped_fit"], ensure_ascii=False))
    print("assert:", out["assert_fails"])
    print("errors:", out["errors"])
    for node, rec in out["nodes"].items():
        print("%s: label %.1fpt note %.1fpt space %.2f bound %.2f icon@%s" %
              (node, rec["label_pt"], rec["note_pt"], rec["space"], rec["bound"], rec["icon_rel"]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main()
