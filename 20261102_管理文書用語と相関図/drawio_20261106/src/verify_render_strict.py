# -*- coding: utf-8 -*-
"""verify_render_strict.py -- 相関図②③④ 図形描画の厳密再検証ハーネス (読み取り専用).

検証クラス:
  C1  page_setup      : 横向きA4 fit1x1 · PrintArea · PrintTitleRows未設定 · フッター様式番号
  C2  inventory       : drawing XML 直読みによる図形インベントリ (名前·box·flip·bodyPr·フォント·全文)
                        + COM 実測幾何との突合。pywin32 TextFrame 系の gen_py 依存は使わない
  C3  text_fit        : (a) nvis推定(マージン10.0) vs PDF実測行数 (b) フレーム高 >= 行数*fsz*1.65+3
                        (c) 固定高 leaf の AutoSize=0。末尾CJK等値で最終行欠落を検出
  C4  clearance       : テキストボックス間 3.75pt (clearance_check.py の実績判定を再利用)
  C5  collision       : postA ベースライン (collision_report_postA3.json) と比較し新規0
                        (②③: collision_check.py 5分類。④: phaseB_verify の豁免スキャン)
  C6  connectors      : EE* 線の向き(flip)実測記録 · ラベル重なりはC5分類c · EE08/n19(R1)は既知例外
  C7  orphans         : 折返し分断·孤行(行末1〜2字)の全図形定量 · 既知P1〜P8と本ラウンド退行の分類
  C8  pdf_roundtrip   : シート別PDF(横向き1頁·fit縮小率記録) → 全頁PNG + 図形単位4xクロップPNG
                        (参照列 refs クロップを自動生成 -- K3 解消)
  C9  data_accuracy   : ②③変更済み文言 = J-02 §9.1 as-built と完全一致 · ④トラブルテーブル = EXPECTED_ACT
                        · 既存図形テキスト = b5_current_state.json と一致(差分は退行疑い)
  C10 err_regression  : ERR-20261109-001〜012 対応の 10 クラス PASS/FAIL と証跡一覧

制約: 冊は ReadOnly で開き保存しない。コンソールに図形テキスト本文を出力しない
(証跡JSONには記録する)。認証情報シートの値は読まない。
"""
import sys, io, os, re, json, math, zipfile, datetime

class _SafeBuf(object):
    """close() されても実バッファを閉じないスタブ。
    clearance_check/collision_check が import 時に sys.stdout を再ラップし、
    前のラッパ GC で実バッファが閉じる事故を防ぐ。"""
    def __init__(self, real):
        self._real = real
    def write(self, b):
        return self._real.write(b)
    def flush(self):
        try:
            self._real.flush()
        except Exception:
            pass
    def close(self):
        pass
    def writable(self):
        return True
    def readable(self):
        return False
    def seekable(self):
        return False
    @property
    def closed(self):
        return False

