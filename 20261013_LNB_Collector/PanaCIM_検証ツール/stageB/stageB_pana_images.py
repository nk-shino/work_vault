# -*- coding: utf-8 -*-
"""Stage B: Pana-CIM管理手順書案への画像挿入(24枚+導入行)
- 画像8・12は認証情報が写り込むため黒塗り伏字処理してから挿入(本文テキストの伏字運用と同じ扱い)
- 挿入位置: 月次再起動r31(行挿入)/バックアップr16(行挿入)/7-5仮r19(行挿入)/異常時の対応r116(空き領域・行高明示)
- 表示サイズ: 幹 min(340pt, 自然幅)・高さ max300pt・拡大しない(96dpi換算 px*0.75pt)
- キャプションは図の下のC列。フォントは各シートの＊出典行から継承
- 保存後: restore_printersettings.py → regtest_flow_v2.py → PDF目視 を別途実施すること
"""
import os, io, sys, glob, math, re, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image, ImageDraw, ImageFont

BOOK = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
IMG_BASE = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\PanaCIMimage"
ROW_PT = 12.75
MAX_W, MAX_H = 340.0, 300.0

# ---------------- 1. 伏字処理 ----------------
MASKS = {
    os.path.join("異常時の対応", "画像8.png"):  [(108, 18, 222, 44)],
    os.path.join("異常時の対応", "画像12.png"): [(446, 45, 651, 70)],
}
LABEL = "［認証情報：伏字］"

def mask_images():
    font = ImageFont.truetype(r"C:\Windows\Fonts\meiryo.ttc", 10)
    out = {}
    for rel, boxes in MASKS.items():
        src = os.path.join(IMG_BASE, rel)
        im = Image.open(src).convert("RGB")
        d = ImageDraw.Draw(im)
        for (x0, y0, x1, y1) in boxes:
            d.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))
            d.text((x0 + 4, y0 + 4), LABEL, fill=(255, 255, 255), font=font)
        dst = src.replace(".png", "_伏字.png")
        im.save(dst)
        out[rel] = dst
        print(f"[mask] {rel} -> {os.path.basename(dst)} boxes={boxes}")
    return out

# ---------------- 2. 挿入計画 ----------------
def disp_size(w_px, h_px):
    nw, nh = w_px * 0.75, h_px * 0.75
    s = min(MAX_W / nw, MAX_H / nh, 1.0)
    return round(nw * s, 1), round(nh * s, 1)

def num_key(p):
    m = re.search(r"(\d+)\.(\w+)$", os.path.basename(p))
    return int(m.group(1)) if m else 0

def build_plan(masked):
    plan = []
    # 月次再起動 r31: 図1・図2
    g = lambda *parts: os.path.join(IMG_BASE, *parts)
    p1 = g("月次再起動", "画像_月次再起動_slide1_01.png")
    p2 = g("月次再起動", "画像_月次再起動_slide1_02.png")
    plan.append(dict(sheet="月次再起動", anchor=31, insert=True, fmt="C27",
        images=[(p1, "図1 手順1：スタート → 再起動(出典：サーバー再起動.pptx スライド1)"),
                (p2, "図2 手順2：理由コード(出典：サーバー再起動.pptx スライド1)")],
        print_area=(100, "$A$1:$AZ$")))
    # バックアップ r16: 図1〜7
    bk = sorted(glob.glob(g("バックアップ", "*.jpg")), key=lambda p: ("p11" not in p, p))
    pages = ["p11"] * 3 + ["p12"] * 4
    plan.append(dict(sheet="バックアップ", anchor=16, insert=True, fmt="C9",
        images=[(f, f"図{i+1}({pg})") for i, (f, pg) in enumerate(zip(bk, pages))]))
    # 7-5仮 r19: 図1・図2 (p213_02 は18x17pxのアイコン断片なので使わない)
    s1 = g("7-5仮_サービス起動停止", "画像_サービスコントローラー_p213_01.png")
    s3 = g("7-5仮_サービス起動停止", "画像_サービスコントローラー_p213_03.png")
    plan.append(dict(sheet="7-5仮_サービス起動停止", anchor=19, insert=True, fmt="C21",
        images=[(s1, "図1 手順1〜2(出典：導入編 p213)"),
                (s3, "図2 手順3(出典：導入編 p213)")]))
    # 異常時の対応 r116: 導入行 + 画像1〜14 (行挿入なし・空き領域)
    ij = [f for f in glob.glob(g("異常時の対応", "*.png"))
          if re.match(r"画像\d+\.png$", os.path.basename(f))]
    ij.sort(key=num_key)
    imgs = []
    for f in ij:
        n = int(re.search(r"画像(\d+)", os.path.basename(f)).group(1))
        fn = masked.get(os.path.join("異常時の対応", f"画像{n}.png"), f)
        cap = "画像2(手順3と確定)" if n == 2 else f"画像{n}(手順との対応：未確定)"
        if n in (8, 12):
            cap = f"画像{n}(手順との対応：未確定・認証情報は伏字)"
        imgs.append((fn, cap))
    plan.append(dict(sheet="異常時の対応", anchor=116, insert=False, fmt="C29",
        lead="参考画像(出典：操作手順書「0494-912039(06) P47」。画像8・12は認証情報を伏字にしている)",
        images=imgs))
    return plan

