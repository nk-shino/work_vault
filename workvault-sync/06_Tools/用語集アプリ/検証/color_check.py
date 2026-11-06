"""色トークンの照合（WCAG コントラスト比・OKLCH の L/C）。

02a_デザイン規則の適用設計.md §2.3・§2.7 の手計算値を再計算する。
Phase 3 では style.css から値を読み直して同じ表を出す想定（今は 02a の値を直書き）。
実行: PYTHONIOENCODING=utf-8 python color_check.py
"""

from __future__ import annotations

import math


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(hex_: str) -> tuple[float, float, float]:
    h = hex_.lstrip("#")
    return tuple(_lin(int(h[i : i + 2], 16) / 255) for i in (0, 2, 4))  # type: ignore[return-value]


def luminance(hex_: str) -> float:
    r, g, b = _rgb(hex_)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def oklch(hex_: str) -> tuple[float, float]:
    r, g, b = _rgb(hex_)
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(v) ** (1 / 3), v) for v in (l_, m_, s_))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(A, B)


LIGHT = {
    "paper": "#f8f7f2", "surface": "#ffffff", "surface-2": "#f1efe8", "ink": "#26282e",
    "muted": "#5c6270", "line": "#d8d5ca", "line-strong": "#767d89", "roku": "#14685b",
    "roku-strong": "#0f544a", "roku-soft": "#e7f1ee", "roku-soft-hover": "#d7e9e4",
    "shu": "#b23a24", "shu-strong": "#8f2a1c", "shu-soft": "#f9ebe7", "kuchi-fg": "#7a5a00",
    "kuchi-bg": "#fbf1d8", "matsu-fg": "#1f6e46", "matsu-bg": "#e8f3ea",
}
DARK = {
    "paper": "#2b2f36", "surface": "#33383f", "surface-2": "#3c424a", "ink": "#e8e6df",
    "muted": "#a8adb8", "line-strong": "#9299a4", "roku": "#7cc8b4", "roku-strong": "#a5dccb",
    "shu": "#e8a898", "shu-strong": "#f6b09c", "kuchi-fg": "#e0b45c", "matsu-fg": "#7cc89b",
}

# (テーマ, 前景, 背景, 02a の記載値, 基準 4.5 or 3.0)
PAIRS = [
    ("明", "ink", "paper", 13.7, 4.5), ("明", "ink", "surface", 14.7, 4.5),
    ("明", "muted", "paper", 5.7, 4.5), ("明", "muted", "surface", 6.1, 4.5),
    ("明", "muted", "surface-2", 5.3, 4.5), ("明", "roku", "paper", 6.2, 4.5),
    ("明", "roku-strong", "paper", 8.2, 4.5), ("明", "roku-strong", "roku-soft", 7.6, 4.5),
    ("明", "roku-strong", "roku-soft-hover", 7.0, 4.5), ("明", "shu", "paper", 5.6, 4.5),
    ("明", "shu-strong", "surface", 8.3, 4.5), ("明", "shu-strong", "shu-soft", 7.2, 4.5),
    ("明", "kuchi-fg", "kuchi-bg", 5.7, 4.5), ("明", "matsu-fg", "matsu-bg", 5.5, 4.5),
    ("明", "line-strong", "surface", 4.2, 3.0), ("明", "line-strong", "paper", 3.9, 3.0),
    ("暗", "ink", "paper", 10.8, 4.5), ("暗", "ink", "surface", 9.5, 4.5),
    ("暗", "ink", "surface-2", 8.1, 4.5), ("暗", "muted", "paper", 6.0, 4.5),
    ("暗", "muted", "surface-2", 4.51, 4.5), ("暗", "roku", "paper", 6.9, 4.5),
    ("暗", "roku", "surface-2", 5.2, 4.5), ("暗", "shu", "paper", 6.7, 4.5),
    ("暗", "shu", "surface-2", 5.1, 4.5), ("暗", "kuchi-fg", "surface-2", 5.2, 4.5),
    ("暗", "matsu-fg", "surface-2", 5.1, 4.5), ("暗", "paper", "shu", 6.7, 4.5),
    ("暗", "line-strong", "surface", 4.1, 3.0), ("暗", "line-strong", "surface-2", 3.5, 3.0),
]

