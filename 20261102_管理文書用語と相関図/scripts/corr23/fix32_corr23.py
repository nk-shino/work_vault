# -*- coding: utf-8 -*-
"""fix32_corr23.py — 相関図②③の重なり修正(確定設計)をPana/LNB両冊へ適用する。

設計: corr23/progress.md の2026-11-05ロック版 (geom_digest実数値·collision_check実装照合済)。
- ②: ノード5グループを下方移動(n02+13/n03+8/n04+6/n15+3/n16+3)、e01/e02/e08/e15/e16/
     e17/e18 を再配線、ラベル8枚と n17_txt を移動·幅修正、凡例4枚を+10pt。
- ③: bandhead を (536,225,195) へ、n08 +15pt / n09 +4pt、e04 は s0 削除と s1 短縮、
     e05/e06 を n08 新上縁まで延伸、e09 は s0/s2 削除と s1/s3 再配置、e03 は
     ungroup→4セグ再構築→regroup(グループ名 g3_e_e03 を保持)、ラベル4枚移動、
     凡例4枚を+11pt。
- 矢印: e17.s3 / e18.s3 は接続方向が旧設計と逆向きのため、矢印を End→Begin へ付け
     替える(反転属性は使わない)。e04③は旧設計から矢印なし(全セグ aB=aE=1)のまま。
- 反転: 変更する単一コネクタ(②e01/e08/e15/e16·③e05/e06)は修正前に drawingml XML から
     反転状態を読み、設定されていれば解除してから幾何を設定する。保存後も XML で
     (False, False) になったことを検証する。
検証: 適用後、同一COMセッション内で全変更箇所の座標を読み戻し、ずれ>0.75ptなら再設定
(最大3回)。図形数36·グループ子数·グループ名も検証する。保存は上書き保存(形式維持)。
テキスト本文は一切読み書きしない(名前·数値·スタイル属性のみ)。
"""
import sys, io, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from collision_check import read_flips_xml  # 修正前の反転状態読み取り(保存済ファイル·stdout をutf-8にwrapする)

import win32com.client as win32

BOOKS = {
    "pana": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
             r"/10_業務全般/PanaCIM_LNB/01_成果物/Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
            r"/10_業務全般/PanaCIM_LNB/01_成果物/LNB管理手順書案_未承認.xlsx"),
}
S2 = "相関図②"
S3 = "相関図③"
TOL = 0.75          # 許容ずれ pt (collision_check と同一)
ARROW_NONE = 1      # msoArrowheadNone
FLIP_H, FLIP_V = 0, 1  # MsoFlipCmd: msoFlipHorizontal=0 / msoFlipVertical=1 (0基底·実機で確認済)
EXPECTED_TOPS = 36

ATTR = {"l": "Left", "t": "Top", "w": "Width", "h": "Height"}


def setgeom(sh, **kw):
    for f in ("l", "t", "w", "h"):
        if kw.get(f) is not None:
            setattr(sh, ATTR[f], float(kw[f]))


def child(grp, name):
    gi = grp.GroupItems
    for k in range(1, int(gi.Count) + 1):
        m = gi.Item(k)
        if m.Name == name:
            return m
    raise KeyError("%s: child %s not found" % (grp.Name, name))


def delchild(grp, name):
    c = child(grp, name)
    c.Delete()


def clear_flips(sh, flips, name):
    fh, fv = flips.get(name, (False, False))
    acted = []
    if fh:
        sh.Flip(FLIP_H)
        acted.append("flipH")
    if fv:
        sh.Flip(FLIP_V)
        acted.append("flipV")
    return acted


class Verifier:
    """変更箇所の座標読み戻しと再設定 (ずれ>TOL を最大3回繰り返す)。"""

    def __init__(self):
        self.items = []  # (desc, shape, {field: expected})

    def reg(self, desc, sh, **exp):
        self.items.append((desc, sh, {k: float(v) for k, v in exp.items() if v is not None}))

    def run(self):
        residual = []
        for rnd in range(1, 4):
            residual = []
            for desc, sh, exp in self.items:
                for f, want in exp.items():
                    cur = float(getattr(sh, ATTR[f]))
                    if abs(cur - want) > TOL:
                        residual.append("%s.%s live=%.2f want=%.2f" % (desc, f, cur, want))
                        setattr(sh, ATTR[f], want)
            if not residual:
                print("  verify: all %d entries within %.2fpt (round %d)" % (len(self.items), TOL, rnd))
                return []
            print("  verify round %d: %d drift -> re-set" % (rnd, len(residual)))
        return residual


