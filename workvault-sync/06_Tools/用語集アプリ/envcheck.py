# 社用PCで用語集PoCが動くかを事前に確かめるための調査スクリプト。
# 標準ライブラリだけで動き、ネットワークには一切出ない。
# 出力はコンソールの文字コードに左右されないよう英数字だけにする。
# 貼り付けて共有される前提なので、パス・ユーザー名・プロキシの値は出さず、
# 「有るか無いか」とバージョンだけを出す。
import locale
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile


def run(cmd):
    # 見つからない・失敗したは区別せず「無し」とする。知りたいのは使えるかどうかだけ
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0] if out.returncode == 0 else "no"
    except Exception:
        return "no"


print("Python        :", sys.version.split()[0], platform.architecture()[0])
print("py>=3.11      :", sys.version_info >= (3, 11))
print("OS            :", platform.system(), platform.release(), platform.version())
print("locale enc    :", locale.getpreferredencoding(False))
print("stdout enc    :", sys.stdout.encoding)
print("PYTHONUTF8    :", os.environ.get("PYTHONUTF8", "unset"))
print("SQLite        :", sqlite3.sqlite_version)
print("pip           :", run([sys.executable, "-m", "pip", "--version"]).split(" from ")[0])
# 社内ミラーの有無はURLそのものではなく、設定が入っているかどうかだけ見る
pip_cfg = run([sys.executable, "-m", "pip", "config", "list"])
print("pip config    :", "yes" if pip_cfg not in ("no", "") else "no")
for name in ("HTTP_PROXY", "HTTPS_PROXY", "PIP_INDEX_URL", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
    print(f"{name:14}:", "set" if os.environ.get(name) or os.environ.get(name.lower()) else "unset")
for tool in ("git", "make", "docker", "uv"):
    print(f"{tool:14}:", "yes" if shutil.which(tool) else "no")
print("PowerShell    :", run(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]))
try:
    with tempfile.NamedTemporaryFile(dir=os.path.expanduser("~"), delete=True):
        pass
    print("home writable : yes")
except Exception:
    print("home writable : no")
input("終了するには Enter キーを押してください...")
