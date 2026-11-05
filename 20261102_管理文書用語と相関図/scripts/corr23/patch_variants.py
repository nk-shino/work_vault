# -*- coding: utf-8 -*-
"""patch_variants.py — 検証用variantを元ファイルのコピーから生成する(元ファイル不変)。

- corr23_probe_after.py   : corr23_probe.py のコピー。出力を geom_after.json へ。
- collision_check_after.py: collision_check.py のコピー。SRC=geom_after.json、
                            OUT=collision_report_after.json。
geom_before.json (216KB原本) と collision_check.py / corr23_probe.py 本体は変更しない。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

JOBS = [
    ("corr23_probe.py", "corr23_probe_after.py",
     [("geom_before.json", "geom_after.json")]),
    ("collision_check.py", "collision_check_after.py",
     [("geom_before.json", "geom_after.json"),
      ("collision_report_before.json", "collision_report_after.json")]),
]

for src_name, dst_name, subs in JOBS:
    src = os.path.join(HERE, src_name)
    dst = os.path.join(HERE, dst_name)
    text = open(src, encoding="utf-8").read()
    for old, new in subs:
        n = text.count(old)
        text = text.replace(old, new)
        print("%s: '%s' -> '%s' x%d" % (dst_name, old, new, n))
    open(dst, "w", encoding="utf-8", newline="").write(text)
    print("wrote %s (%d bytes)" % (dst_name, len(text.encode("utf-8"))))
print("VARIANTS DONE")