def apply_sheet2(ws, flips):
    print(" [%s] applying..." % S2)
    V = Verifier()

    # 1) ノードグループの下方移動 (子は随伴)
    for nm, dy in (("g2_n02", 13.0), ("g2_n03", 8.0), ("g2_n04", 6.0),
                   ("g2_n15", 3.0), ("g2_n16", 3.0)):
        sh = ws.Shapes(nm)
        nt = float(sh.Top) + dy
        sh.Top = nt
        V.reg(nm, sh, t=nt)
        print("  %s Top -> %.2f (+%.0f)" % (nm, nt, dy))

    # 2) e01 (n02 box 下端 273.19 — n03 box 上端 281 正接)
    sh = ws.Shapes("g2_e_e01")
    clear_flips(sh, flips, "g2_e_e01")
    setgeom(sh, t=273.19, h=7.81)
    V.reg("g2_e_e01", sh, t=273.19, h=7.81)

    # 3) e02 (レーン x398.5)
    g = ws.Shapes("g2_e_e02")
    c = child(g, "g2_e_e02_s0"); setgeom(c, t=485.0, w=198.5)
    V.reg("g2_e_e02_s0", c, t=485.0, w=198.5)
    c = child(g, "g2_e_e02_s1"); setgeom(c, l=398.5, t=250.0, h=235.0)
    V.reg("g2_e_e02_s1", c, l=398.5, t=250.0, h=235.0)
    c = child(g, "g2_e_e02_s2"); setgeom(c, t=250.0, w=30.5)
    V.reg("g2_e_e02_s2", c, t=250.0, w=30.5)

    # 4) e08 (斜め→水平 y246.8、反転解除、矢印 aE は保持)
    sh = ws.Shapes("g2_e_e08")
    acted = clear_flips(sh, flips, "g2_e_e08")
    if acted:
        print("  g2_e_e08 flips cleared: %s" % ",".join(acted))
    setgeom(sh, l=380.0, t=246.8, w=220.0, h=0.0)
    V.reg("g2_e_e08", sh, l=380.0, t=246.8, w=220.0, h=0.0)

    # 5) e15/e16 (下端を n15/n16 box 新上縁 379 へ)
    for nm in ("g2_e_e15", "g2_e_e16"):
        sh = ws.Shapes(nm)
        clear_flips(sh, flips, nm)
        setgeom(sh, h=17.81)
        V.reg(nm, sh, h=17.81)

    # 6) e17 (上端を n01 上縁 (100,196)、右レーン x746、n17 右縁 x740 へ右から接続)
    g = ws.Shapes("g2_e_e17")
    c = child(g, "g2_e_e17_s0"); setgeom(c, l=100.0, t=185.0, h=11.0)
    V.reg("g2_e_e17_s0", c, l=100.0, t=185.0, h=11.0)
    c = child(g, "g2_e_e17_s1"); setgeom(c, l=100.0, t=185.0, w=646.0)
    V.reg("g2_e_e17_s1", c, l=100.0, t=185.0, w=646.0)
    c = child(g, "g2_e_e17_s2"); setgeom(c, l=746.0, t=185.0, h=134.21)
    V.reg("g2_e_e17_s2", c, l=746.0, t=185.0, h=134.21)
    c = child(g, "g2_e_e17_s3"); setgeom(c, l=740.0, t=319.21, w=6.0)
    c.Line.BeginArrowheadStyle = 2   # 旧 aE(三角)を始点側へ → (740,319.21) で n17 右縁へ向く
    c.Line.EndArrowheadStyle = ARROW_NONE
    V.reg("g2_e_e17_s3", c, l=740.0, t=319.21, w=6.0)

    # 7) e18 (上端を bandhead 下縁 (44,180)、右レーン x758、n18 右縁 x740 へ右から接続)
    g = ws.Shapes("g2_e_e18")
    c = child(g, "g2_e_e18_s0"); setgeom(c, l=44.0, t=180.0, h=48.0)
    V.reg("g2_e_e18_s0", c, l=44.0, t=180.0, h=48.0)
    c = child(g, "g2_e_e18_s1"); setgeom(c, l=44.0, t=180.0, w=714.0)
    V.reg("g2_e_e18_s1", c, l=44.0, t=180.0, w=714.0)
    c = child(g, "g2_e_e18_s2"); setgeom(c, l=758.0, t=180.0, h=229.75)
    V.reg("g2_e_e18_s2", c, l=758.0, t=180.0, h=229.75)
    c = child(g, "g2_e_e18_s3"); setgeom(c, l=740.0, t=409.75, w=18.0)
    c.Line.BeginArrowheadStyle = 2
    c.Line.EndArrowheadStyle = ARROW_NONE
    V.reg("g2_e_e18_s3", c, l=740.0, t=409.75, w=18.0)

    # 8) ラベル (実tf余裕 ≥0.8pt の幅に修正済み)
    for nm, exp in (("g2_e_e01_l", dict(l=380.0, t=522.2, w=107.0)),
                    ("g2_e_e02_l", dict(t=464.0, w=113.0)),
                    ("g2_e_e04_l", dict(t=377.5)),                 # n05 下 3.25pt へ移動
                    ("g2_e_e08_l", dict(t=416.5, w=128.0)),
                    ("g2_e_e15_l", dict(l=47.0, t=362.5, w=148.0)),
                    ("g2_e_e16_l", dict(t=362.5, w=153.0)),
                    ("g2_e_e17_l", dict(t=152.0, w=160.0)),
                    ("g2_e_e18_l", dict(l=480.0, t=432.0))):
        sh = ws.Shapes(nm)
        setgeom(sh, **exp)
        V.reg(nm, sh, **exp)

    # 9) n17_txt 幅 108→111 ([d] frame 余裕 1.22pt)
    c = child(ws.Shapes("g2_n17"), "g2_n17_txt")
    setgeom(c, w=111.0)
    V.reg("g2_n17_txt", c, w=111.0)

    # 10) 凡例 +10pt
    for nm in ("g2_leg0", "g2_leg1", "g2_leg2", "g2_leg3"):
        sh = ws.Shapes(nm)
        nt = float(sh.Top) + 10.0
        sh.Top = nt
        V.reg(nm, sh, t=nt)

    bad = V.run()
    if int(ws.Shapes.Count) != EXPECTED_TOPS:
        bad.append("tops=%d expect=%d" % (ws.Shapes.Count, EXPECTED_TOPS))
    for nm, kids in (("g2_e_e02", 3), ("g2_e_e17", 4), ("g2_e_e18", 4)):
        if int(ws.Shapes(nm).GroupItems.Count) != kids:
            bad.append("%s children=%d expect=%d" % (nm, ws.Shapes(nm).GroupItems.Count, kids))
    return bad


