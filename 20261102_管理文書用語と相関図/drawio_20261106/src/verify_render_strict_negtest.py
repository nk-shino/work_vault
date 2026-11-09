# -*- coding: utf-8 -*-
"""verify_render_strict_negtest.py -- Gate 1 第2次是正の負例検証 (N1-N6).

第2次是正 (再審査 attempt 2 指摘) により:
  - N1/N2 は純関数の戻り値だけでなく、本番の severity·サブチェック分類
    (tail_severity) を通して確認する (F1·ウ)
  - N3 を拡張: 幅変更·改行(段落)構造変更·baseline項目欠落の3ケースを追加 (F3)
  - N6 を新設: 対象図形の末尾欠落を隣接図形の同じ文字列が補填するケース。
    旧実装 (広域窓の multiset>= 救済) は通し、新実装は 'attribution-undetermined'
    (帰属未確定) として遮断する (F2·エ)。本番 severity で確認する

結果: strictverify/reconsider/negative_test_results.json
終了コード: 全件検出=0 / 未検出あり=1
"""
import sys, os, json, io, datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_render_strict as vrs

OUTDIR = os.path.join(vrs.OUT, 'reconsider')
os.makedirs(OUTDIR, exist_ok=True)

results = []

def old_tail_check(exp_text, got_text):
    """旧実装 (F1是正前) の末尾判定を再現する (比較証明用)"""
    exp_cjk, got_cjk = vrs.cjk(exp_text), vrs.cjk(got_text)
    if not exp_cjk:
        return True
    ce, cg = Counter(exp_cjk), Counter(got_cjk)
    ok = all(cg[ch] >= n for ch, n in ce.items())
    last4 = exp_cjk[-4:]
    if ok and last4 and last4 not in got_cjk:
        ok = False
    return ok

def old_wide_rescue(exp_text, own_text, wide_text):
    """旧実装 (第1次是正) の広域窓救済を再現する: 広域窓の抽出文で multiset>=
    (包含) を満たせば tail_ok=True にしていた (帰属を確認しない)"""
    ce, cg = Counter(vrs.cjk(exp_text)), Counter(vrs.cjk(wide_text))
    return all(cg[ch] >= n for ch, n in ce.items())

def max_severity(items):
    if any(i['severity'] == 'FAIL' for i in items):
        return 'FAIL'
    return 'WARN' if items else 'PASS'

# ---- N1 (F1): ASCII末尾欠落 -- 本番 severity 経路で確認 -------------------
# g2_e_e17_l は changed/fixed ではない。第1次実装では警告に降格されていた
# (実例: g2_e_e17_l ascii_mode='loss' が警告)。第2次で無条件 FAIL。
exp_t1 = '様式番号の確認 NR4030-0300-A3'
got_t1 = '様式番号の確認 NR4030-0300-'          # 末尾の -A3 が描画で欠落
sev1 = vrs.tail_severity('g2_e_e17_l', 'ordered-equal', 'loss', exp_t1, render_same=False)
n1_fail = [i for i in sev1 if i['severity'] == 'FAIL' and i['subcheck'] == 'tail_ascii_separate']
results.append({
    'id': 'N1', 'target_fix': 'F1 (ASCII loss の警告降格廃止·本番severity経路)',
    'path': 'production severity (tail_severity) + subcheck tail_ascii_separate',
    'fixture': {'shape': 'g2_e_e17_l (changed/fixed 以外)', 'exp_text': exp_t1, 'got_text': got_t1,
                'note': 'ASCII末尾 -A3 のみ欠落した合成PDF抽出'},
    'expected': "severity FAIL / subcheck tail_ascii_separate (警告降格の廃止)",
    'actual': {'severity_items': sev1, 'ascii_tail': vrs.ascii_tail(exp_t1),
               'ascii_check': vrs.ascii_tail_check(exp_t1, got_t1)},
    'old_behavior_would_pass': True,   # 第1次実装: 警告に降格 (changed/fixed 以外)
    'detected': bool(n1_fail),
})

# ---- N2 (F1): CJK重複補填 -- 別異常クラス (K4疑いではない) を本番 severity で ---
exp_t2 = '再起動の確認'
got_t2 = '再起動の確認起动'.replace('动', '動')   # 期待文字をすべて含むが「起」を重複補填
tc2 = vrs.tail_check_ordered(exp_t2, got_t2)
sev2 = vrs.tail_severity('g3_n08_txt', tc2['mode'], 'ok', exp_t2, render_same=False)
n2_fail = [i for i in sev2 if i['severity'] == 'FAIL' and i['code'] == 'tail_extra_chars']
results.append({
    'id': 'N2', 'target_fix': 'F1 (multiset 等値化·重複/追加は別異常クラス)',
    'path': 'production severity (tail_severity) + subcheck tail_cjk_ordered',
    'fixture': {'exp_text': exp_t2, 'got_text': got_t2,
                'note': '期待文字はすべて含むが「起」が重複補填 (旧 Counter>= は通過)'},
    'expected': "mode='extra-chars(dup/addition)' (K4疑いではない別異常クラス) + severity FAIL",
    'actual': {'mode': tc2['mode'], 'ordered_ok': tc2['ordered_ok'], 'multiset_ok': tc2['multiset_ok'],
               'severity_items': sev2},
    'old_behavior_would_pass': bool(old_tail_check(exp_t2, got_t2)),
    'detected': (tc2['mode'] == 'extra-chars(dup/addition)' and bool(n2_fail)),
})

