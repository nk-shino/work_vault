# Default workspace
This is the default workspace. The rules below are a default starting point; adapt them to how the user actually works.

- When starting a new topic, create a `YYYYMMDD_<topic>/` folder and work inside it
- Put generated files in the matching topic folder rather than directly at the root of this folder
- When continuing an existing topic, work inside the matching `YYYYMMDD_*` folder
- This folder is a git repository: commit your changes at each natural stopping point of the work without waiting for the user to ask. If git refuses to commit because `user.name`/`user.email` are unset, ask the user for their name and their company email address (`@mbN.nkc.co.jp`, where N is a single digit such as 1–5), then set them with `git config --global`
- Maintain `.gitignore` appropriately for what the work creates: never commit installed dependencies or virtual environments such as `node_modules/` or `.venv/`
- Work that belongs in its own repository fits better outside this workspace: suggest creating a separate folder elsewhere and opening it as a separate project in Kohden Code
- Kohden Code が実行した内容は、日付ごとに実行ログとして個別に記録する。ログは `YYYYMMDD_<topic>/実行ログ_YYYYMMDD.md` に置き、「ユーザーの指示1件＝エントリ1件」として「指示/実施/成果物/状態(コミット番号含む)」を記す。既存の日のログがあればそこに追記する

## About this file

This file holds general rules for this workspace, not notes about the current task. When these rules do not fit how the user works, or an agent made a mistake or worked inefficiently, suggest updating them so things go better next time, and edit the file once the user agrees.
