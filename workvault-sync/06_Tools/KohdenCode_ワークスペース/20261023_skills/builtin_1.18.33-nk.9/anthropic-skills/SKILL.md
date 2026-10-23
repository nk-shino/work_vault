---
name: anthropic-skills
description: Fetches Anthropic's xlsx, docx, pptx, and pdf skills from GitHub into Kohden Code's global skills directory. Use when the user works with spreadsheets, Word documents, slide decks, or PDFs (even if they only name a file or a deliverable like a report) and the matching skill is not in the available skill list. Also use to update those skills.
---

# Anthropic skills

## Purpose

Kohden Code users range from developers to staff who never write code. Both
kinds want a document produced or a spreadsheet analyzed, and neither should
have to know that a "skill" has to be fetched first. This document exists so
that anyone can say "summarize this Excel" and get the result. Fetching the skills is plumbing in service of that request — never the
deliverable.

Consequently:

- There is normally nothing to ask: install the default set and carry on with
  what they actually asked for. Menu-style questions ("which of these five do
  you want?") only burden them. Do ask when something is genuinely uncertain:
  their network may block github.com, their instructions may restrict git use,
  or the request may not need a document skill at all.
- Lead with their task ("I need to set up Excel support first, one moment").
  Match the user's level: skip git vocabulary unless they use it themselves or
  ask what is happening.
- Once the skill is in place, use it to finish the original request in the
  same conversation if possible; if a restart is required, say so plainly and
  tell them exactly what to type again afterwards.

## Mechanics

Source: https://github.com/anthropics/skills
Clone location (called DIR below), chosen once per task:

1. If `~/.agents/skills/anthropic-skills` exists and passes Verify, DIR is that
   path. It is the location used by earlier versions; keep using it, and do not
   move or re-clone it.
2. Otherwise DIR is `<global config dir>/skills/anthropic-skills`, where
   `<global config dir>` is `$KOHDEN_CODE_CONFIG_DIR` if set, else
   `$XDG_CONFIG_HOME/kohden-code`, else `~/.config/kohden-code`. If a legacy
   path from step 1 exists but fails Verify, leave it alone and use this one.

Resolve DIR to an absolute path and write that literal path, single-quoted, in
place of `'DIR'` in every command below. Do not rely on `~` or environment
variables inside the commands; they expand differently across shells. Single
quotes keep `$` and backticks literal in both bash and PowerShell; if the path
itself contains `'`, write it as `''` in PowerShell or `'\''` in bash.

Kohden Code scans both locations for `**/SKILL.md`, so `DIR/skills/<name>/SKILL.md`
is discovered without copying. DIR is a sparse checkout containing only the
skills that were requested.

Unless the user's instructions say otherwise, run the git commands below
yourself instead of asking the user to run them.

**Every git command in this document targets DIR and nothing else.** Other
directories next to DIR may be the user's own or team repositories; never run
git in them because of this skill.

### Decide

1. User explicitly asks to update or add Anthropic skills → Verify, then
   Update / Add.
2. Needed skill is already in the available skill list → use it, stop.
3. DIR does not exist → Install.
4. DIR exists → Verify. Then if `DIR/skills/<name>` is missing → Add.
5. A fetched skill misbehaves in a way that suggests stale content → Verify,
   then Update.

If `git --version` fails, tell the user git is required and how to install it
for their OS, then stop.

### Verify

Run before any Add or Update, and whenever DIR already exists. Step 1 of
choosing DIR also runs it on the legacy path; there a failure only means moving
on to step 2, not stopping.

```sh
git -C 'DIR' remote get-url origin
```

Proceed only if the output is `https://github.com/anthropics/skills` (a trailing
`.git` is fine). Anything else — a different URL, "not a git repository", or a
directory with no `.git` — means DIR is not this skill's clone. Do not run any
further git command there and do not delete or overwrite it; tell the user what
is at that path and stop.

### Install

Only when DIR does not exist:

```sh
git clone --filter=blob:none --sparse https://github.com/anthropics/skills 'DIR'
git -C 'DIR' remote set-url --push origin DISABLED
git -C 'DIR' sparse-checkout set skills/docx skills/pdf skills/pptx skills/xlsx
```

The default set above is always installed together; do not ask the user which
of them they want. Only add other names when the user explicitly asks for a
specific skill by name. The second line disables pushing: fetch and pull keep
working, but any `git push` fails because the push URL is not a repository.

### Add

```sh
git -C 'DIR' sparse-checkout add skills/<name>
```

After Install or Add, confirm `DIR/skills/<name>/SKILL.md` exists for each
requested name. Sparse checkout succeeds silently when the pattern matches
nothing (typo, upstream rename). If one is missing, list
`git -C 'DIR' ls-tree --name-only origin/HEAD skills/`
and, for a user-named skill, ask which name they meant; for a default-set
skill, report which one upstream no longer provides.

### Update

1. `git -C 'DIR' status --porcelain`
   Non-empty output means uncommitted edits exist. Do not stash, commit,
   or discard them. List the files and ask the user how to proceed.
2. `git -C 'DIR' pull --no-rebase`
3. Conflicts can only be between upstream and commits previously made in DIR
   by this workflow (see below). Resolve them: keep the upstream change and
   the intent of the local edit, remove markers, then
   `git -C 'DIR' add <files>` and
   `git -C 'DIR' commit`. If unresolvable,
   `git -C 'DIR' merge --abort` and report.

### When a task changes files inside DIR

A fetched skill may be edited as part of a user's request, for example adding
a lesson learned after a failure. Before finishing that task, commit only the
files changed for it:

```sh
git -C 'DIR' add <changed files>
git -C 'DIR' commit -m "<what and why>"
```

Never `git add -A`. If commit fails because no git identity is configured, ask
the user which name/email to use and set it with
`git -C 'DIR' config user.name` /
`user.email` (local to DIR only).

This keeps local changes mergeable with upstream and makes the Update step's
dirty-tree check meaningful.

### Never, inside DIR

- `git reset --hard`, `git checkout -- .`, `git clean`, `git rebase`, `--force`:
  each one discards or rewrites work, and the local commits in DIR are the only
  copy of the lessons recorded there.
- `git remote set-url --push` to restore a push URL: the disabled push URL is
  what guarantees nothing local can ever reach the upstream repository.
- Delete or re-clone DIR to "fix" a problem: same reason as the first item.
  Prefer `merge --abort` and a report to the user.

### After install or update

- Loaded skills are cached for the lifetime of the process. Tell the user to
  restart Kohden Code after every install, add, or update; until then the
  old content (or no skill) is what gets used.
- The document skills require Python and the packages named in their own
  SKILL.md; follow those when first used.
- Mention once: most skills are Apache 2.0; docx, pdf, pptx, xlsx are
  source-available for demonstration/educational use and must not be
  redistributed.