def apply_sheet3(ws, flips):
    print(" [%s] applying..." % S3)
    V = Verifier()
    bad = []

    # 1) bandhead (492,225,250,22) -> (536,225,195,22)
    sh = ws.Shapes("g3_bandhead")
    setgeom(sh, l=536.0, w=195.0)
    V.reg("g3_bandhead", sh, l=536.0, w=195.0)

    # 2) n08 +15 / n09 +4
    for nm, dy in (("g3_n08", 15.0), ("g3_n09", 4.0)):
        sh = ws.Shapes(nm)
        nt = float(sh.Top) + dy
        sh.Top = nt
        V.reg(nm, sh, t=nt)
        print("  %s Top -> %.2f (+%.0f)" % (nm, nt, dy))

    # 3) e04: s0 削除(箱内走行の死に枝)、s1 を n08 左縁 x40 まで短縮 (矢印なしのまま)
    g = ws.Shapes("g3_e_e04")
    delchild(g, "g3_e_e04_s0")
    print("  g3_e_e04_s0 deleted")
    c = child(g, "g3_e_e04_s1"); setgeom(c, w=14.0)
    V.reg("g3_e_e04_s1", c, w=14.0)

    # 4) e05/e06: n07 下縁 292 — n08 新上縁 345 を結ぶ (h 38->53)
    for nm in ("g3_e_e05", "g3_e_e06"):
        sh = ws.Shapes(nm)
        clear_flips(sh, flips, nm)
        setgeom(sh, h=53.0)
        V.reg(nm, sh, h=53.0)

    # 5) e09: s0/s2 削除、s1 を pcr 下縁 (22,205) から n09 左寄り (22,440) へ、
    #    s3 を (22,440)->(40,440) として n09 左縁 x40 へ接続 (aE=2 保持)
    g = ws.Shapes("g3_e_e09")
    delchild(g, "g3_e_e09_s0")
    delchild(g, "g3_e_e09_s2")
    print("  g3_e_e09_s0/s2 deleted")
    c = child(g, "g3_e_e09_s1"); setgeom(c, l=22.0, t=205.0, h=235.0)
    V.reg("g3_e_e09_s1", c, l=22.0, t=205.0, h=235.0)
    c = child(g, "g3_e_e09_s3"); setgeom(c, l=22.0, t=440.0, w=18.0)
    V.reg("g3_e_e09_s3", c, l=22.0, t=440.0, w=18.0)

    # 6) e03 再構築 (旧: (235,356)-(750,356)-(750,185)-(740,185) の3セグ
    #          新: (235,356)-(262,356)-(262,485)-(740,485)-(740,205) の4セグ)
    rebuild_e03(ws, V)

    # 7) ラベル
    for nm, exp in (("g3_e_e04_l", dict(l=30.0, t=468.0)),
                    ("g3_e_e05_l", dict(t=293.5)),
                    ("g3_e_e06_l", dict(l=288.0, t=307.0)),  # 幅は旧104のまま([d]余裕1.60)
                    ("g3_e_e12_l", dict(t=380.0))):
        sh = ws.Shapes(nm)
        setgeom(sh, **exp)
        V.reg(nm, sh, **exp)

    # 8) 凡例 +11pt
    for nm in ("g3_leg0", "g3_leg1", "g3_leg2", "g3_leg3"):
        sh = ws.Shapes(nm)
        nt = float(sh.Top) + 11.0
        sh.Top = nt
        V.reg(nm, sh, t=nt)

    bad += V.run()
    if int(ws.Shapes.Count) != EXPECTED_TOPS:
        bad.append("tops=%d expect=%d" % (ws.Shapes.Count, EXPECTED_TOPS))
    for nm, kids in (("g3_e_e04", 4), ("g3_e_e09", 2), ("g3_e_e03", 4)):
        g = ws.Shapes(nm)
        if int(g.GroupItems.Count) != kids:
            bad.append("%s children=%d expect=%d" % (nm, g.GroupItems.Count, kids))
    return bad


