import json, sys, urllib.request

# GitHub issue 作成（gh CLI 不要・git credential のトークンを利用）
# 使い方: python github-issue.py <repo> <title> <body-file>
# 例:     python github-issue.py nk-shino/work_vault "タイトル" body.md

def get_token():
    import subprocess
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
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    repo, title, body_file = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(body_file, encoding="utf-8") as f:
        body = f.read()
    token = get_token()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps({"title": title, "body": body}).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            d = json.load(r)
            print(f"created: #{d['number']} {d['html_url']}")
    except urllib.error.HTTPError as e:
        print(f"error {e.code}: {e.read().decode()[:300]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
