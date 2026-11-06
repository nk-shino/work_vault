# -*- coding: utf-8 -*-
# 相関図①②③を draw.io XML として再作図するジェネレータ
# 入力: styles_stage.json(幾何·様式) texts_stage2.json(現行テキスト) runs_stage2.json(矢頭·破線)
# 出力: drawio_20261106/相関図_pana_20261106.drawio (3ページ) + ページ別XML + 検証JSON
import io, sys, json, os, html, re
from xml.sax.saxutils import escape, quoteattr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'C:/Users/ss80751/AppData/Local/Temp/kohden-code/corr23'
OUT  = r'C:/Users/ss80751/kohden-code-workspace/20261102_管理文書用語と相関図/drawio_20261106'
os.makedirs(OUT, exist_ok=True)
S = json.load(open(f'{BASE}/styles_stage.json', encoding='utf-8'))['pana']
TX = json.load(open(f'{BASE}/texts_stage2.json', encoding='utf-8'))['pana']
RN = json.load(open(f'{BASE}/runs_stage2.json', encoding='utf-8'))

def ole2hex(v):
    if v is None: return None
    if v == -2147483648: return None
    r = v & 0xFF; g = (v >> 8) & 0xFF; b = (v >> 16) & 0xFF
    return f'#{r:02X}{g:02X}{b:02X}'

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
    lines = wrap_lines(t, w, fsz)
    return lines * fsz * 1.45 + 3