def rebuild_e03(ws, V):
    grp = ws.Shapes("g3_e_e03")
    OLD = {"g3_e_e03_s0": (235.0, 356.0, 515.0, 0.0),
           "g3_e_e03_s1": (750.0, 185.0, 0.0, 171.0),
           "g3_e_e03_s2": (740.0, 185.0, 10.0, 0.0)}
    NEW = {"g3_e_e03_s0": dict(l=235.0, t=356.0, w=27.0, h=0.0),
           "g3_e_e03_s1": dict(l=262.0, t=356.0, w=0.0, h=129.0),
           "g3_e_e03_s2": dict(l=262.0, t=485.0, w=478.0, h=0.0)}

    # 線スタイルを旧s0から退避 (weight/rgb/dash/visible)
    s0old = child(grp, "g3_e_e03_s0")
    ln = s0old.Line
    props = (float(ln.Weight), int(ln.ForeColor.RGB), int(ln.DashStyle), bool(ln.Visible))

    grp.Ungroup()
    print("  g3_e_e03 ungrouped (3 segments freed)")

    # 解放図形を旧幾何で特定 (ungroupで名前が変わる場合に備える)
    def near(rect, ref):
        return all(abs(a - b) <= 0.51 for a, b in zip(rect, ref))

    found = {}
    for i in range(1, int(ws.Shapes.Count) + 1):
        sh = ws.Shapes(i)
        try:
            if int(sh.Type) == 6:
                continue
        except Exception:
            continue
        rect = (float(sh.Left), float(sh.Top), float(sh.Width), float(sh.Height))
        for nm, ref in OLD.items():
            if nm not in found and near(rect, ref):
                found[nm] = sh
                break
    missing = sorted(set(OLD) - set(found))
    if missing:
        raise RuntimeError("e03 freed segments not matched: %s" % missing)
    for nm, sh in found.items():
        sh.Name = nm  # 正規名へ戻す
        setgeom(sh, **NEW[nm])
        print("  %s -> l=%.1f t=%.1f w=%.1f h=%.1f" % (nm, NEW[nm]["l"], NEW[nm]["t"], NEW[nm]["w"], NEW[nm]["h"]))

    # 新規上昇セグメント (dgsr 右下コーナー (740,205) で底縁に接続、ride長0)
    s3 = ws.Shapes.AddLine(740.0, 205.0, 740.0, 485.0)
    s3.Name = "g3_e_e03_s3"
    ln3 = s3.Line
    ln3.Weight = props[0]
    ln3.ForeColor.RGB = props[1]
    ln3.DashStyle = props[2]
    ln3.Visible = props[3]
    ln3.BeginArrowheadStyle = ARROW_NONE
    ln3.EndArrowheadStyle = ARROW_NONE
    print("  g3_e_e03_s3 added (740,205)-(740,485) weight=%.2f dash=%d rgb=%d" % (props[0], props[2], props[1]))

    # 4セグで再グループ化し、検査器の edge 分類のため名前を g3_e_e03 に戻す
    rng = ws.Shapes.Range(("g3_e_e03_s0", "g3_e_e03_s1", "g3_e_e03_s2", "g3_e_e03_s3"))
    ng = rng.Group()
    ng.Name = "g3_e_e03"
    print("  regrouped as g3_e_e03 (4 segments)")

    # グループ化後の新しい子参照で検証登録
    g2 = ws.Shapes("g3_e_e03")
    for nm, exp in NEW.items():
        c = child(g2, nm)
        V.reg(nm, c, **exp)
    c = child(g2, "g3_e_e03_s3")
    V.reg("g3_e_e03_s3", c, l=740.0, t=205.0, w=0.0, h=280.0)


