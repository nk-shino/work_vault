# GitHub issue クローズ（gh CLI 不要・git credential のトークンを利用）
# 使い方: python github-issue-close.py <repo> <issue-number> [comment-file]
# 例:     python github-issue-close.py nk-shino/work_vault 1 done.md

import json, subprocess, sys, urllib.request

def get_token():
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("git credential からトークンを取得できなかった")

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    repo, num = sys.argv[1], int(sys.argv[2])
    body = None
    if len(sys.argv) >= 4:
        with open(sys.argv[3], encoding="utf-8") as f:
            body = f.read()
    token = get_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    if body:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues/{num}/comments",
            data=json.dumps({"body": body}).encode("utf-8"),
            headers=headers, method="POST",
        )
        with urllib.request.urlopen(req) as r:
            d = json.load(r)
            print(f"comment: {d['html_url']}")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{num}",
        data=json.dumps({"state": "closed"}).encode("utf-8"),
        headers=headers, method="PATCH",
    )
    with urllib.request.urlopen(req) as r:
        d = json.load(r)
        print(f"closed: #{d['number']} state={d['state']}")

if __name__ == "__main__":
    main()