# --- 明示調整表(clip修正ラウンドの算定を引き継ぎ) ---
# 仕上げラウンドの方針:
# · ②下段(n15/n16/n06r/liner)を+10pt下げ、EE15/EE16ラベル用の帯(383.4〜399.5)を確保。
#   e15/e16の縦セグメントはtap位置を箱右端寄り(x=190/360)へ移し、ラベルは各線の左に1行で置く
#   (e16_lは現幅153では2行になるため170に拡幅。wrap計算済: 1行=13.88)。
# · n06rは注記の必要高さが90(現行のままでは下端541.5で凡例536と衝突)。箱を164·注記を158に
#   広げて6行(68.25)に収め、下端529.8で凡例との間を6.2確保。
# · n17は注記必要高さ58.1に箱を圧縮(現行92は過剰)。N10下端(277)とN18タグ(378)の間に収める。
# · e02の底辺(s0)はlinerの+10追従で515へ、s1はそれに合わせて延長。
# · EE01ラベルは凡例と重なる位置(518.2+2行)からラベル群の列(l=404)へ移動。
# · e17_lは帯上端(150)と交差していたため帯内(155)へ。e18_s0はESXi箱上端(196)で止める。
# · タグは「box左端-2·上端-7」に統一(左2·上6ptの重ね)。n04のみN03下端341.8との
#   衝突を避け現行(340.8)維持。アイコンはbox左+5·上+4に統一(後段の相対配置パス)。
# · ①は凡例を463へ上げてE03線(455)との空きを8に。S1/E-a/E-b/N10/S2タグを統一位置へ。
# · ③はN11群を+10xしてEE14ラベルとの間を14に、e14_l/e07_l/e06_lを各線と干渉しない位置へ。
#   凡例の行送りを①②と同じ17.52に統一。
# 規格化ラウンド(2026-11-06·site-design仕様 4-1〜4-11·Q1·Q2):
# · 線幅語彙を統一(箱1.5·コンテナ2.25·注記/帯/タグ0.75·別図参照1.0·③設備3.0→1.5)。
# · 枠の破線パターンを6 4に統一。推定接続の線色を#808080に統一(凡例文言と一致)。
# · ①の本文を9.5·エッジラベルを7.5に統一(box/txtの明示高さを廃止し汎用則で再計算)。
# · 凡例行を3頁共通で528.2基準·行送り17.52に統一(②は536基準でleg3下端が頁下端595を
#   超過する既存欠陥を同時に解消。②n06r下端は527.7へ圧縮)。
# · 注記(n05)は角なし(rounded=0)。凡例■は分類色で着色(Q1)·**太字**記法は<b>へ変換(Q2)。
# · ②の子箱を親左端+16(l=56)に寄せ、タグ/注記を追従。
ADJ = {
 '相関図②': {
   'g2_n01_txt': {'h': 31.6},
   'g2_n01_box': {'h': 187.4},
   'g2_n02_box': {'l': 56, 'h': 51.4}, 'g2_n02_txt': {'l': 82, 'h': 45.4}, 'g2_n02_tag': {'l': 54, 't': 230},
   'g2_n03_tag': {'l': 54, 't': 289}, 'g2_n03_box': {'l': 56, 't': 290.4, 'h': 51.4}, 'g2_n03_txt': {'l': 82, 't': 293.4, 'h': 45.4},
   'g2_n04_tag': {'l': 54, 't': 342.8}, 'g2_n04_box': {'l': 56, 't': 343.8, 'h': 37.6}, 'g2_n04_txt': {'l': 82, 't': 346.8, 'h': 31.6},
   'g2_n19_box': {'h': 51.9}, 'g2_n19_txt': {'h': 45.4}, 'g2_n19_tag': {'t': 191},
   'g2_n10_box': {'h': 79}, 'g2_n10_txt': {'h': 73}, 'g2_n10_tag': {'t': 191},
   'g2_n17_tag': {'t': 279}, 'g2_n17_box': {'t': 286, 'h': 76.9}, 'g2_n17_txt': {'t': 289, 'h': 71.9},
   'g2_n18_tag': {'t': 378.07},
   'g2_liner_box': {'h': 36.1, 't': 468.86}, 'g2_liner_txt': {'h': 30.1, 't': 471.86},
   'g2_n15_box': {'t': 399.5}, 'g2_n15_txt': {'t': 402.5},
   'g2_n16_box': {'t': 399.5}, 'g2_n16_txt': {'t': 402.5},
   'g2_n06r_box': {'t': 455.53, 'w': 164, 'h': 72.2},
   'g2_n06r_txt': {'t': 458.53, 'l': 43, 'w': 158, 'h': 68.25},
   'g2_e_e15': {'l': 190}, 'g2_e_e16': {'l': 360},
   'g2_e_e15_l': {'t': 384.5}, 'g2_e_e16_l': {'l': 199, 't': 384.5, 'w': 170},
   'g2_e_e02_s0': {'t': 515}, 'g2_e_e02_s1': {'h': 253},
   'g2_e_e01_l': {'l': 404, 't': 496},
   'g2_e_e02_l': {'l': 404}, 'g2_e_e04_l': {'l': 404}, 'g2_e_e08_l': {'l': 404},
   'g2_e_e17_l': {'t': 155},
   'g2_e_e18_s0': {'h': 14},
   'g2_leg0': {'t': 528.2}, 'g2_leg1': {'t': 545.72}, 'g2_leg2': {'t': 563.24}, 'g2_leg3': {'t': 580.76},
 },
 '相関図③': {
   'g3_n13_tag': {'l': 512, 't': 407.5}, 'g3_n13_box': {'l': 514, 'w': 162}, 'g3_n13_txt': {'l': 540, 'w': 130},
   'g3_n12_box': {'h': 51.4}, 'g3_n12_txt': {'h': 45.4}, 'g3_n12_tag': {'t': 413},
   'g3_n14_box': {'h': 65.2}, 'g3_n14_txt': {'h': 59.2}, 'g3_n14_tag': {'t': 289},
   'g3_pcr_box': {'h': 41.6}, 'g3_pcr_txt': {'h': 30.1},
   'g3_dgsr_box': {'h': 41.6}, 'g3_dgsr_txt': {'h': 30.1},
   'g3_n07_tag': {'t': 230}, 'g3_n08_tag': {'t': 338.8}, 'g3_n09_tag': {'t': 417},
   'g3_n09_txt': {'w': 192},
   'g3_n11_box': {'l': 340}, 'g3_n11_tag': {'l': 338, 't': 233}, 'g3_n11_txt': {'l': 366, 'w': 152},
   'g3_e_e14_l': {'t': 238.5},
   'g3_e_e07_l': {'t': 184},
   'g3_e_e06_l': {'t': 308},
   'g3_e_e03_l': {'t': 344.5},
   'g3_e_e04_l': {'t': 474.8},
   'g3_leg0': {'t': 528.2}, 'g3_leg1': {'t': 545.72}, 'g3_leg2': {'t': 563.24}, 'g3_leg3': {'t': 580.76},
 },
 '相関図①': {
   'g1_s1_tag': {'l': 298, 't': 143},
   'g1_ea_tag': {'l': 638, 't': 143},
   'g1_eb_tag': {'l': 638, 't': 248},
   'g1_s2_tag': {'l': 328, 't': 348},
   'g1_n10_tag': {'l': 638, 't': 358},
   'g1_e_e02_l': {'t': 152},
   'g1_leg0': {'t': 528.2}, 'g1_leg1': {'t': 545.72}, 'g1_leg2': {'t': 563.24}, 'g1_leg3': {'t': 580.76},
 },
}

