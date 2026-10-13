# 用語集PoC Phase 0：社用PCで確認すること

作成: 2026-09-24

用語集PoCは社用PCで動かして検証するのが前提。コードは別の場所で書くが、動くかどうかの判定は社用PCで下す。そのために、社用PCの環境を先に知っておく必要がある。

## やること

- [ ] 同じフォルダの `envcheck.py` を社用PCで実行し、出力の20行を控える
  - コマンド: `python envcheck.py`
  - 標準ライブラリだけで動き、ネットワークには出ない。パス・ユーザー名・プロキシのアドレスは出力しないので、そのまま共有してよい
  - `python` が見つからなければ、それ自体が結果。「Pythonなし」と控える
- [ ] 私物PCで書いたコードを社用PCへ持ち込んでよいか、規程を確認する
  - データはすべて明らかに架空のもので、社内の情報は入れない
  - それでも、コードやソフトの持ち込み自体を禁止している職場はある。これが一番大きな制約になる
- [ ] 持ち込めるとしたら、どの経路を使うかを決める（git のリモート / 業務USB / その他）

## 持ち込めた後にやること（Phase 0 は実装済み）

コード一式は開発PCの `C:\Projects\glossary-poc` にある。中身と結果は同じフォルダの「用語集PoC_Phase0_実装報告」を参照。社用PCでは、上から順に実行して**どこで止まったか**を控える。

- [ ] `python tasks.py setup`：仮想環境の作成 → 依存の導入 → DB の作成
  - pip が社外に出られない場合は、開発PCで `python tasks.py wheelhouse wheels --python-version <社用PCの版>` を実行し、できた `wheels` フォルダも一緒に運ぶ。社用PCでは `python tasks.py setup --wheelhouse wheels` を実行する（約100MB）
- [ ] `python tasks.py check`：lint・型チェック・テスト。開発PCでは105件がすべて通った
- [ ] `python tasks.py demo`：架空メール50通で最初から最後まで通す
- [ ] `python tasks.py serve --db data/demo/glossary-demo.db`：ブラウザで http://127.0.0.1:8000 を開き、用語が13件並ぶことと、「竜舎」の詳細に赤枠の「混同注意」が出ることを確かめる

## 結果で何が決まるか

| 確認項目 | 決まること |
|---|---|
| Pythonのバージョン | 3.11 未満、またはPythonが無い場合は設計の前提が崩れる。Pythonを入れてもらえるかどうかが最初の論点になる |
| pip が社外に出られるか（プロキシ・社内ミラー・SSL検査） | 出られない場合は、依存パッケージを外で取得してまとめて運ぶ。SudachiPy の辞書だけで約70MBある |
| 文字コード（cp932 か） | ファイルの読み書きはすべて文字コードを明示して作る。コンソールへの出力も、cp932 で表示が崩れない作りにする |
| make・Docker の有無 | どちらも前提にしない。実行は `python tasks.py setup/test/lint/serve`、DBはSQLiteにする |

## すでに決めたこと（理由つき）

- **DBはSQLite。** 社用PCにDockerがあるとは限らないため。「用例のない定義は保存できない」という制約は、語義と用例の2つの表にまたがるので、CHECK制約では書けない。そこで、語義と用例を同時に受け取る専用の入口（INSTEAD OF トリガー付きのビュー）でしか書き込めないようにして担保する。本番でPostgreSQLに移すときは、この部分を書き直す必要がある
- **タスクは `python tasks.py`。** make は入っていない前提。PowerShell 5.1 は、BOMなしのUTF-8で書いたスクリプトを読むと文字化けするので、.ps1 も使わない
- **sentence-transformers は Phase 0 では骨組みだけにする。** 初めて使うときにモデルをインターネットから取りに行くので、「オフラインで完結」という方針と両立しないため
- **LLM は、社内の LiteLLM ゲートウェイの仕様が確定するまでモックで動かす。** それ以外の中継サービスは使わない


---
実行結果
```
Python        : 3.14.6 64bit
py>=3.11      : True
OS            : Windows 11 10.0.26200
locale enc    : cp932
stdout enc    : utf-8
PYTHONUTF8    : unset
SQLite        : 3.50.4
pip           : pip 26.1.2
pip config    : no
HTTP_PROXY    : unset
HTTPS_PROXY   : unset
PIP_INDEX_URL : unset
REQUESTS_CA_BUNDLE: unset
SSL_CERT_FILE : unset
git           : yes
make          : no
docker        : yes
uv            : no
PowerShell    : 5.1.26100.9444
home writable : yes
```
