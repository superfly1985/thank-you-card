# -*- coding: utf-8 -*-
"""用三款候选中性笔字体各渲染一张测试卡，并拼成纵向对比图"""
import json, subprocess, os
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\03.其他应用\01.感谢卡"
CFG_BASE = os.path.join(ROOT, "config_test.json")
OUTDIR = os.path.join(ROOT, "output")

FONTS = [
    ("Yozai 中性笔", os.path.join(ROOT, "fonts", "Yozai-Regular.ttf"), "yozai"),
    ("Xiaolai 小赖", os.path.join(ROOT, "fonts", "Xiaolai-Regular.ttf"), "xiaolai"),
    ("LXGW WenKai 文楷", os.path.join(ROOT, "fonts", "LXGWWenKai-Regular.ttf"), "wenkai"),
]

with open(CFG_BASE, encoding="utf-8") as f:
    base_cfg = json.load(f)

imgs = []
label_font = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 40)

for name, font_path, tag in FONTS:
    cfg = dict(base_cfg)
    cfg["font"] = font_path
    cfg_path = os.path.join(OUTDIR, f"_cfg_{tag}.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    out_path = os.path.join(OUTDIR, f"test_{tag}.jpg")
    subprocess.run(["python", os.path.join(ROOT, "tools", "render_card.py"), cfg_path, out_path], check=True)
    img = Image.open(out_path).convert("RGB")
    imgs.append((name, img))

# 纵向拼接：每张上方加 70px 标签条
W = imgs[0][1].width
LABEL_H = 70
total_h = sum(img.height + LABEL_H for _, img in imgs) + 20
canvas = Image.new("RGB", (W, total_h), (245, 245, 245))
y = 0
d = ImageDraw.Draw(canvas)
for name, img in imgs:
    d.rectangle([0, y, W, y + LABEL_H], fill=(60, 60, 70))
    d.text((30, y + 12), name, font=label_font, fill=(255, 255, 255))
    y += LABEL_H
    canvas.paste(img, (0, y))
    y += img.height
cmp_path = os.path.join(OUTDIR, "compare_fonts.jpg")
canvas.save(cmp_path, quality=88)
print("saved:", cmp_path)