# 02a に無いが実画面で起きる組み合わせ（参考）
EXTRA = [
    ("明", "roku", "surface-2", 4.5), ("明", "roku", "roku-soft", 4.5),
    ("明", "kuchi-fg", "paper", 4.5), ("明", "matsu-fg", "paper", 4.5),
    ("明", "line-strong", "surface-2", 3.0), ("暗", "muted", "surface", 4.5),
    ("暗", "roku", "surface", 4.5), ("暗", "roku-strong", "surface-2", 4.5),
]


def main() -> None:
    print("## コントラスト比（02a §2.7 の照合）")
    print("| テーマ | 前景/背景 | 02a | 再計算 | 差 | 基準 |")
    for theme, fg, bg, stated, need in PAIRS:
        pal = LIGHT if theme == "明" else DARK
        v = contrast(pal[fg], pal[bg])
        flag = "OK" if v >= need else "NG"
        diff = "" if abs(v - stated) < 0.15 else " ←差"
        print(f"| {theme} | {fg}/{bg} | {stated} | {v:.2f}{diff} | | {need} {flag} |")
    print("\n## 02a に無い組み合わせ（参考）")
    for theme, fg, bg, need in EXTRA:
        pal = LIGHT if theme == "明" else DARK
        v = contrast(pal[fg], pal[bg])
        print(f"| {theme} | {fg}/{bg} | {v:.2f} | {need} {'OK' if v >= need else 'NG'} |")

    print("\n## 相対輝度（規則 3 のダークグレー帯 0.025〜0.040）")
    for name, hx in [("暗 paper 最終", "#2b2f36"), ("02 候補", "#23262b"), ("現行", "#191b1f"),
                     ("暗 surface", "#33383f"), ("暗 surface-2", "#3c424a")]:
        print(f"| {name} {hx} | {luminance(hx):.4f} |")

    print("\n## OKLCH（02a §2.3 のパステル基準）")
    groups = [
        ("a 面の淡色地 L>=0.88 C<=0.06", [("roku-soft", "#e7f1ee"), ("shu-soft", "#f9ebe7"),
          ("kuchi-bg", "#fbf1d8"), ("matsu-bg", "#e8f3ea"), ("roku-soft-hover", "#d7e9e4"),
          ("明 paper", "#f8f7f2"), ("明 surface-2", "#f1efe8")]),
        ("b 暗の前景 L>=0.70 C<=0.12", [("roku-d", "#7cc8b4"), ("roku-strong-d", "#a5dccb"),
          ("shu-d 最終", "#e8a898"), ("shu-strong-d", "#f6b09c"), ("matsu-d", "#7cc89b"),
          ("kuchi-d", "#e0b45c")]),
        ("c 禁止帯 L>=0.75 C>0.12 の候補", [("現行 暗 shu", "#f08a72"), ("favicon 紺", "#4a5ec9")]),
        ("参考 明の深色アクセント（未決 1）", [("roku", "#14685b"), ("roku-strong", "#0f544a"),
          ("shu", "#b23a24"), ("shu-strong", "#8f2a1c"), ("kuchi-fg", "#7a5a00"), ("matsu-fg", "#1f6e46")]),
    ]
    for title, items in groups:
        print(f"### {title}")
        for name, hx in items:
            L, C = oklch(hx)
            banned = L >= 0.75 and C > 0.12
            print(f"| {name} {hx} | L={L:.3f} C={C:.3f} | 禁止帯={'該当' if banned else '-'} |")


if __name__ == "__main__":
    main()
