# -*- coding: utf-8 -*-
# wrap計算プローブ: 調整予定のテキストセルの必要高さを gen_drawio.py と同じモデルで算出
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'C:/Users/ss80751/AppData/Local/Temp/kohden-code/corr23'
S = json.load(open(BASE + '/styles_stage.json', encoding='utf-8'))['pana']
TX = json.load(open(BASE + '/texts_stage2.json', encoding='utf-8'))['pana']

def wrap_lines(text, w, fsz):
    usable = max(w - 8, 20)
    n = 0
    for para in text.split('\n'):
        if not para.strip():
            n += 1; continue
        width = 0.0; k = 1
        for ch in para:
            cw = fsz if ord(ch) > 0x2E80 else fsz * 0.55
            if width + cw > usable:
                k += 1; width = cw
            else:
                width += cw
        n += k
    return n

def txt_need(t, w, fsz):
    return wrap_lines(t, w, fsz) * fsz * 1.45 + 3

NAME2SHEET = {}
for sn in S:
    for s in S[sn]['shapes']:
        NAME2SHEET[s['name']] = sn

probes = [
 ('g2_n06r_txt', 146, 7.5), ('g2_n06r_txt', 158, 7.5), ('g2_n06r_txt', 162, 7.5),
 ('g2_n17_txt', 118, 9.5),
 ('g2_n05_txt', 146, 6.5),
 ('g2_e_e15_l', 148, 7.5), ('g2_e_e15_l', 152, 7.5),
 ('g2_e_e16_l', 153, 7.5), ('g2_e_e16_l', 166, 7.5), ('g2_e_e16_l', 170, 7.5),
 ('g2_e_e01_l', 112, 7.5),
 ('g2_e_e02_l', 120, 7.5), ('g2_e_e04_l', 130, 7.5), ('g2_e_e08_l', 134, 7.5), ('g2_e_e17_l', 176, 7.5),
 ('g3_n11_txt', 152, 9.5), ('g3_n11_txt', 179, 9.5),
 ('g3_e_e14_l', 82, 7.5), ('g3_e_e07_l', 150, 7.5),
 ('g1_e_e02_l', 110, 8.0),
 ('g2_n15_txt', 128, 9.5), ('g2_n16_txt', 128, 9.5),
 ('g2_n10_txt', 108, 9.5),
]
for name, w, fsz in probes:
    sn = NAME2SHEET[name]
    t = TX[sn][name]
    lines = wrap_lines(t, w, fsz)
    need = lines * fsz * 1.45 + 3
    ole_h = next(s['h'] for s in S[sn]['shapes'] if s['name'] == name)
    print(f'{name}  w={w} fsz={fsz}  lines={lines} need={need:.2f}  ole_h={ole_h}')
