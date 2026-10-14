# Default workspace
This is the default workspace. The rules below are a default starting point; adapt them to how the user actually works.

- When starting a new topic, create a `YYYYMMDD_<topic>/` folder and work inside it
- Put generated files in the matching topic folder rather than directly at the root of this folder
- When continuing an existing topic, work inside the matching `YYYYMMDD_*` folder
- This folder is a git repository: commit your changes at each natural stopping point of the work without waiting for the user to ask.
- **Commit identity is per repository. Never use `git config --global` for it.** The global setting on this user's machines is the personal account (`Liff22`), and overwriting it leaks one identity's name into every other repository. Set identity with `git config --local` inside the repository you are working in.
- **Which identity belongs to which work is decided by where the material came from**, not by what kind of file it is. The table and the verification steps live in `06_Tools/スクリプトと手順/gh-accounts.ps1` in Work_Vault — that script holds the only copy of the mapping, so read it rather than guessing:
  - material from `Work_Vault` → work account `soushi.shinohara22`
  - material from `Zettelkasten` → personal account `Liff22`
  - material from the アイデンリリィ / 切り抜き site → `kirinukifallstay`
- **Use the GitHub noreply address for commits, not the company address.** `gh api user --jq '"\(.id)+\(.login)@users.noreply.github.com"'` returns it for the account you are logged in as. Issue bodies and commit messages in work repositories carry internal host names, customer names and colleagues' real names, so a repository that is private today may still be opened or handed over later — and commit history is the hardest place to correct afterwards. Use the company address only if the company requires it for commits.
- **Do not run `gh auth login` or `gh auth switch` yourself.** Authentication is the user's action. Accounts are kept apart by `GH_CONFIG_DIR`, one directory per division; `gh auth switch` changes the active account for the whole host and a forgotten switch commits silently under the wrong name. Run gh through `gh-accounts.ps1 -Run <division> -- <args>`, which checks the identity before acting and stops if it does not match.
- **`project` scope is not granted by default.** Without it every board operation (`gh project create` / `field-create` / `item-edit` / `item-list`) fails. `gh-accounts.ps1 -Setup <division>` runs `gh auth refresh -s project` after login.
- Maintain `.gitignore` appropriately for what the work creates: never commit installed dependencies or virtual environments such as `node_modules/` or `.venv/`
- Maintain `.gitignore` appropriately for what the work creates: never commit installed dependencies or virtual environments such as `node_modules/` or `.venv/`
- Work that belongs in its own repository fits better outside this workspace: suggest creating a separate folder elsewhere and opening it as a separate project in Kohden Code

## About this file

This file holds general rules for this workspace, not notes about the current task. When these rules do not fit how the user works, or an agent made a mistake or worked inefficiently, suggest updating them so things go better next time, and edit the file once the user agrees.

**This copy is not the original.** The working repository is `C:\Users\ss80751\kohden-code-workspace` on the company PC. This is the Work_Vault mirror, kept so the rules survive and can be read from the private PC. The git history is bundled next to it as `kohden-code-workspace_2026-10-13.bundle`.

**2026-10-14: the identity rules above were corrected.** The earlier version said to ask for a company address of the form `@mbN.nkc.co.jp` and set it with `git config --global`. Both were wrong — the account is registered as `ss80751@ad.nkc.co.jp`, and `--global` would overwrite the personal identity used by every other repository on the machine. **Apply the same correction to the original on the company PC; until then the two copies disagree.**
