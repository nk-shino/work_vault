# -*- coding: utf-8 -*-
# 目視検証用クロップ(原点補正済み: 図面内座標pt × 3 = px)
from PIL import Image
import os

SRC = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
OUT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\icons_dl\crops"
os.makedirs(OUT, exist_ok=True)
S = 3.0

def crop(img, name, x0, y0, x1, y1):
    box = (int(x0 * S), int(y0 * S), int(x1 * S), int(y1 * S))
    img.crop(box).save(os.path.join(OUT, name))
    print("saved", name, box)

# 図③: N07/N11/E14/E03/E10 コリドー(図面内座標 + OX,OY=(40,182))
line = Image.open(os.path.join(SRC, "c4_mock_3_line.png"))
crop(line, "line_corridor.png", 60, 220, 620, 420)
crop(line, "line_right.png", 480, 220, 830, 500)
crop(line, "line_left.png", 0, 220, 340, 420)
# 図②: 右列の交差3件 + E15/E16
mgmt = Image.open(os.path.join(SRC, "c4_mock_2_mgmt.png"))
crop(mgmt, "mgmt_right.png", 320, 190, 830, 540)
crop(mgmt, "mgmt_top.png", 300, 180, 830, 330)