def open_book(app, path):
    last = None
    for i in range(6):
        try:
            return app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=False)
        except Exception as e:  # OneDrive排他など
            last = e
            print("  open retry %d: %s" % (i + 1, str(e)[:120]))
            time.sleep(3)
    raise RuntimeError("cannot open %s: %s" % (path, last))


def main():
    for bk, path in BOOKS.items():
        print("== %s" % bk)
        flips = read_flips_xml(path, [S2, S3])
        app = win32.DispatchEx("Excel.Application")
        app.Visible = False
        app.DisplayAlerts = False
        try:
            try:
                app.ScreenUpdating = False
            except Exception:
                pass
            wb = open_book(app, path)
            try:
                wb.AutoSaveOn = False
            except Exception:
                pass
            problems = []
            problems += apply_sheet2(wb.Worksheets(S2), flips[S2])
            problems += apply_sheet3(wb.Worksheets(S3), flips[S3])
            if problems:
                for p in problems:
                    print("  PROBLEM: %s" % p)
                raise RuntimeError("fix32 verification failed for %s" % bk)
            wb.Save()
            wb.Close(SaveChanges=False)
            print("  saved.")
        finally:
            try:
                app.Quit()
            except Exception:
                pass
        # 保存後の反転状態を XML で検証 (単一コネクタは無反転であること)
        flips_after = read_flips_xml(path, [S2, S3])
        for sn, names in ((S2, ("g2_e_e01", "g2_e_e08", "g2_e_e15", "g2_e_e16")),
                          (S3, ("g3_e_e05", "g3_e_e06"))):
            for nm in names:
                fh, fv = flips_after[sn].get(nm, (False, False))
                if fh or fv:
                    raise RuntimeError("flip remains after save: %s %s (%s,%s)" % (sn, nm, fh, fv))
        print("  flip check after save: OK (e01/e08/e15/e16/e05/e06 = no flip)")
    print("FIX32 DONE")


if __name__ == "__main__":
    main()