# ---- N3 (F3): 描画状態一致の比較拡張 (4ケース) -----------------------------
T3 = '上位スイッチへの疎通確認ラベル'
base3 = {'path': 'grp/g2_e_e17_l', 'text': T3, 'h': 26.02, 'w': 100.0, 'autosize': 1, 'wordwrap': -1}
# (a) 高さ変更 (e17_l 実例と同型)
c3a = vrs.classify_render_state(base3, T3, 39.3, 100.0, 2, -1)
# (b) 幅変更 (高さは不変)
c3b = vrs.classify_render_state(base3, T3, 26.02, 120.0, 1, -1)
# (c) 改行(段落)構造変更 -- norm() は改行を除去するため旧実装は同一扱いだった
base3c = dict(base3, text='甲\n乙')
c3c = vrs.classify_render_state(base3c, '甲乙', 26.02, 100.0, 1, -1)
# (d) baseline 項目欠落 -- 「一致」にしない (比較不能)
base3d = {k: v for k, v in base3.items() if k != 'w'}
c3d = vrs.classify_render_state(base3d, T3, 26.02, 100.0, 1, -1)
results.append({
    'id': 'N3', 'target_fix': 'F3 (描画状態一致: 幅+改行/段落構造·baseline欠落は比較不能)',
    'path': 'classify_render_state (main と同一関数)',
    'fixture': {'baseline': {'h': 26.02, 'w': 100.0, 'autosize': 1, 'wordwrap': -1},
                'cases': ['h change 26.02->39.3', 'w change 100->120', "text '甲\\n乙' vs '甲乙'",
                          'baseline lacks w field']},
    'expected': "(a)(b) render-changed-origin-unknown / (c) text-changed (改行構造の同値扱い廃止) / "
                "(d) render-state-not-comparable (一致にしない)",
    'actual': {'h_change': c3a, 'w_change': c3b, 'newline_change': c3c, 'baseline_field_missing': c3d},
    'old_behavior_would_pass': True,   # 旧実装: (a)以外は高さのみ·改行除去·欠落項目は無視で「一致」
    'detected': (c3a == 'render-changed-origin-unknown' and c3b == 'render-changed-origin-unknown'
                 and c3c == 'text-changed' and c3d == 'render-state-not-comparable'),
})

# ---- N4 (F5): 両冊共通の既存図形欠落 ------------------------------------
baseline4 = [
    {'path': 'g2_n01', 'text': ''}, {'path': 'g2_n01/g2_n01_txt', 'text': 'ノード1'},
    {'path': 'g2_n02', 'text': ''}, {'path': 'g2_n02/g2_n02_txt', 'text': 'ノード2'},
]
cur_names4 = {'g2_n01', 'g2_n01_txt', 'g2_n02'}          # g2_n02_txt が欠落
cur_texts4 = {'g2_n01_txt': 'ノード1'}
miss4 = vrs.reverse_baseline_missing(baseline4, cur_names4, cur_texts4)
results.append({
    'id': 'N4', 'target_fix': 'F5 (ベースライン→現在の逆方向比較)',
    'path': 'reverse_baseline_missing (C9 subcheck baseline_reverse_23 から呼ばれる本番関数)',
    'fixture': {'baseline_names': [e['path'] for e in baseline4],
                'current_names': sorted(cur_names4), 'note': 'ベースラインに存在する g2_n02_txt を現在冊から削除'},
    'expected': '欠落 g2_n02_txt を検出 (reason=shape-missing)',
    'actual': {'missing': miss4},
    'old_behavior_would_pass': True,   # 旧実装は順方向比較のみで存在しない図形は比較対象外
    'detected': any(m['name'] == 'g2_n02_txt' and m['reason'] == 'shape-missing' for m in miss4),
})

# ---- N5 (F2): 隣接行混入 (スパン単位帰属) --------------------------------
wins5 = {'shapeA': (100.0, 100.0, 300.0, 120.0), 'shapeB': (100.0, 122.0, 300.0, 142.0)}
spans5 = [
    (110.0, 105.0, 200.0, 115.0, 'A行目のテキスト'),      # A 内 -> A に帰属
    (110.0, 127.0, 200.0, 137.0, 'B行目のテキスト'),      # B 内 -> B に帰属
    (110.0, 112.0, 200.0, 128.0, 'またがりスパン'),        # A/B 両方にまたがる (混入候補)
]
attrib5, un5, strad5 = vrs.attribute_spans(spans5, wins5)
assign = {nm: len(sp) for nm, sp in attrib5.items()}
n_clean = sum(1 for sp in spans5[:2]
              if any(sp in attrib5[nm] for nm in attrib5))
