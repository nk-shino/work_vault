<!--
  Built-in skill. Name and description are registered in code at
  packages/core/src/plugin/skill.ts
  and CUSTOMIZE_KOHDEN_CODE_SKILL_DESCRIPTION). The body below becomes the
  skill's content.
-->

# Customizing Kohden Code

Kohden Code validates its own config strictly and refuses to start when a field
is wrong. The shapes below cover the common surface area, but they are a
**summary, not the source of truth**.

## Full schema reference

The authoritative list of every config option — with field types, enums,
defaults, and descriptions — lives in the published JSON Schema:

**<https://opencode.ai/config.json>**

If a field is not documented in this skill, or you need to confirm an exact
shape before writing config, **fetch that URL and read the schema directly**
rather than guessing. Kohden Code hard-fails on invalid config, so the cost of
a wrong shape is a broken startup.

Independently, every `opencode.json` should declare
`"$schema": "https://opencode.ai/config.json"` so the user's editor catches
mistakes as they type.

## Applying changes

Config is loaded once when Kohden Code starts and is not hot-reloaded. After
saving changes to `opencode.json`, an agent file, a skill, a plugin, or any
other config-time file, **tell the user to quit and restart Kohden Code** for
the changes to take effect. The running session will keep using the
already-loaded config until then.

## Where files live

The global paths below show the default location; `KOHDEN_CODE_CONFIG_DIR` overrides it, otherwise `xdg-basedir` resolves the config root from the platform/XDG environment, including `XDG_CONFIG_HOME`.

| Scope                         | Path                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Project config                | `./opencode.json`, `./opencode.jsonc`, or `.kohden-code/opencode.json` (Kohden Code walks up from the cwd to the worktree root) |
| Global config                 | `~/.config/kohden-code/opencode.json` or `~/.config/kohden-code/opencode.jsonc` (NOT `~/.opencode/`; NOT `~/.config/opencode/` which belongs to upstream opencode) |
| Project agents                | `.kohden-code/agent/<name>.md` or `.kohden-code/agents/<name>.md`                                                               |
| Global agents                 | `~/.config/kohden-code/agent(s)/<name>.md` |
| Project commands              | `.kohden-code/command/<name>.md` or `.kohden-code/commands/<name>.md`                                                           |
| Global commands               | `~/.config/kohden-code/command(s)/<name>.md` |
| Project skills                | `.kohden-code/skill(s)/<name>/SKILL.md`                                                                                      |
| Global skills                 | `~/.config/kohden-code/skill(s)/<name>/SKILL.md` |
| External skills (auto-loaded) | `~/.claude/skills/<name>/SKILL.md`, `~/.agents/skills/<name>/SKILL.md`, `~/.copilot/skills/<name>/SKILL.md`; project `.claude/skills/`, `.agents/skills/`, `.github/skills/` (walks up from the cwd to the worktree root) |

Configs from each scope are deep-merged. Project overrides global. Unknown
top-level keys in `opencode.json` are rejected with `ConfigInvalidError`.

## opencode.json

The config file name is `opencode.json` (upstream-compatible), even though the
product is Kohden Code.

Every field is optional.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "username": "string",
  "model": "provider/model-id",
  "small_model": "provider/model-id",
  "default_agent": "agent-name",
  "shell": "/bin/zsh",
  "logLevel": "DEBUG" | "INFO" | "WARN" | "ERROR",
  "share": "manual" | "auto" | "disabled",
  "autoupdate": true | false | "notify",
  "snapshot": true,
  "instructions": ["AGENTS.md", "docs/style.md"],

  "skills": {
    "paths": [".kohden-code/skills", "/abs/path/to/skills"],
    "urls": ["https://example.com/.well-known/skills/"]
  },

  "references": {
    "docs": {
      "path": "../docs",
      "description": "Use for product behavior and documentation conventions"
    },
    "sdk": {
      "repository": "owner/sdk",
      "branch": "main",
      "description": "Use for SDK implementation details",
      "hidden": true
    }
  },

  "agent": {
    "my-agent": {
      "model": "anthropic/claude-sonnet-4-6",
      "mode": "subagent",
      "description": "...",
      "permission": { "edit": "deny" }
    }
  },

  "command": {
    "deploy": { "description": "...", "template": "..." }
  },

  "provider": {
    "anthropic": { "options": { "apiKey": "..." } }
  },
  "disabled_providers": ["openai"],
  "enabled_providers": ["anthropic"],

  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp"],
      "enabled": true,
      "environment": {}
    },
    "remote-thing": {
      "type": "remote",
      "url": "https://...",
      "headers": { "Authorization": "Bearer ..." }
    }
  },

  "plugin": [
    "opencode-gemini-auth",
    "opencode-foo@1.2.3",
    "./local-plugin.ts",
    ["opencode-bar", { "option": "value" }]
  ],

  "permission": {
    "edit": "deny",
    "bash": { "git *": "allow", "*": "ask" }
  },

  "formatter": false,
  "lsp": false,

  "experimental": {
    "primary_tools": ["edit"],
    "mcp_timeout": 30000
  },

  "tool_output": { "max_lines": 200, "max_bytes": 8192 },

  "compaction": { "auto": true, "tail_turns": 15 }
}
```

Shape notes worth being explicit about:

- `model` always carries a provider prefix: `"anthropic/claude-sonnet-4-6"`.
- `skills` is an object with `paths` and/or `urls`, not an array.
- `references` is an object keyed by alias. Each value is a local path, Git repository, or string shorthand.
- `agent` is an object keyed by agent name, not an array.
- `command` is an object keyed by command name, not an array.
- `plugin` is an array of strings or `[name, options]` tuples, not an object.
- `mcp[name].command` is an array of strings, never a single string. `type` is required.
- `permission` is either a string action or an object keyed by tool name.

## Skills

Kohden Code's skill loader scans for `**/SKILL.md` inside skill directories. The
file is named `SKILL.md` exactly, and lives in its own folder named after the
skill:

```
.kohden-code/skills/my-skill/SKILL.md
```

Frontmatter:

```markdown
---
name: my-skill
description: One sentence covering what this skill does AND when to trigger it. Front-load the literal keywords or filenames the user is likely to say.
---