# ---------------- 3. COM 挿入 ----------------
def run_com(plan):
    import pythoncom, win32com.client
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    summary = []
    try:
        wb = excel.Workbooks.Open(BOOK, 0)
        try:
            for blk in plan:
                ws = wb.Worksheets(blk["sheet"])
                # 事前確認: アンカー行が空であること
                v = ws.Range(f"C{blk['anchor']}").Value
                assert v in (None, ""), f"{blk['sheet']} C{blk['anchor']} が空でない: {v!r}"
                print(f"[{blk['sheet']}] shapes before = {ws.Shapes.Count}")
                imgs = []
                for path, cap in blk["images"]:
                    im = Image.open(path)
                    w, h = disp_size(im.width, im.height)
                    rows = max(1, math.ceil(h / ROW_PT))
                    imgs.append((path, cap, w, h, rows))
                total = sum(r[4] for r in imgs) + 2 * len(imgs)
                a = blk["anchor"]
                if blk.get("lead"):
                    total += 2   # 導入行+空行
                if blk["insert"]:
                    ws.Rows(f"{a}:{a + total - 1}").Insert()
                # 行高を明示(空き領域利用時は既定高が保証されないため)
                ws.Rows(f"{a}:{a + total - 1}").RowHeight = ROW_PT
                # フォント継承元
                ref = ws.Range(blk["fmt"])
                fname, fsize = ref.Font.Name, ref.Font.Size
                cur = a
                if blk.get("lead"):
                    c = ws.Range(f"C{cur}")
                    c.Value = blk["lead"]
                    c.Font.Name, c.Font.Size, c.Font.Bold = fname, fsize, False
                    cur += 2
                left = ws.Range(f"C{cur}").Left
                for i, (path, cap, w, h, rows) in enumerate(imgs, 1):
                    top = ws.Range(f"C{cur}").Top + 1.0
                    sh = ws.Shapes.AddPicture(os.path.abspath(path), False, True, left, top, w, h)
                    sh.Name = f"img_{i}"
                    cap_row = cur + rows
                    c = ws.Range(f"C{cap_row}")
                    c.Value = cap
                    c.Font.Name, c.Font.Size, c.Font.Bold = fname, fsize, False
                    summary.append(f"[{blk['sheet']}] img_{i} {os.path.basename(path)} {w}x{h}pt rows={rows} img=行{cur}〜 cap=C{cap_row}")
                    cur = cap_row + 2
                if blk.get("print_area"):
                    base, prefix = blk["print_area"]
                    ws.PageSetup.PrintArea = prefix + str(base + total)
                print(f"[{blk['sheet']}] 挿入 {len(imgs)}枚 / {total}行 / shapes after = {ws.Shapes.Count}")
            wb.Save()
        finally:
            try:
                wb.Close(SaveChanges=False)
            except Exception as e:
                print(f"WARN: Close失敗(既知の0xE0000002系): {e} -> Quitへ進む")
    finally:
        try:
            excel.Quit()
        except Exception as e:
            print(f"WARN: Quit失敗: {e}")
        pythoncom.CoUninitialize()
    return summary

if __name__ == "__main__":
    masked = mask_images()
    plan = build_plan(masked)
    print("=== 挿入計画 ===")
    n_all = 0
    for blk in plan:
        tot = sum(max(1, math.ceil(disp_size(*Image.open(p).size)[1] / ROW_PT)) for p, _ in blk["images"]) + 2 * len(blk["images"]) + (2 if blk.get("lead") else 0)
        n_all += len(blk["images"])
        print(f"  {blk['sheet']}: anchor=C{blk['anchor']} 挿入{len(blk['images'])}枚 {tot}行 insert={blk['insert']}")
    print(f"合計 {n_all}枚")
    if "--dry" in sys.argv:
        for blk in plan:
            for p, cap in blk["images"]:
                w, h = disp_size(*Image.open(p).size)
                print(f"  {os.path.basename(p)} {w}x{h}pt -> 「{cap}」")
        sys.exit(0)
    summ = run_com(plan)
    print("=== 実行結果 ===")
    for s in summ:
        print(" ", s)
    print("DONE")
