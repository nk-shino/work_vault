# -*- coding: utf-8 -*-
"""G-pass 検証: backup(pre) と 正本(post) のダンプ diff を編集リスト(許容差分)と照合する.
- 変更セルは2つの報告書JSONの許容リスト内のみ
- LNB チェックシート(日次) は行9削除により1行シフト(特別扱い)
- LNB 認証情報一覧 は新設シート(存在と主要セルを点検)
- cred(申し送り(認証情報)) diff = 0
- 会議課題一覧(一時)·相関図_old diff = 0 (両冊)
- 引用原文セルは1字も不変
- 置換禁止文字列の有無が前後で不変
- 数式0(=で始まる値のセルが無い)
"""
import os, json, warnings, sys
warnings.filterwarnings("ignore")
import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOKS = {
    "pana": {
        "pre": os.path.join(BASE, "backup_20261102", "Pana-CIM管理手順書案_未承認_Gpass前_20261104.xlsx"),
        "post": os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.xlsx"),
        "report": os.path.join(BASE, "scripts", "fix30_gpass_pana_report.json"),
    },
    "lnb": {
        "pre": os.path.join(BASE, "backup_20261102", "LNB管理手順書案_未承認_Gpass前_20261104.xlsx"),
        "post": os.path.join(VDIR, "LNB管理手順書案_未承認.xlsx"),
        "report": os.path.join(BASE, "scripts", "fix30_gpass_lnb_report.json"),
    },
}
OUT = os.path.join(BASE, "scripts", "fix30_verify_report.json")

FORBID = ["windwos", "Route Editer", "LNB再起動", "LNB-PCリブート", "LNB-PC電源OFF"]
QUOTE_PANA = [("異常時の対応", [f"C{r}" for r in range(42, 64)]),
              ("付録 引用元と確認範囲", ["C9", "C10", "C14", "C17", "C20"]),
              ("7-5仮_サービス起動停止", [f"C{r}" for r in range(12, 19)])]
QUOTE_LNB = [("引用と部品照合", ["C13", "C16", "C20"])]
NO_TOUCH = ["会議課題一覧(一時)", "相関図_old"]

def dump(path):
    wb = openpyxl.load_workbook(path, data_only=False)
    d = {}
    formulas = 0
    for ws in wb.worksheets:
        sd = {}
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if v is None or (isinstance(v, str) and v == ""):
                    continue
                if isinstance(v, str) and v.startswith("="):
                    formulas += 1
                sd[c.coordinate] = str(v)
        d[ws.title] = sd
    names = [ws.title for ws in wb.worksheets]
    wb.close()
    return d, names, formulas

def diff(a, b):
    """セル単位の差分: {addr: (old, new)}"""
    keys = set(a) | set(b)
    out = {}
    for k in sorted(keys):
        va, vb = a.get(k), b.get(k)
        if va != vb:
            out[k] = (va, vb)
    return out

