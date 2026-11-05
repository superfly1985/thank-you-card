# -*- coding: utf-8 -*-
"""make_subset.py — 从完整版悠哉体生成精简子集字体(GB2312全汉字+ASCII+常用标点)
用法:
  python tools/make_subset.py                 # 用本地完整字体生成/更新子集
  python tools/make_subset.py 王 堃          # 额外补充生僻字后重新生成
  python tools/make_subset.py --download      # 本地无完整字体时, 走镜像链下载
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
FULL = os.path.join(FONTS, "Yozai-Regular.ttf")
SUBSET = os.path.join(FONTS, "Yozai-Subset.ttf")
CHARSET_TXT = os.path.join(FONTS, "charset_extra.txt")

MIRRORS = [
    "https://ghfast.top/https://github.com/lxgw/yozai-font/releases/latest/download/Yozai-Regular.ttf",
    "https://gh-proxy.com/https://github.com/lxgw/yozai-font/releases/latest/download/Yozai-Regular.ttf",
    "https://github.com/lxgw/yozai-font/releases/latest/download/Yozai-Regular.ttf",
]


def build_charset(extra=""):
    chars = set(extra)
    for hb in range(0xB0, 0xF8):          # GB2312 全部 6763 汉字
        for lb in range(0xA1, 0xFF):
            try:
                chars.add(bytes([hb, lb]).decode("gb2312"))
            except Exception:
                pass
    chars.update(chr(c) for c in range(0x20, 0x7F))   # ASCII 可见字符
    chars.update("，。！？、；：""''（）《》〈〉【】〔〕…—·～￥％＋－×÷°℃㎡〇〔〕")
    chars.discard("\n"); chars.discard("\r")
    return chars


def download_full():
    import urllib.request
    os.makedirs(FONTS, exist_ok=True)
    for url in MIRRORS:
        try:
            print("尝试:", url[:60])
            urllib.request.urlretrieve(url, FULL)
            if os.path.getsize(FULL) > 5 * 1024 * 1024:
                print("下载成功:", FULL, os.path.getsize(FULL), "bytes")
                return True
        except Exception as e:
            print("  失败:", e)
    return False


def main():
    extra = "".join(a for a in sys.argv[1:] if not a.startswith("--"))
    if not os.path.exists(FULL) or "--download" in sys.argv:
        print("完整字体缺失, 开始下载...")
        if not download_full():
            sys.exit("所有下载源均失败, 请手动下载 Yozai-Regular.ttf 到 fonts/ 目录")
    chars = build_charset(extra)
    txt = "".join(sorted(chars))
    with open(CHARSET_TXT, "w", encoding="utf-8") as f:
        f.write(txt)
    cmd = [
        sys.executable, "-m", "fontTools.subset", FULL,
        "--text-file=" + CHARSET_TXT,
        "--output-file=" + SUBSET,
        "--layout-features=*", "--glyph-names",
        "--recalc-bounds", "--recalc-average-width",
    ]
    subprocess.run(cmd, check=True)
    size = os.path.getsize(SUBSET)
    print("SUBSET:", SUBSET, round(size / 1048576, 2), "MB,", len(txt), "字符")

    # 覆盖率抽检: 用 PIL 实际渲染验证非空
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(SUBSET, 48)
    missing = []
    sample = list(txt)[:: max(1, len(txt) // 500)]
    for ch in sample:
        img = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(img).text((10, 10), ch, font=f, fill=255)
        if not img.getbbox():
            missing.append(ch)
    print("抽检", len(sample), "字, 缺字:", missing if missing else "无")


if __name__ == "__main__":
    main()
