# -*- coding: utf-8 -*-
"""检测感谢卡底图上的横线坐标（手写文字需要落在这些线上）"""
from PIL import Image
import json, sys

SRC = r"D:\03.其他应用\01.感谢卡\assets\base_card.jpg"

img = Image.open(SRC).convert("L")
W, H = img.size
px = img.load()

X0, X1 = int(W * 0.17), int(W * 0.85)   # 白色内卡区域的大致横向范围
Y0, Y1 = int(H * 0.18), int(H * 0.82)   # 纵向搜索范围（避开顶部标题与底部名言）

TH_DARK = 170       # 灰度低于此视为深色
MIN_COUNT = int((X1 - X0) * 0.55)  # 一行中深色像素数量超过此值视为横线

candidates = []
for y in range(Y0, Y1):
    cnt = 0
    for x in range(X0, X1, 2):  # 步长2加速
        if px[x, y] < TH_DARK:
            cnt += 1
    cnt *= 2  # 补偿步长
    if cnt >= MIN_COUNT:
        candidates.append((y, cnt))

# 合并相邻行（一条横线可能有2-4px厚度）
groups = []
for y, cnt in candidates:
    if groups and y - groups[-1][-1][0] <= 3:
        groups[-1].append((y, cnt))
    else:
        groups.append([(y, cnt)])

lines = []
for g in groups:
    ys = [y for y, _ in g]
    peak = max(g, key=lambda t: t[1])
    lines.append({"y_center": round(sum(ys) / len(ys), 1), "y_peak": peak[0], "dark_count": peak[1], "thickness": len(ys)})

print(json.dumps({"size": [W, H], "search_x": [X0, X1], "lines": lines}, ensure_ascii=False, indent=1))

# 顺便输出BIA复选框那一行的深色列分布（用于定位四个方框）
bia_band = None
if lines:
    pass
# BIA行大约在 To 行下方，用固定比例估计：显示图中约 y=325/1044 → 全图
bia_y = int(H * 0.311)
row = []
for x in range(X0, X1):
    dark = 0
    for dy in range(-10, 11):
        yy = bia_y + dy
        if 0 <= yy < H and px[x, yy] < 140:
            dark += 1
    row.append((x, dark))
# 找出深色聚集的列段
segs = []
cur = None
for x, d in row:
    if d >= 3:
        if cur is None:
            cur = [x, x]
        else:
            cur[1] = x
    else:
        if cur and cur[1] - cur[0] >= 4:
            segs.append(cur)
        cur = None
if cur and cur[1] - cur[0] >= 4:
    segs.append(cur)
print("BIA_row_y_est:", bia_y)
print("BIA_dark_segments:", json.dumps(segs))
