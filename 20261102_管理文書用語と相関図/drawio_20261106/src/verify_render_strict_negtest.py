# -*- coding: utf-8 -*-
"""verify_render_strict_negtest.py -- Gate 1 是正 (F1〜F6) の負例検証.

合成フィクスチャ 5 種が各是正で検出されることを確認する:
  N1 (F1) ASCII末尾欠落      -- 旧実装は CJK のみ検査するため見逃す
  N2 (F1) CJK重複補填        -- 旧実装 (Counter>= + 末尾4字部分一致) は通過する
  N3 (F3) 本文不変の高さ変更  -- 旧実装は「テキスト不変=既存」で警告に格下げする
  N4 (F5) 既存図形の欠落      -- 旧実装は順方向比較のみで見逃す
  N5 (F2) 隣接行混入          -- スパン単位帰属で複数窓またがりを検出する

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

# ---- N1 (F1): ASCII末尾欠落 --------------------------------------------
exp_t1 = '様式番号の確認 NR4030-0300-A3'
got_t1 = '様式番号の確認 NR4030-0300-'          # 末尾の -A3 が描画で欠落
n1_new = vrs.ascii_tail_ok(exp_t1, got_t1)
n1_old = old_tail_check(exp_t1, got_t1)          # 旧: CJK等値のみなので True (=見逃し)
results.append({
    'id': 'N1', 'target_fix': 'F1 (ASCII末尾の別確認)',
    'fixture': {'exp_text': exp_t1, 'got_text': got_t1, 'note': 'ASCII末尾 -A3 のみ欠落した合成PDF抽出'},
    'expected': 'ascii_tail_ok == False (検出)',
    'actual': {'ascii_tail': vrs.ascii_tail(exp_t1), 'ascii_ok': n1_new, 'new_ordered_cjk_mode': vrs.tail_check_ordered(exp_t1, got_t1)['mode']},
    'old_behavior_would_pass': bool(n1_old),
    'detected': (n1_new is False),
})

# ---- N2 (F1): CJK重複補填 (順序不一致を文字数の補填で偽装) --------------
exp_t2 = '再起動の確認'
got_t2 = '再起動の確認起動'                      # 多い文字を重複補填し multiset は満たす
tc2 = vrs.tail_check_ordered(exp_t2, got_t2)
n2_old = old_tail_check(exp_t2, got_t2)          # 旧: Counter>= 且つ 末尾4字「動の確認」が部分一致するため True
results.append({
    'id': 'N2', 'target_fix': 'F1 (順序付きCJK等値への回帰)',
    'fixture': {'exp_text': exp_t2, 'got_text': got_t2, 'note': '文字種はすべて含むが順序が不一致 (重複補填)'},
    'expected': "tail_check_ordered.mode == 'multiset-only(k4-suspect)' (順序不一致を検出)",
    'actual': {'mode': tc2['mode'], 'ordered_ok': tc2['ordered_ok'], 'multiset_ok': tc2['multiset_ok']},
    'old_behavior_would_pass': bool(n2_old),
    'detected': (tc2['mode'] != 'ordered-equal') and (tc2['ordered_ok'] is False),
})

# ---- N3 (F3): 本文不変の高さ変更 (e17_l 実例と同型) ---------------------
T3 = '上位スイッチへの疎通確認ラベル'
base3 = {'path': 'grp/g2_e_e17_l', 'text': T3, 'h': 26.02, 'autosize': 1, 'wordwrap': -1}
cls3_new = vrs.classify_render_state(base3, T3, 39.3, 2, -1)
cls3_old = 'preexisting' if base3['text'] == T3 else 'text-changed'   # 旧: テキスト不変=既存扱い
results.append({
    'id': 'N3', 'target_fix': 'F3 (描画状態の一致で既存扱いを判定)',
    'fixture': {'baseline': {'h': 26.02, 'autosize': 1, 'wordwrap': -1},
                'current': {'h': 39.3, 'autosize': 2, 'wordwrap': -1},
                'text': 'both same', 'note': '本文不変のまま高さ 26.02->39.3 に成長した合成ケース'},
    'expected': "classify_render_state == 'render-changed-origin-unknown' (既存扱いにしない)",
    'actual': {'classify_render_state': cls3_new},
    'old_behavior_would_pass': cls3_old == 'preexisting',
    'detected': (cls3_new == 'render-changed-origin-unknown'),
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
    'fixture': {'windows': wins5, 'spans': [list(s) for s in spans5],
                'note': '3つ目のスパンは A/B 両窓にまたがる (行境界をまたぐ混入)'},
    'expected': 'またがりスパンが straddle として検出され、正常2スパンは正しい窓に帰属',
    'actual': {'assigned': assign, 'unattributed': len(un5), 'straddles': strad5},
    'old_behavior_would_pass': True,   # 旧実装は行y座標の窓内選別のみでまたがりを判定しない
    'detected': (len(strad5) == 1 and strad5[0]['assigned'] in wins5
                 and assign.get('shapeA', 0) >= 2 and assign.get('shapeB', 0) >= 1 and n_clean == 2),
})

# ---- 出力 ----------------------------------------------------------------
all_detected = all(r['detected'] for r in results)
out = {'generated': datetime.datetime.now().isoformat(timespec='seconds'),
       'harness': 'verify_render_strict.py (Gate1是正 F1-F6)',
       'n_fixtures': len(results), 'n_detected': sum(1 for r in results if r['detected']),
       'all_detected': all_detected, 'results': results}
path = os.path.join(OUTDIR, 'negative_test_results.json')
with io.open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for r in results:
    print('%s [%s] %s -> detected=%s' % (r['id'], r['target_fix'], r['expected'], r['detected']))
    print('    actual: %s' % json.dumps(r['actual'], ensure_ascii=False)[:200])
print('NEGATIVE TEST: %d/%d detected -> %s' % (out['n_detected'], out['n_fixtures'], path))
sys.exit(0 if all_detected else 1)
