# -*- coding: utf-8 -*-
"""检测 To/From/日期 行三条横线的 x 线段范围"""
from PIL import Image
import json

SRC = r"D:\03.其他应用\01.感谢卡\assets\base_card.jpg"
img = Image.open(SRC).convert("L")
W, H = img.size
px = img.load()

# 横线 y 已知约 342.5，扫描该带
Y0, Y1 = 336, 350
segs = []
cur = None
for x in range(200, 1200):
    dark = sum(1 for y in range(Y0, Y1) if px[x, y] < 150)
    if dark >= 2:
        if cur is None:
            cur = [x, x]
        else:
            cur[1] = x
    else:
        if cur and cur[1] - cur[0] >= 15:  # 线段至少15px
            segs.append(cur)
        cur = None
if cur and cur[1] - cur[0] >= 15:
    segs.append(cur)

print(json.dumps({"to_row_segments": segs}, ensure_ascii=False))

# 同时确认各段的中点，便于摆放文字
mids = [((a + b) // 2, a, b) for a, b in segs]
print("segments(mid,start,end):", mids)
