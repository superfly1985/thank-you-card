# 4C 感谢卡工作流

手写模拟"4C"感谢卡 + 腾讯问卷自动预填的一条龙工具。
渲染卡面照片（手写字体模拟）→ 自动填写线上登记问卷 → 上传照片 → **人工确认后手动点提交**。

## 环境要求

- Windows + 自带 Edge 浏览器（无需下载任何浏览器）
- Python 3.9+

## 快速上手（3 条命令）

```bash
python tools/setup_env.py              # ① 自检并安装依赖（清华源失败自动回退官方）
python tools/send_card.py --register   # ② 登记发卡人信息（姓名/职级/部门，只需一次）
python tools/login.py                  # ③ 弹出窗口扫码登录问卷（只需一次，会话自动复用）
```

日常用：

```bash
python tools/send_card.py --interactive    # 问答式生成一张卡（无需 AI）
python tools/send_card.py spec_xxx.json    # 或用模板批量生成
```

流程：脚本自动渲染卡面 → 预填问卷 → 上传照片 → 弹出核验报告。
**提交按钮永远由你本人在 Edge 窗口里亲手点击。**

## spec.json 字段

| 字段 | 说明 |
|---|---|
| to / recipient_dept | 收卡人姓名 / 部门（问卷选项原文，如 `Quality 质量部`） |
| category | 合规 / 担当 / 贡献 / 关爱（手写卡勾选） |
| behaviour / impact | 各 ≤2 行，**每段首行 14–16 字**（铺满行宽的关键），尾行自然 |
| appreciation | 1 行 |
| date | YYYY-MM-DD，默认今天 |
| product | 文创产品，默认 背包 |
| from_name / issuer_dept / issuer_level | 缺省取 users.json 第一个注册用户 |

## 常见问题

| 症状 | 处理 |
|---|---|
| 提示 NEED_LOGIN / 跳到登录页 | `python tools/login.py` 重新扫码（会话 Cookie 偶尔过期） |
| 提示缺字（生僻姓名） | `python tools/make_subset.py 该字` 重新生成子集字体 |
| pip 安装失败 | 脚本已自动换源；公司内网可设 `HTTPS_PROXY` 后重跑 setup_env.py |
| 非 Windows | 把脚本里 `channel="msedge"` 改为 `"chrome"`，并 `playwright install chromium` |
| 字迹/铺行要调 | `tools/render_card.py`（字号/间距/勾选坐标）与 `spec` 分行 |

## 目录说明

- `tools/render_card.py` 渲染引擎（坐标已校准：To/From/日期线、三区横线、四个勾选框）
- `tools/send_card.py` 一条龙主脚本 / `tools/login.py` 登录 / `tools/setup_env.py` 环境
- `tools/make_subset.py` 字体子集生成（GB2312 全汉字 + ASCII，缺字可补）
- `fonts/Yozai-Subset.ttf` 悠哉体精简子集（OFL 开源，可商用）
- `assets/` 卡面底图；`output/` 生成物（不入库）；`cards_log.jsonl` 提交记录

## 隐私

- `auth_state.json` / `.edge-profile/` / `output/` 均已 gitignore，**不会**上传登录凭据
- `assets/` 含公司卡面照片，**请将本仓库保持为 Private**
