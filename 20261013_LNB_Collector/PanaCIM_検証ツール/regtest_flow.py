# -*- coding: utf-8 -*-
"""回帰テスト: 異常時の対応シート図解のコネクタ接続グラフ検証 (ERR-20261023-004 対策)
(1) 図形分類と個数 (2) 全コネクタの矢印先/根元の接続先 (3) 期待経路グラフとの突合
(4) 意味論検査: START→END の全経路が手順14を通ること(迂回経路の混入を検出)
読み取り専用で開く。ファイルは変更しない。"""
import sys, io, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

F = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
SHEET = "異常時の対応"
TOL = 4.0        # 矩形辺との一致許容(pt)
VTOL = 6.0       # ダイヤ頂点との一致許容(pt)

# 期待される有向エッジ(根元ノード → 矢先ノード)。ERR-20261023-004 修正後の正解グラフ
EXPECTED_EDGES = {
    ("fc_start", "fc_L1"), ("fc_L1", "fc_L2"), ("fc_L2", "fc_L3"),
    ("fc_L3", "fc_L4"), ("fc_L4", "fc_L5"), ("fc_L5", "fc_L6"),
    ("fc_L6", "fc_R7"),                                    # 橋渡し(矢なし2本+矢あり1本)
    ("fc_R7", "fc_R8"), ("fc_R8", "fc_R9"), ("fc_R9", "fc_R10"),
    ("fc_R10", "fc_R11"), ("fc_R11", "fc_R12"), ("fc_R12", "fc_R13"),
    ("fc_R13", "fc_dia"), ("fc_dia", "fc_side"),           # はい→Continue
    ("fc_dia", "fc_14"),                                   # いいえ→手順14
    ("fc_side", "fc_14"),                                  # Continue→手順14へ合流(修正対象)
    ("fc_14", "fc_end"),
}
N_NODES, N_LABELS, N_CONN = 18, 3, 21

def rect(sh):
    return (sh.Left, sh.Top, sh.Left + sh.Width, sh.Top + sh.Height)

def on_rect_edge(pt, r, tol=TOL):
    x, y = pt
    L, T, R, B = r
    if abs(x - L) <= tol and T - tol <= y <= B + tol: return True
    if abs(x - R) <= tol and T - tol <= y <= B + tol: return True
    if abs(y - T) <= tol and L - tol <= x <= R + tol: return True
    if abs(y - B) <= tol and L - tol <= x <= R + tol: return True
    return False

def dia_vertex_match(pt, r):
    x, y = pt
    L, T, R, B = r
    cx, my = (L + R) / 2.0, (T + B) / 2.0
    for vx, vy in ((L, my), (R, my), (cx, T), (cx, B)):
        if abs(x - vx) <= VTOL and abs(y - vy) <= VTOL:
            return True
    return False

def attach_node(pt, nodes):
    hits = []
    for name, r in nodes.items():
        if name == "fc_dia":
            if dia_vertex_match(pt, r): hits.append(name)
        else:
            if on_rect_edge(pt, r): hits.append(name)
    return hits[0] if len(hits) == 1 else (hits if hits else None)

def endpoints(sh):
    """フリップを考慮した begin/end 座標。斜めコネクタは None を返す。"""
    l, t, w, h = sh.Left, sh.Top, sh.Width, sh.Height
    hf, vf = bool(sh.HorizontalFlip), bool(sh.VerticalFlip)
    if abs(h) < 0.5:                       # 水平
        bx, ex = (l, l + w) if not hf else (l + w, l)
        return (bx, t), (ex, t)
    if abs(w) < 0.5:                       # 垂直
        by, ey = (t, t + h) if not vf else (t + h, t)
        return (l, by), (l, ey)
    return None

