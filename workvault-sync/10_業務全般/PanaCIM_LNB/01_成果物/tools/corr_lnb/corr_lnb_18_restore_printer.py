# -*- coding: utf-8 -*-
"""corr_lnb_18_restore_printer.py — printerSettings(DEVMODE)復元(apply段階用·本段階では未実行)。
移植元: corr_pana_restore_printer.py(20261013_LNB_Collector/PanaCIM_印刷設定基準)。
差分: 基準binを「対象冊と同じ本来のprinterSettings」から抽出する方式に変更。
Pana-CIM冊は基準binが既知だったが、LNB冊は未取得のため、applyの前にLNB原本から
binを抽出して基準とし、apply後の保存で書き換わった場合に復元する。

使い方(apply段階):
  1) 適用前: python corr_lnb_18_restore_printer.py --extract 原本.xlsx 出力dir
     → 原本内の xl/printerSettings/*.bin を出力dirへ取り出す(基準の確保)
  2) 適用後: python corr_lnb_18_restore_printer.py --restore 原本.xlsx 出力dir
     → bin以外のエントリを無変更のまま、binだけを基準へ戻す
注意: .learnings の失敗記録どおり、xlsx保存時にExcelがprinterSettingsを書き換えることがある。
復元は zip エントリ単位の置換(openpyxl 不使用·図形に触れない)。
"""
import os
import shutil
import sys
import time
import zipfile


def extract(target, outdir):
    os.makedirs(outdir, exist_ok=True)
    n = 0
    with zipfile.ZipFile(target) as z:
        for name in z.namelist():
            if name.startswith("xl/printerSettings/") and name.endswith(".bin"):
                data = z.read(name)
                with open(os.path.join(outdir, os.path.basename(name)), "wb") as f:
                    f.write(data)
                print("extracted:", name, len(data), "bytes")
                n += 1
    if n == 0:
        print("printerSettings not found in", target)
    return n


def restore(target, refdir):
    ref = {}
    for fn in os.listdir(refdir):
        if fn.endswith(".bin"):
            ref["xl/printerSettings/" + fn] = os.path.join(refdir, fn)
    if not ref:
        print("no reference bins in", refdir)
        sys.exit(1)
    refdata = {k: open(v, "rb").read() for k, v in ref.items()}
    tmp = target + ".restore_tmp"
    with zipfile.ZipFile(target) as zin:
        cur = {k: zin.read(k) for k in ref if k in zin.namelist()}
        same = {k for k, v in cur.items() if v == refdata[k]}
        print("基準と一致済み:", sorted(same) if same else "なし(要復元)")
        if len(same) == len(ref):
            print("復元不要")
            return
        with zipfile.ZipFile(tmp, "w") as zout:
            for info in zin.infolist():
                data = refdata.get(info.filename) or zin.read(info.filename)
                zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                zi.compress_type = info.compress_type
                zi.external_attr = info.external_attr
                zout.writestr(zi, data)
    for _ in range(5):
        try:
            shutil.move(tmp, target)
            break
        except PermissionError as e:
            print("待機(ファイル使用中):", e)
            time.sleep(2)
    else:
        sys.exit(1)
    print("復元完了:", sorted(set(ref) - same))


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("--extract", "--restore"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "--extract":
        extract(sys.argv[2], sys.argv[3])
    else:
        restore(sys.argv[2], sys.argv[3])
