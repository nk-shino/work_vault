# -*- coding: utf-8 -*-
"""printerSettings(DEVMODE)を基準版に復元する。
使いどころ: COM保存を伴うxlsx編集の後、PDF出力の前に実行する(ERR-20261023-006)。
- 基準binは 2026-10-23 の efb8991 版(頁サイズ 595.20x841.68pt)から採取
- 復元後、zip内の差分が bin2/3 のみであることを検証してから上書きする"""
import sys, io, time, warnings, zipfile, shutil, os
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REF = {"xl/printerSettings/printerSettings2.bin": os.path.join(HERE, "printerSettings2.bin"),
       "xl/printerSettings/printerSettings3.bin": os.path.join(HERE, "printerSettings3.bin")}
# 対象は第1引数で指定する(ERR-20261023-007: 引数を無視して既定ファイルを検査していた事故の修正)。
# 省略時の既定は保管庫の現行ファイル。
F = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
TMP = F + ".restore_tmp"
print(f"対象: {F}")

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

# 検証: 差分は bin2/3 のみ
za, zb = zipfile.ZipFile(TMP), zipfile.ZipFile(F)
diffs = [n for n in zb.namelist() if za.read(n) != zb.read(n)]
za.close(); zb.close()
assert set(diffs) == set(REF), f"予期しない差分: {diffs}"
for _ in range(5):
    try:
        shutil.move(TMP, F)
        break
    except PermissionError as e:
        print(f"待機(ファイル使用中): {e}"); time.sleep(2)
else:
    sys.exit(1)
print("復元完了: printerSettings2.bin/3.bin を基準版へ戻し、他エントリは無変更")