# My Skill

(skill body in markdown: instructions, examples, references)
```

- `name` is required, lowercase hyphen-separated, up to 64 chars, and matches the folder name.
- `description` is effectively required: skills without one are filtered out and never surfaced to the model. Cover both _what_ the skill does and _when_ to use it. Write in third person ("Use when...", not "I help with..."). Front-load concrete trigger keywords and filenames; gate with "Use ONLY when..." if the skill should stay quiet on adjacent topics.
- Optional: `license`, `compatibility`, `metadata` (string-string map).

Register skills from non-default locations via `skills.paths` (scanned
recursively for `**/SKILL.md`) and `skills.urls` (each URL serves a list of
skills).

## References

References make local directories and Git repositories outside the active
project available as supporting context. Configure them under `references`,
keyed by the alias used in `@` autocomplete:

```json
{
  "references": {
    "docs": {
      "path": "../product-docs",
      "description": "Use for product behavior and terminology"
    },
    "effect": {
      "repository": "Effect-TS/effect",
      "branch": "main",
      "description": "Use for Effect implementation details"
    }
  }
}
```

Local `path` values may be relative to the declaring config, absolute, or use
`~/`. Git `repository` values accept Git URLs, host/path references, and GitHub
`owner/repo` shorthand; `branch` is optional. Both forms support optional
`description` and `hidden` fields.

- Only references with a `description` are advertised to agents in system context.
- `hidden: true` removes a reference from TUI `@` autocomplete only. It remains available to agents and by direct path.
- Reference directories are automatically allowed through the external-directory boundary; normal read/edit/tool permissions still apply.
- String shorthand is supported: use `"docs": "../docs"` for local paths or `"effect": "Effect-TS/effect"` for Git repositories.

## Agents

Two ways to define an agent. Use the file form for anything non-trivial.

### Inline (in `opencode.json`)

```json
{
  "agent": {
    "my-reviewer": {
      "description": "Reviews PRs for style violations.",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-6",
      "permission": { "edit": "deny", "bash": "ask" },
      "prompt": "You are a strict PR reviewer..."
    }
  }
}
```

### File

```
.kohden-code/agent/my-reviewer.md      OR     .kohden-code/agents/my-reviewer.md
```

```markdown
---
description: Reviews PRs for style violations.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: deny
  bash: ask
---