# アイコンの相対位置: icon_aはbox左+5·上+4。ストライプ(b0/b1/b2)はa基準。
# 端末スタンド(b)はa右+4·下+0.5。アンドン(n09)のみ実測形状を名前指定で維持。
ICON_REL_SUF = {'_icon_b0': (2, 3), '_icon_b1': (2, 7.5), '_icon_b2': (2, 12), '_icon_b': (4, 15.5)}
ICON_REL_NAME = {'g3_n09_icon_b': (6, 10), 'g3_n09_icon_c': (2, 16)}

def cell_vertex(cid, style, value, l, t, w, h):
    v = quoteattr(value) if value is not None else '""'
    return (f'<mxCell id={quoteattr(cid)} vertex="1" parent="1" style={quoteattr(style)} value={v}>'
            f'<mxGeometry x="{l:g}" y="{t:g}" width="{w:g}" height="{h:g}" as="geometry"/></mxCell>')

def cell_edge(cid, style, p1, p2):
    return (f'<mxCell id={quoteattr(cid)} edge="1" parent="1" style={quoteattr(style)}>'
            f'<mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{p1[0]:g}" y="{p1[1]:g}" as="sourcePoint"/>'
            f'<mxPoint x="{p2[0]:g}" y="{p2[1]:g}" as="targetPoint"/>'
            f'</mxGeometry></mxCell>')

SQ_COLS = ['#7B5FA3', '#9BBB59', '#A94438', '#969696']  # 凡例■の着色順: サーバ·端末·設備·推定
# 長いASCII連続列(バックアップパス)は折返し不可で箱外へ出るため、区切り文字後に<wbr>を注入する
WBR_NAMES = {'g2_n17_txt'}

def make_value(text, bold_flag, sq=False, wbr=False):
    t = text.replace('\r', '\n')
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    if wbr:
        t = t.replace('\\', '\\<wbr>').replace('_', '_<wbr>')
    t = t.replace('\n', '<br>')
    if sq:
        # プレースホルダ経由(逐次replaceは直前の置換結果内の■に再マッチするため)
        marks = [f'\x00{i}\x00' for i in range(5)]
        for i in range(4):
            t = t.replace('■', marks[i], 1)
        t = t.replace('□', marks[4], 1)
        for i, c in enumerate(SQ_COLS):
            t = t.replace(marks[i], f'<font color="{c}">■</font>')
        t = t.replace(marks[4], '<font color="#969696">□</font>')
    if bold_flag == -2 and '<br>' in t:
        a, b = t.split('<br>', 1)
        t = f'<b>{a}</b><br>{b}'
    elif bold_flag == -2:
        t = f'<b>{t}</b>'
    return t

def arc_for(w, h):
    # 角丸は絶対値で統一(箱4pt·小形は高さの1/4まで)
    return round(min(4.0, min(w, h) / 4.0), 2)

def frame_lw(n, fill, line, dashed, default):
    # 線幅語彙の統一: 箱1.5 / コンテナ2.25 / 注記·帯·タグ0.75 / 別図参照·外部1.0
    if n == 'g2_n01_box':
        return 2.25
    if line == '#8C8C8C':
        return 0.75
    if line == '#BFBFBF' or n.endswith('_tag'):
        return 0.75
    if dashed and line == '#969696' and (fill is None or fill == '#FFFFFF'):
        return 1.0
    if line in ('#7B5FA3', '#9BBB59', '#A94438', '#808080', '#969696'):
        return 1.5
    return default

