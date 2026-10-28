# -*- coding: utf-8 -*-
"""corr_pana_restore_printer.py — printerSettings(DEVMODE)を基準版に復元(移植版)。
移植元: 20261013_LNB_Collector/PanaCIM_印刷設定基準/restore_printersettings.py
差分: 既定対象を corr_dryrun_pana.xlsx に変更。基準binは原本と同一のものを参照。
使い方: python corr_pana_restore_printer.py [対象xlsx]
"""
import sys, io, time, warnings, zipfile, shutil, os
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REFBASE = r"C:\Users\ss80751\kohden-code-workspace\20261013_LNB_Collector\PanaCIM_印刷設定基準"
REF = {"xl/printerSettings/printerSettings2.bin": os.path.join(REFBASE, "printerSettings2.bin"),
       "xl/printerSettings/printerSettings3.bin": os.path.join(REFBASE, "printerSettings3.bin")}
F = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "corr_dryrun_pana.xlsx")
TMP = F + ".restore_tmp"
print("対象:", F)

refdata = {k: open(v, "rb").read() for k, v in REF.items()}
zin = zipfile.ZipFile(F)
cur = {k: zin.read(k) for k in REF}
same = {k for k in REF if cur[k] == refdata[k]}
print("基準と一致済み:", sorted(same) if same else "なし(要復元)")
if len(same) == len(REF):
    zin.close()
    print("復元不要")
    sys.exit(0)

zout = zipfile.ZipFile(TMP, "w")
for info in zin.infolist():
    data = refdata.get(info.filename) or zin.read(info.filename)
    zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    zi.compress_type = info.compress_type
    zi.external_attr = info.external_attr
    zout.writestr(zi, data)
zout.close(); zin.close()

za, zb = zipfile.ZipFile(TMP), zipfile.ZipFile(F)
diffs = [n for n in zb.namelist() if za.read(n) != zb.read(n)]
za.close(); zb.close()
assert set(diffs) == set(REF) - same, "予期しない差分: %r" % diffs
for _ in range(5):
    try:
        shutil.move(TMP, F)
        break
    except PermissionError as e:
        print("待機(ファイル使用中):", e); time.sleep(2)
else:
    sys.exit(1)
print("復元完了: printerSettings2.bin/3.bin を基準版へ戻し、他エントリは無変更")
