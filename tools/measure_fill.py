# -*- coding: utf-8 -*-
"""量化诊断: 横线可写宽度 vs 实际墨迹占用(渲染卡 + 人工样张)"""
from PIL import Image

ROOT = r"D:\03.其他应用\01.感谢卡"
BODY_YS = [537, 599, 722, 784, 909, 972]


def load_px(p):
    return Image.open(p).convert("L").load()


def ink_extent(px, y, thresh=110, up=55, down=6, x0=150, x1=1250):
    """横线上方区域的墨迹(深色)x范围, 避开横线本身"""
    xs = [x for x in range(x0, x1)
          if any(px[x, yy] < thresh for yy in range(y - up, y - down))]
    return (min(xs), max(xs)) if xs else None


def line_extent(px, y, thresh=170, x0=200, x1=1150):
    xs = [x for x in range(x0, x1) if any(px[x, yy] < thresh for yy in range(y - 3, y + 4))]
    return (min(xs), max(xs)) if xs else None


# 1) 底图: 各横线自身的 x 范围 = 可写容量
px_base = load_px(ROOT + r"\assets\base_card.jpg")
print("== 底图横线(可写区域) ==")
for y in [342] + BODY_YS:
    e = line_extent(px_base, y)
    print("  y={} 范围{} 宽{}px".format(y, e, e[1] - e[0] if e else 0))

# 2) 王宁渲染卡: 各正文线墨迹占用
px_wang = load_px(ROOT + r"\output\card_王宁_20261105.jpg")
print("== 王宁卡(渲染) 墨迹占用 vs 线右端(约1120) ==")
for y, label in [(537, "B1"), (599, "B2"), (722, "I1"), (784, "I2"), (909, "A1")]:
    e = ink_extent(px_wang, y)
    if e:
        print("  {} y={} 墨迹{} 到右端空白约{}px (~{}字)".format(label, y, e, 1120 - e[1], round((1120 - e[1]) / 55)))

# 3) 人工样张(周跃): 先检测它的横线, 再量墨迹
px_ref = load_px(ROOT + r"\assets\ref_card_filled.jpg")
W, H = Image.open(ROOT + r"\assets\ref_card_filled.jpg").size
cands = []
for y in range(int(H * 0.3), int(H * 0.82)):
    cnt = sum(1 for x in range(int(W * 0.18), int(W * 0.85), 2) if px_ref[x, y] < 170) * 2
    if cnt >= (int(W * 0.85) - int(W * 0.18)) * 0.55:
        cands.append(y)
groups = []
for y in cands:
    if groups and y - groups[-1][-1] <= 3:
        groups[-1].append(y)
    else:
        groups.append([y])
ref_ys = [sum(g) // len(g) for g in groups]
print("== 人工样张: 检测到横线 y =", ref_ys)
for i, y in enumerate(ref_ys):
    e = ink_extent(px_ref, y)
    le = line_extent(px_ref, y)
    if e and le:
        print("  线{} y={} 线范围{} 墨迹{} 右侧空白{}px".format(i + 1, y, le, e, le[1] - e[1]))
