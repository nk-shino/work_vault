# -*- coding: utf-8 -*-
import zipfile, re
z = zipfile.ZipFile(r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題\BOSS計画.xlsm")
for i in range(1, 22):
    d = z.read(f"xl/charts/chart{i}.xml").decode("utf-8")
    refs = sorted(set(re.findall(r"<c:f>([^<]+)</c:f>", d)))
    maxrows = []
    for r in refs:
        for m in re.finditer(r"\$(\d+)", r):
            maxrows.append(int(m.group(1)))
    print(f"chart{i}: 参照範囲最大行={max(maxrows) if maxrows else None}, 例={refs[1] if len(refs)>1 else (refs[0] if refs else None)}")
