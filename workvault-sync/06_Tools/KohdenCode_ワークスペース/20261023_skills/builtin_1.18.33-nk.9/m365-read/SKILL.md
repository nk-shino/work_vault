---
name: m365-read
description: "Reads the user's own Microsoft 365 data through the Microsoft Graph API. Use when the user asks to see their mail or unread mail, recent Teams chats, SharePoint or OneDrive files, their exchanges with a colleague, or someone's email address. Covers mail, Teams chats, SharePoint, OneDrive, People search, and file downloads. Read-only: calendar, any write operation, and bare /me are not available."
---

# M365 Read skill (Graph API, read-only)

## How it works

- Borrows the official Microsoft app ID of the former Work IQ MCP, `ba081686-5d24-4bc6-a0d6-d034ecffed87`.
  It is **admin-consented** in the NK tenant (tenant ID: `ca9c2885-f052-48d0-98f2-4ee2bfc5cc07`).
- The first run authenticates in Edge. Later runs refresh the saved token headlessly.
- The token is stored encrypted at `%LOCALAPPDATA%\m365-read\msal_cache.bin`.

## Prohibited (strict)

- **Never try to read the token cache yourself (any file under `%LOCALAPPDATA%\m365-read\`).**
  This applies to every method (`read`, `cat`, `Get-Content`, decryption, opening it directly from Python, and so on). Never print, copy, or move its contents.
  Leave acquiring and refreshing tokens to `m365_read.py`.

## Usage

```powershell
# First run only (browser sign-in; no consent screen because the app is admin-consented)
uv run "<path to this skill>/scripts/m365_read.py" --auth

# Normal run (headless, non-interactive)
[Console]::OutputEncoding = [Text.Encoding]::UTF8; uv run "<path to this skill>/scripts/m365_read.py" --uri 'me/mailfolders/inbox/messages?$top=5&$select=subject,receivedDateTime'

# Binary download (save a SharePoint/OneDrive file; use the item-id from a listing)
uv run "<path to this skill>/scripts/m365_read.py" --uri 'sites/{site-id}/drive/items/{item-id}/content' --out-file output.xlsx
```

- When you need to read the output, put `[Console]::OutputEncoding = [Text.Encoding]::UTF8;` **at the start of the same line**. Without it, non-ASCII text such as Japanese is garbled (both Windows PowerShell 5.1 and PowerShell 7).
- `--uri` accepts a relative path (`https://graph.microsoft.com/v1.0/` is prepended) or a full URL. The token is only ever sent to `https://graph.microsoft.com`.
- To page, pass the response's `@odata.nextLink` to `--uri` as is.
- A `--uri` containing `$search` or `$count` automatically gets the `ConsistencyLevel: eventual` header.
- **Always wrap `--uri` in single quotes**: with double quotes PowerShell expands `$top` and `$select` as variables, leaving them empty.
- **Do not put double quotes `"` inside arguments** (Windows PowerShell 5.1 strips them). Write `%22` instead.
- The token expires after about 90 days (or is invalidated by a password change and the like). Run `--auth` again when that happens.

## Consented scopes (only these work)

`Mail.Read` `Chat.Read` `ChannelMessage.Read.All` `People.Read.All` `Sites.Read.All` `OnlineMeetingTranscript.Read.All` `ExternalItem.Read.All`

## Recipes

| Purpose | `--uri` |
|---------|---------|
| Latest N inbox messages | `me/mailfolders/inbox/messages?$top=10&$select=subject,receivedDateTime,from,bodyPreview` |
| Mail folders | `me/mailfolders?$top=100&$select=displayName,totalItemCount,unreadItemCount` |
| Latest N sent messages | `me/mailfolders/sentitems/messages?$top=10&$select=subject,receivedDateTime,toRecipients` |
| Message body | `me/mailfolders/inbox/messages/{id}?$select=subject,body,from,toRecipients` |
| Mail search (KQL) | `me/mailfolders/inbox/messages?$search=%22from:xxx@nkc.co.jp budget%22` |
| Teams chats | `chats?$top=50` |
| Chat messages | `chats/{chat-id}/messages?$top=50` |
| SharePoint site search | `sites?search=keyword` |
| Files in a site | `sites/{site-id}/drive/root/children` |
| Related people | `me/people?$top=20&$select=displayName,scoredEmailAddresses` (ordered by relevance, with email addresses) |
| Personal OneDrive | `me/drive/root/children?$top=50&$select=id,name,folder,file,size` |
| OneDrive/SharePoint file download | `me/drive/items/{item-id}/content` (OneDrive) or `sites/{site-id}/drive/items/{item-id}/content` (SharePoint) plus **`--out-file`** (binary save). Do not address files by path; get the `id` from a listing first, then download by ID |

## Not available (no admin consent, returns 403)

| Operation | Missing scope |
|-----------|---------------|
| **Anything calendar** (read, create, update) | `Calendars.Read/ReadWrite` |
| **Any write** (sending mail, creating events, and so on) | `Mail.Send` and others |
| Bare `/me` and user profiles | `User.Read` |
| Listing Teams teams/channels | `Team.ReadBasic.All` (`ChannelMessage.Read.All` is granted, but listing channels needs a Team scope that is not) |
| Teams meeting transcripts | `/me/onlineMeetings` returns 403 (insufficient even with the `OnlineMeetingTranscript.Read.All` scope) |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No token found` | Run `--auth` to sign in for the first time |
| `invalid_grant` / refresh failure | The token expired (90 days or a password change). Run `--auth` again |
| The browser does not open / blocked by conditional access | The NK tenant only allows Edge, so the script launches Edge. Reopen the sign-in in Edge |
| `Access is denied by tenant policy` and similar | Check that no new scope is being requested. Request only the 7 consented scopes |
| 403 Forbidden | See "Not available" above. Adding a scope requires tenant admin approval |
