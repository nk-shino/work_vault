# -*- coding: utf-8 -*-
"""活動テーマ進捗管理表(下期)への記載: 10月セル+アクション列+シート名変更。
XML 直接編集で drawing1.xml 等を保護する（openpyxl は図形を落とすため不使用）。"""
import zipfile, glob, os, re, shutil, sys

src = sorted(glob.glob(os.environ['TEMP'] + '/theme_backup_*.xlsx'))[-1]
out = os.environ['TEMP'] + '/theme_new.xlsx'

texts = {
    'AM14': '管理手順書案を作成（10/15・未承認）。10/19の三者レビュー準備中',
    'AY14': ('PanaCIM/LNBの管理手順書案を実物様式（0494-913473 P1/P2）に沿って作成した。'
             '10/15時点で未承認。管理書の草案には再起動手順の原文転記とデータフローの整理を反映済みで、'
             '点検項目と判定基準は10/14会議で持ち寄り案を提示した。確定は次回会議以降になる。'
             '10/19の三者レビューと10/21の作成チーム確認に向けて、実物資料（0494-912039(06)）との'
             '突合検証とレビュー用資料を準備している。初版登録は12月末まで。'),
    'AM20': '0確認マクロは採用版を確定。整合性検証完了（10/13）。ver2の実機検証は未',
    'AY20': ('現行棚卸セットの照合を進め、0確認マクロは採用版（完走版）を確定した。'
             '10/13の整合性検証では、10/02版CSVの再計算（29,345行・0確認7,155件）が記録値と一致する'
             'ことをSHA-256の照合込みで確認済み。運用確定質問票（Q1〜Q35）の回答も記入済み。'
             'ただし正本（0確認マクロ_ver2.xlsm）への反映は未実施で、今後の作業になる。'
             '棚卸本番は実績のある旧来運用で遂行し、ver2は試し実行10件から段階的に検証する方針。'
             'その前提として、固定マスタへの到達確認とリール消費の取消可否の現場確認が残っている。'),
    'AM26': 'ツール・手順書を保管庫へ整備（10/8）。TOOL.xlam実機確認は未実施',
    'AY26': ('ジョブ作成業務のツールと手順書を保管庫へ整備した（10/8・31ファイル）。'
             '現行は不足部品リスト作成（ver7・原本と製品別5本）。容量計算ツール（TOOL.xlam）には'
             '「本体」と「コピー」の2版があり、実機で動作している版の確認が未了。この確認が要る。'
             '鹿島品目の導入に向けては、不足部品計算リストB列修正の経緯資料化と、'
             '品目選定システム改修の検討着手が課題。'),
}

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

zin = zipfile.ZipFile(src)
sheet = zin.read('xl/worksheets/sheet1.xml').decode('utf-8')
wbxml = zin.read('xl/workbook.xml').decode('utf-8')

# 1) sheet rename (上期 -> 下期, trailing space kept)
assert '【上期】' in wbxml, 'sheet name pattern missing'
wbxml_new = wbxml.replace('【上期】', '【下期】')

# 2) cell edits
for coord, text in texts.items():
    col = re.match(r'([A-Z]+)(\d+)', coord).group(1)
    rn = re.match(r'([A-Z]+)(\d+)', coord).group(2)
    m = re.search(r'<row r="%s"[^>]*>.*?</row>' % rn, sheet, re.S)
    assert m, 'row not found: ' + rn
    row = m.group(0)
    new_cell = '<c r="%s" s="11" t="inlineStr"><is><t>%s</t></is></c>' % (coord, esc(text)) if col == 'AM' \
        else '<c r="%s" s="44" t="inlineStr"><is><t>%s</t></is></c>' % (coord, esc(text))
    cm = re.search(r'<c r="%s"[^>]*?(?:/>|>.*?</c>)' % coord, row, re.S)
    if cm:
        row_new = row.replace(cm.group(0), new_cell)
    else:
        # insert keeping column order
        cells = re.findall(r'<c r="([A-Z]+)\d+"[^>]*?(?:/>|>.*?</c>)', row, re.S)
        import functools
        def colnum(c):
            n = 0
            for ch in c: n = n * 26 + (ord(ch) - 64)
            return n
        target = colnum(col)
        parts = re.split(r'(<c r="[A-Z]+\d+"[^>]*?(?:/>|>.*?</c>))', row, flags=re.S)
        # parts: [pre, cell, mid, cell, ..., post]
        outrow = ''
        inserted = False
        for i, p in enumerate(parts):
            if re.match(r'<c r="([A-Z]+)\d+"', p or ''):
                cc = re.match(r'<c r="([A-Z]+)\d+"', p).group(1)
                if not inserted and colnum(cc) > target:
                    outrow += new_cell
                    inserted = True
                outrow += p
            else:
                outrow += p
        if not inserted:
            outrow += new_cell
        row_new = outrow
    sheet = sheet.replace(m.group(0), row_new)

zout = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == 'xl/worksheets/sheet1.xml':
        data = sheet.encode('utf-8')
    elif item.filename == 'xl/workbook.xml':
        data = wbxml_new.encode('utf-8')
    zout.writestr(item, data)
zout.close()
zin.close()

# verify with openpyxl (read-only check)
import openpyxl
wb = openpyxl.load_workbook(out)
ws = wb.worksheets[0]
print('sheetname:', ws.title)
for coord in texts:
    v = ws[coord].value
    ok = v == texts[coord]
    print(coord, 'OK' if ok else 'MISMATCH', (str(v)[:40] + '…') if v and len(str(v)) > 40 else v)
# drawing preserved?
z2 = zipfile.ZipFile(out)
print('drawing kept:', 'xl/drawings/drawing1.xml' in z2.namelist())