REP = {"pana": {}, "lnb": {}}
ok_all = True
for book, cfg in BOOKS.items():
    pre, pre_names, pre_f = dump(cfg["pre"])
    post, post_names, post_f = dump(cfg["post"])
    rj = json.load(open(cfg["report"], encoding="utf-8"))
    R = REP[book]
    R["sheets_pre"] = pre_names
    R["sheets_post"] = post_names
    R["formulas_pre"] = pre_f
    R["formulas_post"] = post_f

    # 許容リスト(報告書の編集セル + 一覧挿入行 + 目次挿入 + 新設シート)
    allow = set()
    for e in rj["edits"]:
        allow.add((e["sheet"], e["cell"]))
    new_rows = rj.get("new_rows") or rj.get("list_rows") or []
    for nr in new_rows:
        allow.add(("要確認事項一覧", f"C{nr['row']}"))
    toc = rj.get("toc_g3") or {}
    if toc:
        for a in ("A20", "B20", "C20", "A21", "C21", "C22"):
            allow.add(("目次", a))

    sheet_diffs = {}
    unallowed = []
    for sh in set(pre_names) | set(post_names):
        if sh not in pre:
            sheet_diffs[sh] = f"NEW SHEET ({len(post[sh])} cells)"
            continue
        if sh not in post:
            sheet_diffs[sh] = "SHEET MISSING!"
            ok_all = False
            continue
        d = diff(pre[sh], post[sh])
        if not d:
            sheet_diffs[sh] = "no change"
            continue
        if sh == "チェックシート(日次)" and book == "lnb":
            # 行9削除: post[r] == pre[r+1] (r>=9)。編集は pre C13/C19/A12 → post C12/C18/A11
            shifted_pre = {}
            for r, cells in pre[sh].items():
                rn = int("".join(ch for ch in r if ch.isdigit()))
                col = r[:len(r) - len(str(rn))]
                if rn >= 10:
                    shifted_pre[f"{col}{rn-1}"] = cells
            post_shift = {k: v for k, v in post[sh].items()
                          if int("".join(ch for ch in k if ch.isdigit())) >= 9}
            d2 = diff(shifted_pre, post_shift)
            shift_allow = {"C12", "C18", "A11"}  # 編集3セル(削除後のアドレス)
            bad = {k: v for k, v in d2.items() if k not in shift_allow}
            sheet_diffs[sh] = f"shift-compare: {len(d2)} diffs, unallowed {len(bad)}"
            for k, v in bad.items():
                unallowed.append((sh, k, v))
            # 非シフト領域(行1-8)も確認
            d1 = diff({k: v for k, v in pre[sh].items() if int("".join(ch for ch in k if ch.isdigit())) <= 8},
                      {k: v for k, v in post[sh].items() if int("".join(ch for ch in k if ch.isdigit())) <= 8})
            bad1 = {k: v for k, v in d1.items() if (sh, k) not in allow}
            sheet_diffs[sh] += f", rows1-8 diffs {len(d1)} unallowed {len(bad1)}"
            for k, v in bad1.items():
                unallowed.append((sh, k, v))
            continue
        if sh == "目次" and book == "lnb" and toc:
            # 行20挿入: pre r(r>=20) → post r+1。新行 post20 = A20/B20/C20
            shifted_pre = {}
            for r, cells in pre[sh].items():
                rn = int("".join(ch for ch in r if ch.isdigit()))
                col = r[:len(r) - len(str(rn))]
                if rn >= 20:
                    shifted_pre[f"{col}{rn+1}"] = cells
            d_shift = diff(shifted_pre, {k: v for k, v in post[sh].items()
                                         if int("".join(ch for ch in k if ch.isdigit())) >= 21})
            bad = {k: v for k, v in d_shift.items() if (sh, k) not in allow}
            sheet_diffs[sh] = f"toc-shift: {len(d_shift)} diffs, unallowed {len(bad)}"
            for k, v in bad.items():
                unallowed.append((sh, k, v))
            # 新行20 と 行1-19
            d_new = diff({}, {k: v for k, v in post[sh].items() if k in ("A20", "B20", "C20")})
            d_top = diff({k: v for k, v in pre[sh].items() if int("".join(ch for ch in k if ch.isdigit())) <= 19},
                         {k: v for k, v in post[sh].items() if int("".join(ch for ch in k if ch.isdigit())) <= 19})
            for dpart in (d_new, d_top):
                bad = {k: v for k, v in dpart.items() if (sh, k) not in allow}
                sheet_diffs[sh] += f", +{len(dpart)} diffs unallowed {len(bad)}"
                for k, v in bad.items():
                    unallowed.append((sh, k, v))
            continue
        bad = {k: v for k, v in d.items() if (sh, k) not in allow}
        sheet_diffs[sh] = f"{len(d)} diffs, unallowed {len(bad)}"
        for k, v in bad.items():
            unallowed.append((sh, k, v))
    R["sheet_diffs"] = sheet_diffs
    R["unallowed"] = [{"sheet": s, "cell": c, "pre": (v[0] or "")[:120], "post": (v[1] or "")[:120]}
                      for s, c, v in unallowed[:40]]
    if unallowed:
        ok_all = False

    # 新設シートの点検(LNB)
    if book == "lnb":
        ns = post.get("認証情報一覧") or {}
        spot = {k: ns.get(k) for k in ("A1", "A3", "A6", "G4", "C7", "A8", "C8", "E8", "G8", "I8", "K8")}
        R["new_sheet_spot"] = spot
        if spot.get("A6") != "14. 認証情報一覧" or spot.get("G4") != "　認証情報一覧" or not spot.get("A8") == "No":
            ok_all = False
            R["new_sheet_spot_ok"] = False
        else:
            R["new_sheet_spot_ok"] = True

    # 引用原文の1字不変
    qbad = []
    for sh, cells in (QUOTE_PANA if book == "pana" else QUOTE_LNB):
        for a in cells:
            if pre.get(sh, {}).get(a) != post.get(sh, {}).get(a):
                qbad.append(f"{sh}!{a}")
    R["quote_immutable_ok"] = not qbad
    if qbad:
        ok_all = False
        R["quote_bad"] = qbad

    # 無編集シート
    nt_bad = []
    for sh in NO_TOUCH:
        if sh in pre_names and sh in post_names:
            if pre[sh] != post[sh]:
                nt_bad.append(sh)
        elif sh in pre_names or sh in post_names:
            nt_bad.append(sh + " (presence changed)")
    R["no_touch_ok"] = not nt_bad
    if nt_bad:
        ok_all = False
        R["no_touch_bad"] = nt_bad

    # 置換禁止文字列の有無が前後で不変
    fb = []
    for s in FORBID:
        cnt_pre = sum(1 for sh in pre.values() for v in sh.values() if s in v)
        cnt_post = sum(1 for sh in post.values() for v in sh.values() if s in v)
        if cnt_pre != cnt_post:
            fb.append({"s": s, "pre": cnt_pre, "post": cnt_post})
        elif cnt_pre:
            R.setdefault("forbid_kept", []).append({"s": s, "count": cnt_post})
    R["forbid_ok"] = not fb
    if fb:
        ok_all = False
        R["forbid_bad"] = fb

    # 数式0
    if post_f != 0:
        ok_all = False
        R["formulas_bad"] = post_f

    act = "OK" if (not unallowed and not qbad and not nt_bad and not fb and post_f == 0) else "NG"
    print(f"[{book}] diffs per sheet:", flush=True)
    for sh, msg in sheet_diffs.items():
        if msg != "no change":
            print(f"  {sh}: {msg}", flush=True)
    print(f"[{book}] unallowed={len(unallowed)} quote_ok={not qbad} no_touch_ok={not nt_bad} "
          f"forbid_ok={not fb} formulas={post_f} => {act}", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(REP, f, ensure_ascii=False, indent=1)
print("VERIFY " + ("OK" if ok_all else "NG") + " -> " + OUT, flush=True)
sys.exit(0 if ok_all else 1)