report = {'sheets': {}}
page_xmls = []
for sn in ['相関図①', '相関図②', '相関図③']:
    shapes = S[sn]['shapes']; texts = TX[sn]; runs = RN[sn]
    adj = ADJ.get(sn, {})
    G = {s['name']: dict(l=s['l'], t=s['t'], w=s['w'], h=s['h']) for s in shapes}
    # フォント統一(①: 本文9.5·エッジラベル7.5)。幅·高さの全計算に先立って確定する。
    FZOVR = {'相関図①': (9.5, 7.5)}
    FS = {}
    ov = FZOVR.get(sn)
    for s in shapes:
        f0 = s.get('fsz', 9); n0 = s['name']
        if ov:
            if s['type'] == 17 and n0.endswith('_l'):
                f0 = ov[1]
            elif (s['type'] == 17 and n0.endswith('_txt')) or (s['type'] == 1 and texts.get(n0, s.get('text', ''))):
                f0 = ov[0]
        FS[n0] = f0
    # txt の必要高さ(汎用ルール)とbox収容(①は箱内余白20.3まで許容)
    insw = 21.5 if sn == '相関図①' else 20
    for s in shapes:
        n = s['name']
        if n.endswith('_txt') and n in texts and s['type'] == 17:
            need = max(txt_need(texts[n], G[n]['w'], FS[n]), G[n]['h'])
            G[n]['h'] = round(need, 2)
            bn = n[:-4] + '_box'
            if bn in G:
                Tins = G[n]['t'] - G[bn]['t']
                Bins = (G[bn]['t'] + G[bn]['h']) - (G[n]['t'] + s['h'])
                if 0 <= Tins <= insw and 0 <= Bins <= insw:
                    G[bn]['h'] = round(Tins + G[n]['h'] + max(Bins, 2), 2)
    # 明示調整の適用
    for n, d in adj.items():
        if n in G:
            G[n].update(d)
    # ラベル(_l)の高さを最終幅で再計算(_txtは上の汎用ルール·ADJで確定済み)
    for s in shapes:
        n = s['name']
        if n.endswith('_l') and n in texts and s['type'] == 17:
            need = max(txt_need(texts[n], G[n]['w'], FS[n]), G[n]['h'])
            G[n]['h'] = round(need, 2)
    # アイコン位置を所属boxからの相対位置に統一
    for s in shapes:
        n = s['name']
        if n.endswith('_icon_a'):
            bn = n[:-7] + '_box'
            if bn in G:
                G[n]['l'] = round(G[bn]['l'] + 5, 2)
                G[n]['t'] = round(G[bn]['t'] + 4, 2)
        elif n in ICON_REL_NAME:
            dx, dy = ICON_REL_NAME[n]
            an = n[:-7] + '_icon_a'
            if an in G:
                G[n]['l'] = round(G[an]['l'] + dx, 2)
                G[n]['t'] = round(G[an]['t'] + dy, 2)
        else:
            for suf, (dx, dy) in ICON_REL_SUF.items():
                if n.endswith(suf):
                    an = n[:-len(suf)] + '_icon_a'
                    if an in G:
                        G[n]['l'] = round(G[an]['l'] + dx, 2)
                        G[n]['t'] = round(G[an]['t'] + dy, 2)
                    break
    # 線分端点の再スナップ(移動·拡縮したbox境界へ)
    moved = []
    for s in shapes:
        n = s['name']
        if s['type'] == 1:
            o = {'l': s['l'], 't': s['t'], 'w': s['w'], 'h': s['h']}; nw = G[n]
            if any(abs(o[k] - nw[k]) > 0.01 for k in 'ltwh'):
                moved.append((o, nw))

    def snap(x, y):
        for o, nw in moved:
            ol, ot, orr, ob = o['l'], o['t'], o['l'] + o['w'], o['t'] + o['h']
            nl, nt, nr, nb = nw['l'], nw['t'], nw['l'] + nw['w'], nw['t'] + nw['h']
            if abs(y - ot) <= 2 and ol - 2 <= x <= orr + 2: y = nt
            elif abs(y - ob) <= 2 and ol - 2 <= x <= orr + 2: y = nb
            if abs(x - ol) <= 2 and ot - 2 <= y <= ob + 2: x = nl
            elif abs(x - orr) <= 2 and ot - 2 <= y <= ob + 2: x = nr
        return round(x, 2), round(y, 2)

    cells = []
    for s in shapes:
        n = s['name']; g = G[n]; ty = s['type']
        if ty == 6:
            continue
        if ty == 9:
            r = runs.get(n, {})
            dash = r.get('dash', s.get('dash', 1))
            col = ole2hex(r.get('col', s.get('line'))) or '#000000'
            lw = r.get('lw', s.get('lw', 1.0))
            if dash != 1:
                col = '#808080'  # 推定接続は凡例文言どおりグレーに統一
            st = f'html=1;strokeColor={col};strokeWidth={lw:g};'
            if dash != 1:
                st += 'dashed=1;dashPattern=6 4;'
            if r.get('end', 1) != 1:
                st += 'endArrow=classic;endSize=4;'
            else:
                st += 'endArrow=none;'
            if r.get('beg', 1) != 1:
                st += 'startArrow=classic;startSize=4;'
            p1 = snap(g['l'], g['t']); p2 = snap(g['l'] + g['w'], g['t'] + g['h'])
            cells.append(cell_edge(n, st, p1, p2))
            continue
        fill = ole2hex(s.get('fill')); line = ole2hex(s.get('line'))
        fnt = s.get('font') or 'Meiryo UI'; fsz = FS[n]; bold = s.get('bold', 0)
        tc = ole2hex(s.get('tcolor')) or '#000000'
        text = texts.get(n, s.get('text', ''))
        arc = arc_for(g['w'], g['h'])
        if ty == 1 and not text:
            if line == '#BFBFBF' or n.endswith('_tag'):
                lwv = 0.75
            elif '_icon' in n:
                lwv = s.get('lw', 1)   # アイコンは現行維持
            else:
                lwv = frame_lw(n, fill, line, s.get('dash', 1) != 1, s.get('lw', 1))
            rounded = '0' if line == '#8C8C8C' else '1'   # 注記(n05)は角なし
            st = f'rounded={rounded};absoluteArcSize=1;arcSize={arc:g};whiteSpace=wrap;html=1;fontFamily={fnt};'
            st += f'fillColor={fill};' if fill else 'fillColor=none;'
            st += f'strokeColor={line};' if line else 'strokeColor=none;'
            st += f'strokeWidth={lwv:g};'
            if s.get('dash', 1) != 1:
                st += 'dashed=1;dashPattern=6 4;'
            cells.append(cell_vertex(n, st, None, g['l'], g['t'], g['w'], g['h']))
            continue
        if ty == 1:
            rounded = '0' if line == '#8C8C8C' else '1'
            lwv = frame_lw(n, fill, line, s.get('dash', 1) != 1, s.get('lw', 0.75))
            st = f'rounded={rounded};absoluteArcSize=1;arcSize={arc:g};whiteSpace=wrap;html=1;fontFamily={fnt};fontSize={fsz:g};fontColor={tc};'
            st += f'fillColor={fill};' if fill else 'fillColor=none;'
            st += f'strokeColor={line};' if line else 'strokeColor=none;'
            st += f'strokeWidth={lwv:g};align=center;verticalAlign=middle;'
            if bold == -1:
                st += 'fontStyle=1;'
            val = make_value(text, bold, sq=n.endswith('_leg1'))
            cells.append(cell_vertex(n, st, val, g['l'], g['t'], g['w'], g['h']))
            continue
        wbr = n in WBR_NAMES
        st = f'text;html=1;whiteSpace=wrap;fontFamily={fnt};fontSize={fsz:g};fontColor={tc};'
        st += 'align=left;verticalAlign=top;spacingLeft=2;spacingRight=2;spacingTop=1;spacingBottom=1;'
        val = make_value(text, bold, sq=n.endswith('_leg1'), wbr=wbr)
        cells.append(cell_vertex(n, st, val, g['l'], g['t'], g['w'], g['h']))
    model = ('<mxGraphModel dx="900" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
             'arrows="1" fold="1" page="1" pageScale="1" pageWidth="842" pageHeight="595" math="0" shadow="0">'
             '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
             + ''.join(cells) + '</root></mxGraphModel>')
    page_xmls.append((sn, model))
    allval = html.unescape(html.unescape(''.join(cells))).replace('<br>', '\n')
    for tg in ('<b>', '</b>', '<wbr>'):
        allval = allval.replace(tg, '')
    allval = re.sub(r'</?font[^>]*>', '', allval)
    # Q2変換(**X**→<b>X</b>)と対称化: 均衡した**のみ除去し、リテラルの****(n17のファイル名)は残す
    missing = [k for k, t in texts.items()
               if re.sub(r'\*\*(.+?)\*\*', r'\1', t.replace('\r', '\n')) not in allval]
    nv = sum(1 for s in shapes if s['type'] != 6)
    ns = sum(1 for s in shapes if s['type'] == 9)
    na = sum(1 for k, v in runs.items() if 'beg' in v and (v['beg'] != 1 or v['end'] != 1))
    report['sheets'][sn] = {'cells': nv, 'segments': ns, 'arrows': na, 'missing_texts': missing}
    print(sn, 'cells', nv, 'segments', ns, 'arrows', na, 'missing', missing)

pages = []
for i, (sn, m) in enumerate(page_xmls):
    pages.append(f'<diagram name="{sn}" id="p{i+1}">{escape(m, {chr(34): "&quot;"})}</diagram>')
    open(f'{OUT}/corr{"123"[i]}_page.xml', 'w', encoding='utf-8').write(m)
mx = ('<mxfile host="kohden-code" modified="2026-11-06" agent="kohden-code" version="24.7.0">'
      + ''.join(pages) + '</mxfile>')
open(f'{OUT}/相関図_pana_20261106.drawio', 'w', encoding='utf-8').write(mx)
json.dump(report, open(f'{OUT}/verify_structural.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved:', f'{OUT}/相関図_pana_20261106.drawio')
