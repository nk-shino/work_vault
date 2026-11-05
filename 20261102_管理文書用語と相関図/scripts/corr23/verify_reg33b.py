import sys, io, fitz, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
STASH = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pdf_stash_20261105"
BOOKS = ["Pana-CIM管理手順書案_未承認.pdf", "LNB管理手順書案_未承認.pdf"]
ok = True
for fn in BOOKS:
    new = fitz.open(f"{VAULT}/{fn}"); old = fitz.open(f"{STASH}/{fn}")
    tn = [p.get_text() for p in new]; to = [p.get_text() for p in old]
    # ②頁: EE01 を含む頁 / ③頁: N07 を含む頁(目次は除外)
    p2n = next(i for i,t in enumerate(tn) if "EE01" in t)
    p2o = next(i for i,t in enumerate(to) if "EE01" in t)
    p3n = next(i for i,t in enumerate(tn) if "N07" in t)
    p3o = next(i for i,t in enumerate(to) if "N07" in t)
    print(f"== {fn[:12]}.. ②new idx{p2n}/old idx{p2o}  ③new idx{p3n}/old idx{p3o}")
    ln = [l for l in tn[p2n].splitlines() if l.strip().startswith("EE")]
    lo = [l for l in to[p2o].splitlines() if l.strip().startswith("EE")]
    for d in difflib.unified_diff(lo, ln, "old②EE", "new②EE", lineterm="", n=0):
        if d.startswith(("---","+++","@@")): continue
        print("   ", d[:80])
    same3 = tn[p3n] == to[p3o]
    print("    ③頁テキスト新旧同一:", "OK" if same3 else "**DIFF**"); ok &= same3
    nacim = [(i+1, t.count("NACIM")) for i,t in enumerate(tn) if "NACIM" in t]
    print("    NACIM表記頁(1-based):", nacim)
    new.close(); old.close()
print("RESULT:", "OK" if ok else "CHECK ABOVE")