results.append({
    'id': 'N5', 'target_fix': 'F2 (スパン単位帰属·隣接行混入の検出)',
    'path': 'attribute_spans (C3本文比較·残差検査に接続済み)',
    'fixture': {'windows': wins5, 'spans': [list(s) for s in spans5],
                'note': '3つ目のスパンは A/B 両窓にまたがる (行境界をまたぐ混入)'},
    'expected': 'またがりスパンが straddle として検出され、正常2スパンは正しい窓に帰属',
    'actual': {'assigned': assign, 'unattributed': len(un5), 'straddles': strad5},
    'old_behavior_would_pass': True,   # 旧実装は行y座標の窓内選別のみでまたがりを判定しない
    'detected': (len(strad5) == 1 and strad5[0]['assigned'] in wins5
                 and assign.get('shapeA', 0) >= 2 and assign.get('shapeB', 0) >= 1 and n_clean == 2),
})

# ---- N6 (F2·新設): 隣接図形の同文字列による末尾補填を遮断 -----------------
# 対象図形 A の末尾「先」が描画で欠落し、隣接図形 B の窓内の「先」が
# 広域窓救済で A の末尾のように扱われるケース。
# 旧実装 (第1次): 広域窓の文字列で multiset>= が満たされ tail_ok=True (通過)。
# 新実装: 「先」は B 帰属スパンにしかない -> 'attribution-undetermined' (帰属未確定)
# となり tail_ok=False。本番 severity では FAIL (changed/fixed でない図形も)。
exp_a = '認証情報の保管先'
own_span_a = [(110.0, 105.0, 290.0, 115.0, '認証情報の保管')]     # A 窓内·末尾「先」を欠く
other_span_b = [(110.0, 175.0, 290.0, 185.0, '先の確認を要する')]  # B 窓内·「先」を含む
# A の窓に帰属した抽出 (attribute_spans と同じ帰属を模した合成)
own_text_a = ''.join(s[4] for s in own_span_a)
wide_spans = [(own_span_a[0][4], 'own'), (other_span_b[0][4], 'other')]
vr6 = vrs.tail_rescue(exp_a, own_text_a, wide_spans)
sev6 = vrs.tail_severity('g3_n12_txt', vr6['mode'], 'ok', exp_a, render_same=False)
old_rescue6 = old_wide_rescue(exp_a, own_text_a,
                              own_span_a[0][4] + other_span_b[0][4])
results.append({
    'id': 'N6', 'target_fix': 'F2 (隣接図形の同文字列による末尾補填の遮断·帰属未確定)',
    'path': 'production tail_rescue + tail_severity (本番経路)',
    'fixture': {'exp_text_A': exp_a, 'own_window_text': own_text_a,
                'adjacent_window_text': other_span_b[0][4],
                'note': 'A の末尾「先」は描画で欠落·B の窓内の「先」が広域窓に存在する'},
    'expected': "tail_rescue mode='attribution-undetermined' (tail_ok=False) + 本番 severity FAIL",
    'actual': {'tail_rescue': vr6, 'severity_items': sev6},
    'old_behavior_would_pass': bool(old_rescue6),   # 旧: 広域窓 multiset>= で tail_ok=True
    'detected': (vr6['mode'] == 'attribution-undetermined' and vr6['tail_ok'] is False
                 and any(i['severity'] == 'FAIL' and i['subcheck'] == 'tail_cjk_ordered' for i in sev6)),
})

# ---- 出力 ----------------------------------------------------------------
all_detected = all(r['detected'] for r in results)
out = {'generated': datetime.datetime.now().isoformat(timespec='seconds'),
       'harness': 'verify_render_strict.py (Gate1第2次是正 F1/F2/F3/F5)',
       'n_fixtures': len(results), 'n_detected': sum(1 for r in results if r['detected']),
       'all_detected': all_detected, 'results': results}
path = os.path.join(OUTDIR, 'negative_test_results.json')
with io.open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for r in results:
    print('%s [%s] detected=%s old_would_pass=%s' % (r['id'], r['target_fix'], r['detected'], r['old_behavior_would_pass']))
    print('    expected: %s' % r['expected'])
    print('    actual: %s' % json.dumps(r['actual'], ensure_ascii=False)[:260])
print('NEGATIVE TEST: %d/%d detected -> %s' % (out['n_detected'], out['n_fixtures'], path))
sys.exit(0 if all_detected else 1)