def run_once():
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(F, False, True)  # ReadOnly
        try:
            ws = wb.Worksheets(SHEET)
            nodes, labels, conns = {}, [], []
            for sh in ws.Shapes:
                if sh.Name.startswith("fc_"):
                    nodes[sh.Name] = rect(sh)
                elif sh.Name.startswith("TextBox"):
                    labels.append(sh.Name)
                else:
                    conns.append(sh)
            fails = []
            if len(nodes) != N_NODES:
                fails.append(f"ノード数 {len(nodes)} != {N_NODES}: {sorted(nodes)}")
            if len(labels) != N_LABELS:
                fails.append(f"ラベル数 {len(labels)} != {N_LABELS}: {labels}")
            if len(conns) != N_CONN:
                fails.append(f"コネクタ数 {len(conns)} != {N_CONN}")
            if fails:
                print("\n".join(fails)); return fails

            arrowless = []   # (begin, end, name)
            arrowed = []     # (tail, tip, name)
            for sh in conns:
                ep = endpoints(sh)
                if ep is None:
                    fails.append(f"[斜めコネクタ] {sh.Name} 許可されていない")
                    continue
                b, e = ep
                bs = int(sh.Line.BeginArrowheadStyle)   # 1=none, 2=triangle
                es = int(sh.Line.EndArrowheadStyle)
                if bs != 1 and es != 1:
                    fails.append(f"[両端矢印] {sh.Name} Begin={bs} End={es}")
                    continue
                if bs == 1 and es == 1:
                    arrowless.append((b, e, sh.Name))
                else:
                    tip, tail = (e, b) if es == 2 else (b, e)
                    arrowed.append((tail, tip, sh.Name))
            if len(arrowed) != 18 or len(arrowless) != 3:
                fails.append(f"矢あり {len(arrowed)}(期待18) / 矢なし {len(arrowless)}(期待3)")
                return fails

            # 矢なしセグメントを経由して根元をノードまで辿る
            def resolve_tail(pt, visited):
                hit = attach_node(pt, nodes)
                if hit: return hit
                for i, (b, e, nm) in enumerate(arrowless):
                    if i in visited: continue
                    for seg_pt, other in ((b, e), (e, b)):
                        if abs(pt[0]-seg_pt[0]) <= TOL and abs(pt[1]-seg_pt[1]) <= TOL:
                            visited.add(i)
                            r = resolve_tail(other, visited)
                            if r: return r
                return None

            edges = set()
            for tail, tip, nm in arrowed:
                tnode = attach_node(tip, nodes)
                if tnode is None:
                    fails.append(f"[矢先未接続] {nm} tip={tip} どのノードにも接していない")
                    continue
                snode = resolve_tail(tail, set())
                if snode is None:
                    fails.append(f"[根元未接続] {nm} tail={tail} ノードに辿れない")
                    continue
                edges.add((snode, tnode))
            if not fails:
                miss = EXPECTED_EDGES - edges
                extra = edges - EXPECTED_EDGES
                if miss:   fails.append(f"[欠落エッジ] {sorted(miss)}")
                if extra:  fails.append(f"[過剰エッジ] {sorted(extra)}")
            if not fails:
                # 意味論検査: START→END の全経路
                adj = {}
                for s, t in edges:
                    adj.setdefault(s, []).append(t)
                paths = []
                def walk(n, acc):
                    if n == "fc_end":
                        paths.append(list(acc)); return
                    for m in adj.get(n, []):
                        acc.append(m); walk(m, acc); acc.pop()
                walk("fc_start", ["fc_start"])
                n_via14 = sum(1 for p in paths if "fc_14" in p)
                n_via_side = sum(1 for p in paths if "fc_side" in p)
                if len(paths) != 2:
                    fails.append(f"[経路数] START→END の経路が {len(paths)} 本(期待2)")
                if n_via14 != len(paths):
                    fails.append(f"[迂回検出] 手順14を通らない経路が {len(paths)-n_via14} 本")
                if n_via_side != 1:
                    fails.append(f"[Continue経路] fc_side を通る経路が {n_via_side} 本(期待1)")
                print(f"経路: {[ '→'.join(p) for p in paths ]}")
            if not fails:
                print(f"検査対象: ノード{len(nodes)} ラベル{len(labels)} コネクタ{len(conns)}"
                      f"(矢あり{len(arrowed)}/矢なし{len(arrowless)}) / エッジ{len(edges)}本 すべて期待どおり")
            return fails
        finally:
            wb.Close(SaveChanges=False)
    finally:
        excel.Quit()
        pythoncom.CoUninitialize()

for attempt in range(1, 6):
    try:
        fails = run_once()
        break
    except Exception as e:
        print(f"retry {attempt}: {e}")
        time.sleep(1.5)
else:
    sys.exit(1)
print("RESULT:", "PASS" if not fails else f"FAIL({len(fails)})")
if fails:
    for f in fails:
        print("  -", f)
sys.exit(0 if not fails else 1)
