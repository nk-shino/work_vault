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

 Gate 1 是正 (F1〜F6, 2026-11-09):
   F1 末尾判定を順序付きCJK等値へ回帰·ASCII末尾の別確認·高さ検査の折返し分離
   F2 PDF枠線による独立較正+残差点検査·スパン単位帰属·クロップ台帳·右端あふれ拡張
   F3 既存扱いは描画状態の一致で判定 (テキスト不変のみでは根拠にしない)
   F4 C4豁免を固定ペア/ベースライン由来に限定·悪化差分を記録
   F5 ②③ベースライン→現在の逆方向比較·read_tf失敗を無音除外しない
   F6 C10回帰表と C6/C8 の状態表示を実サブチェックから集約 (RECORDED 導入)

 Gate 1 第2次是正 (再審査 attempt 2 指摘, 2026-11-09):
   F1 (ア) multiset 判定を等値に変更 — 重複·追加文字は 'extra-chars(dup/addition)'
       として K4 疑いと別の異常クラスで報告
       (イ) ASCII loss の警告降格を廃止 — changed/fixed 以外でも FAIL
       (ウ) 末尾異常の severity·サブチェック分類を tail_severity() に集約し
       負例検証が本番経路で N1/N2 を確認する
   F2 (ア) 枠線独立較正に PrintArea 先頭行補正 (above_h) を適用し原点を統一
       (ウ) attribute_spans を C3 本文比較に接続 — 広域窓だけで文字が見つかる
       ケースは 'attribution-undetermined' (帰属未確定) とし tail_ok にしない
       (エ) N6: 隣接図形の同文字列による末尾補填を本番 severity で検出
   F3 classify_render_state に幅·改行/段落構造の比較を追加 — baseline 項目
       欠落は 'render-state-not-comparable' (一致にしない)
   F6 失敗注入の自己検証 (--selftest) を追加 — EXP_LINE2 不一致の changed 登録,
       unexpected extra wrap のサブチェック反映, リンク NOT-RUN の非 PASS 集約,
       enforce_aggregation_consistency でサブチェック FAIL をクラス PASS にしない

 Gate 1 第3次是正 (再審査 attempt 3 指摘, 2026-11-09):
   (1) 帰属識別子の安定化 — attribute_spans は元 spans と同一オブジェクトを
       格納し, 帰属が owner 検索 -> tail_rescue -> severity まで一続きで伝搬する
   (2) 帰属未確定 (attribution-undetermined) の severity 分離 — baseline (描画
       設定) の一致は帰属の証拠にならないため, render_same でも FAIL を維持
   (3) own 救済の文字再利用排除 — tail_rescue は own_text 未含まの own 帰属
       スパンだけで全文を再構成し, 同じ順序付き等値検査を再適用する
   (4) 終了コードと ALL PASS 表示をクラス FAIL を含む実状態に連動
       (enforce_aggregation_consistency が違反メッセージを登録する)
   (5) 分類集計の単位分離 — 残差 (CJK 文字数) と C3 末尾救済 (図形件数) を
       別単位で計上·表示する
  """
import sys, io, os, re, json, math, zipfile, datetime, bisect

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
        # F2: 枠線保有フラグ (a:ln があり noFill でない) -- 独立較正の
        # 予測矩形はこの図形に限定する (罫線は枠線図形からしか生まれない)
        bordered = False
        for pr in ('spPr', 'grpSpPr'):
            spr = obj.find(XDR + pr)
            if spr is not None:
                ln = spr.find(ANS + 'ln')
                if ln is not None and ln.find(ANS + 'noFill') is None:
                    bordered = True
        entry = {'name': name, 'kind': tag,
                 'box': [round(l, 2), round(t, 2), round(w, 2), round(h, 2)],
                 'flip': [fh != pflip[0], fv != pflip[1]], 'bordered': bordered}
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
    """F5: 取得失敗を無音で除外しない。例外は {'_error': ...} として呼び出し側に
    返し、C2/C9 で失敗として扱う (HasText=False の図形は None のまま = 正常)"""
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
    except Exception as ex:
        return {'_error': repr(ex)}

def tf_ok(tf):
    return bool(tf) and '_error' not in tf

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

# ---------------------------------------------------------------- F1/F2/F3/F5 pure checks
# Gate 1 是正 (F1〜F6) で追加。合成フィクスチャによる負例検証
# (verify_render_strict_negtest.py) からも直接呼び出せるよう、
# Excel/PDF に依存しない純粋関数として切り出している。

def cjk_seq(s):
    """順序を保持した CJK 列 (F1: 順序付き等値の主判定用)"""
    return re.sub(r'[^\u4e00-\u9fff\u3040-\u30ff]', '', norm(s)) if s else ''

def tail_check_ordered(exp_text, got_text):
    """F1: 末尾検査を順序付き CJK 等値に戻す。
    mode: 'ordered-equal' 完全一致 / 'multiset-only(k4-suspect)' 文字種はそろうが
    順序不一致 (K4 化け疑い·描画証跡と警告で受容) /
    'extra-chars(dup/addition)' 期待文字はすべて含むが重複·追加文字がある
    (K4 疑いではなく別異常クラス: 隣接行混入·抽出重複として報告) /
    'loss' 欠落 / 'empty' 期待CJKなし。
    第2次是正: multiset 判定を Counter>= (包含) から等値に変更した。
    重複·追加は K4 疑いに吸収せず独立の異常クラスとして返す。"""
    se, sg = cjk_seq(exp_text), cjk_seq(got_text)
    if not se:
        return {'mode': 'empty', 'ordered_ok': True, 'multiset_ok': True}
    ordered = (se == sg)
    ce, cg = Counter(se), Counter(sg)
    multiset = (ce == cg)                       # 第2次: 包含ではなく等値
    extra = (not multiset) and not (ce - cg)    # 期待文字は全部ある·余分がある
    if ordered:
        mode = 'ordered-equal'
    elif multiset:
        mode = 'multiset-only(k4-suspect)'
    elif extra:
        mode = 'extra-chars(dup/addition)'
    else:
        mode = 'loss'
    return {'mode': mode, 'ordered_ok': ordered, 'multiset_ok': multiset,
            'extra': extra}

def ascii_tail(text, minlen=3):
    """F1: 本文末尾側の ASCII 連続列 (>=minlen) を返す (ASCII末尾は別確認)"""
    if not text:
        return ''
    m = re.findall(r'[!-~]{%d,}' % minlen, norm(text))
    return m[-1] if m else ''

# K4 (P8) のグリフ置換を吸収する等価表現: ダッシュ類·中点類は抽出時に
# 別コードポイント (U+2010 等·中点) に置き換わる実測がある
_ASCII_EQUIV = {0x2010: '-', 0x2011: '-', 0x2012: '-', 0x2013: '-', 0x2014: '-',
                0x2015: '-', 0xFF0D: '-', 0x2212: '-',
                0x00B7: '-', 0xFF65: '-', 0x30FB: '-', 0x2027: '-', 0x2022: '-'}

def norm_ascii(s):
    return ''.join(_ASCII_EQUIV.get(ord(c), c) for c in norm(s or ''))

def ascii_tail_check(text, got_text):
    """F1: ASCII 末尾の 3 段階判定
    'ok'         : 抽出文に末尾がそのまま含まれる (K4 等価吸収後)
    'k4-variant' : 英数字のみの比較なら含まれる (ダッシュ·丸付き数字隣接等の
                   K4 グリフ置換の疑い。クロップ証跡で視覚確認する)
    'loss'       : どの比較でも見つからない (描画欠落の疑い)"""
    t = ascii_tail(text)
    if not t:
        return 'ok'
    g8 = norm_ascii(got_text or '')
    if norm_ascii(t) in g8:
        return 'ok'
    ta = re.sub(r'[^A-Za-z0-9]', '', t)
    ga = re.sub(r'[^A-Za-z0-9]', '', g8)
    if len(ta) >= 2 and ta in ga:
        return 'k4-variant'
    return 'loss'

def ascii_tail_ok(text, got_text):
    return ascii_tail_check(text, got_text) != 'loss'

# K4 (P8) 候補の裁定台帳: クロップによる人裁定が記録済みの図形
# (Gate1是正パス報告 2026-11-09 §2(b): 描画は正常·抽出ドロップと裁定済み。
# FAIL 自体は維持する。第2次是正 F1(ウ): 「人裁定未了」と「受容済み」を区別する)
K4_ADJUDICATED = {'g2_bandhead', 'g2_bandnote', 'g3_n12_txt'}

def tail_severity(nm, tc_mode, amode, exp_text, render_same=False):
    """F1(第2次·ウ): 末尾異常の本番 severity·サブチェック分類。
    main() の C3 判定と負例検証 (verify_render_strict_negtest.py)·selftest が
    同じ関数を共有する (純関数の戻り値だけの確認を廃止し、本番の
    severity·サブチェック経路で負例を確認する)。
    戻り値: {'severity': 'FAIL'|'WARN', 'subcheck': ..., 'code': ..., 'message': ...} のリスト"""
    out = []
    is_cf = nm in FIXED_LEAVES or nm in CHANGED_TEXT
    if tc_mode == 'multiset-only(k4-suspect)':
        if is_cf:
            k4_state = 'crop-adjudicated' if nm in K4_ADJUDICATED else 'undecided(awaiting-human-review)'
            out.append({'severity': 'FAIL', 'subcheck': 'tail_cjk_ordered', 'code': 'tail_k4_changed_fixed',
                        'message': 'CJK tail order mismatch (multiset-only; k4-suspect; changed/fixed; %s)' % k4_state})
        else:
            k4_state = 'accepted(crop-adjudicated)' if nm in K4_ADJUDICATED else 'undecided(awaiting-human-review)'
            out.append({'severity': 'WARN', 'subcheck': 'tail_cjk_ordered',
                        'code': 'tail_k4_accepted' if nm in K4_ADJUDICATED else 'tail_k4_undecided',
                        'message': 'CJK tail order mismatch (multiset-only; k4-suspect; %s; see crop)' % k4_state})
    elif tc_mode == 'extra-chars(dup/addition)':
        # F1(第2次·ア): 重複·追加は K4 疑いではなく別異常クラス
        out.append({'severity': 'FAIL', 'subcheck': 'tail_cjk_ordered', 'code': 'tail_extra_chars',
                    'message': 'CJK extra/duplicate chars vs expected (dup/addition anomaly; not a K4 variant)'})
    elif tc_mode == 'loss':
        if render_same:
            out.append({'severity': 'WARN', 'subcheck': 'tail_cjk_ordered', 'code': 'tail_loss_preexisting',
                        'message': 'last-line loss (loss; pre-existing, render state matches baseline)'})
        else:
            out.append({'severity': 'FAIL', 'subcheck': 'tail_cjk_ordered', 'code': 'tail_loss',
                        'message': 'last-line loss (loss)'})
    elif tc_mode == 'attribution-undetermined':
        # 第3次是正 (修正2): baseline (描画設定) の一致は「現在の文字が対象図形に
        # 帰属する」証拠にならない。帰属未確定は loss と同一分岐にせず、独立した
        # 帰属証拠または人裁定で解決するまで render_same の有無にかかわらず FAIL
        # を維持する (既存/発生時点の分類は orphans 側で別途記録する)
        out.append({'severity': 'FAIL', 'subcheck': 'tail_cjk_ordered',
                    'code': 'tail_attribution_undetermined',
                    'message': 'last-line loss (attribution-undetermined; baseline match is '
                               'not attribution evidence; independent attribution evidence '
                               'or human review required)'})
    # 'ordered-equal' / 'empty' / 'loss-window-precision' は CJK 側の異常なし
    if amode == 'loss':
        # F1(第2次·イ): 警告降格を廃止 -- changed/fixed 以外でも FAIL
        out.append({'severity': 'FAIL', 'subcheck': 'tail_ascii_separate', 'code': 'ascii_loss',
                    'message': 'ASCII tail loss: %r' % ascii_tail(exp_text)})
    elif amode == 'k4-variant':
        k4_state = 'accepted(crop-adjudicated)' if nm in K4_ADJUDICATED else 'undecided(awaiting-human-review)'
        out.append({'severity': 'WARN', 'subcheck': 'tail_ascii_separate',
                    'code': 'ascii_k4_accepted' if nm in K4_ADJUDICATED else 'ascii_k4_undecided',
                    'message': 'ASCII tail %r only matches as k4-variant (glyph substitution; %s; see crop)'
                               % (ascii_tail(exp_text), k4_state)})
    return out

def tail_rescue(exp_text, own_spans, wide_spans):
    """F2(第2次·ウ): 末尾欠落時の救済判定に帰属証拠を要求する。
    own_spans: 自図形の窓に帰属したスパン (attribute_spans の結果·元 spans と
    同一オブジェクト)。
    wide_spans: 広域窓 (±15/+30pt) に存在する (span, owner) のリスト。
    owner は 'own' (自図形窓に帰属) / 'other' (他図形窓に帰属) / 'unattributed'。
    欠落文字の扱い:
      - 自帰属スパンだけで全文が順序付き等値になる -> 'loss-window-precision'
        (tail_ok=True。合格根拠は自図形への帰属証拠。第3次是正 (修正3): 救済に
        使える own スパンは own_text の構成元に**含まれない**スパンに限定し、
        重複排除済みのスパン集合から全文を再構成した上で、own_text に適用した
        のと同じ順序付き等値検査を再適用する。既に own_text に含めた同じ文字の
        再利用 (反例: 期待「確認確認」取得「確認」+広域own「確認」が通過する)
        を構造的に排除する)
      - 他図形帰属·未帰属スパンを必要とする -> 'attribution-undetermined'
        (帰属未確定。tail_ok は False のまま -- 広域窓で文字が見つかっただけでは
        合格にしない。独立した帰属証拠または人裁定を要求する)
      - 広域窓にも存在しない -> 'loss' のまま (真の欠落)"""
    own_text = ''.join(r['t'] for r in rows_from_spans(own_spans))
    tc = tail_check_ordered(exp_text, own_text)
    res = {'mode': tc['mode'], 'tail_ok': tc['ordered_ok'], 'rescue_owners': [],
           'missing_chars': ''}
    if tc['mode'] != 'loss':
        return res
    # 修正3: own_text の構成元スパンを救済候補から除外 (同じ文字の再利用を排除)
    seen = set(id(s) for s in own_spans)
    extra_own = [s for (s, o) in wide_spans if o == 'own' and id(s) not in seen]
    other_cnt = Counter()
    for s, o in wide_spans:
        if o != 'own' and id(s) not in seen:
            other_cnt += Counter(cjk_seq(s[4]))
    if extra_own:
        # 重複排除済みスパン集合から全文を再構成し、同じ順序付き等値検査を再適用
        merged_text = ''.join(r['t'] for r in rows_from_spans(list(own_spans) + extra_own))
        tc2 = tail_check_ordered(exp_text, merged_text)
        if tc2['ordered_ok']:
            res['mode'] = 'loss-window-precision'
            res['tail_ok'] = True
            res['rescue_owners'] = ['own']
            return res
    ce, cg = Counter(cjk_seq(exp_text)), Counter(cjk_seq(own_text))
    missing = ce - cg
    if not missing:
        return res
    res['missing_chars'] = ''.join(sorted(missing.elements()))
    own_extra_cnt = Counter(cjk_seq(''.join(s[4] for s in extra_own)))
    present, owners = True, set()
    for ch, n in missing.items():
        rem = n - own_extra_cnt[ch]
        if rem <= 0:
            continue
        if other_cnt[ch] >= rem:
            owners.add('other' if other_cnt[ch] else 'unattributed')
        else:
            present = False
    if not present:
        return res                       # 'loss' のまま (真の欠落)
    res['mode'] = 'attribution-undetermined'
    res['tail_ok'] = False
    res['rescue_owners'] = sorted(owners) or ['own']
    return res

def rows_from_spans(spans):
    """F2(第2次): 帰属スパンを視覚行に統合する (clusters_in の帰属版)。
    spans: (x0,y0,x1,y1,text)。y近接 (<=2pt) のスパンを 1 行にまとめる"""
    cls = []
    for yy, xx0, xx1, tt in sorted((s[1], s[0], s[2], s[4]) for s in spans):
        if cls and yy - cls[-1]['y'] <= 2.0:
            c = cls[-1]
            c['x0'] = min(c['x0'], xx0)
            c['x1'] = max(c['x1'], xx1)
            c['t'] += tt
        else:
            cls.append({'y': yy, 'x0': xx0, 'x1': xx1, 't': tt})
    return cls

def height_need_pt(nvis, fsz, name):
    """F1: 高さ必要量 = nvis * fsz * 1.65 + マージン。
    マージンの適用条件: +3.0pt = 既定 (枠余白の実測) ·
    +2.0pt = エッジラベル (名前が _l<数字> で終わる) のみ。
    適用は wrap 有無によらず nvis>=2 で行う (複数段落は wrap='none' でも適用)。"""
    margin = 2.0 if re.search(r'_l\d+$', name or '') else 3.0
    return nvis * fsz * PITCH + margin, margin

def classify_render_state(base_entry, cur_text, cur_h, cur_w, cur_autosize, cur_wrap):
    """F3: 「既存扱い」の判定を描画状態の一致で行う。テキストが不変でも
    高さ/幅/AutoSize/折返しがベースラインと異なれば 'render-changed-origin-unknown'
    (発生時点不明·要確認) を返し、既存扱いの根拠にしない。
    第2次是正:
      - norm() は改行を除去するため '甲\\n乙' と '甲乙' が同一扱いになる問題を
        修正 -- 段落構造 (改行で分割した各行の正規化列) を比較する
      - 幅 (w) の比較を追加
      - baseline に h/w/autosize/wordwrap のいずれかが欠ける場合は
        'render-state-not-comparable' (比較不能) を返し「一致」としない"""
    if base_entry is None:
        return 'no-baseline'
    para_sig = lambda t: [norm(p) for p in (t or '').split('\n')]
    if para_sig(base_entry.get('text', '')) != para_sig(cur_text or ''):
        return 'text-changed'
    bh = base_entry.get('h')
    bw = base_entry.get('w')
    ba = base_entry.get('autosize')
    bww = base_entry.get('wordwrap')
    if any(v is None for v in (bh, bw, ba, bww)):
        return 'render-state-not-comparable'
    h_same = abs(float(bh) - float(cur_h)) <= 0.5
    w_same = abs(float(bw) - float(cur_w)) <= 0.5
    a_same = int(ba) == int(cur_autosize)
    ww_same = int(bww) == int(cur_wrap)
    if h_same and w_same and a_same and ww_same:
        return 'render-same'
    return 'render-changed-origin-unknown'

def reverse_baseline_missing(baseline_entries, current_names, current_texts=None):
    """F5: ベースライン→現在の逆方向比較。戻り値: 欠落/読取失敗リスト"""
    missing = []
    for en in baseline_entries:
        nm = en['path'].split('/')[-1]
        if nm not in current_names:
            missing.append({'name': nm, 'reason': 'shape-missing'})
        elif current_texts is not None and (en.get('text') or '').strip():
            if nm not in current_texts:
                missing.append({'name': nm, 'reason': 'text-unreadable'})
    return missing

# ---- F6(第2次): 集約の一貫性ヘルパー (main と --selftest が共有) ------------

def register_changed_result(acc, key, ok, reason=None):
    """F6(第2次): changed/EXP_LINE2 の成否を必ず acc['changed'] に登録する。
    失敗を登録せず changed_text_asbuilt が PASS になる経路を構造的に塞ぐ"""
    rec = {'ok': bool(ok)}
    if reason:
        rec['reason'] = reason
    acc.setdefault('changed', {})[key] = rec
    return rec

def changed_text_status(acc):
    """F6(第2次): changed_text_asbuilt サブチェックは実登録値から集約する。
    登録が 1 件も無ければ NOT-RUN (PASS にしない)"""
    if not acc.get('changed'):
        return 'NOT-RUN'
    return 'FAIL' if any(not v.get('ok') for v in acc['changed'].values()) else 'PASS'

def link_rows_status(statuses):
    """F6(第2次): リンク回帰行の集約。NOT-RUN を PASS にしない"""
    if 'FAIL' in statuses:
        return 'FAIL'
    if 'NOT-RUN' in statuses or len(statuses) < 3:
        return 'NOT-RUN'
    return 'PASS'

def wrap_estimate_status(cnt):
    """F6(第2次): unexpected extra wrap のサブチェック反映"""
    return 'FAIL' if cnt.get('wrap_extra') else 'PASS'

def enforce_aggregation_consistency(results):
    """F6(第2次): 集約の一貫性 -- サブチェックに FAIL があればクラスを PASS にしない。
    第3次是正 (修正4): FAIL 化のときに違反メッセージも登録する。違反メッセージを
    追加しないままクラスだけ FAIL にすると、終了判定 (violations 件数) と ALL PASS
    表示が実際の FAIL 状態と乖離する (EXP_LINE2 の baseline 欠落で「失敗登録+
    警告のみ」の経路が実在した)。
    戻り値: 修正した (bk, cls, old, new) のリスト (--selftest が注入で確認する)"""
    fixes = []
    for (bk, cls), r in results.items():
        if r.get('status') == 'PASS' and any(
                sv.get('status') == 'FAIL' for sv in r.get('subchecks', {}).values()):
            fixes.append((bk, cls, 'PASS', 'FAIL'))
            r['status'] = 'FAIL'
            r.setdefault('violations', []).append(
                'aggregation consistency: class status was PASS while a subcheck is FAIL '
                '(auto-corrected; violation registered so exit code / ALL PASS follow the real state)')
    return fixes

def aggregate_fail_state(results):
    """第3次是正 (修正4): 終了コードと ALL PASS 表示の材料を実 FAIL 状態
    (クラス status を含む) から集約する。違反メッセージ件数だけでは、
    enforce_aggregation_consistency によるクラス FAIL 化を取りこぼす経路が
    あったため、クラス FAIL 数を併せて返す。
    戻り値: (違反メッセージ総数, status=FAIL のクラス数)"""
    nviol = 0
    ncls_fail = 0
    for r in results.values():
        nviol += len(r.get('violations', []))
        if r.get('status') == 'FAIL':
            ncls_fail += 1
    return nviol, ncls_fail

def run_selftest():
    """F6(第2次): 失敗注入による集約追従の自己検証 (Excel·ブック不要)。
    合成の失敗を注入し、クラス·サブチェック·回帰行の集約表示が追従することを
    確認する。結果は reconsider/selftest_results.json にも記録する"""
    checks = []
    def check(sid, desc, ok, actual):
        checks.append({'id': sid, 'desc': desc, 'ok': bool(ok), 'actual': actual})
        print('%s %s -> %s' % (sid, desc, 'OK' if ok else 'NG'))
        print('    actual: %s' % json.dumps(actual, ensure_ascii=False)[:220])

    # ST1: EXP_LINE2 不一致を本番の登録関数で注入 -> changed_text_asbuilt は FAIL
    acc1 = {'changed': {}}
    register_changed_result(acc1, 'g2_bandhead', True)
    register_changed_result(acc1, 'g3_n07_txt@相関図③', False, reason='line-2 replacement mismatch')
    st1 = changed_text_status(acc1)
    check('ST1', 'EXP_LINE2 mismatch -> changed_text_asbuilt=FAIL (旧実装は未登録で PASS の恐れ)',
          st1 == 'FAIL', {'status': st1, 'registered': sorted(acc1['changed'])})

    # ST2: changed 登録ゼロは NOT-RUN (PASS にしない)
    st2 = changed_text_status({'changed': {}})
    check('ST2', 'changed 登録ゼロ -> NOT-RUN (PASS にしない)', st2 == 'NOT-RUN', {'status': st2})

    # ST3: unexpected extra wrap の注入 -> wrap_estimate サブチェック FAIL
    st3 = wrap_estimate_status({'wrap_extra': 1})
    st3b = wrap_estimate_status({'wrap_extra': 0})
    check('ST3', 'extra wrap 注入 -> wrap_estimate=FAIL / 0件なら PASS',
          st3 == 'FAIL' and st3b == 'PASS', {'injected': st3, 'clean': st3b})

    # ST4: リンク回帰行 -- NOT-RUN を PASS に集約しない
    st4a = link_rows_status(['PASS', 'NOT-RUN', 'PASS'])
    st4b = link_rows_status(['FAIL', 'PASS', 'PASS'])
    st4c = link_rows_status(['PASS', 'PASS', 'PASS'])
    check('ST4', 'リンク回帰行: NOT-RUN は NOT-RUN のまま·FAIL は FAIL',
          st4a == 'NOT-RUN' and st4b == 'FAIL' and st4c == 'PASS',
          {'notrun': st4a, 'fail': st4b, 'allpass': st4c})

    # ST5: サブチェック FAIL を持つクラスを PASS のままにしない (注入→enforce で FAIL 化)
    results5 = {('pana', 'C9_data_accuracy'): {'status': 'PASS', 'violations': [],
                                               'subchecks': {'changed_text_asbuilt': {'status': 'FAIL'}}}}
    fixes5 = enforce_aggregation_consistency(results5)
    check('ST5', 'サブチェック FAIL を含むクラスが PASS で残らない (enforce で FAIL 化)',
          results5[('pana', 'C9_data_accuracy')]['status'] == 'FAIL' and len(fixes5) == 1,
          {'fixes': fixes5})

    # ST6: 本番 severity 経路 -- ASCII loss は changed/fixed 以外でも FAIL (警告降格廃止の確認)
    sev6 = tail_severity('g2_e_e17_l', 'ordered-equal', 'loss', '確認 NR4030-0300-A3')
    ok6 = any(i['severity'] == 'FAIL' and i['subcheck'] == 'tail_ascii_separate' for i in sev6)
    check('ST6', 'ASCII loss (changed/fixed 以外) -> 本番 severity FAIL',
          ok6, {'items': sev6})

    # ST7: 本番 severity 経路 -- 重複·追加文字は別異常クラスで FAIL (K4 疑いにしない)
    tc7 = tail_check_ordered('再起動の確認', '再起動の確認起動')
    sev7 = tail_severity('g3_n08_txt', tc7['mode'], 'ok', '再起動の確認')
    ok7 = (tc7['mode'] == 'extra-chars(dup/addition)'
           and any(i['severity'] == 'FAIL' and i['code'] == 'tail_extra_chars' for i in sev7))
    check('ST7', '重複·追加文字 -> extra-chars(dup/addition) 別異常クラス FAIL',
          ok7, {'mode': tc7['mode'], 'items': sev7})

    # ST8: K4 候補の受容済み/未裁定の区別 (受容済み=クロップ人裁定記録あり·FAIL は維持)
    sev8a = tail_severity('g2_bandnote', 'multiset-only(k4-suspect)', 'ok', 'x')
    sev8b = tail_severity('g3_n08_txt', 'multiset-only(k4-suspect)', 'ok', 'x')
    ok8 = (any('crop-adjudicated' in i['message'] for i in sev8a)
           and any('undecided(awaiting-human-review)' in i['message'] for i in sev8b))
    check('ST8', 'K4 候補: 受容済み (台帳あり) と人裁定未了を区別して記録', ok8,
          {'adjudicated': [i['message'] for i in sev8a], 'undecided': [i['message'] for i in sev8b]})

    # ST9 (第3次是正·修正4): 違反0+サブチェックFAIL -- enforce によるクラス FAIL 化
    # が終了コードと ALL PASS 表示に反映されること (修正前は「クラス FAIL 表示+
    # STRICT VERIFY: ALL PASS+終了コード 0」が起こり得た)
    results9 = {('pana', 'C9_data_accuracy'): {'status': 'PASS', 'violations': [], 'warnings': [],
                                               'subchecks': {'changed_text_asbuilt': {'status': 'FAIL'}}}}
    fixes9 = enforce_aggregation_consistency(results9)
    nviol9, ncls9 = aggregate_fail_state(results9)
    exit9 = 1 if (nviol9 or ncls9) else 0
    display9 = 'FAIL' if (nviol9 or ncls9) else 'ALL PASS'
    check('ST9', '違反0+サブチェックFAIL -> enforce でクラス FAIL 化+違反登録され、終了コード 0 / ALL PASS 表示にならない',
          exit9 == 1 and nviol9 == 1 and ncls9 == 1 and display9 == 'FAIL' and len(fixes9) == 1,
          {'violations': nviol9, 'class_fail': ncls9, 'exit_code': exit9, 'display': display9,
           'registered': results9[('pana', 'C9_data_accuracy')]['violations']})

    all_ok = all(c['ok'] for c in checks)
    out = {'generated': datetime.datetime.now().isoformat(timespec='seconds'),
           'n_checks': len(checks), 'n_ok': sum(1 for c in checks if c['ok']),
           'all_ok': all_ok, 'checks': checks}
    outdir = os.path.join(OUT, 'reconsider')
    os.makedirs(outdir, exist_ok=True)
    with io.open(os.path.join(outdir, 'selftest_results.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('SELFTEST: %d/%d OK -> %s' % (out['n_ok'], out['n_checks'],
                                        os.path.join('reconsider', 'selftest_results.json')))
    return 0 if all_ok else 1

def attribute_spans(spans, windows, min_straddle=0.05):
    """F2: スパン単位の窓帰属。
    spans: (x0,y0,x1,y1,text) · windows: {name: (x0,y0,x1,y1)}。
    戻り値: (attrib {name: [span]}, unattributed [span], straddles [rec])。
    straddle = 複数窓にまたがるスパン (隣接行混入·隣接図形への食い込み検出用)。
    第3次是正 (修正1): attrib/unattributed には**元 spans と同一の tuple
    オブジェクト**を格納する (新しい tuple を生成しない)。後段の span_owner
    (id キー) 検索が元 spans に対して成立し、帰属識別子が
    attribute_spans -> owner 検索 -> tail_rescue -> severity まで一続きで安定する"""
    attrib = defaultdict(list)
    un, strad = [], []
    for s in spans:
        x0, y0, x1, y1, t = s
        aa = max(1e-6, (x1 - x0) * (y1 - y0))
        ratios = {}
        for nm, (wx0, wy0, wx1, wy1) in windows.items():
            ox = min(x1, wx1) - max(x0, wx0)
            oy = min(y1, wy1) - max(y0, wy0)
            if ox > 0 and oy > 0:
                ratios[nm] = (ox * oy) / aa
        if not ratios:
            un.append(s)
            continue
        best = max(ratios, key=lambda k: ratios[k])
        attrib[best].append(s)
        others = {k: v for k, v in ratios.items() if k != best and v >= min_straddle}
        if others:
            strad.append({'span': [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                          'text': t, 'assigned': best,
                          'straddle_ratio': {k: round(v, 2) for k, v in others.items()}})
    return attrib, un, strad

def collect_pdf_lines(page):
    """F2: PDF のベクター線分 (罫線·枠線) を収集する。
    戻り値: ('h'|'v', a0, a1, fixed) のリスト。fixed = 水平線なら y / 垂直線なら x"""
    segs = []
    for dr in page.get_drawings():
        for it in dr['items']:
            if it[0] == 'l':
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) <= 0.5 and abs(p1.x - p2.x) > 2.0:
                    segs.append(('h', min(p1.x, p2.x), max(p1.x, p2.x), (p1.y + p2.y) / 2.0))
                elif abs(p1.x - p2.x) <= 0.5 and abs(p1.y - p2.y) > 2.0:
                    segs.append(('v', min(p1.y, p2.y), max(p1.y, p2.y), (p1.x + p2.x) / 2.0))
            elif it[0] == 're':
                r = it[1]
                segs.append(('h', r.x0, r.x1, r.y0))
                segs.append(('h', r.x0, r.x1, r.y1))
                segs.append(('v', r.y0, r.y1, r.x0))
                segs.append(('v', r.y0, r.y1, r.x1))
    return segs

def _near_dist(arr_sorted, v, tol):
    """arr_sorted 内で v±tol に収る最接近値の距離 (無ければ None)"""
    i = bisect.bisect_left(arr_sorted, v - tol)
    best = None
    while i < len(arr_sorted) and arr_sorted[i] <= v + tol:
        d = abs(arr_sorted[i] - v)
        if best is None or d < best:
            best = d
        i += 1
    return best

def line_calibration(pred_rects, segs, s_cands, offx_priors=(), offy_priors=(),
                     step=0.0005, tol=1.2, offwin=25.0):
    """F2: PDF 枠線による独立較正 (テキスト非依存) -- X/Y 各軸を独立に求める。
    (第2次是正: 呼び出し側で pred_rects の y から above_h (PrintArea 先頭行の
    行高·約103.8pt) を差し引き、COM 幾何と PDF の原点を統一してから渡す。
    前回「X/Y で異なる倍率になる (sx=0.936/sy=0.971)」という実測説明は
    原点不一致を含んだ値であり、補正後の再評価結果で訂正する)
    s_cands: 印刷条件 (fit方程式·余白·PrintArea寸法) から導出したスケール候補。
    各軸ごとに、各 s でオフセットを (a) 差分ヒストグラム上位峰
    (b) 印刷原点の事前候補 から採り、整合した予測辺数が最大の (s, off) を選ぶ。
    戻り値: dict(sx, ox, sy, oy, n_edges_x/y, matched_x/y, residual_max_pt)"""
    hy = sorted(set(round(s3[3], 1) for s3 in segs if s3[0] == 'h'))
    vx = sorted(set(round(s3[3], 1) for s3 in segs if s3[0] == 'v'))
    if not hy or not vx or not pred_rects:
        return None
    ss = set()
    for b in s_cands:
        if b is None:
            continue
        k = -16
        while k <= 16:
            ss.add(round(b + k * step, 5))
            k += 1
    ss = sorted(ss)

    def fit_axis(edges_pred, det, priors):
        # オフセットは印刷原点の事前候補 (余白·センタリング) から ±3pt に限定する
        # (centerH/V が偽なら原点は余白に一致する)。を広げると線分密度ゆえの
        # 偽一致 (どの s でも半数近くが ±1pt 内に何か引っかかる) で収束しない
        off_cands = set()
        for p in priors:
            k = -6
            while k <= 6:
                off_cands.add(round(p + k * 0.5, 2))
                k += 1
        best = None
        for s in ss:
            for off in off_cands:
                matched = 0
                resmax = 0.0
                for ep in edges_pred:
                    r = _near_dist(det, ep * s + off, tol)
                    if r is not None:
                        matched += 1
                        resmax = max(resmax, r)
                if best is None or matched > best['matched']:
                    best = {'s': round(s, 4), 'off': round(off, 2), 'matched': matched,
                            'residual_max_pt': round(resmax, 2)}
        return best

    ex, ey = [], []
    for (l, t, w, h) in pred_rects:
        ex += [l, l + w]
        ey += [t, t + h]
    fx = fit_axis(ex, vx, offx_priors)
    fy = fit_axis(ey, hy, offy_priors)
    if not fx or not fy:
        return None
    return {'sx': fx['s'], 'ox': fx['off'], 'sy': fy['s'], 'oy': fy['off'],
            'n_edges_x': len(ex), 'matched_x': fx['matched'],
            'n_edges_y': len(ey), 'matched_y': fy['matched'],
            'matched_ratio_x': round(fx['matched'] / max(1, len(ex)), 3),
            'matched_ratio_y': round(fy['matched'] / max(1, len(ey)), 3),
            'residual_max_pt': max(fx['residual_max_pt'], fy['residual_max_pt'])}

def pdf_spans(page):
    """F2: スパン単位の生テキスト (帰属と残差検査用)"""
    out = []
    for blk in page.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            for sp in ln['spans']:
                if sp['text'].strip():
                    x0, y0, x1, y1 = sp['bbox']
                    out.append((x0, y0, x1, y1, sp['text']))
    return out

# ---------------------------------------------------------------- shared state
DIGEST = {}
COMSTORE = {}

def main():
    results = {}
    def R(bk, cls):
        return results.setdefault((bk, cls), {'status': 'PASS', 'violations': [], 'warnings': [],
                                              'info': {}, 'evidence': [], 'subchecks': {}})
    def sub(bk, cls, name, status, evidence=None):
        """F6: サブチェック単位の状態を記録する (C10 回帰表はクラス全体の
        status を転記せず、この実サブチェックから集約する)"""
        r = R(bk, cls)
        r['subchecks'][name] = {'status': status, 'evidence': evidence}
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
                n_pa_fail = n_ptr_fail = n_other_fail = 0
                for sn in SHEETS:
                    ps = sheets[sn].PageSetup
                    pa_want = PA4 if sn == '相関図④' else PA23[bk][0 if sn == '相関図②' else 1]
                    pa_act = ps.PrintArea or ''
                    if norm(pa_act) != norm(pa_want):
                        fail(bk, 'C1_page_setup', '%s: PrintArea %r != %r' % (sn, pa_act, pa_want))
                        n_pa_fail += 1
                    if int(ps.Orientation) != 2:
                        fail(bk, 'C1_page_setup', '%s: orientation=%s' % (sn, ps.Orientation))
                        n_other_fail += 1
                    if int(ps.PaperSize) != 9:
                        fail(bk, 'C1_page_setup', '%s: paper=%s' % (sn, ps.PaperSize))
                        n_other_fail += 1
                    if not (int(ps.FitToPagesWide) == 1 and int(ps.FitToPagesTall) == 1 and not ps.Zoom):
                        fail(bk, 'C1_page_setup', '%s: fit/zoom=%s/%s/%s' % (sn, ps.Zoom, ps.FitToPagesWide, ps.FitToPagesTall))
                        n_other_fail += 1
                    try:
                        ptr = ps.PrintTitleRows or ''
                    except Exception:
                        ptr = '<unreadable>'
                    ev1['print_title_rows'][sn] = ptr
                    if ptr not in ('', None):
                        fail(bk, 'C1_page_setup', '%s: PrintTitleRows set: %r' % (sn, ptr))
                        n_ptr_fail += 1
                    ftr = {'C': ps.CenterFooter or '', 'L': ps.LeftFooter or '', 'R': ps.RightFooter or ''}
                    ev1['footer'][sn] = ftr
                    if FOOTER_KEY not in (ftr['C'] + ftr['L'] + ftr['R']):
                        fail(bk, 'C1_page_setup', '%s: footer lacks %s' % (sn, FOOTER_KEY))
                        n_other_fail += 1
                sub(bk, 'C1_page_setup', 'print_area', 'FAIL' if n_pa_fail else 'PASS')
                sub(bk, 'C1_page_setup', 'print_title_rows_unset', 'FAIL' if n_ptr_fail else 'PASS')
                sub(bk, 'C1_page_setup', 'orientation_paper_fit_footer', 'FAIL' if n_other_fail else 'PASS')
                with io.open(os.path.join(OUT, 'strict_page_setup_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(ev1, f, ensure_ascii=False, indent=1)
                R(bk, 'C1_page_setup')['evidence'].append('strict_page_setup_%s.json' % bk)

                # ---------------- COM shapes ----------------
                com = {sn: com_sheet_shapes(sheets[sn]) for sn in SHEETS}
                COMSTORE[bk] = com
                # F5: read_tf 失敗の無音除外を禁止 -- 失敗は C2 の違反として扱う
                com_tf_errors = []
                for sn in SHEETS:
                    for e in com[sn]:
                        if e.get('tf') and '_error' in e['tf']:
                            com_tf_errors.append((sn, e['name']))
                            fail(bk, 'C2_inventory', '%s: read_tf failed on %s: %s' % (sn, e['name'], e['tf']['_error']))
                        for c in e.get('children', []):
                            if c.get('tf') and '_error' in c['tf']:
                                com_tf_errors.append((sn, c['name']))
                                fail(bk, 'C2_inventory', '%s: read_tf failed on %s: %s' % (sn, c['name'], c['tf']['_error']))
                sub(bk, 'C2_inventory', 'read_tf_no_silent_skip', 'FAIL' if com_tf_errors else 'PASS')
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
                    sub(bk, 'C2_inventory', 'xml_com_name_match_%s' % SN_TAG[sn],
                        'FAIL' if real_miss_com else 'PASS')
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
                        if tf_ok(e.get('tf')):
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
                            if tf_ok(c.get('tf')):
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
                # F4: 豁免は「固定ペア」と「ベースライン(postA3 c-list)由来」に限定する。
                # 旧実装の動的豁免 ((1) 同一オーナー内 (3) 所属ノード同士の重なり設計
                # (4) エッジラベルの埋め込み) は新規違反を自動解除するため廃止。
                # 動的ルールで豁免されていたペアのうちベースラインに無いものは、
                # 以降は新規違反として記録され、人間の判断を待つ。
                FIXED_CLR_PAIRS = [{'g2_bandhead', 'g2_bandnote'}, {'g3_bandhead', 'g3_bandnote'}]
                lbl_edge = re.compile(r'^(g\d_e_e\d+)_l$')
                clr_out = {}
                n_exempt_fixed = n_exempt_baseline = 0
                for sn in ('相関図②', '相関図③'):
                    # リーフテキスト矩形 (グループ子 + 非グループtop)
                    ltexts = []
                    for sh in tops23[sn]:
                        if int(sh['type']) == 6:
                            for c in sh.get('children', []):
                                if tf_ok(c.get('tf')):
                                    ltexts.append((c['name'], (c['l'], c['t'], c['w'], c['h'])))
                        elif tf_ok(sh.get('tf')):
                            ltexts.append((sh['name'], (sh['l'], sh['t'], sh['w'], sh['h'])))
                    base_c_pairs = {(min(v['a'], v['b']), max(v['a'], v['b']))
                                    for v in postA_file['books'][bk][sn]['violations']['c']}
                    # 同一ノードの _txt/_tag はタグがノード箱の右上に重なる設計であり、
                    # ギャップ 0 が常態。名前パターンから導出する固定ペアとして扱う
                    # (幾何から導出する動的豁免ではない。理由は証跡 JSON に記録する)
                    owner = {}
                    for sh in tops23[sn]:
                        for c in sh.get('children', []):
                            owner[c['name']] = sh['name']

                    def same_node_txt_tag(na, nb):
                        oa, ob = owner.get(na), owner.get(nb)
                        return (oa is not None and oa == ob and oa not in
                                ('g2_band', 'g3_band')
                                and {na.rsplit('_', 1)[-1], nb.rsplit('_', 1)[-1]} == {'txt', 'tag'})

                    def baseline_gap(pk):
                        """F4: 既存ペアの悪化差分算出用に、ベースライン幾何 (b5) から
                        当時のギャップを再計算する"""
                        ea = baseline_idx.get((bk, sn, pk[0]))
                        eb = baseline_idx.get((bk, sn, pk[1]))
                        if not ea or not eb or any(k not in e for e in (ea, eb) for k in ('l', 't', 'w', 'h')):
                            return None
                        return clc.rect_rect_dist((ea['l'], ea['t'], ea['w'], ea['h']),
                                                  (eb['l'], eb['t'], eb['w'], eb['h']))

                    viols, known, worsened = [], [], []
                    for i in range(len(ltexts)):
                        for j in range(i + 1, len(ltexts)):
                            (na, ra), (nb, rb) = ltexts[i], ltexts[j]
                            g = clc.rect_rect_dist(ra, rb)
                            if g >= CLEAR_PT:
                                continue
                            ent = {'a': na, 'b': nb, 'gap_pt': round(g, 2)}
                            pk = (min(na, nb), max(na, nb))
                            if any({na, nb} == fp for fp in FIXED_CLR_PAIRS):
                                ent['exempt_reason'] = 'fixed-design-pair'
                                n_exempt_fixed += 1
                                known.append(ent)
                            elif same_node_txt_tag(na, nb):
                                ent['exempt_reason'] = 'fixed-design-pair(same-node txt/tag)'
                                n_exempt_fixed += 1
                                known.append(ent)
                            elif pk in base_c_pairs:
                                ent['exempt_reason'] = 'baseline(postA3 c-list)'
                                n_exempt_baseline += 1
                                bg = baseline_gap(pk)
                                if bg is None:
                                    ent['baseline_gap_pt'] = 'unknown'
                                else:
                                    ent['baseline_gap_pt'] = round(bg, 2)
                                    if g < bg - 1.0:
                                        ent['worsened_by_pt'] = round(bg - g, 2)
                                        worsened.append(dict(ent))
                                known.append(ent)
                            else:
                                ent['exempt_reason'] = None
                                viols.append(ent)
                    base_cnt = base_clear['books'][bk]['sheets'][sn]['count']
                    clr_out[sn] = {'leaf_texts': len(ltexts), 'violations_new': viols,
                                   'baseline_known_overlaps': known, 'worsened_baseline_pairs': worsened,
                                   'clearance_report_baseline_count': base_cnt}
                    for v in viols:
                        fail(bk, 'C4_clearance', '%s: text-text clearance %.2fpt < 3.75pt (new): %s x %s'
                             % (sn, v['gap_pt'], v['a'], v['b']))
                    for w in worsened:
                        warn(bk, 'C4_clearance', '%s: baseline pair worsened %.2fpt -> %.2fpt: %s x %s'
                             % (sn, w['baseline_gap_pt'], w['gap_pt'], w['a'], w['b']))
                sub(bk, 'C4_clearance', 'exemptions_recorded', 'RECORDED',
                    'fixed=%d baseline=%d (reasons in strict_clearance_%s.json)' % (n_exempt_fixed, n_exempt_baseline, bk))
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
                                if tf_ok(c.get('tf')):
                                    k = 'txt' if c['name'].endswith('_txt') else ('tag' if c['name'].endswith('_tag') else 'membertext')
                                    texts.append((c['name'], cc.R(c), sh['name'], k, c['tf']))
                        elif tf_ok(sh.get('tf')):
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
                # F6: C6 は「記録のみ」を PASS と表示せず RECORDED とし、
                # 期待比較 (XML/COM の接続線集合と箱の一致) を実施する。
                # ラベル重なりの分類は C5 分類c、EE08/n19(R1) は既知例外として記録。
                conn_out = {}
                conn_mismatch = []
                for sn in SHEETS:
                    rec = []
                    for e in com[sn]:
                        if cc.cls_of(e['name'], e['type']) == 'edge' or re.match(r'^t4_b3_ln\d+$', e['name']):
                            xe = inv_flat[sn].get(e['name']) or {}
                            rec.append({'name': e['name'], 'box': [e['l'], e['t'], e['w'], e['h']],
                                        'flip': xe.get('flip'), 'conn': e.get('conn'),
                                        'orient': 'h' if e['h'] <= 0.5 else ('v' if e['w'] <= 0.5 else 'multi')})
                            if not xe:
                                conn_mismatch.append('%s: connector %s absent in drawing XML' % (sn, e['name']))
                            else:
                                d = max(abs(e['l'] - xe['box'][0]), abs(e['t'] - xe['box'][1]),
                                        abs(e['w'] - xe['box'][2]), abs(e['h'] - xe['box'][3]))
                                if d > 0.5:
                                    conn_mismatch.append('%s: connector %s XML/COM box drift %.2fpt' % (sn, e['name'], d))
                    conn_out[sn] = rec
                for v in coll_out['相関図②']['violations']['b']:
                    ids = v.get('a', '') + ' ' + v.get('b', '')
                    if 'g2_e_e08' in ids and 'n19' in ids:
                        conn_out.setdefault('known_R1_EE08', []).append(v)
                with io.open(os.path.join(OUT, 'strict_connectors_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(conn_out, f, ensure_ascii=False, indent=1)
                R(bk, 'C6_connectors')['evidence'].append('strict_connectors_%s.json' % bk)
                for mmsg in conn_mismatch:
                    fail(bk, 'C6_connectors', mmsg)
                R(bk, 'C6_connectors')['status'] = 'FAIL' if conn_mismatch else 'RECORDED'
                sub(bk, 'C6_connectors', 'xml_com_connector_match', 'FAIL' if conn_mismatch else 'PASS')
                R(bk, 'C6_connectors')['info']['expectation'] = ('connectors recorded with flip/orient/conn; '
                                                                 'XML vs COM box <=0.5pt; label overlaps judged in C5-c; EE08/n19=R1 recorded (P7)')

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
                        if tf_ok(e.get('tf')):
                            tx[e['name']] = e['tf']['text']
                        for c in e.get('children', []):
                            if tf_ok(c.get('tf')):
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
                        # F6(第2次): 失敗も acc['changed'] に登録する (未登録のまま
                        # changed_text_asbuilt が PASS になる経路を塞ぐ)
                        register_changed_result(acc, nm + '@相関図③', False, reason='shape missing')
                        fail(bk, 'C9_data_accuracy', '相関図③: %s missing' % nm); continue
                    base = baseline_idx.get((bk, '相関図③', nm))
                    if not base:
                        register_changed_result(acc, nm + '@相関図③', False, reason='not in baseline')
                        warn(bk, 'C9_data_accuracy', '相関図③: %s not in baseline' % nm); continue
                    bp = base['text'].split('\n')
                    expect = [bp[0], line2] + bp[2:]
                    if norm(act) != norm('\n'.join(expect)) or len(act.split('\n')) != len(expect):
                        register_changed_result(acc, nm + '@相関図③', False, reason='line-2 replacement mismatch')
                        fail(bk, 'C9_data_accuracy', '相関図③: %s line-2 replacement mismatch' % nm)
                    else:
                        register_changed_result(acc, nm + '@相関図③', True)
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
                # F5: ベースライン→現在の逆方向比較 (②③)。
                # 既存図形の欠落·テキスト読取失敗を網羅する。④は変更前基準が無いため対象外。
                acc['baseline_reverse'] = {}
                n_rev_fail = 0
                for sn in ('相関図②', '相関図③'):
                    cur_names = (set(inv_flat[sn]) | {e['name'] for e in com[sn]}
                                 | {c['name'] for e in com[sn] for c in e.get('children', [])})
                    miss = reverse_baseline_missing(baselines[bk][sn], cur_names, all_text[sn])
                    acc['baseline_reverse'][sn] = miss
                    for m5 in miss:
                        n_rev_fail += 1
                        fail(bk, 'C9_data_accuracy', '%s: baseline shape missing/unreadable in current book: %s (%s)'
                             % (sn, m5['name'], m5['reason']))
                sub(bk, 'C9_data_accuracy', 'baseline_reverse_23', 'FAIL' if n_rev_fail else 'PASS',
                    'missing=%d' % n_rev_fail)
                # 記録訂正 (第2次): ①の除外理由を「b5に対応データが無い」から
                # 「本ハーネスは①を収集していない (対象範囲)」に訂正する。
                # b5_current_state.json には①の幾何·本文が実在する (各冊24図形)。
                acc['baseline_reverse']['相関図①'] = {
                    'status': 'not-collected',
                    'note': '相関図①は本ハーネスの収集対象外 (SHEETS=相関図②③④)。'
                            'b5ベースラインには①の幾何·本文が実在する (各冊24図形) が、'
                            '現在側の収集が無いため逆比較は未実施'}
                sub(bk, 'C9_data_accuracy', 'baseline_reverse_scope_sheet1', 'NOT-RUN',
                    'sheet1 (相関図①) not collected by this harness; baseline exists in b5 '
                    '(24 shapes/book); reverse comparison not run (scope, corrected in 2nd pass)')
                sub(bk, 'C9_data_accuracy', 'changed_text_asbuilt', changed_text_status(acc),
                    'entries=%d' % len(acc.get('changed', {})))
                sub(bk, 'C9_data_accuracy', 't4_expected_act',
                    'FAIL' if acc['t4_table'] and not all(acc['t4_table'].values()) else 'PASS')
                with io.open(os.path.join(OUT, 'strict_data_accuracy_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(acc, f, ensure_ascii=False, indent=1)
                R(bk, 'C9_data_accuracy')['evidence'].append('strict_data_accuracy_%s.json' % bk)
                R(bk, 'C9_data_accuracy')['info']['unchanged_missing_baseline'] = len(acc['unchanged_missing_baseline'])

                # ---------------- hyperlinks (④) ----------------
                ws4 = sheets['相関図④']
                nhl = len(ws4.Hyperlinks)
                n_link_fail = 0
                if nhl != WANT_LINKS[bk]:
                    fail(bk, 'C10_err_regression', '④ hyperlinks %d != %d' % (nhl, WANT_LINKS[bk]))
                    n_link_fail += 1
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
                n_target_fail = 0
                if exp_links is not None:
                    map_ok = (act_links == exp_links)
                    if not map_ok:
                        fail(bk, 'C10_err_regression', '④ link map mismatch (%d act vs %d exp)' % (len(act_links), len(exp_links)))
                        n_link_fail += 1
                    for nm, tgt in exp_links.items():
                        sheet, cell = tgt.rsplit('!', 1)
                        if sheet in CRED_SHEETS:
                            continue
                        try:
                            v = wb.Worksheets(sheet).Range(cell).Value
                        except Exception:
                            fail(bk, 'C10_err_regression', '%s target %s!%s unreadable' % (nm, sheet, cell))
                            n_target_fail += 1
                            continue
                        if v is None or norm(str(v)) == '':
                            fail(bk, 'C10_err_regression', '%s target %s!%s empty' % (nm, sheet, cell))
                            n_target_fail += 1
                sub(bk, 'C10_err_regression', 'link_count', 'FAIL' if nhl != WANT_LINKS[bk] else 'PASS')
                sub(bk, 'C10_err_regression', 'link_map', 'FAIL' if map_ok is False else ('PASS' if map_ok else 'NOT-RUN'))
                sub(bk, 'C10_err_regression', 'link_targets_nonempty', 'FAIL' if n_target_fail else 'PASS')
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
                # F2: 較正は PDF 枠線 (ベクター線) で独立に行い、テキスト依存の
                # 収蔵率較正は交差検証に降格する。帰属はスパン単位で行い、
                # 残差 (どの図形で何文字抽出できなかったか) を説明責任付きで記録する。
                fit_all = []
                orphans = []
                crops_ledger = []
                # 第3次是正 (修正5): 文字数と図形件数を別単位で計上する。
                # attr_undet_chars = 残差検査の CJK 文字数 / attr_undet_cases =
                # C3 末尾救済の図形件数 / tail_attr_undet = C3 severity FAIL の図形件数。
                # 単位の異なる数値を合算して「CJK chars」と表示しない
                cnt = {'tail_loss': 0, 'tail_k4': 0, 'ascii_fail': 0, 'height_fail': 0,
                       'ascii_k4': 0, 'tail_winprec': 0, 'tail_extra': 0,
                       'tail_attr_undet': 0, 'attr_undet_chars': 0, 'attr_undet_cases': 0,
                       'wrap_extra': 0,
                       'autosize_fail': 0, 'page_fail': 0, 'calib_note': 0, 'unexplained': 0}
                for sn in SHEETS:
                    doc = fitz.open(pdf_map[sn])
                    if doc.page_count != 1:
                        fail(bk, 'C8_pdf_roundtrip', '%s: pdf pages %d != 1' % (sn, doc.page_count))
                        cnt['page_fail'] += 1
                    page = doc[0]
                    if page.rect.width <= page.rect.height:
                        fail(bk, 'C8_pdf_roundtrip', '%s: pdf not landscape (%.0fx%.0f)' % (sn, page.rect.width, page.rect.height))
                        cnt['page_fail'] += 1
                    jrows = pdf_rows(page)
                    txmap = {}
                    for e in com[sn]:
                        if tf_ok(e.get('tf')):
                            txmap[e['name']] = e
                        for c in e.get('children', []):
                            if tf_ok(c.get('tf')):
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
                        if tf_ok(e2.get('tf')) and not e2['name'].endswith('_tag'):
                            cal_items.append((e2['name'], e2['tf'], (e2['l'], e2['t'], e2['w'], e2['h'])))
                        for c2 in e2.get('children', []):
                            if tf_ok(c2.get('tf')) and not c2['name'].endswith('_tag'):
                                cal_items.append((c2['name'], c2['tf'], (c2['l'], c2['t'], c2['w'], c2['h'])))

                    def coverage_at(sx, sy, offx, offy, need_list=None):
                        tot = 0.0
                        for nm2, tf2, (L2, T2, W2, H2) in cal_items:
                            x0 = (L2 + tf2['mL']) * sx + offx - 2.0
                            y0 = (T2 + tf2['mT'] - above_h) * sy + offy - 3.0
                            x1 = (L2 + W2 - tf2['mR']) * sx + offx + 2.0
                            y1 = (T2 + H2 - tf2['mB'] - above_h) * sy + offy + 3.0
                            got = ''.join(t for (yy, rx0, rx1, t) in jrows
                                          if y0 <= yy <= y1 and rx0 < x1 and rx1 > x0)
                            ce, cg = Counter(cjk(tf2['text'])), Counter(cjk(got))
                            cov = sum(min(n2, cg[ch]) for ch, n2 in ce.items()) / max(1, sum(ce.values()))
                            tot += cov
                            if need_list is not None:
                                need_list.append((nm2, round(cov, 3)))
                        return tot / max(1, len(cal_items))

                    best_s, best_cov = s_est, coverage_at(s_est, s_est, offx0, offy0)
                    s_try = 0.80
                    while s_try <= 1.0001:
                        cov = coverage_at(s_try, s_try, float(ps.LeftMargin), float(ps.TopMargin))
                        if cov > best_cov + 1e-9:
                            best_s, best_cov = s_try, cov
                        s_try = round(s_try + 0.001, 4)
                    # F2: 独立較正 (PDF 枠線·テキスト非依存) -- 主判定に使用する。
                    # スケール候補は印刷条件 (fit方程式·余白·PrintArea寸法) から導出し、
                    # 予測矩形は枠線を持つ図形 (XML a:ln 有効) に限定する。
                    pred_rects = []
                    for e3 in com[sn]:
                        xe3 = inv_flat[sn].get(e3['name']) or {}
                        if xe3.get('bordered') and e3['w'] > 5 and e3['h'] > 5:
                            pred_rects.append((e3['l'], e3['t'], e3['w'], e3['h']))
                        for c3 in e3.get('children', []):
                            xe4 = inv_flat[sn].get(c3['name']) or {}
                            if xe4.get('bordered') and c3['w'] > 5 and c3['h'] > 5:
                                pred_rects.append((c3['l'], c3['t'], c3['w'], c3['h']))
                    s_cands = [s_est]
                    if rw and rh:
                        s_cands += [avail_w / rw, avail_h / rh]
                    offx_priors = [float(ps.LeftMargin)]
                    offy_priors = [float(ps.TopMargin)]
                    if centerH and rw:
                        offx_priors.append(float(ps.LeftMargin) + (avail_w - rw * s_est) / 2.0)
                    if centerV and rh:
                        offy_priors.append(float(ps.TopMargin) + (avail_h - rh * s_est) / 2.0)
                    # F2(第2次·ア): PrintArea 先頭行補正 -- COM 幾何の y はシート原点、
                    # PDF の y はページ原点。本文窓と同じ (T - above_h) 変換で
                    # 原点を統一してから較正する (above_h は②③で約103.8pt。
                    # 補正前の比較は約100pt の原点差を含んでおり、オフセット探索
                    # (±3pt) では吸収不能だった。前回の「異方性」説明はこの
                    # 原点不一致の誤認の可能性があるため再評価する)
                    pred_rects_corr = [(l, t - above_h, w, h) for (l, t, w, h) in pred_rects]
                    calib_line = line_calibration(pred_rects_corr, collect_pdf_lines(page), s_cands,
                                                  offx_priors, offy_priors)
                    calib_mode = 'text-coverage(fallback)'
                    sx = sy = best_s
                    offx, offy = offx0, offy0
                    agree = None
                    # 採用条件: 各軸の整合率 35% 以上 · 残差 (coverage) がテキスト較正の
                    # 0.9 倍以上 (cross-check)。不採用のときは黙ってテキスト較正を使わず
                    # 'calibration-unresolved' を記録する (偽合格の隠蔽を避ける)。
                    # 注: テキスト較正 (単一スケール) は X/Y 異方性を表現できないため、
                    # 一致判定は行わず coverage の cross-check のみを用いる。
                    strong = (calib_line and calib_line['matched_ratio_x'] >= 0.6
                              and calib_line['matched_ratio_y'] >= 0.6)
                    if strong:
                        cov_line = coverage_at(calib_line['sx'], calib_line['sy'],
                                               calib_line['ox'], calib_line['oy'])
                        if cov_line >= 0.9 * best_cov:
                            calib_mode = 'pdf-frame-lines'
                            sx, offx = calib_line['sx'], calib_line['ox']
                            sy, offy = calib_line['sy'], calib_line['oy']
                            agree = {'dsx_vs_text': round(abs(calib_line['sx'] - best_s), 4),
                                     'dsy_vs_text': round(abs(calib_line['sy'] - best_s), 4)}
                        else:
                            cnt['calib_note'] += 1
                            warn(bk, 'C8_pdf_roundtrip',
                                 '%s: calibration-unresolved: frame-line cov=%.3f vs text cov=%.3f (text-coverage used)'
                                 % (sn, cov_line, best_cov))
                    else:
                        cnt['calib_note'] += 1
                        warn(bk, 'C8_pdf_roundtrip',
                             '%s: frame-line calibration weak (rx=%r ry=%r); fell back to text coverage calibration'
                             % (sn, calib_line['matched_ratio_x'] if calib_line else None,
                                calib_line['matched_ratio_y'] if calib_line else None))
                    cov_primary = coverage_at(sx, sy, offx, offy)
                    mapping = {'sx': round(sx, 4), 'sy': round(sy, 4), 'offx': round(offx, 1),
                               'offy': round(offy, 1), 'scale_est_print': round(s_est, 4),
                               'coverage': round(cov_primary, 4),
                               'coverage_text_calib': round(best_cov, 4),
                               'calib_mode': calib_mode,
                               'calib_line': calib_line, 'calib_agreement': agree,
                               'frame_origin_correction': ('pred_rect y -= above_h (%.1fpt) applied; origin unified'
                                                           % above_h),
                               'print_area_start_row': start_row, 'above_h': round(above_h, 1),
                               'centerH': centerH, 'centerV': centerV}
                    # F2: スパン単位帰属 (窓=図形の本文領域) + 残差の説明責任
                    spans = pdf_spans(page)
                    windows = {}
                    for nm2, tf2, (L2, T2, W2, H2) in cal_items:
                        windows[nm2] = ((L2 + tf2['mL']) * sx + offx,
                                        (T2 + tf2['mT'] - above_h) * sy + offy,
                                        (L2 + W2 - tf2['mR']) * sx + offx,
                                        (T2 + H2 - tf2['mB'] - above_h) * sy + offy)
                    attrib, unattrib, strads = attribute_spans(spans, windows)
                    n_strad_big = sum(1 for s4 in strads if max(s4['straddle_ratio'].values()) >= 0.3)
                    if n_strad_big:
                        warn(bk, 'C8_pdf_roundtrip', '%s: %d spans straddle >=2 text windows (adjacent-row mixing candidates)'
                             % (sn, n_strad_big))
                    unattr_cjk = sum(len(cjk(t)) for (_, _, _, _, t) in unattrib)
                    # F2(第2次·ウ): 残差点検査も自図形への帰属を根拠にする。
                    # 「PDF 上の自図形の帰属スパンに存在しない文字」を残差とし:
                    #   - 自帰属スパンだけで充足 -> 窓精度として説明 (合格根拠は帰属証拠)
                    #   - 他図形帰属·未帰属スパンを必要とする -> 'attribution-undetermined'
                    #     (帰属未確定。他図形の文字を合格根拠にしない)
                    #   - ページ近傍 (±15pt) にも存在しない -> 'unexplained' (真の残差·FAIL)
                    span_owner = {}
                    for wnm, lst in attrib.items():
                        for s5 in lst:
                            span_owner[id(s5)] = wnm
                    for nm2, tf2, (L2, T2, W2, H2) in cal_items:
                        ce = Counter(cjk(tf2['text']))
                        cg = Counter(cjk(''.join(t for (_, _, _, _, t) in attrib.get(nm2, []))))
                        miss = ce - cg
                        if not miss:
                            continue
                        wx0, wy0, wx1, wy1 = windows[nm2]
                        ex0, ey0, ex1, ey1 = wx0 - 15.0, wy0 - 15.0, wx1 + 15.0, wy1 + 15.0
                        own_extra, other = Counter(), Counter()
                        for s5 in spans:
                            if s5[0] < ex1 and s5[2] > ex0 and s5[1] < ey1 and s5[3] > ey0:
                                if span_owner.get(id(s5)) == nm2:
                                    own_extra += Counter(cjk(s5[4]))
                                else:
                                    other += Counter(cjk(s5[4]))
                        for ch, n in miss.items():
                            if own_extra[ch] >= n:
                                continue
                            if own_extra[ch] + other[ch] >= n:
                                # 修正5: 残差は「文字数」単位で計上する
                                cnt['attr_undet_chars'] += n
                                cnt.setdefault('attr_undet_entries', []).append('%s/%s:%s:%d'
                                        % (sn, nm2, ch, n))
                            else:
                                cnt['unexplained'] += n
                                cnt.setdefault('unexplained_shapes', []).append('%s/%s:%s:%d'
                                        % (sn, nm2, ch, n))

                    pix = page.get_pixmap(matrix=fitz.Matrix(2.4, 2.4))
                    png_full = 'strict_%s_%s_full.png' % (bk, SN_TAG[sn])
                    pix.save(os.path.join(OUT, png_full))
                    fit_info = {'pages': doc.page_count, 'mapping': mapping, 'png_full': png_full,
                                'spans_total': len(spans), 'spans_unattributed': len(unattrib),
                                'unattributed_cjk_chars': unattr_cjk,
                                'straddle_spans': strads[:40]}

                    fit3 = []
                    crops = []
                    for e in com[sn]:
                        tfitems = []
                        if tf_ok(e.get('tf')):
                            tfitems.append((e['name'], e['tf'], (e['l'], e['t'], e['w'], e['h'])))
                        for c in e.get('children', []):
                            if tf_ok(c.get('tf')):
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

                            # F2(第2次·ウ): C3 本文比較は attribute_spans の帰属結果を使う。
                            # clusters_in の交差取得 (他図形の文字を合格根拠にできる) は廃止。
                            if nm in windows:
                                own_spans = sorted(attrib.get(nm, []), key=lambda s: (s[1], s[0]))
                                attrib_basis = 'own-window'
                            else:
                                # タグ (縦書き) 等は帰属窓の対象外 -- 幾何窓で取得するが
                                # 帰属証拠は無い (救済は attribution-undetermined 扱い)
                                own_spans = sorted((s for s in spans
                                                    if s[0] < x1 and s[2] > x0
                                                    and s[1] < y1 and s[3] > y0),
                                                   key=lambda s: (s[1], s[0]))
                                attrib_basis = 'geometry-window(no-attribution)'
                            rows_own = rows_from_spans(own_spans)
                            nvis_act = len(rows_own)
                            got_own = ''.join(r['t'] for r in rows_own)
                            got_cjk = cjk(got_own)
                            # F3(第2次): 描画状態の一致判定 (幅·改行/段落構造を含む) --
                            # severity 判定の前に行う
                            base0 = baseline_idx.get((bk, sn, nm))
                            rstate = classify_render_state(base0, tf['text'], H, W, tf['autosize'], tf['wrap'])
                            render_same = rstate == 'render-same'
                            # F1/F2(第2次): 末尾検査は順序付き CJK 等値。'loss' の救済は
                            # 帰属証拠付きで行い、他図形の文字では合格にしない
                            tc = tail_check_ordered(tf['text'], got_own)
                            tail_mode, tail_ok = tc['mode'], tc['ordered_ok']
                            rescue_owners, missing_chars = [], ''
                            if tc['mode'] == 'loss':
                                wide = []
                                for s5 in spans:
                                    if s5[0] < x1 + 15.0 and s5[2] > x0 - 15.0 \
                                       and s5[1] < y1 + 30.0 and s5[3] > y0 - 15.0:
                                        w5 = span_owner.get(id(s5))
                                        wide.append((s5, 'own' if w5 == nm else
                                                     ('other' if w5 else 'unattributed')))
                                # 修正1/3 (第3次): 自帰属スパン (元 spans と同一
                                # オブジェクト) を渡し、救済は own_text 未含まの
                                # own スパンに限定して順序付き等値を再適用する
                                vr = tail_rescue(tf['text'], attrib.get(nm, []), wide)
                                tail_mode, tail_ok = vr['mode'], vr['tail_ok']
                                rescue_owners, missing_chars = vr['rescue_owners'], vr['missing_chars']
                                if tail_mode == 'loss-window-precision':
                                    cnt['tail_winprec'] += 1
                                    warn(bk, 'C3_text_fit', '%s %s: tail chars rescued by own-attributed spans (window precision; evidence=own attribution)'
                                         % (sn, nm))
                                elif tail_mode == 'attribution-undetermined':
                                    # 修正5: 図形件数単位で計上 (文字数とは合算しない)
                                    cnt['attr_undet_cases'] += 1
                                    warn(bk, 'C3_text_fit', '%s %s: missing tail chars %r found only in %s spans (attribution undetermined; no pass without independent evidence)'
                                         % (sn, nm, missing_chars, '/'.join(rescue_owners) or 'nearby'))
                            # F1(第2次): ASCII 末尾は CJK とは別に確認 (loss は無条件で FAIL)。
                            # severity·サブチェック分類は本番経路 tail_severity に集約する
                            amode = ascii_tail_check(tf['text'], got_own)
                            for it in tail_severity(nm, tail_mode, amode, tf['text'], render_same=render_same):
                                code = it['code']
                                if it['severity'] == 'FAIL':
                                    fail(bk, 'C3_text_fit', '%s %s: %s' % (sn, nm, it['message']))
                                    if code == 'ascii_loss':
                                        cnt['ascii_fail'] += 1
                                    elif code == 'tail_extra_chars':
                                        cnt['tail_extra'] += 1
                                    elif code in ('tail_loss', 'tail_k4_changed_fixed'):
                                        cnt['tail_loss'] += 1
                                    elif code == 'tail_attribution_undetermined':
                                        # 修正2/5 (第3次): 帰属未確定は独立の FAIL
                                        # コード。図形件数単位で計上する
                                        cnt['tail_attr_undet'] += 1
                                else:
                                    warn(bk, 'C3_text_fit', '%s %s: %s' % (sn, nm, it['message']))
                                    if code in ('tail_k4_accepted', 'tail_k4_undecided'):
                                        cnt['tail_k4'] += 1
                                    elif code.startswith('ascii_k4'):
                                        cnt['ascii_k4'] += 1
                            # F2: 右端あふれ (spill) -- 抽出は完全でもクロップ窓で切れる反例の検出
                            aspans = attrib.get(nm, [])
                            span_right = max([s5[2] for s5 in aspans] or [0])
                            spill = max(0.0, span_right - (x1 - 2.0))
                            rec = {'sheet': sn, 'name': nm, 'fsz': fsz, 'nvis_est': nvis_est,
                                   'nvis_pdf': nvis_act, 'tail_ok': tail_ok, 'tail_mode': tail_mode,
                                   'attrib_basis': attrib_basis,
                                   'rescue_owners': rescue_owners, 'missing_chars': missing_chars,
                                   'tail_exp20': cjk_seq(tf['text'])[-20:], 'tail_got20': cjk_seq(got_cjk)[-20:],
                                   'ascii_tail': ascii_tail(tf['text']), 'ascii_mode': amode,
                                   'spill_pt': round(spill, 2), 'rows_short': [],
                                   'rows_short_ascii': []}
                            for c in rows_own:
                                vis = len(re.sub(r'\s+', '', c['t']))
                                if vis <= 2:
                                    rec['rows_short'].append(c['t'])
                                elif vis <= 5 and not cjk(c['t']):
                                    rec['rows_short_ascii'].append(c['t'])
                            fit3.append(rec)
                            # C7 orphans: 分類 = 既知P* / 既存同型(描画状態まで一致) /
                            # 発生時点不明(テキスト不変だが描画状態が変化) /
                            # 比較不能(baseline項目欠落) / 本ラウンド退行
                            # F3: 「テキスト不変」だけでは既存扱いの根拠にしない
                            if rstate == 'render-changed-origin-unknown':
                                orphans.append({'sheet': sn, 'name': nm, 'class': 'render-state-changed-origin-unknown',
                                                'baseline_h': base0.get('h'), 'current_h': H,
                                                'baseline_w': base0.get('w'), 'current_w': W,
                                                'baseline_autosize': base0.get('autosize'), 'current_autosize': tf['autosize']})
                                warn(bk, 'C7_orphans_wrap', '%s %s: render state changed without text change (h %s->%s, w %s->%s, autosize %s->%s); origin unknown, verify'
                                     % (sn, nm, base0.get('h'), H, base0.get('w'), W, base0.get('autosize'), tf['autosize']))
                            elif rstate == 'render-state-not-comparable':
                                # F3(第2次): baseline 項目欠落は「一致」にしない (比較不能として記録)
                                orphans.append({'sheet': sn, 'name': nm, 'class': 'render-state-not-comparable',
                                                'baseline_fields': {k: base0.get(k) for k in ('h', 'w', 'autosize', 'wordwrap')}})
                                warn(bk, 'C7_orphans_wrap', '%s %s: render state not comparable (baseline lacks h/w/autosize/wordwrap); not treated as match'
                                     % (sn, nm))
                            if nvis_act >= 2:
                                for tt in rec['rows_short']:
                                    kd = KNOWN_DEFECT.get((sn, nm))
                                    if kd:
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'known-' + kd})
                                    elif render_same:
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'preexisting-baseline-isomorphic'})
                                        warn(bk, 'C7_orphans_wrap', '%s %s: short row (baseline-isomorphic, pre-existing)' % (sn, nm))
                                    elif rstate == 'render-changed-origin-unknown':
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'origin-unknown-verify'})
                                        warn(bk, 'C7_orphans_wrap', '%s %s: short row (render state changed, origin unknown)' % (sn, nm))
                                    elif rstate == 'render-state-not-comparable':
                                        orphans.append({'sheet': sn, 'name': nm, 'row': tt, 'class': 'render-state-not-comparable'})
                                        warn(bk, 'C7_orphans_wrap', '%s %s: short row (render state not comparable; baseline incomplete)' % (sn, nm))
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
                            # C3 の末尾·ASCII の FAIL/WARN は上の tail_severity 適用で
                            # 報告済み (二重報告しない)。以降は wrap·高さ·AutoSize
                            if wrap and nvis_act > nvis_est:
                                kd = KNOWN_DEFECT.get((sn, nm))
                                if kd:
                                    orphans.append({'sheet': sn, 'name': nm, 'class': 'known-%s(extra wrap)' % kd,
                                                    'nvis_est': nvis_est, 'nvis_pdf': nvis_act})
                                elif nm in FIXED_LEAVES or nm in CHANGED_TEXT:
                                    # F6(第2次): unexpected extra wrap の FAIL を
                                    # wrap_estimate サブチェックに反映する
                                    cnt['wrap_extra'] += 1
                                    fail(bk, 'C3_text_fit', '%s %s: unexpected extra wrap est %d pdf %d' % (sn, nm, nvis_est, nvis_act))
                                elif render_same:
                                    warn(bk, 'C3_text_fit', '%s %s: wrap estimate off est %d pdf %d (pre-existing text)' % (sn, nm, nvis_est, nvis_act))
                                else:
                                    warn(bk, 'C3_text_fit', '%s %s: extra wrap vs estimate est %d pdf %d' % (sn, nm, nvis_est, nvis_act))
                            if wrap and nvis_act < nvis_est and tail_ok:
                                warn(bk, 'C3_text_fit', '%s %s: benign print merge est %d pdf %d' % (sn, nm, nvis_est, nvis_act))
                            # F1: 高さ検査は折返し設定と分離 (複数段落は wrap='none' でも適用)。
                            # マージンの適用条件: +3.0 既定 / +2.0 エッジラベル(_l<数字>)のみ
                            if (wrap or len(paras) >= 2) and max(nvis_est, nvis_act) >= 2:
                                need, margin_used = height_need_pt(max(nvis_est, nvis_act), fsz, nm)
                                if H < need - 0.01:
                                    if tail_ok:
                                        warn(bk, 'C3_text_fit', '%s %s: frame height tight h %.1f < need %.1f (render OK, margin +%s)'
                                             % (sn, nm, H, need, margin_used))
                                    elif nm in FIXED_LEAVES or nm in CHANGED_TEXT:
                                        cnt['height_fail'] += 1
                                        fail(bk, 'C3_text_fit', '%s %s: frame height too small h %.1f < need %.1f (margin +%s)'
                                             % (sn, nm, H, need, margin_used))
                                    else:
                                        warn(bk, 'C3_text_fit', '%s %s: frame height below analytic need h %.1f < need %.1f (pre-existing shape, margin +%s)'
                                             % (sn, nm, H, need, margin_used))
                            if nm in FIXED_LEAVES and tf['autosize'] != 0:
                                cnt['autosize_fail'] += 1
                                fail(bk, 'C3_text_fit', '%s %s: fixed leaf autosize=%d' % (sn, nm, tf['autosize']))
                            # F2: クロップはスパン実測右端を含むよう拡張し、台帳に記録する
                            cx0, cy0 = max(0, x0 + 0.5), max(0, y0 + 1.0)
                            cx1, cy1 = min(page.rect.x1, x1 - 0.5), min(page.rect.y1, y1 - 1.0)
                            widened = False
                            if aspans and span_right > cx1 - 0.2:
                                cx1 = min(page.rect.x1, span_right + 2.0)
                                widened = True
                            # 第2次 (記録訂正4): 末尾·行の裁定が必要な図形はクロップ窓を
                            # 上下に 1 行分広げる (crop_pana_s4_t4_b3_l3.png に2行目が
                            # 含まれず裁定できなかった不備の修正)
                            widened_v = False
                            need_adjudication = (tail_mode not in ('ordered-equal', 'empty', 'loss-window-precision')
                                                 or rec['rows_short'] or rec['rows_short_ascii'])
                            if need_adjudication:
                                line_h = fsz * 1.65 * sy + 4.0
                                ny0, ny1 = cy0 - line_h, cy1 + line_h
                                if ny0 < cy0 - 1.0 or ny1 > cy1 + 1.0:
                                    cy0, cy1 = max(0.0, ny0), min(page.rect.y1, ny1)
                                    widened_v = True
                            if cx1 - cx0 > 2 and cy1 - cy0 > 2:
                                fname = 'crop_%s_%s_%s.png' % (bk, SN_TAG[sn], re.sub(r'[^A-Za-z0-9_-]', '_', nm))
                                crops.append((nm, fitz.Rect(cx0, cy0, cx1, cy1), fname, widened, rec['tail_mode']))
                                crops_ledger.append({'file': fname, 'sheet': sn, 'shape': nm,
                                                     'window': [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                                                     'clip': [round(cx0, 1), round(cy0, 1), round(cx1, 1), round(cy1, 1)],
                                                     'widened': widened, 'widened_v': widened_v,
                                                     'widened_reason': ('tail/row adjudication' if widened_v else ''),
                                                     'spill_pt': rec['spill_pt'],
                                                     'text_match': rec['tail_mode']})
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
                    for nm, cr, fname, widened, tmode in crops:
                        try:
                            page.get_pixmap(matrix=fitz.Matrix(4.0, 4.0), clip=cr).save(os.path.join(OUT, fname))
                        except Exception:
                            pass
                    R(bk, 'C8_pdf_roundtrip')['info'][sn] = fit_info
                    doc.close()
                with io.open(os.path.join(OUT, 'strict_text_fit_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(fit_all, f, ensure_ascii=False, indent=1)
                with io.open(os.path.join(OUT, 'strict_orphans_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(orphans, f, ensure_ascii=False, indent=1)
                with io.open(os.path.join(OUT, 'strict_crops_%s.json' % bk), 'w', encoding='utf-8') as f:
                    json.dump(crops_ledger, f, ensure_ascii=False, indent=1)
                R(bk, 'C3_text_fit')['evidence'].append('strict_text_fit_%s.json' % bk)
                R(bk, 'C7_orphans_wrap')['evidence'].append('strict_orphans_%s.json' % bk)
                R(bk, 'C8_pdf_roundtrip')['evidence'].append('strict_crops_%s.json' % bk)
                R(bk, 'C7_orphans_wrap')['info']['known'] = sum(1 for o in orphans if o['class'].startswith('known'))
                R(bk, 'C7_orphans_wrap')['info']['new'] = sum(1 for o in orphans if o['class'] == 'new-regression-candidate')
                # F6: サブチェック状態の確定 (C10 回帰表はここから集約する)
                sub(bk, 'C3_text_fit', 'tail_cjk_ordered',
                    'FAIL' if (cnt['tail_loss'] or cnt['tail_extra'] or cnt['tail_attr_undet']) else 'PASS',
                    'loss=%d extra(dup/addition)=%d attribution_undetermined=%d k4_accepted/undecided=%d'
                    % (cnt['tail_loss'], cnt['tail_extra'], cnt['tail_attr_undet'], cnt['tail_k4']))
                sub(bk, 'C3_text_fit', 'tail_ascii_separate', 'FAIL' if cnt['ascii_fail'] else 'PASS',
                    'loss=%d k4=%d (loss は changed/fixed 以外でも FAIL -- 第2次是正)'
                    % (cnt['ascii_fail'], cnt['ascii_k4']))
                sub(bk, 'C3_text_fit', 'frame_height_multi_para', 'FAIL' if cnt['height_fail'] else 'PASS')
                sub(bk, 'C3_text_fit', 'autosize_fixed_leaves', 'FAIL' if cnt['autosize_fail'] else 'PASS')
                sub(bk, 'C3_text_fit', 'wrap_estimate', wrap_estimate_status(cnt),
                    'unexpected extra wrap (changed/fixed)=%d' % cnt['wrap_extra'])
                sub(bk, 'C8_pdf_roundtrip', 'landscape_1page', 'FAIL' if cnt['page_fail'] else 'PASS')
                sub(bk, 'C8_pdf_roundtrip', 'independent_calibration',
                    'RECORDED', 'mode=%s; notes=%d; detail in strict_full_results.json' % (calib_mode, cnt['calib_note']))
                sub(bk, 'C8_pdf_roundtrip', 'crop_ledger', 'RECORDED',
                    'n=%d; ledger=strict_crops_%s.json' % (len(crops_ledger), bk))
                sub(bk, 'C8_pdf_roundtrip', 'mapping_residual_explained',
                    'FAIL' if cnt['unexplained'] else 'PASS', 'unexplained_cjk=%d' % cnt['unexplained'])
                # 修正5 (第3次): 文字数 (残差) と図形件数 (C3 末尾救済) を別単位で
                # 表示する。単位の異なる数値を合算して「CJK chars」と表示しない
                sub(bk, 'C8_pdf_roundtrip', 'mapping_residual_attribution', 'RECORDED',
                    'attribution-undetermined: residual=%d CJK chars (own窓に無く他図形帰属·'
                    '未帰属スパンで充足される文字) + tail_cases=%d shapes (C3 末尾救済の'
                    '図形件数)。単位が異なるため合算しない。合格根拠にしない。人力裁定待ち'
                    % (cnt['attr_undet_chars'], cnt['attr_undet_cases']))
                if cnt['attr_undet_chars'] or cnt['attr_undet_cases']:
                    warn(bk, 'C8_pdf_roundtrip',
                         '%s-residual: attribution-undetermined = %d CJK chars (residual, char unit) '
                         '+ %d shapes (tail cases, shape unit); units counted separately (not summed); human review pending'
                         % (bk, cnt['attr_undet_chars'], cnt['attr_undet_cases']))
                if cnt['unexplained']:
                    fail(bk, 'C8_pdf_roundtrip', 'unexplained CJK mapping residual: %d chars (see strict_crops ledger)' % cnt['unexplained'])
                R(bk, 'C8_pdf_roundtrip')['info']['residual'] = {k: v for k, v in cnt.items()
                                                                 if k.startswith('unexplained') or k.startswith('attr_undet')
                                                                 or k in ('tail_loss', 'tail_extra', 'tail_k4', 'ascii_fail', 'ascii_k4', 'tail_winprec', 'wrap_extra')}
                R(bk, 'C3_text_fit')['info']['tail_counts'] = {k: v for k, v in cnt.items()
                                                               if k.startswith(('tail', 'ascii'))}
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
    # F6: 回帰表はクラス全体の status を転記せず、実サブチェックから集約する。
    # 要約 (クラス別 status) と回帰表の矛盾を構造的に排除する。
    def sub_status(bk, cls, name):
        r = results.get((bk, cls), {})
        return r.get('subchecks', {}).get(name, {}).get('status', 'NOT-RUN')
    c10 = []
    for bk in ('pana', 'lnb'):
        c10.append({'err': 'autosize refit (ERR-005族)', 'check': "C3 subcheck 'autosize_fixed_leaves'", 'book': bk,
                    'status': sub_status(bk, 'C3_text_fit', 'autosize_fixed_leaves'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'フレーム高不足 (ERR-004族)', 'check': "C3 subcheck 'frame_height_multi_para' (wrap非依存·段落数>=2)", 'book': bk,
                    'status': sub_status(bk, 'C3_text_fit', 'frame_height_multi_para'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'BoundWidth過小評価 (ERR-012)', 'check': "C3 subcheck 'tail_cjk_ordered' (順序付きCJK等値)", 'book': bk,
                    'status': sub_status(bk, 'C3_text_fit', 'tail_cjk_ordered'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'ASCII末尾 (F1追加)', 'check': "C3 subcheck 'tail_ascii_separate'", 'book': bk,
                    'status': sub_status(bk, 'C3_text_fit', 'tail_ascii_separate'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'PDF抽出偽陰性の構造回避 (ERR-004/K4)', 'check': "C8 subcheck 'independent_calibration' (PDF枠線較正) + 'mapping_residual_explained'", 'book': bk,
                    'status': sub_status(bk, 'C8_pdf_roundtrip', 'mapping_residual_explained'), 'evidence': 'strict_crops_%s.json' % bk})
        c10.append({'err': 'pywin32 gen_py 回避 (ERR-005)', 'check': "C2 subcheck 'read_tf_no_silent_skip' + XML直読み", 'book': bk,
                    'status': sub_status(bk, 'C2_inventory', 'read_tf_no_silent_skip'), 'evidence': 'strict_inventory_%s.json' % bk})
        c10.append({'err': 'PrintTitleRows干渉', 'check': "C1 subcheck 'print_title_rows_unset'", 'book': bk,
                    'status': sub_status(bk, 'C1_page_setup', 'print_title_rows_unset'), 'evidence': 'strict_page_setup_%s.json' % bk})
        c10.append({'err': 'PrintArea (A9/B4/④)', 'check': "C1 subcheck 'print_area'", 'book': bk,
                    'status': sub_status(bk, 'C1_page_setup', 'print_area'), 'evidence': 'strict_page_setup_%s.json' % bk})
        c10.append({'err': 'fit往復', 'check': "C8 subcheck 'landscape_1page' + mapping recorded", 'book': bk,
                    'status': sub_status(bk, 'C8_pdf_roundtrip', 'landscape_1page'), 'evidence': 'strict_%s_s2/s3/s4.pdf' % bk})
        c10.append({'err': 'ダイジェストキー一致 (novalue)', 'check': 'cross-book names/geometry digest', 'book': bk,
                    'status': 'PASS' if ok_digest else 'FAIL', 'evidence': 'strict_digest_pana.json/strict_digest_lnb.json'})
        c10.append({'err': 'unexpected extra wrap (F6第2次)', 'check': "C3 subcheck 'wrap_estimate'", 'book': bk,
                    'status': sub_status(bk, 'C3_text_fit', 'wrap_estimate'), 'evidence': 'strict_text_fit_%s.json' % bk})
        c10.append({'err': 'リンク実測', 'check': "C10 subchecks 'link_count'+'link_map'+'link_targets_nonempty'", 'book': bk,
                    'status': link_rows_status([sub_status(bk, 'C10_err_regression', 'link_count'),
                                                sub_status(bk, 'C10_err_regression', 'link_map'),
                                                sub_status(bk, 'C10_err_regression', 'link_targets_nonempty')]),
                    'evidence': 'strict_links_%s.json' % bk})
        c10.append({'err': '既存図形の逆方向比較 (F5)', 'check': "C9 subcheck 'baseline_reverse_23'", 'book': bk,
                    'status': sub_status(bk, 'C9_data_accuracy', 'baseline_reverse_23'), 'evidence': 'strict_data_accuracy_%s.json' % bk})
        c10.append({'err': 'C4豁免の記録と悪化差分 (F4)', 'check': "C4 subcheck 'exemptions_recorded' + worsened_baseline_pairs", 'book': bk,
                    'status': sub_status(bk, 'C4_clearance', 'exemptions_recorded'), 'evidence': 'strict_clearance_%s.json' % bk})
        c10.append({'err': 'C6接続線の期待比較 (F6)', 'check': "C6 subcheck 'xml_com_connector_match' (status=RECORDED)", 'book': bk,
                    'status': sub_status(bk, 'C6_connectors', 'xml_com_connector_match'), 'evidence': 'strict_connectors_%s.json' % bk})
    with io.open(os.path.join(OUT, 'strict_err_regression_table.json'), 'w', encoding='utf-8') as f:
        json.dump(c10, f, ensure_ascii=False, indent=1)

    # ---- aggregation consistency (F6第2次) ----
    # サブチェックに FAIL が残るクラスを PASS のままにしない (失敗注入の
    # 自己検証は --selftest で実施する)
    agg_fixes = enforce_aggregation_consistency(results)
    for bk, cls, old, new in agg_fixes:
        print('AGGREGATION FIX: %s/%s %s -> %s (subcheck FAIL present)' % (bk, cls, old, new))

    # ---- summary ----
    summary = {'generated': datetime.datetime.now().isoformat(timespec='seconds'),
               'books': {}, 'new_issues': [], 'known_issues': KNOWN_P_NOTES,
               'k3': 'resolved (refs crops + per-shape crops generated under strictverify/)',
               'note_f6': 'subchecks are the authoritative granularity; C10 regression table is aggregated from them',
               'note_pass2': '2nd correction pass: tail equality+extra-chars class, ASCII loss unconditional FAIL, '
                             'attribution-connected C3/residual, render-state width+paragraph compare, '
                             'frame calibration above_h correction, selftest (--selftest)'}
    for (bk, cls), r in sorted(results.items()):
        summary['books'].setdefault(bk, {})[cls] = {'status': r['status'],
                                                    'n_viol': len(r['violations']), 'n_warn': len(r['warnings']),
                                                    'subchecks': r.get('subchecks', {})}
        for v in r['violations']:
            summary['new_issues'].append('%s/%s: %s' % (bk, cls, v))
    with io.open(os.path.join(WORK, 'verify_strict_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(OUT, 'strict_full_results.json'), 'w', encoding='utf-8') as f:
        json.dump({'%s/%s' % k: v for k, v in results.items()}, f, ensure_ascii=False, indent=1)

    print('==== RESULT ====')
    for (bk, cls), r in sorted(results.items()):
        print('%-7s %-18s %s (viol=%d warn=%d)' % (bk, cls, r['status'], len(r['violations']), len(r['warnings'])))
        for sname, sv in sorted(r.get('subchecks', {}).items()):
            print('         - %-30s %s' % (sname, sv['status']))
    # 修正4 (第3次): 終了コードと ALL PASS 表示を実際の FAIL 状態 (クラス status
    # を含む) に連動させる。違反メッセージ件数のみの判定は、enforce による
    # クラス FAIL 化 (違反メッセージなし経路) を取りこぼしていた
    nfail, ncls_fail = aggregate_fail_state(results)
    print('TOTAL VIOLATIONS: %d' % nfail)
    print('CLASS FAIL COUNT: %d' % ncls_fail)
    print('SUMMARY -> verify_strict_summary.json')
    if nfail or ncls_fail:
        print('STRICT VERIFY: FAIL (class FAIL=%d, violations=%d)' % (ncls_fail, nfail))
        sys.exit(1)
    print('STRICT VERIFY: ALL PASS')

if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(run_selftest())
    main()
