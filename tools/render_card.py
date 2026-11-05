# -*- coding: utf-8 -*-
"""手写模拟感谢卡：在空白卡底图上叠加手写风格文字
用法: python render_card.py <config.json> <output.jpg>
"""
from PIL import Image, ImageDraw, ImageFont
import random, json, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 仓库根(任意克隆位置可用)
BASE = os.path.join(ROOT, "assets", "base_card.jpg")
_SUBSET = os.path.join(ROOT, "fonts", "Yozai-Subset.ttf")
_FULL = os.path.join(ROOT, "fonts", "Yozai-Regular.ttf")
FONT_PATH = _SUBSET if os.path.exists(_SUBSET) else _FULL


def make_glyph(ch, size, angle, ink):
    f = ImageFont.truetype(FONT_PATH, size)
    pad = size // 2 + 8
    tmp = Image.new("RGBA", (size * 2 + pad * 2, size * 2 + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((pad, pad), ch, font=f, fill=ink)
    bbox = tmp.getbbox()
    if not bbox:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    tmp = tmp.crop(bbox)
    if abs(angle) > 0.2:
        tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
    return tmp


def write_line(base, x, line_y, text, size=54, ink=(50, 46, 60, 235), jitter=1.0, rise=6,
               fit_right=None, stretch_cap=9.0):
    """在横线上写字：line_y=横线y坐标，字底落在横线上方 rise 像素处。
    fit_right: 若给定(横线右端x)，自然宽度不足时摊加字间距铺满行宽(每字最多 stretch_cap px)，
    模拟真实书写把行写到边；超过则不动(不缩字，避免破坏手写感)。"""
    cx = float(x)
    extra = 0.0
    if fit_right:
        f = ImageFont.truetype(FONT_PATH, size)
        # getbbox/getlength/getmask 对 CJK 都返回版面宽(em宽), 会把 extra 算成 0;
        # 唯一可信的是画布渲染后裁剪的墨迹宽(悠哉体 em=56 时墨迹仅 ~45)
        natural = 0.0
        for ch in text:
            # 黑底白字: getbbox 算的是非零区域, 白底会把整张画布都算成"墨迹"
            probe = Image.new("L", (size * 2, size * 2), 0)
            ImageDraw.Draw(probe).text((10, 10), ch, font=f, fill=255)
            bb = probe.getbbox()
            natural += ((bb[2] - bb[0]) * 0.94) if bb else size * 0.5
        natural += len(text) * size * 0.04
        gap = fit_right - x - natural - 25  # 留25px收笔余量
        extra = max(0.0, min(gap / max(1, len(text)), stretch_cap))
    for ch in text:
        sz = max(10, int(size * random.uniform(0.95, 1.05)))
        ang = random.uniform(-3.0, 3.0) * jitter
        dx = random.uniform(-1.5, 1.5) * jitter
        dy = random.uniform(-2.0, 2.0) * jitter
        g = make_glyph(ch, sz, ang, ink)
        adv = g.width * 0.94 + (sz * 0.04 if not (ch.isascii() and ch.isalnum()) else 0) + extra
        base.alpha_composite(g, (int(cx + dx), int(line_y - rise - g.height + dy)))
        cx += adv
    return cx


def check_mark(base, cx, cy, size=34, width=5, ink=(50, 46, 60, 240)):
    d = ImageDraw.Draw(base)
    pts = [(cx - size * 0.45, cy + size * 0.08),
           (cx - size * 0.08, cy + size * 0.42),
           (cx + size * 0.55, cy - size * 0.48)]
    d.line(pts, fill=ink, width=width, joint="curve")


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else r"D:\03.其他应用\01.感谢卡\config_test.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else r"D:\03.其他应用\01.感谢卡\output\test_card.jpg"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    global FONT_PATH
    FONT_PATH = cfg.get("font", FONT_PATH)  # 支持在配置中指定字体
    random.seed(cfg.get("seed", 7))
    base = Image.open(BASE).convert("RGBA")
    ink = tuple(cfg.get("ink", [50, 46, 60, 235]))
    for item in cfg.get("texts", []):
        write_line(base, item["x"], item["line_y"], item["text"],
                   size=item.get("size", cfg.get("font_size", 54)),
                   ink=tuple(item.get("ink", ink)),
                   jitter=item.get("jitter", 1.0),
                   rise=item.get("rise", 6),
                   fit_right=item.get("fit_right"),
                   stretch_cap=item.get("stretch_cap", 9.0))
    for c in cfg.get("checks", []):
        check_mark(base, c["cx"], c["cy"], size=c.get("size", 34), width=c.get("width", 5))
    out = base.convert("RGB")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.save(out_path, quality=92)
    print("saved:", out_path)


if __name__ == "__main__":
    main()