sys.stdout = io.TextIOWrapper(_SafeBuf(sys.stdout.buffer), encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(_SafeBuf(sys.stderr.buffer), encoding='utf-8', errors='replace')
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
import win32com.client as wc
import pymupdf as fitz

BASE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23"
OUT = os.path.join(BASE, "strictverify")
os.makedirs(OUT, exist_ok=True)
WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\drawio_20261106"
sys.path.insert(0, BASE)
import clearance_check as clc     # 実績: 3.75pt 離隔判定
import collision_check as cc      # 実績: 5分類衝突判定

BK = {
 'pana': os.path.join(BASE, r"deepwork_bk\stage2\edited_Pana-CIM管理手順書案_未承認.xlsx"),
 'lnb':  os.path.join(BASE, r"deepwork_bk\stage2\edited_LNB管理手順書案_未承認.xlsx"),
}
SHEETS = ['相関図②', '相関図③', '相関図④']
SN_TAG = {'相関図②': 's2', '相関図③': 's3', '相関図④': 's4'}
PA23 = {'pana': ['$A$5:$AZ$66', '$A$5:$AZ$66'], 'lnb': ['$A$5:$AZ$67', '$A$5:$AZ$67']}
PA4 = '$A$1:$BA$66'
FOOTER_KEY = 'NR4030-0300-A3'
EMU = 12700.0
CLEAR_PT = 3.75
NMARGIN = 10.0            # nvis 計算のマージン (as-built §9.5.1)
PITCH = 1.65              # 行ピッチ実測 = fsz * 1.65 (as-built §9.2)
FIXED_LEAVES = {'g2_n05_txt', 'g2_n06r_txt', 'g3_n07_txt', 'g3_n11_txt', 'g3_n12_txt'}
CHANGED_TEXT = {'g2_bandhead', 'g2_bandnote', 'g2_n05_txt', 'g2_n06r_txt',
                'g3_n07_txt', 'g3_n11_txt', 'g3_n12_txt'}
ALLOWED_GEOM_DIFF = {('相関図②', 'g2_n15')}          # lnb のみ高さ差 85.7/68.8 (設計差分)
CRED_SHEETS = ('認証情報一覧', '申し送り(認証情報)')
WANT_LINKS = {'pana': 13, 'lnb': 10}

# ---- J-02 §9.1 as-built 期待文言 ----
EXP = {
 'g2_bandhead': 'PanaCIM管理側ネットワーク — 上位網 192.168.30.xx〔T1:-9-/-10-〕',
 'g2_bandnote': '当Site実測: 制限セグメント 172.25.253.0/24〔T1b: ネットワークイメージ.pptx·2026-10-27〕',
 'g2_n05_txt': ('当Site運用: PanaCIM(CIMA)環境はESXi(172.25.253.45)上VM「CIMC-SV」で稼働。'
                '別系統CIMA-SV(172.25.253.42·物理)を確認(X02-⑪)。\n'
                '再起動対象 — 月次: CIMC-SV / 異常時: CIM-C·CIM-A PC·ESXi·CIMC-SV'
                '(0494-912039(06)·管理書第3章)。順序の全体像は未確定→注記X02-③。'),
 'g2_n06r_txt': '【上位システム】NPM-DGS\n172.25.253.10 複数台接続可(-8-)\n管理境界·DGS-SV同一性はX02-⑫(要確認)',
}
EXP_LINE2 = {
 'g3_n07_txt': 'L1〜L3は§8で追記·iLNB同一性は要確認#1',
 'g3_n11_txt': 'T1の「LWSエディター」との同一性は要確認',
 'g3_n12_txt': 'ライン毎に前/後側用(-9-)·照合はLNB設定前提(A-2)',
}
# ④ 対処法セル期待値 (phaseB_build TABLE 写し·phaseB_verify と同一)
EXPECTED_ACT = {
 'pana': {
  't4_b2_r1_c2': '作業を止め、第3章の管理体制に記載された者へ連絡する(7-2)。連絡先は未確定 要確認(No.8)',
  't4_b2_r2_c2': '異常時のサーバー再起動(手順1〜14)を実施する(7-4)',
  't4_b2_r3_c2': '要確認(No.4) 判定基準(正常画面名)が未確定。再起動で扱う対応は候補(7-1)',
  't4_b2_r4_c2': '記録番号を付して申し送る(7-2)。復旧操作とサーバ構成の変更は本手順の範囲外 要確認(No.10)',
  't4_b2_r5_c2': '付録A-5のQ-1〜Q-6の手順で取得する',
  't4_b2_r6_c2': '要確認(No.36) 起動·停止·再起動の手順(7-5仮)の採否が未決',
 },
 'lnb': {
  't4_b2_r1_c2': '点検を中断して連絡する(8-2)。判定基準と連絡先は未確定 要確認(No.14·No.18)',
  't4_b2_r2_c2': '要確認(No.30·No.37) 「LNB再起動」「LNB-PC電源OFF」「LNB-PCリブート」の対応付けは推定',
  't4_b2_r3_c2': '最初の連絡先へ連絡する(8-2)。連絡先欄は未記入 要確認(No.18)',
  't4_b2_r4_c2': '8-3 ベンダーへの依頼。依頼方法·対応時間帯·自社とベンダーの境界は未記入 要確認(No.7·No.8)',
  't4_b2_r5_c2': '8-2の「点検中にサービスが停止した場合の応急処置」に従う。欄は未記入 要確認(No.18)',
  't4_b2_r6_c2': '画面に出ていた文言をそのまま記入する(10-2の記入方法)',
 },
}
# 既知視覚欠陥 (引き継ぎ資料照合 §5): (sheet, leaf名) -> P記号
KNOWN_DEFECT = {
 ('相関図③', 'g3_n11_txt'): 'P2', ('相関図②', 'g2_n10_txt'): 'P3',
 ('相関図③', 'g3_e_e07_l'): 'P4', ('相関図③', 'g3_e_e09_l'): 'P5',
 ('相関図②', 'g2_n03_txt'): 'P6', ('相関図③', 'g3_n08_txt'): 'P6',
}
KNOWN_P_NOTES = ['P1: ③g3_n11 タイトルとアイコンの重なり(適用前から·図形レベルのため本ハーネスでは再計測せず記録のみ)',
                 'P7: ②EE08線が n19 背後(R1·postAベースラインにも存在)', 'P8: PDFテキスト抽出の化け(検証手法の注意·CJK等値で回避)']

_dotmap = {0x00B7: '·', 0xFF65: '·', 0x30FB: '·'}
def norm(s):
    return re.sub(r'\s+', '', s.translate(_dotmap)) if s else ''

def cjk(s):
    return re.sub(r'[^\u4e00-\u9fff\u3040-\u30ff]', '', norm(s)) if s else ''

def char_w(ch, fsz):
    o = ord(ch)
    if ch == ' ':
        return 0.36 * fsz
    if 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFF9F \
       or 0x3000 <= o <= 0x303F or 0x2460 <= o <= 0x24FF or 0x2010 <= o <= 0x2027:
        return 1.0 * fsz
    if ch.isdigit() or ch.isupper():
        return 0.60 * fsz
    if ch.islower():
        return 0.52 * fsz
    return 0.55 * fsz

def est_line_w(text, fsz):
    return sum(char_w(c, fsz) for c in text)

def para_nvis(text, usable, fsz, wrap):
    if not wrap or usable <= 1:
        return 1
    return max(1, int(math.ceil(est_line_w(text, fsz) / (usable - NMARGIN))))

# ---------------------------------------------------------------- XML inventory
SNS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
XDR = '{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}'
ANS = '{http://schemas.openxmlformats.org/drawingml/2006/main}'

def norm_part(base, t):
    if t.startswith('/'):
        return t[1:]
    st = []
    for p in (base + '/' + t).split('/'):
        if p == '..':
            if st:
                st.pop()
        elif p not in ('', '.'):
            st.append(p)
    return '/'.join(st)

def resolve_drawings(z):
    wbx = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {e.get('Id'): e.get('Target') for e in rels}
    out = {}
    for sh in wbx.find(SNS + 'sheets'):
        nm, rid = sh.get('name'), sh.get(RNS + 'id')
        tgt = relmap[rid]
        part = tgt if tgt.startswith('xl/') else 'xl/' + tgt
        d = part.rsplit('/', 1)
        dr = None
        try:
            srels = ET.fromstring(z.read(d[0] + '/_rels/' + d[1] + '.rels'))
        except KeyError:
            srels = []
        for e in srels:
            if e.get('Type', '').endswith('/drawing'):
                dr = norm_part(d[0], e.get('Target'))
        out[nm] = dr
    return out

def parse_txbody(sp):
    tb = sp.find(XDR + 'txBody')
    if tb is None:
        return None
    bp = tb.find(ANS + 'bodyPr')
    info = {'wrap': 'square', 'anchor': 't', 'insets': [0.75, 0.375, 0.75, 0.375], 'autofit': 'none'}
    if bp is not None:
        info['wrap'] = bp.get('wrap', 'square')
        info['anchor'] = bp.get('anchor', 't')
        info['insets'] = [round(int(bp.get(k, d)) / EMU, 2) for k, d in
                          (('lIns', '91440'), ('tIns', '45720'), ('rIns', '91440'), ('bIns', '45720'))]
        for ch in bp:
            tag = ch.tag.split('}')[1]
            if tag in ('spAutoFit', 'normAutofit', 'noAutofit'):
                info['autofit'] = {'spAutoFit': 'resize', 'normAutofit': 'shrink', 'noAutofit': 'none'}[tag]
    paras = []
    for p in tb.findall(ANS + 'p'):
        runs, szs = [], []
        for r in p.iter():
            tag = r.tag.split('}')[1]
            if tag == 'rPr':
                szs.append(int(r.get('sz', '1800')) / 100.0)
            elif tag == 't' and r.text:
                runs.append(r.text)
        paras.append({'sz': max(szs) if szs else None, 'text': ''.join(runs)})
    info['paras'] = paras
    info['text'] = '\n'.join(p['text'] for p in paras)
    return info

def xfrm_of(obj):
    for pr in ('spPr', 'grpSpPr'):
        x = obj.find(XDR + pr + '/' + ANS + 'xfrm')
        if x is not None:
            return x
    return None

def parse_drawing(z, part):
    """戻り値: トップレベル図形リスト。ctx=(ox,oy,sx,sy,cox,coy): abs = o + (child_pt - c)*s"""
    root = ET.fromstring(z.read(part))
    out = []
    TOP = (0.0, 0.0, 1.0, 1.0, 0.0, 0.0)

    def walk(obj, ctx, pflip):
        x = xfrm_of(obj)
        fh = fv = False
        l = t = w = h = 0.0
        if x is not None:
            fh = x.get('flipH') in ('1', 'true')
            fv = x.get('flipV') in ('1', 'true')
            off = x.find(ANS + 'off'); ext = x.find(ANS + 'ext')
            if off is not None and ext is not None:
                cl, ct = int(off.get('x')) / EMU, int(off.get('y')) / EMU
                cw, chh = int(ext.get('cx')) / EMU, int(ext.get('cy')) / EMU
                l = ctx[0] + (cl - ctx[4]) * ctx[2]
                t = ctx[1] + (ct - ctx[5]) * ctx[3]
                w, h = cw * ctx[2], chh * ctx[3]
        ox, oy, _, _, _, _ = ctx
        tag = obj.tag.split('}')[1]
        nv = obj.find('.//' + XDR + 'cNvPr')
        name = nv.get('name') if nv is not None else '?'
        entry = {'name': name, 'kind': tag,
                 'box': [round(l, 2), round(t, 2), round(w, 2), round(h, 2)],
                 'flip': [fh != pflip[0], fv != pflip[1]]}
        if tag == 'grpSp' and x is not None:
            ext = x.find(ANS + 'ext'); choff = x.find(ANS + 'chOff'); chext = x.find(ANS + 'chExt')
            gsx = (int(ext.get('cx')) / int(chext.get('cx'))) if chext is not None and int(chext.get('cx')) else 1.0
            gsy = (int(ext.get('cy')) / int(chext.get('cy'))) if chext is not None and int(chext.get('cy')) else 1.0
            nctx = (l, t, ctx[2] * gsx, ctx[3] * gsy,
                    (int(choff.get('x')) / EMU) if choff is not None else 0.0,
                    (int(choff.get('y')) / EMU) if choff is not None else 0.0)
            kids = []
            for ch in obj:
                ctag = ch.tag.split('}')[1]
                if ctag in ('sp', 'cxnSp', 'grpSp', 'pic'):
                    kids.append(walk(ch, nctx, (fh, fv)))
            entry['children'] = kids
        else:
            tf = parse_txbody(obj)
            if tf:
                entry['tf'] = tf
        return entry

    for anchor in root:
        objs = [k for k in anchor if k.tag.split('}')[1] not in ('from', 'to', 'ext', 'clientData')]
        if not objs:
            continue
        e = walk(objs[0], TOP, (False, False))
        e['anchor'] = anchor.tag.split('}')[1]
        out.append(e)
    return out

def flatten(entries, out=None, parent=None):
    if out is None:
        out = {}
    for e in entries:
        d = {k: e[k] for k in e if k != 'children'}
        d['parent'] = parent
        out[d['name']] = d
        if 'children' in e:
            flatten(e['children'], out, e['name'])
    return out

# ---------------------------------------------------------------- COM collection
def read_tf(obj):
    try:
        tf2 = obj.TextFrame2
        if not tf2.HasText:
            return None
        tr = tf2.TextRange
        return {'text': tr.Text,
                'mL': float(tf2.MarginLeft), 'mR': float(tf2.MarginRight),
                'mT': float(tf2.MarginTop), 'mB': float(tf2.MarginBottom),
                'boundW': round(float(tr.BoundWidth), 2), 'boundH': round(float(tr.BoundHeight), 2),
                'fsz': round(float(tr.Font.Size), 2),
                'autosize': int(tf2.AutoSize), 'wrap': int(tf2.WordWrap)}
    except Exception:
        return None

def com_sheet_shapes(ws):
    tops = []
    for i in range(1, int(ws.Shapes.Count) + 1):
        sh = ws.Shapes.Item(i)
        e = {'name': sh.Name, 'type': int(sh.Type),
             'l': round(float(sh.Left), 2), 't': round(float(sh.Top), 2),
             'w': round(float(sh.Width), 2), 'h': round(float(sh.Height), 2)}
        if e['type'] == 6:
            kids = []
            gi = sh.GroupItems
            for k in range(1, int(gi.Count) + 1):
                m = gi.Item(k)
                c = {'name': m.Name, 'type': int(m.Type),
                     'l': round(float(m.Left), 2), 't': round(float(m.Top), 2),
                     'w': round(float(m.Width), 2), 'h': round(float(m.Height), 2)}
                tf = read_tf(m)
                if tf:
                    c['tf'] = tf
                kids.append(c)
            e['children'] = kids
        else:
            tf = read_tf(sh)
            if tf:
                e['tf'] = tf
        if e['type'] == 9:
            try:
                cf = sh.ConnectorFormat
                e['conn'] = [cf.BeginConnectedShape.Name if cf.BeginConnected else None,
                             cf.EndConnectedShape.Name if cf.EndConnected else None]
            except Exception:
                e['conn'] = [None, None]
        tops.append(e)
    return tops

# ---------------------------------------------------------------- PDF helpers
def pdf_rows(page):
    d = page.get_text('dict')
    raw = []
    for blk in d['blocks']:
        for ln in blk.get('lines', []):
            for sp in ln['spans']:
                raw.append(sp)
    rows = defaultdict(list)
    for sp in raw:
        rows.setdefault(round(sp['bbox'][1], 1), []).append(sp)
    merged = []
    for yk in sorted(rows):
        if merged and abs(yk - merged[-1][0]) <= 0.8:
            merged[-1][1].extend(rows[yk])
        else:
            merged.append((yk, list(rows[yk])))
    jrows = []
    for yk, sps in merged:
        sps.sort(key=lambda s: s['bbox'][0])
        cur = []
        for sp in sps:
            if cur and sp['bbox'][0] - cur[-1]['bbox'][2] > 5.5:
                jrows.append((yk, cur[0]['bbox'][0], cur[-1]['bbox'][2], ''.join(s['text'] for s in cur)))
                cur = []
            cur.append(sp)
        if cur:
            jrows.append((yk, cur[0]['bbox'][0], cur[-1]['bbox'][2], ''.join(s['text'] for s in cur)))
    return jrows

def find_anchor(jrows, frag, used_ys, exp_y=None):
    nf = cjk(frag)
    if len(nf) >= 5:
        nf = nf[:5]
    elif len(nf) < 3:
        nf = norm(frag)[:6]
    hits = [r for r in jrows if nf in cjk(r[3]) and all(abs(r[0] - u) > 2 for u in used_ys)]
    if not hits:
        return None
    if exp_y is not None:
        return min(hits, key=lambda r: abs(r[0] - exp_y))
    return hits[0] if len(hits) == 1 else None

# ---------------------------------------------------------------- shared state
DIGEST = {}
COMSTORE = {}

def main():
    results = {}
    def R(bk, cls):
        return results.setdefault((bk, cls), {'status': 'PASS', 'violations': [], 'warnings': [], 'info': {}, 'evidence': []})
    def fail(bk, cls, msg):
        r = R(bk, cls); r['status'] = 'FAIL'; r['violations'].append(msg)
    def warn(bk, cls, msg):
        R(bk, cls)['warnings'].append(msg)

    baselines = json.load(io.open(os.path.join(BASE, r'ab_work4_archive_b5\b5_current_state.json'), encoding='utf-8'))
    baseline_idx = {}
    for bk in baselines:
        for sn, entries in baselines[bk].items():
            for en in entries:
                baseline_idx[(bk, sn, en['path'].split('/')[-1])] = en

    excel = wc.DispatchEx('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        for bk, path in BK.items():
            print('==== STRICT VERIFY %s ====' % bk)
            z = zipfile.ZipFile(path)
            dmap = resolve_drawings(z)
            xml_inv = {}
            for sn in SHEETS:
                part = dmap.get(sn)
                xml_inv[sn] = parse_drawing(z, part) if part else []
                if not part:
                    print('  WARN: no drawing part for %s' % sn)
            inv_flat = {sn: flatten(xml_inv[sn]) for sn in SHEETS}
            with io.open(os.path.join(OUT, 'strict_inventory_%s.json' % bk), 'w', encoding='utf-8') as f:
                json.dump({'drawings': dmap, 'sheets': xml_inv}, f, ensure_ascii=False, indent=1)
            z.close()
            R(bk, 'C2_inventory')['evidence'].append('strict_inventory_%s.json' % bk)

            wb = excel.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            try:
                try:
                    wb.AutoSaveOn = False
                except Exception:
                    pass
                sheets = {sn: wb.Worksheets(sn) for sn in SHEETS}

                # ---------------- C1 page setup ----------------
                ev1 = {'footer': {}, 'print_title_rows': {}}
                for sn in SHEETS:
                    ps = sheets[sn].PageSetup
                    pa_want = PA4 if sn == '相関図④' else PA23[bk][0 if sn == '相関図②' else 1]
                    pa_act = ps.PrintArea or ''
                    if norm(pa_act) != norm(pa_want):
                        fail(bk, 'C1_page_setup', '%s: PrintArea %r != %r' % (sn, pa_act, pa_want))
                    if int(ps.Orientation) != 2:
                        fail(bk, 'C1_page_setup', '%s: orientation=%s' % (sn, ps.Orientation))
                    if int(ps.PaperSize) != 9:
                        fail(bk, 'C1_page_setup', '%s: paper=%s' % (sn, ps.PaperSize))
                    if not (int(ps.FitToPagesWide) == 1 and int(ps.FitToPagesTall) == 1 and not ps.Zoom):
                        fail(bk, 'C1_page_setup', '%s: fit/zoom=%s/%s/%s' % (sn, ps.Zoom, ps.FitToPagesWide, ps.FitToPagesTall))
                    try:
                        ptr = ps.PrintTitleRows or ''
                    except Exception:
                        ptr = '<unreadable>'
                    ev1['print_title_rows'][sn] = ptr
                    if ptr not in ('', None):
                        fail(bk, 'C1_page_setup', '%s: PrintTitleRows set: %r' % (sn, ptr))
                    ftr = {'C': ps.CenterFooter or '', 'L': ps.LeftFooter or '', 'R': ps.RightFooter or ''}
                    ev1['footer'][sn] = ftr
                    if FOOTER_KEY not in (ftr['C'] + ftr['L'] + ftr['R']):
                        fail(bk, 'C1_page_setup', '%s: footer lacks %s' % (sn, FOOTER_KEY))
                with io.open(os.path.join(OUT, 'strict_page_setup_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(ev1, f, ensure_ascii=False, indent=1)
                R(bk, 'C1_page_setup')['evidence'].append('strict_page_setup_%s.json' % bk)

                # ---------------- COM shapes ----------------
                com = {sn: com_sheet_shapes(sheets[sn]) for sn in SHEETS}
                COMSTORE[bk] = com
                for sn in SHEETS:
                    com_names = {e['name'] for e in com[sn]}
                    com_names |= {c['name'] for e in com[sn] for c in e.get('children', [])}
                    xml_names = set(inv_flat[sn])
                    miss_xml = sorted(com_names - xml_names)
                    miss_com = sorted(xml_names - com_names)
                    # COMは入れ子グループの中間コンテナ名を返さない(子は返す)。
                    # XML側のみの名前でも「子孫がすべてCOM側に存在」ならコンテナ名の差異として許容する
                    real_miss_com = []
                    for nm in miss_com:
                        desc = set()
                        frontier = [nm]
                        while frontier:
                            cur = frontier.pop()
                            for n2, d2 in inv_flat[sn].items():
                                if d2.get('parent') == cur and n2 not in desc:
                                    desc.add(n2)
                                    frontier.append(n2)
                        if desc and desc <= com_names:
                            warn(bk, 'C2_inventory', '%s: XML container name %s absent in COM (children present)'
                                 % (sn, nm))
                        else:
                            real_miss_com.append(nm)
                    if miss_xml:
                        warn(bk, 'C2_inventory', '%s: COM-only shapes: %s' % (sn, ','.join(miss_xml[:8])))
                    if real_miss_com:
                        fail(bk, 'C2_inventory', '%s: XML-only shapes: %s' % (sn, ','.join(real_miss_com[:8])))
                    drift = 0
                    for e in com[sn]:
                        xe = inv_flat[sn].get(e['name'])
                        if not xe:
                            continue
                        d = max(abs(e['l'] - xe['box'][0]), abs(e['t'] - xe['box'][1]),
                                abs(e['w'] - xe['box'][2]), abs(e['h'] - xe['box'][3]))
                        if d > 0.5:
                            drift += 1
                    if drift:
                        warn(bk, 'C2_inventory', '%s: XML/COM box drift on %d shapes (COM used for checks)' % (sn, drift))
                    R(bk, 'C2_inventory')['info'].setdefault(sn, {})['counts'] = {
                        'com': len(com[sn]), 'xml': len(inv_flat[sn]), 'drift': drift}

                # ---------------- unit shapes for ②③ ----------------
                def unit_shapes(sn):
                    tops = []
                    for e in com[sn]:
                        d = {'name': e['name'], 'type': e['type'], 'l': e['l'], 't': e['t'],
                             'w': e['w'], 'h': e['h'], 'children': [], 'conn': e.get('conn')}
                        xe = inv_flat[sn].get(e['name'])
                        d['flipH'], d['flipV'] = xe['flip'] if xe else (False, False)
                        if e.get('tf'):
                            tf = e['tf']
                            d['tf'] = {'mL': tf['mL'], 'mR': tf['mR'], 'mT': tf['mT'], 'mB': tf['mB'],
                                       'boundW': tf['boundW'], 'boundH': tf['boundH']}
                        elif e['type'] == 6:
                            # グループの空フレームquirk (geom_stage.json と同一の形):
                            # check_a の「テキスト同士は分類c」判定をベースラインと揃える
                            d['tf'] = {'mL': 0.0, 'mR': 0.0, 'mT': 0.0, 'mB': 0.0,
                                       'boundW': 2.49, 'boundH': 13.43}
                        for c in e.get('children', []):
                            cd = {'name': c['name'], 'l': c['l'], 't': c['t'], 'w': c['w'], 'h': c['h']}
                            if c.get('tf'):
                                tf = c['tf']
                                cd['tf'] = {'mL': tf['mL'], 'mR': tf['mR'], 'mT': tf['mT'], 'mB': tf['mB'],
                                            'boundW': tf['boundW'], 'boundH': tf['boundH']}
                            d['children'].append(cd)
                        tops.append(d)
                    return tops

                tops23 = {sn: unit_shapes(sn) for sn in ('相関図②', '相関図③')}

                # ---------------- C4 clearance (テキストボックス間 3.75pt) ----------------
                base_clear = json.load(io.open(os.path.join(BASE, 'clearance_report.json'), encoding='utf-8'))
                postA_file = json.load(io.open(os.path.join(BASE, 'collision_report_postA3.json'), encoding='utf-8'))
                # 設計上の豁免: (1) 同一ノード内 (2) 帯ヘッダーx帯注記 (3) 所属ノード同士が
                # 重なり設計(例: n17がn10の下に潜る) (4) 接続エッジのラベルと接続先ノード部品
                def owner_of(nm):
                    for sh in tops23[sn]:
                        if int(sh['type']) == 6:
                            if sh['name'] == nm or any(c['name'] == nm for c in sh.get('children', [])):
                                return sh['name'], sh
                        elif sh['name'] == nm:
                            return nm, sh
                    return nm, None
                lbl_edge = re.compile(r'^(g\d_e_e\d+)_l$')
                clr_out = {}
                for sn in ('相関図②', '相関図③'):
                    conn_by_edge = {sh['name']: [c for c in (sh.get('conn') or []) if c] for sh in tops23[sn]}
                    # リーフテキスト矩形 (グループ子 + 非グループtop)
                    ltexts = []
                    for sh in tops23[sn]:
                        if int(sh['type']) == 6:
                            for c in sh.get('children', []):
                                if c.get('tf'):
                                    ltexts.append((c['name'], (c['l'], c['t'], c['w'], c['h'])))
                        elif sh.get('tf'):
                            ltexts.append((sh['name'], (sh['l'], sh['t'], sh['w'], sh['h'])))
                    rect_by_name = dict(ltexts)
                    top_rect = {sh['name']: (sh['l'], sh['t'], sh['w'], sh['h']) for sh in tops23[sn]}
                    base_c_pairs = {(min(v['a'], v['b']), max(v['a'], v['b']))
                                    for v in postA_file['books'][bk][sn]['violations']['c']}

                    def design_exempt(na, nb):
                        own_a = owner_of(na)
                        own_b = owner_of(nb)
                        # (1) 同一ノード内の部品 (txt x tag など)
                        if own_a[0] == own_b[0]:
                            return True
                        # (2) 帯ヘッダー x 帯注記 (積層設計 3.0pt)
                        if {na, nb} in ({'g2_bandhead', 'g2_bandnote'}, {'g3_bandhead', 'g3_bandnote'}):
                            return True
                        # (3) 所属ノード同士が重なり設計ならその部品ペアは豁免
                        ta, tb = top_rect.get(own_a[0]), top_rect.get(own_b[0])
                        if ta and tb:
                            ox = min(ta[0] + ta[2], tb[0] + tb[2]) - max(ta[0], tb[0])
                            oy = min(ta[1] + ta[3], tb[1] + tb[3]) - max(ta[1], tb[1])
                            if ox > 1 and oy > 1:
                                return True
                        # (4) エッジラベル x 接続先ノードの部品
                        for lbl, other in ((na, nb), (nb, na)):
                            m = lbl_edge.match(lbl)
                            if not m:
                                continue
                            conns = conn_by_edge.get(m.group(1)) or []
                            other_owner, other_sh = owner_of(other)
                            hit = any(c and (c == other_owner or other_owner.startswith(c)
                                             or c.startswith(other_owner)) for c in conns)
                            if not hit:
                                # 座標指定線: 端点が相手ノードの可視部に埋め込まれていれば接続設計
                                edge_top = next((x for x in tops23[sn] if x['name'] == m.group(1)), None)
                                if edge_top is not None:
                                    pts = []
                                    if int(edge_top['type']) == 9:
                                        seg = cc.line_seg(edge_top, (bool(edge_top.get('flipH')), bool(edge_top.get('flipV'))))
                                        pts = list(seg)
                                    else:
                                        for c3 in edge_top.get('children', []):
                                            l3, t3, w3, h3 = c3['l'], c3['t'], c3['w'], c3['h']
                                            pts += [(l3, t3), (l3 + w3, t3 + h3), (l3 + w3, t3), (l3, t3 + h3)]
                                    if int((other_sh or {}).get('type') or 0) == 6:
                                        parts = [(c3['l'], c3['t'], c3['w'], c3['h'])
                                                 for c3 in other_sh.get('children', [])] or \
                                                [(other_sh['l'], other_sh['t'], other_sh['w'], other_sh['h'])]
                                    elif other_sh is not None:
                                        parts = [(other_sh['l'], other_sh['t'], other_sh['w'], other_sh['h'])]
                                    else:
                                        parts = []
                                    hit = any(clc.pt_rect_dist(p, pr) <= 2.0 for p in pts for pr in parts)
                            if hit:
                                return True
                        return False

                    viols, known = [], []
                    for i in range(len(ltexts)):
                        for j in range(i + 1, len(ltexts)):
                            (na, ra), (nb, rb) = ltexts[i], ltexts[j]
                            g = clc.rect_rect_dist(ra, rb)
                            if g >= CLEAR_PT:
                                continue
                            ent = {'a': na, 'b': nb, 'gap_pt': round(g, 2)}
                            if (min(na, nb), max(na, nb)) in base_c_pairs or design_exempt(na, nb):
                                known.append(ent)
                            else:
                                viols.append(ent)
                    base_cnt = base_clear['books'][bk]['sheets'][sn]['count']
                    clr_out[sn] = {'leaf_texts': len(ltexts), 'violations_new': viols,
                                   'baseline_known_overlaps': known, 'clearance_report_baseline_count': base_cnt}
                    for v in viols:
                        fail(bk, 'C4_clearance', '%s: text-text clearance %.2fpt < 3.75pt (new): %s x %s'
                             % (sn, v['gap_pt'], v['a'], v['b']))
                with io.open(os.path.join(OUT, 'strict_clearance_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(clr_out, f, ensure_ascii=False, indent=1)
                R(bk, 'C4_clearance')['evidence'].append('strict_clearance_%s.json' % bk)

                # ---------------- C5 collision ----------------
                postA = json.load(io.open(os.path.join(BASE, 'collision_report_postA3.json'), encoding='utf-8'))
                coll_out = {}
                for sn in ('相関図②', '相関図③'):
                    tops = tops23[sn]
                    flips = {sh['name']: (bool(sh.get('flipH')), bool(sh.get('flipV'))) for sh in tops}
                    edges = cc.build_edges(tops, flips, {'assumed_diag': 0})
                    containers = cc.container_nodes(tops)
                    targets = []
                    for sh in tops:
                        cls = cc.cls_of(sh['name'], sh['type'])
                        if cls == 'bandhead':
                            targets.append((sh['name'], cc.R(sh)))
                        elif cls == 'node' and sh['name'] not in containers:
                            for c in sh.get('children', []):
                                if c['name'].endswith('_box'):
                                    targets.append((c['name'], cc.R(c)))
                    texts = []
                    for sh in tops:
                        cls = cc.cls_of(sh['name'], sh['type'])
                        if int(sh['type']) == 6:
                            for c in sh.get('children', []):
                                if c.get('tf'):
                                    k = 'txt' if c['name'].endswith('_txt') else ('tag' if c['name'].endswith('_tag') else 'membertext')
                                    texts.append((c['name'], cc.R(c), sh['name'], k, c['tf']))
                        elif sh.get('tf'):
                            texts.append((sh['name'], cc.R(sh), sh['name'], cls, sh['tf']))
                    items = [(eid, sid, seg) for eid, segs in edges.items() for sid, seg in segs]
                    e_out, e_wl = [], []
                    for i in range(len(items)):
                        for j in range(i + 1, len(items)):
                            if items[i][0] == items[j][0]:
                                continue
                            v = cc.seg_pair_violation(items[i][2], items[j][2])
                            if v:
                                rec = {'kind': v[0], 'a': items[i][1], 'b': items[j][1],
                                       'd': [v[1], v[2]] if v[0] == 'cross' else [v[1]]}
                                pair = tuple(sorted((rec['a'].split('.')[0], rec['b'].split('.')[0])))
                                (e_wl if pair == ('g3_e_e03', 'g3_e_e10') else e_out).append(rec)
                    cats = {
                        'a': sorted(cc.check_a(tops), key=cc.sortkey),
                        'b': sorted(cc.check_b(edges, targets), key=cc.sortkey),
                        'c': sorted(cc.check_c(texts), key=cc.sortkey),
                        'd': sorted(cc.check_d(tops, texts), key=cc.sortkey),
                        'e': sorted(e_out, key=cc.sortkey),
                    }
                    base_cats = postA['books'][bk][sn]['violations']
                    base_keys = {(v['kind'], v.get('a', ''), v.get('b', '')) for cat in 'abcde' for v in base_cats[cat]}
                    now_keys = {(v['kind'], v.get('a', ''), v.get('b', '')) for cat in 'abcde' for v in cats[cat]}
                    new = sorted(now_keys - base_keys)
                    gone = sorted(base_keys - now_keys)
                    coll_out[sn] = {'by_category': {k: len(v) for k, v in cats.items()},
                                    'total': sum(len(v) for v in cats.values()),
                                    'baseline_total': postA['books'][bk][sn]['total'],
                                    'new': [list(x) for x in new], 'resolved': [list(x) for x in gone],
                                    'violations': cats, 'e_whitelist_exempt': e_wl}
                    for x in new:
                        fail(bk, 'C5_collision', '%s: NEW collision %s' % (sn, ' x '.join(x)))
                    for x in gone:
                        warn(bk, 'C5_collision', '%s: baseline pair resolved (unexpected): %s' % (sn, ' x '.join(x)))
                # ④: phaseB 豁免スキャン (期待 0)
                sn = '相関図④'
                geo4 = {e['name']: (e['l'], e['t'], e['w'], e['h']) for e in com[sn]}
                def exempt4(a, b):
                    SUB4 = re.compile(r'(_ic|_bd\d+)(_[abc])?$')
                    if b.startswith(a + '_') or a.startswith(b + '_'):
                        return True
                    if SUB4.search(a) or SUB4.search(b):
                        return True
                    if a.startswith('t4_b3_ln') or b.startswith('t4_b3_ln'):
                        return True
                    if 't4_b1_c4' in (a, b) and {a, b} & {'t4_b1_c40', 't4_b1_c41', 't4_b1_c42', 't4_b1_c43'}:
                        return True
                    pa, pb = a.rsplit('_', 1), b.rsplit('_', 1)
                    if len(pa) == 2 and len(pb) == 2 and pa[0] == pb[0] and pa[1] in ('a', 'b', 'c') and pb[1] in ('a', 'b', 'c'):
                        return True
                    return False
                names4 = sorted(geo4)
                bad4 = []
                for i in range(len(names4)):
                    for j in range(i + 1, len(names4)):
                        a, b = names4[i], names4[j]
                        if exempt4(a, b):
                            continue
                        aL, aT, aW, aH = geo4[a]; bL, bT, bW, bH = geo4[b]
                        ox = min(aL + aW, bL + bW) - max(aL, bL)
                        oy = min(aT + aH, bT + bH) - max(aT, bT)
                        if ox > 0.25 and oy > 0.25:
                            bad4.append('%s x %s (%.1fx%.1f)' % (a, b, ox, oy))
                coll_out[sn] = {'violations_flat': bad4, 'baseline': 'phaseB ALL PASS (0)'}
                for bd in bad4:
                    fail(bk, 'C5_collision', '%s: collision %s' % (sn, bd))
                with io.open(os.path.join(OUT, 'strict_collision_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(coll_out, f, ensure_ascii=False, indent=1)
                R(bk, 'C5_collision')['evidence'].append('strict_collision_%s.json' % bk)

                # ---------------- C6 connectors ----------------
                conn_out = {}
                for sn in SHEETS:
                    rec = []
                    for e in com[sn]:
                        if cc.cls_of(e['name'], e['type']) == 'edge' or re.match(r'^t4_b3_ln\d+$', e['name']):
                            xe = inv_flat[sn].get(e['name']) or {}
                            rec.append({'name': e['name'], 'box': [e['l'], e['t'], e['w'], e['h']],
                                        'flip': xe.get('flip'), 'conn': e.get('conn'),
                                        'orient': 'h' if e['h'] <= 0.5 else ('v' if e['w'] <= 0.5 else 'multi')})
                    conn_out[sn] = rec
                for v in coll_out['相関図②']['violations']['b']:
                    ids = v.get('a', '') + ' ' + v.get('b', '')
                    if 'g2_e_e08' in ids and 'n19' in ids:
                        conn_out.setdefault('known_R1_EE08', []).append(v)
                with io.open(os.path.join(OUT, 'strict_connectors_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(conn_out, f, ensure_ascii=False, indent=1)
                R(bk, 'C6_connectors')['evidence'].append('strict_connectors_%s.json' % bk)
                R(bk, 'C6_connectors')['info']['R1_EE08'] = 'known exception (recorded only, P7)'

                # ---------------- C8 PDF export ----------------
                pdf_map = {}
                for sn in SHEETS:
                    pdf = os.path.join(OUT, 'strict_%s_%s.pdf' % (bk, SN_TAG[sn]))
                    sheets[sn].ExportAsFixedFormat(0, pdf)
                    pdf_map[sn] = pdf
                R(bk, 'C8_pdf_roundtrip')['evidence'].append('strict_%s_s2/s3/s4.pdf' % bk)

                # ---------------- C9 COM-side data accuracy ----------------
                all_text = {}
                for sn in SHEETS:
                    tx = {}
                    for e in com[sn]:
                        if e.get('tf'):
                            tx[e['name']] = e['tf']['text']
                        for c in e.get('children', []):
                            if c.get('tf'):
                                tx[c['name']] = c['tf']['text']
                    all_text[sn] = tx
                acc = {'changed': {}, 'unchanged_diff': [], 'unchanged_missing_baseline': [], 't4_table': {}}
                for nm, exp_t in EXP.items():
                    act = None
                    for sn in SHEETS:
                        if nm in all_text[sn]:
                            act = all_text[sn][nm]; break
                    okv = act is not None and norm(act) == norm(exp_t)
                    acc['changed'][nm] = {'ok': bool(okv), 'n_paras': (len(act.split('\n')) if act else 0)}
                    if not okv:
                        fail(bk, 'C9_data_accuracy', 'changed text mismatch: %s' % nm)
                for nm, line2 in EXP_LINE2.items():
                    act = all_text['相関図③'].get(nm)
                    if act is None:
                        fail(bk, 'C9_data_accuracy', '相関図③: %s missing' % nm); continue
                    base = baseline_idx.get((bk, '相関図③', nm))
                    if not base:
                        warn(bk, 'C9_data_accuracy', '相関図③: %s not in baseline' % nm); continue
                    bp = base['text'].split('\n')
                    expect = [bp[0], line2] + bp[2:]
                    if norm(act) != norm('\n'.join(expect)) or len(act.split('\n')) != len(expect):
                        fail(bk, 'C9_data_accuracy', '相関図③: %s line-2 replacement mismatch' % nm)
                    else:
                        acc['changed'][nm + '@相関図③'] = {'ok': True}
                for cnm, exp_t in EXPECTED_ACT[bk].items():
                    act_t = all_text['相関図④'].get(cnm)
                    okv = act_t is not None and norm(act_t) == norm(exp_t)
                    acc['t4_table'][cnm] = okv
                    if not okv:
                        fail(bk, 'C9_data_accuracy', '相関図④: %s text mismatch' % cnm)
                for sn in SHEETS:
                    for nm, txt in sorted(all_text[sn].items()):
                        if nm in CHANGED_TEXT:
                            continue
                        base = baseline_idx.get((bk, sn, nm))
                        if not base:
                            acc['unchanged_missing_baseline'].append({'sheet': sn, 'name': nm})
                            continue
                        if norm(base['text']) != norm(txt):
                            acc['unchanged_diff'].append({'sheet': sn, 'name': nm})
                            fail(bk, 'C9_data_accuracy', '%s: unchanged-shape text drift: %s' % (sn, nm))
                with io.open(os.path.join(OUT, 'strict_data_accuracy_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(acc, f, ensure_ascii=False, indent=1)
                R(bk, 'C9_data_accuracy')['evidence'].append('strict_data_accuracy_%s.json' % bk)
                R(bk, 'C9_data_accuracy')['info']['unchanged_missing_baseline'] = len(acc['unchanged_missing_baseline'])

                # ---------------- hyperlinks (④) ----------------
                ws4 = sheets['相関図④']
                nhl = len(ws4.Hyperlinks)
                if nhl != WANT_LINKS[bk]:
                    fail(bk, 'C10_err_regression', '④ hyperlinks %d != %d' % (nhl, WANT_LINKS[bk]))
                exp_links = None
                try:
                    with io.open(os.path.join(BASE, 'phaseB_report_%s.json' % bk), encoding='utf-8') as f:
                        exp_links = {}
                        for e in json.load(f).get('links', []):
                            nm, tgt = e.split(' -> ')
                            exp_links[nm] = tgt.replace("'", '')
                except Exception:
                    exp_links = None
                act_links = {}
                for hl in ws4.Hyperlinks:
                    try:
                        act_links[hl.Shape.Name] = (hl.SubAddress or '').replace("'", '')
                    except Exception:
                        pass
                map_ok = None
                if exp_links is not None:
                    map_ok = (act_links == exp_links)
                    if not map_ok:
                        fail(bk, 'C10_err_regression', '④ link map mismatch (%d act vs %d exp)' % (len(act_links), len(exp_links)))
                    for nm, tgt in exp_links.items():
                        sheet, cell = tgt.rsplit('!', 1)
                        if sheet in CRED_SHEETS:
                            continue
                        try:
                            v = wb.Worksheets(sheet).Range(cell).Value
                        except Exception:
                            fail(bk, 'C10_err_regression', '%s target %s!%s unreadable' % (nm, sheet, cell))
                            continue
                        if v is None or norm(str(v)) == '':
                            fail(bk, 'C10_err_regression', '%s target %s!%s empty' % (nm, sheet, cell))
                with io.open(os.path.join(OUT, 'strict_links_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump({'count': nhl, 'want': WANT_LINKS[bk], 'map_ok': map_ok,
                               'n_measured': len(act_links)}, f, ensure_ascii=False, indent=1)
                R(bk, 'C10_err_regression')['evidence'].append('strict_links_%s.json' % bk)

                # ---------------- novalue digest (names + printarea + links, no values/text) ----------------
                DIGEST[bk] = {}
                for sn in SHEETS:
                    DIGEST[bk][sn] = {
                        'names': sorted([e['name'] for e in com[sn]] +
                                        [c['name'] for e in com[sn] for c in e.get('children', [])]),
                        'printarea': sheets[sn].PageSetup.PrintArea or '',
                        'links': sorted(act_links.items()) if sn == '相関図④' else [],
                        'nshapes': len(com[sn])}
                with io.open(os.path.join(OUT, 'strict_digest_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(DIGEST[bk], f, ensure_ascii=False, indent=1)

                # ---------------- C3/C7: PDF analysis ----------------
                fit_all = []
                orphans = []
                for sn in SHEETS:
                    doc = fitz.open(pdf_map[sn])
                    if doc.page_count != 1:
                        fail(bk, 'C8_pdf_roundtrip', '%s: pdf pages %d != 1' % (sn, doc.page_count))
                    page = doc[0]
                    if page.rect.width <= page.rect.height:
                        fail(bk, 'C8_pdf_roundtrip', '%s: pdf not landscape (%.0fx%.0f)' % (sn, page.rect.width, page.rect.height))
                    jrows = pdf_rows(page)
                    cands = {'相関図②': ['g2_expl', 'g2_bandhead', 'g2_leg0', 'g2_e_e01_l'],
                             '相関図③': ['g3_expl', 'g3_leg0', 'g3_e_e03_l'],
                             '相関図④': ['t4_head', 't4_b1_src', 't4_b2_src', 't4_upd', 't4_b3_src']}[sn]
                    txmap = {}
                    for e in com[sn]:
                        if e.get('tf'):
                            txmap[e['name']] = e
                        for c in e.get('children', []):
                            if c.get('tf'):
                                txmap[c['name']] = c
                    ps = sheets[sn].PageSetup
                    pa = ps.PrintArea or ''
                    m0 = re.match(r'\$?[A-Z]+\$?(\d+)', pa.split(':')[0])
                    start_row = int(m0.group(1)) if m0 else 1
                    above_h = 0.0
                    if start_row > 1:
                        above_h = float(sheets[sn].Range('1:%d' % (start_row - 1)).Height)
                    try:
                        rng = sheets[sn].Range(pa.split(':')[0], pa.split(':')[1])
                        rw, rh = float(rng.Width), float(rng.Height)
                    except Exception:
                        rw = rh = 0.0
                    avail_w = page.rect.width - float(ps.LeftMargin) - float(ps.RightMargin)
                    avail_h = page.rect.height - float(ps.TopMargin) - float(ps.BottomMargin)
                    s_est = min(avail_w / rw, avail_h / rh, 1.0) if rw and rh else 1.0
                    centerH = bool(ps.CenterHorizontally)
                    centerV = bool(ps.CenterVertically)
                    # 印刷原点は左上余白(実測較正済み)。シート座標は PrintArea 先頭行より
                    # 上の行高(above_h)を差し引く。スケールは Excel の fit 計算と
                    # Range 寸法の誤差があるため、PDF 自身の CJK 文字収蔵率で較正する。
                    offx0 = float(ps.LeftMargin) + ((avail_w - rw * s_est) / 2.0 if centerH and rw else 0.0)
                    offy0 = float(ps.TopMargin) + ((avail_h - rh * s_est) / 2.0 if centerV and rh else 0.0)
                    # 較正対象: タグ(縦書き)以外の tf 図形
                    cal_items = []
                    for e2 in com[sn]:
                        if e2.get('tf') and not e2['name'].endswith('_tag'):
                            cal_items.append((e2['name'], e2['tf'], (e2['l'], e2['t'], e2['w'], e2['h'])))
                        for c2 in e2.get('children', []):
                            if c2.get('tf') and not c2['name'].endswith('_tag'):
                                cal_items.append((c2['name'], c2['tf'], (c2['l'], c2['t'], c2['w'], c2['h'])))

                    def coverage_at(s, offx, offy, need_list=None):
                        tot = 0.0
                        for nm2, tf2, (L2, T2, W2, H2) in cal_items:
                            x0 = (L2 + tf2['mL']) * s + offx - 2.0
                            y0 = (T2 + tf2['mT'] - above_h) * s + offy - 3.0
                            x1 = (L2 + W2 - tf2['mR']) * s + offx + 2.0
                            y1 = (T2 + H2 - tf2['mB'] - above_h) * s + offy + 3.0
                            got = ''.join(t for (yy, rx0, rx1, t) in jrows
                                          if y0 <= yy <= y1 and rx0 < x1 and rx1 > x0)
                            ce, cg = Counter(cjk(tf2['text'])), Counter(cjk(got))
                            cov = sum(min(n2, cg[ch]) for ch, n2 in ce.items()) / max(1, sum(ce.values()))
                            tot += cov
                            if need_list is not None:
                                need_list.append((nm2, round(cov, 3)))
                        return tot / max(1, len(cal_items))

                    best_s, best_cov = s_est, coverage_at(s_est, offx0, offy0)
                    s_try = 0.80
                    while s_try <= 1.0001:
                        cov = coverage_at(s_try, float(ps.LeftMargin), float(ps.TopMargin))
                        if cov > best_cov + 1e-9:
                            best_s, best_cov = s_try, cov
                        s_try = round(s_try + 0.001, 4)
                    sx = sy = best_s
                    offx, offy = offx0, offy0
                    mapping = {'sx': round(sx, 4), 'sy': round(sy, 4), 'offx': round(offx, 1),
                               'offy': round(offy, 1), 'scale_est_print': round(s_est, 4),
                               'coverage': round(best_cov, 4),
                               'print_area_start_row': start_row, 'above_h': round(above_h, 1),
                               'centerH': centerH, 'centerV': centerV}
                    if best_cov < 0.90:
                        warn(bk, 'C8_pdf_roundtrip', '%s: PDF mapping coverage low (%.2f at s=%.4f)' % (sn, best_cov, best_s))

                    pix = page.get_pixmap(matrix=fitz.Matrix(2.4, 2.4))
                    png_full = 'strict_%s_%s_full.png' % (bk, SN_TAG[sn])
                    pix.save(os.path.join(OUT, png_full))
                    fit_info = {'pages': doc.page_count, 'mapping': mapping, 'png_full': png_full}

                    fit3 = []
                    crops = []
                    for e in com[sn]:
                        tfitems = []
                        if e.get('tf'):
                            tfitems.append((e['name'], e['tf'], (e['l'], e['t'], e['w'], e['h'])))
                        for c in e.get('children', []):
                            if c.get('tf'):
                                tfitems.append((c['name'], c['tf'], (c['l'], c['t'], c['w'], c['h'])))
                        for nm, tf, (L, T, W, H) in tfitems:
                            xe = inv_flat[sn].get(nm) or {}
                            xml_tf = xe.get('tf') or {}
                            paras_xml = xml_tf.get('paras') or []
                            szs = [p['sz'] for p in paras_xml if p.get('sz')]
                            fsz = max(szs) if szs else tf['fsz']
                            wrap = xml_tf.get('wrap', 'square') != 'none' and tf['wrap'] != 0
                            mL, mR, mT, mB = tf['mL'], tf['mR'], tf['mT'], tf['mB']
                            usable = W - mL - mR
                            paras = tf['text'].split('\n')
                            nvis_est = sum(para_nvis(p, usable, fsz, wrap) for p in paras)
                            x0 = (L + mL) * sx + offx - 2.0
                            y0 = (T + mT - above_h) * sy + offy - 3.0
                            x1 = (L + W - mR) * sx + offx + 2.0
                            y1 = (T + H - mB - above_h) * sy + offy + 3.0
                            sel = [r for r in jrows if y0 <= r[0] <= y1 and r[1] < x1 and r[2] > x0]
                            # PDF行はx-gapで断片化するため、y近接(<=2pt)の断片を視覚行に統合する
                            clusters = []
                            for (yy, xx0, xx1, tt) in sorted(sel):
                                if clusters and yy - clusters[-1]['y'] <= 2.0:
                                    c = clusters[-1]
                                    c['x0'] = min(c['x0'], xx0)
                                    c['x1'] = max(c['x1'], xx1)
                                    c['t'] += tt
                                else:
                                    clusters.append({'y': yy, 'x0': xx0, 'x1': xx1, 't': tt})
                            nvis_act = len(clusters)
                            got_cjk = cjk(''.join(c['t'] for c in clusters))
                            exp_cjk = cjk(tf['text'])
                            tail_ok = True
                            if exp_cjk:
                                ce, cg = Counter(exp_cjk), Counter(got_cjk)
                                tail_ok = all(cg[ch] >= n for ch, n in ce.items())
                                last4 = exp_cjk[-4:]
                                if tail_ok and last4 and last4 not in got_cjk:
                                    tail_ok = False
                            rec = {'sheet': sn, 'name': nm, 'fsz': fsz, 'nvis_est': nvis_est,
                                   'nvis_pdf': nvis_act, 'tail_ok': tail_ok, 'rows_short': [],
                                   'rows_short_ascii': []}
                            for c in clusters:
                                vis = len(re.sub(r'\s+', '', c['t']))
                                if vis <= 2:
                                    rec['rows_short'].append(c['t'])
                                elif vis <= 5 and not cjk(c['t']):
                                    rec['rows_short_ascii'].append(c['t'])
                            fit3.append(rec)
                            # C7 orphans: 分類 = 既知P* / 既存同型(ベースラインと同テキスト) / 本ラウンド退行
                            base0 = baseline_idx.get((bk, sn, nm))
                            unchanged = base0 is not None and norm(base0['text']) == norm(tf['text'])
                            if nvis_act >= 2:
                                for tt in rec['rows_short']:
                                    kd = KNOWN_DEFECT.get((sn, nm))
                                    if kd:
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'known-' + kd})
                                    elif unchanged:
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'preexisting-baseline-isomorphic'})
                                        warn(bk, 'C7_orphans_wrap', '%s %s: short row (baseline-isomorphic, pre-existing)' % (sn, nm))
                                    elif sn == '相関図④':
                                        # ④は変更前の基準が無い: 末尾が保たれていれば視覚確認候補(警告)にとどめる
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt,
                                                        'class': 'new-candidate-visual(warn)'})
                                        warn(bk, 'C7_orphans_wrap', '%s %s: short row (no baseline; visual candidate)' % (sn, nm))
                                    else:
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'new-regression-candidate'})
                                        fail(bk, 'C7_orphans_wrap', '%s %s: orphan/short row (new candidate)' % (sn, nm))
                                for tt in rec['rows_short_ascii']:
                                    orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'short-ascii-row(info)'})
                            # C3 checks
                            if not tail_ok:
                                if nm in FIXED_LEAVES or nm in CHANGED_TEXT:
                                    fail(bk, 'C3_text_fit', '%s %s: last-line loss (CJK tail mismatch)' % (sn, nm))
                                elif base0 is not None and norm(base0['text']) == norm(tf['text']):
                                    warn(bk, 'C3_text_fit', '%s %s: last-line loss (pre-existing, unchanged text; ERR-004 family)' % (sn, nm))
                                else:
                                    fail(bk, 'C3_text_fit', '%s %s: last-line loss (CJK tail mismatch)' % (sn, nm))
                            if wrap and nvis_act > nvis_est:
                                kd = KNOWN_DEFECT.get((sn, nm))
                                base = baseline_idx.get((bk, sn, nm))
                                preexisting = base is not None and norm(base['text']) == norm(tf['text'])
                                if kd:
                                    orphans.append({'sheet': sn, 'name': nm, 'class': 'known-%s(extra wrap)' % kd,
                                                    'nvis_est': nvis_est, 'nvis_pdf': nvis_act})
                                elif nm in FIXED_LEAVES or nm in CHANGED_TEXT:
                                    fail(bk, 'C3_text_fit', '%s %s: unexpected extra wrap est %d pdf %d' % (sn, nm, nvis_est, nvis_act))
                                elif preexisting:
                                    warn(bk, 'C3_text_fit', '%s %s: wrap estimate off est %d pdf %d (pre-existing text)' % (sn, nm, nvis_est, nvis_act))
                                else:
                                    warn(bk, 'C3_text_fit', '%s %s: extra wrap vs estimate est %d pdf %d' % (sn, nm, nvis_est, nvis_act))
                            if wrap and nvis_act < nvis_est and tail_ok:
                                warn(bk, 'C3_text_fit', '%s %s: benign print merge est %d pdf %d' % (sn, nm, nvis_est, nvis_act))
                            if wrap and max(nvis_est, nvis_act) >= 2:
                                need = max(nvis_est, nvis_act) * fsz * PITCH + (2.0 if re.search(r'_l\d+$', nm) else 3.0)
                                if H < need - 0.01:
                                    if tail_ok:
                                        warn(bk, 'C3_text_fit', '%s %s: frame height tight h %.1f < need %.1f (render OK)' % (sn, nm, H, need))
                                    elif nm in FIXED_LEAVES or nm in CHANGED_TEXT:
                                        fail(bk, 'C3_text_fit', '%s %s: frame height too small h %.1f < need %.1f' % (sn, nm, H, need))
                                    else:
                                        warn(bk, 'C3_text_fit', '%s %s: frame height below analytic need h %.1f < need %.1f (pre-existing shape)' % (sn, nm, H, need))
                            if nm in FIXED_LEAVES and tf['autosize'] != 0:
                                fail(bk, 'C3_text_fit', '%s %s: fixed leaf autosize=%d' % (sn, nm, tf['autosize']))
                            cx0, cy0 = max(0, x0 + 0.5), max(0, y0 + 1.0)
                            cx1, cy1 = min(page.rect.x1, x1 - 0.5), min(page.rect.y1, y1 - 1.0)
                            if cx1 - cx0 > 2 and cy1 - cy0 > 2:
                                crops.append((nm, fitz.Rect(cx0, cy0, cx1, cy1)))
                    fit_all.extend(fit3)
                    # refs column crop (K3 fix)
                    if sn == '相関図④':
                        rects = [(x['l'], x['t'], x['w'], x['h']) for x in com[sn] if re.match(r'^t4_b2_r\d_c3$', x['name'])]
                        if rects:
                            ux0 = min(r[0] for r in rects) * sx + offx
                            uy0 = min(r[1] for r in rects) * sy + offy - above_h * sy
                            ux1 = max(r[0] + r[2] for r in rects) * sx + offx
                            uy1 = max(r[1] + r[3] for r in rects) * sy + offy
                            cr = fitz.Rect(max(0, ux0 - 2), max(0, uy0 - 2),
                                           min(page.rect.x1, ux1 + 2), min(page.rect.y1, uy1 + 2))
                            page.get_pixmap(matrix=fitz.Matrix(4.0, 4.0), clip=cr).save(
                                os.path.join(OUT, 'strict_%s_s4_refscol.png' % bk))
                            fit_info['png_refscol'] = 'strict_%s_s4_refscol.png' % bk
                    for nm, cr in crops:
                        try:
                            page.get_pixmap(matrix=fitz.Matrix(4.0, 4.0), clip=cr).save(
                                os.path.join(OUT, 'crop_%s_%s_%s.png' % (bk, SN_TAG[sn], re.sub(r'[^A-Za-z0-9_-]', '_', nm))))
                        except Exception:
                            pass
                    R(bk, 'C8_pdf_roundtrip')['info'][sn] = fit_info
                    doc.close()
                with io.open(os.path.join(OUT, 'strict_text_fit_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(fit_all, f, ensure_ascii=False, indent=1)
                with io.open(os.path.join(OUT, 'strict_orphans_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(orphans, f, ensure_ascii=False, indent=1)
                R(bk, 'C3_text_fit')['evidence'].append('strict_text_fit_%s.json' % bk)
                R(bk, 'C7_orphans_wrap')['evidence'].append('strict_orphans_%s.json' % bk)
                R(bk, 'C7_orphans_wrap')['info']['known'] = sum(1 for o in orphans if o['class'].startswith('known'))
                R(bk, 'C7_orphans_wrap')['info']['new'] = sum(1 for o in orphans if o['class'] == 'new-regression-candidate')
                R(bk, 'C8_pdf_roundtrip')['info']['k3_refs_crops'] = 'generated'

                wb.Close(SaveChanges=False)
            except Exception:
                try:
                    wb.Close(SaveChanges=False)
                except Exception:
                    pass
                raise
    finally:
        excel.Quit()

    # ---- cross-book digest (C10: ダイジェストキー一致) ----
    ok_digest = True
    cross = R('(cross)', 'C10_err_regression')
    REF_RE = re.compile(r'^t4_b2_r\d_c3_l\d$')
    try:
        for sn in SHEETS:
            np_, nl_ = set(DIGEST['pana'][sn]['names']), set(DIGEST['lnb'][sn]['names'])
            only_p, only_l = np_ - nl_, nl_ - np_
            if sn == '相関図④':
                # ref列幅の設計差 (pana 162 / lnb 172, J-02 §9.5.1) による折返し行数差は許容
                if only_p - set(n for n in only_p if REF_RE.match(n)):
                    ok_digest = False
                    cross['violations'].append('%s: shape name sets differ between books: only_pana=%s only_lnb=%s'
                                               % (sn, sorted(only_p), sorted(only_l)))
                if only_l:
                    ok_digest = False
                    cross['violations'].append('%s: shape name sets differ between books: only_lnb=%s' % (sn, sorted(only_l)))
            elif only_p or only_l:
                ok_digest = False
                cross['violations'].append('%s: shape name sets differ between books: only_pana=%s only_lnb=%s'
                                           % (sn, sorted(only_p), sorted(only_l)))
            g1 = {e['name']: (e['l'], e['t'], e['w'], e['h']) for e in COMSTORE['pana'][sn]}
            g2 = {e['name']: (e['l'], e['t'], e['w'], e['h']) for e in COMSTORE['lnb'][sn]}
            for nm in sorted(set(g1) & set(g2)):
                if (sn, nm) in ALLOWED_GEOM_DIFF or (sn == '相関図④' and REF_RE.match(nm)):
                    continue
                if max(abs(a - b) for a, b in zip(g1[nm], g2[nm])) > 0.5:
                    ok_digest = False
                    cross['violations'].append('%s: geometry differs between books: %s' % (sn, nm))
    except Exception as ex:
        ok_digest = False
        cross['violations'].append('digest comparison error: %r' % (ex,))
    if not ok_digest:
        cross['status'] = 'FAIL'
    cross['evidence'].append('strict_digest_pana.json / strict_digest_lnb.json')

    # ---- C10 table ----
    def cls_status(bk, cls):
        return results.get((bk, cls), {}).get('status', 'NOT-RUN')
    c10 = []
    for bk in ('pana', 'lnb'):
        c10.append({'err': 'autosize refit (ERR-005族)', 'check': 'C3(c) fixed leaves AutoSize=0', 'book': bk,
                    'status': cls_status(bk, 'C3_text_fit'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'フレーム高不足 (ERR-004族)', 'check': 'C3(b) height >= rows*fsz*1.65+3', 'book': bk,
                    'status': cls_status(bk, 'C3_text_fit'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'BoundWidth過小評価 (ERR-012)', 'check': 'C3(a) nvis margin 10.0 + CJK tail equality', 'book': bk,
                    'status': cls_status(bk, 'C3_text_fit'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'PDF抽出偽陰性の構造回避 (ERR-004/K4)', 'check': 'C8 geometric + CJK-tolerant checks only', 'book': bk,
                    'status': cls_status(bk, 'C8_pdf_roundtrip'), 'evidence': 'strict_%s_s2/s3/s4.pdf' % bk})
        c10.append({'err': 'pywin32 gen_py 回避 (ERR-005)', 'check': 'C2 drawing XML direct read', 'book': bk,
                    'status': cls_status(bk, 'C2_inventory'), 'evidence': 'strict_inventory_%s.json' % bk})
        c10.append({'err': 'PrintTitleRows干渉', 'check': 'C1 PrintTitleRows unset on ②③④', 'book': bk,
                    'status': cls_status(bk, 'C1_page_setup'), 'evidence': 'strict_page_setup_%s.json' % bk})
        c10.append({'err': 'PrintArea (A9/B4/④)', 'check': 'C1 PrintArea $A$5:.. / $A$1:$BA$66', 'book': bk,
                    'status': cls_status(bk, 'C1_page_setup'), 'evidence': 'strict_page_setup_%s.json' % bk})
        c10.append({'err': 'fit往復', 'check': 'C8 landscape 1 page + scale recorded', 'book': bk,
                    'status': cls_status(bk, 'C8_pdf_roundtrip'), 'evidence': 'strict_%s_s2/s3/s4.pdf' % bk})
        c10.append({'err': 'ダイジェストキー一致 (novalue)', 'check': 'cross-book names/geometry digest', 'book': bk,
                    'status': 'PASS' if ok_digest else 'FAIL', 'evidence': 'strict_digest_pana.json/strict_digest_lnb.json'})
        c10.append({'err': 'リンク実測', 'check': 'ws.Hyperlinks enumeration + target non-empty', 'book': bk,
                    'status': cls_status(bk, 'C10_err_regression'), 'evidence': 'strict_links_%s.json' % bk})
    with io.open(os.path.join(OUT, 'strict_err_regression_table.json'), 'w', encoding='utf-8') as f:
        json.dump(c10, f, ensure_ascii=False, indent=1)

    # ---- summary ----
    summary = {'generated': datetime.datetime.now().isoformat(timespec='seconds'),
               'books': {}, 'new_issues': [], 'known_issues': KNOWN_P_NOTES,
               'k3': 'resolved (refs crops + per-shape crops generated under strictverify/)'}
    for (bk, cls), r in sorted(results.items()):
        summary['books'].setdefault(bk, {})[cls] = {'status': r['status'],
                                                    'n_viol': len(r['violations']), 'n_warn': len(r['warnings'])}
        for v in r['violations']:
            summary['new_issues'].append('%s/%s: %s' % (bk, cls, v))
    with io.open(os.path.join(WORK, 'verify_strict_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(OUT, 'strict_full_results.json'), 'w', encoding='utf-8') as f:
        json.dump({'%s/%s' % k: v for k, v in results.items()}, f, ensure_ascii=False, indent=1)

    print('==== RESULT ====')
    nfail = 0
    for (bk, cls), r in sorted(results.items()):
        print('%-7s %-18s %s (viol=%d warn=%d)' % (bk, cls, r['status'], len(r['violations']), len(r['warnings'])))
        nfail += len(r['violations'])
    print('TOTAL VIOLATIONS: %d' % nfail)
    print('SUMMARY -> verify_strict_summary.json')
    if nfail:
        sys.exit(1)
    print('STRICT VERIFY: ALL PASS')

if __name__ == '__main__':
    main()
