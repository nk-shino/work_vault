async (page) => {
  // 用語集アプリの動作確認(1/3): 実在の業務用語を「用語を登録」画面のフォームから登録する。
  // 実行: Playwright MCP の browser_run_code_unsafe に filename で渡す。サーバーは http://127.0.0.1:8000
  // 定義は一般的な知識の範囲で書いた。用例は作例で、出典欄にその旨を入れる。
  // 「棚卸」は同じ見出しで2回登録し、語義が2つになることを確かめる。
  // 「リフロ」は表記ゆれの重複登録で、後の手順でアーカイブする。
  const BASE = 'http://127.0.0.1:8000';
  const SRC = '動作確認用の作例（2026-11-05）';
  const TERMS = [
    { headword: '表面実装', reading: 'ひょうめんじっそう', english: 'surface mount technology', abbreviation: 'SMT', context_tag: '製造',
      definition: 'プリント基板の表面に電子部品を載せ、はんだで接合する実装方式。部品のリードを基板の穴に通して接合する挿入実装とは区別する。',
      excerpt: 'この基板は表面実装の部品だけで構成されているため、手はんだの工程はありません。' },
    { headword: 'リフロー', reading: 'りふろー', english: 'reflow soldering', context_tag: '製造',
      definition: 'はんだペーストを印刷して部品を載せた基板を炉で加熱し、はんだを溶かして接合する工程。加熱の条件は温度プロファイルとして管理する。',
      excerpt: 'リフロー後の外観検査で、ブリッジが2か所見つかりました。',
      scope_note: '炉そのもの（リフロー炉）を指して使うこともある。' },
    { headword: 'はんだペースト', reading: 'はんだぺーすと', english: 'solder paste', context_tag: '材料',
      definition: '粉末状のはんだとフラックスを練り合わせたペースト状の材料。メタルマスクを使って基板のランドに印刷する。',
      excerpt: '冷蔵庫から出したはんだペーストは、常温に戻してから開封してください。' },
    { headword: 'メタルマスク', reading: 'めたるますく', english: 'stencil', context_tag: '製造',
      definition: 'はんだペーストの印刷に使う薄い金属板。部品を接合する位置に合わせて開口部が設けてある。',
      excerpt: 'メタルマスクの開口部が詰まると、はんだの量が不足します。' },
    { headword: '自動光学検査', reading: 'じどうこうがくけんさ', english: 'automated optical inspection', abbreviation: 'AOI', context_tag: '品質',
      definition: 'カメラで撮影した基板の画像を基準と照らし合わせ、部品の欠品や位置ずれ、はんだ付けの異常を自動で判定する検査。',
      excerpt: 'AOI で不良と判定された基板は、目視で確認してから修理に回します。' },
    { headword: 'X線検査', reading: 'えっくすせんけんさ', english: 'automated X-ray inspection', abbreviation: 'AXI', context_tag: '品質',
      definition: 'X線の透過画像を使い、BGA のように外から見えないはんだ接合部を検査する方法。',
      excerpt: 'BGA の接合状態は外観では確認できないため、X線検査で確かめます。' },
    { headword: 'フィーダ', reading: 'ふぃーだ', context_tag: '製造',
      definition: 'テープなどに収めた部品を、マウンタへ1個ずつ送り出す装置。部品の種類ごとに用意し、マウンタの決められた位置に取り付ける。',
      excerpt: '段取り替えの前に、次の機種で使うフィーダを準備しておきます。' },
    { headword: 'マウンタ', reading: 'まうんた', english: 'chip mounter', context_tag: '製造',
      definition: 'フィーダから部品を吸着して取り出し、基板上の決められた位置に載せる装置。',
      excerpt: 'マウンタの吸着ミスが続くときは、ノズルの汚れを確認します。',
      scope_note: '「実装機」と呼ぶ部署もある。' },
    { headword: '段取り替え', reading: 'だんどりがえ', english: 'changeover', context_tag: '製造',
      definition: '生産する機種を切り替えるために、部品・治具・プログラムなどを入れ替える作業。作業中はラインが止まるため、時間の短縮が改善の対象になる。',
      excerpt: '午後の段取り替えは30分以内を目標にしています。' },
    { headword: '部品表', reading: 'ぶひんひょう', english: 'bill of materials', abbreviation: 'BOM', context_tag: '設計',
      definition: '製品を構成する部品の品番・名称・数量をまとめた一覧。設計・購買・製造が同じ部品を指すときの基準になる。',
      excerpt: '設計変更で部品表が改版されたため、手配数を見直しました。' },
    { headword: '設計変更通知', reading: 'せっけいへんこうつうち', english: 'engineering change notice', abbreviation: 'ECN', context_tag: '設計',
      definition: '図面や部品表を変更したことを関係部署へ知らせる文書。変更の内容と理由、適用する時期を記載する。',
      excerpt: 'ECN の適用ロットを確認してから、現品を入れ替えます。' },
    { headword: 'ロット', reading: 'ろっと', english: 'lot', context_tag: '品質',
      definition: '同じ条件で続けて生産した製品、または同時に受け入れた材料のまとまり。不具合が出たときは、影響の範囲をロット単位で調べる。',
      excerpt: '同じロットのはんだペーストを使った基板を、抜き取りで検査しました。' },
    { headword: 'トレーサビリティ', reading: 'とれーさびりてぃ', english: 'traceability', context_tag: '品質',
      definition: '製品や部品が、いつ・どこで・どの材料と設備で作られたかを記録し、後からたどれるようにすること。',
      excerpt: 'トレーサビリティを確保するため、基板ごとにシリアル番号を記録しています。' },
    { headword: '棚卸', reading: 'たなおろし', english: 'stocktaking', context_tag: '経理',
      definition: '決算のために、期末時点の在庫の数量を確かめ、在庫の金額を確定させること。',
      excerpt: '期末の棚卸で確定した在庫金額を、決算に反映します。' },
    { headword: '棚卸', context_tag: '物流',
      definition: '保管場所の現品を数え、帳簿上の在庫数と合っているかを確かめる作業。',
      excerpt: '棚卸で現品が帳簿より2個少なかったため、出庫の記録を確認しました。',
      scope_note: '月末に行う現品の確認だけを指して使うことが多い。' },
    { headword: 'リフロ', reading: 'りふろ', context_tag: '製造',
      definition: 'はんだを溶かして部品を接合する工程。',
      excerpt: 'リフロの温度を確認してください。' },
  ];
  const FIELDS = ['headword', 'definition', 'excerpt', 'context_tag', 'scope_note', 'reading', 'english', 'abbreviation'];
  const out = [];
  for (const t of TERMS) {
    await page.goto(BASE + '/new');
    for (const k of FIELDS) {
      await page.fill('#' + k, t[k] || '');
    }
    await page.fill('#source_ref', SRC);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'load' }),
      page.locator('form.edit button[type=submit]').click(),
    ]);
    const err = page.locator('p.error');
    const senses = await page.locator('article.sense').count();
    out.push({
      headword: t.headword,
      url: page.url().replace(BASE, ''),
      result: (await err.count()) ? 'NG: ' + (await err.first().innerText()) : 'OK',
      senses,
    });
  }
  return out;
}