You are a strict PR reviewer. Focus on...
```

The file body becomes the agent's `prompt`. Do not also put `prompt:` in the
frontmatter.

`mode` is one of `"primary"`, `"subagent"`, `"all"`.

Allowed top-level frontmatter fields: `name, model, variant, description, mode,
hidden, color, steps, options, permission, disable, temperature, top_p`. Any
unknown field is silently routed into `options`.

To disable a built-in agent: `agent: { build: { disable: true } }`, or in a
file, `disable: true` in frontmatter.

`default_agent` must point to a non-hidden, primary-mode agent.

### Built-in agents

Kohden Code ships with `build`, `plan`, `general`, `explore`. Hidden internal agents:
`compaction`, `title`, `summary`. To override a built-in's fields, define the
same key in `agent: { <name>: { ... } }`.

## Commands

Kohden Code's command loader scans for `**/*.md` inside command directories. The
file is named after the command, and lives directly inside the `command` folder:

```
.kohden-code/command/deploy.md
```

Frontmatter:

```markdown
---
description: One sentence describing what the command does.
agent: build
model: anthropic/claude-sonnet-4-6
---

(command body in markdown: the prompt Kohden Code runs, with $ARGUMENTS for the user's input)
```

- `template` is the command body — everything below the frontmatter — and is required: it is the prompt Kohden Code runs when the command is invoked. Do not also put a `template:` key in the frontmatter.
- `$ARGUMENTS` is replaced with everything the user typed after the command; `$1`, `$2`, … pull individual positional arguments.
- Optional: `description`, `agent`, `model`, `variant`, `subtask`.

## Plugins

`plugin:` is an array. Each entry is one of:

```json
"plugin": [
  "opencode-gemini-auth",            // npm spec, latest
  "opencode-foo@1.2.3",              // npm spec, pinned
  "./local-plugin.ts",               // file path, relative to the declaring config
  "file:///abs/path/plugin.js",      // file URL
  ["opencode-bar", { "key": "val" }] // tuple form with options
]
```

Auto-discovered plugins (no config entry needed): any `*.ts` or `*.js` file in
`.kohden-code/plugin/` or `.kohden-code/plugins/`.

A plugin module exports `default` (or any named export) of type
`Plugin = (input: PluginInput, options?) => Promise<Hooks>`. The export is a
function, not a plain object literal, and the function returns an object
(return `{}` if there is nothing to register).

```ts
import type { Plugin } from "@kohden-code/plugin"

export default (async ({ client, project, directory, $ }) => {
  return {
    config: (cfg) => {
      // cfg is the live merged config; mutate fields here.
    },
    "tool.execute.before": async (input, output) => {
      // mutate output.args before the tool runs
    },
  }
}) satisfies Plugin
```

Hook surface (mutate `output` in place; return `void`):

- `event(input)`: every bus event
- `config(cfg)`: once on init with the merged config
- `chat.message`, `chat.params`, `chat.headers`
- `tool.execute.before`, `tool.execute.after`
- `tool.definition`
- `command.execute.before`
- `shell.env`
- `permission.ask`
- `experimental.chat.messages.transform`, `experimental.chat.system.transform`,
  `experimental.session.compacting`, `experimental.compaction.autocontinue`,
  `experimental.text.complete`

Special object-shaped (not callbacks): `tool: { my_tool: { ... } }`,
`auth: { ... }`, `provider: { ... }`.

## MCP servers

`mcp:` is an object keyed by server name. Each server is discriminated by
`type`:

```json
{
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp"],
      "enabled": true,
      "environment": { "BROWSER": "chromium" }
    },
    "github": {
      "type": "remote",
      "url": "https://...",
      "enabled": true,
      "headers": { "Authorization": "Bearer {env:GITHUB_TOKEN}" }
    },
    "old-server": { "enabled": false }
  }
}
```

`command` is an array of strings. `environment` sets environment variables for
a local MCP server. `type` is required. Use `enabled: false` to
disable a server inherited from a parent config. String values such as header
tokens support `{env:VAR}` interpolation (and `{file:path}`); the shell-style
`${VAR}` is not substituted.

## Permissions

```json
"permission": {
  "edit": "deny",
  "bash": { "git *": "allow", "rm *": "deny", "*": "ask" },
  "external_directory": { "~/secrets/**": "deny", "*": "allow" }
}
```

Actions: `"allow"`, `"ask"`, `"deny"`.

Per-tool value forms: `"allow"` shorthand (treated as `{"*": "allow"}`), or an
object `{ pattern: action }`. Within an object, **insertion order matters**.
Kohden Code evaluates the LAST matching rule, so put broad rules first and narrow
rules last.

`permission: "allow"` (a string at the top level) is shorthand for "allow
everything" and is rarely what the user wants.

Known permission keys: `read, edit, glob, grep, list, bash, task,
external_directory, todowrite, question, webfetch, websearch, lsp, doom_loop,
skill`. Some of these (`todowrite,
question, webfetch, websearch, doom_loop`) only accept a flat
action, not a per-pattern object.

`external_directory` patterns are filesystem paths (use `~/`, absolute paths,
or globs like `~/projects/**`).

Per-agent `permission:` overrides top-level `permission:`. Plan Mode lives on
the `plan` agent's permission ruleset (`edit: deny *`).

## Escape hatches

When a user's config is broken and Kohden Code won't start, these env vars help:

- `KOHDEN_CODE_DISABLE_PROJECT_CONFIG=1`: skip the project's local `opencode.json`
  and start from globals only. Run from the project directory, Kohden Code loads,
  the user edits the broken file, then they restart without the flag.
- `KOHDEN_CODE_CONFIG=/path/to/file.json`: load an additional explicit config.
- `KOHDEN_CODE_CONFIG_CONTENT='{"$schema":"https://opencode.ai/config.json"}'`:
  inject inline JSON as a final local-scope merge.
- `KOHDEN_CODE_DISABLE_DEFAULT_PLUGINS=1`: skip default plugins.
- `KOHDEN_CODE_PURE=1`: skip external plugins entirely.
- `KOHDEN_CODE_DISABLE_EXTERNAL_SKILLS=1`: skip all external skill scans
  (`.claude/`, `.agents/`, `.github/`, `~/.copilot/`).
  `KOHDEN_CODE_DISABLE_CLAUDE_CODE_SKILLS=1` skips only `.claude/skills/`;
  `KOHDEN_CODE_DISABLE_GITHUB_COPILOT_SKILLS=1` skips only `.github/skills/` and
  `~/.copilot/skills/`.

## When proposing edits

- Validate against the schema before writing. If you are unsure of a field's
  exact shape, or the field is not covered in this skill, fetch
  `https://opencode.ai/config.json` and read the schema rather than guessing.
- Preserve `$schema` and any existing fields the user did not ask to change.
- For agent, command, skill, and plugin definitions, prefer creating new files
  in the correct location over inlining everything in `opencode.json`.
- If the user's existing config is malformed, point them at the env-var escape
  hatches above so they can edit from inside Kohden Code without breaking their
  session.
- After saving any config change, remind the user to quit and restart Kohden Code
  — running sessions keep using the already-loaded config.

## Kohden Code user documentation

If the `gai_support_docs` tools are available, use them to look up Kohden Code's
user documentation (pages under `developers/kohden-code/`) for anything
Kohden Code-specific: config locations, `kohden.json`, models, and security
restrictions. Keep using the JSON Schema above for `opencode.json` field shapes.

## kohden.json

Kohden Code's own settings live in `kohden.json`, separate from `opencode.json`.

| Scope   | Path                                                                   |
| ------- | ---------------------------------------------------------------------- |
| Global  | `~/.config/kohden-code/kohden.json` (`KOHDEN_CODE_CONFIG_DIR` overrides the directory) |
| Project | `.kohden-code/kohden.json` (skipped with `KOHDEN_CODE_DISABLE_PROJECT_CONFIG=1`)        |

```json
{
  "translation": {
    "enabled": true,
    "target_language": "ja",
    "model": "provider/model-id"
  },
  "takumi_guard": { "enabled": true },
  "auto_review": { "enabled": false },
  "sandbox": { "enabled": false }
}
```

- `translation`: automatic translation of assistant replies. `enabled` defaults
  to `true`; `target_language` defaults to the OS display language; `model`
  must be `provider/model-id`, otherwise it is ignored.
- `takumi_guard.enabled`: route package installs through the Takumi Guard
  malicious-package proxy. Defaults to `true`.
- `auto_review.enabled`: automatic review of bash commands. Preview feature,
  defaults to `false`.
- `sandbox.enabled`: run bash commands inside the OS sandbox (Windows and
  Linux; Windows uses Microsoft MXC, Linux uses MXC and bubblewrap, on glibc
  x64 and arm64 builds — not musl). Preview feature, defaults to `false`.
  Inside the sandbox, commands can read the whole disk but write only to the
  workspace and the temp folder (`/tmp` is private to the sandbox on Linux);
  `.git` is read-only and all network access is blocked. Commands that need
  more are re-run outside the sandbox with a reason the user sees; those are
  always reviewed by `auto_review` when it is enabled, and asked to the user
  when it is disabled (explicit user `allow` rules still pass). On Windows and
  Linux, enabling it makes the bash default `ask` (except read-only and common
  dev commands) even without `auto_review`, including where the sandbox is
  unavailable (unsupported Windows build, Git Bash as the shell; on Linux,
  when the sandbox cannot start, for example user namespaces restricted by the
  kernel or AppArmor, or WSL1). It has no effect on other OSes.

Restart Kohden Code after changing `takumi_guard`, `auto_review`, or `sandbox`.
Changes to `translation` apply from the next translation without a restart.

Shape notes:

- Merging is per top-level section: a section in the project file replaces the
  same section in the global file wholesale. Fields inside a section are not
  merged.
- There is no `$schema`, and invalid values do not stop startup. A section with a
  wrong type is silently ignored and falls back to its defaults, so double-check
  types when a setting "does nothing".
- The global file may also contain a `seed` key written by Kohden Code itself.
  Preserve it and keep the file valid JSON.
