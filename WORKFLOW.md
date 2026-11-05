# 4C 感谢卡工作流 v1.1（2026-11-05 共享打包版）

> 本仓库可直接分享：`git clone` → `python tools/setup_env.py` → `--register` → `login.py` → `--interactive`
> 详见 README.md。所有路径动态定位（任意克隆位置可用）；子集字体 3.81MB 已入库（GB2312 全汉字 6889 字，缺字用 make_subset.py 补）。
> 新增坑位：问卷会对未提交草稿弹「继续填写/重新填写」对话框挡住表单——脚本已自动点「重新填写」。
> 共享版命令：send_card.py `--interactive`(无AI问答) / `--register` / spec 模式；`login.py` 纯 Python 扫码；`setup_env.py` 一键环境。
> **分发决策（2026-11-05）**：维持源码分发 + setup_env 自动装环境（否决 PyInstaller exe 打包——50-80MB/杀软误报/每改必重打包；若未来要发给无法装 Python 的机器再上 exe 路线：`pyinstaller --collect-all playwright`）。
> 实测记录：C盘跨目录 dry 全绿、interactive 管道测试全绿、setup_env 4/4、login 已登录路径、register 流程。

## 业务流程（每次执行按此顺序）

0. **注册用户**（仅首次）：询问发卡人 姓名 / 职级 / 部门 → 写入 `users.json`。
   之后每次执行，"你的姓名（From）"从注册用户中选。
1. **提问收集**（每次都问）：
   - To 收卡人姓名（必问）
   - 收卡人部门
   - 日期（留空则默认当天）
   - 具体事件（必填，用户给素材，AI 润色）
   - BIA 四选一：合规 / 担当 / 贡献 / 关爱
2. **生成完整文案**：【Behaviour】具体事件 +【Impact】积极作用 +【Appreciation】感谢与认可，
   每段控制在 1–2 行（卡片每段只有 2 条横线）→ **等用户确认/修改后才继续**。
3. **生成手写模拟卡照片**：`python tools/render_card.py <config.json> <output.jpg>`，交用户验收。
4. **自动预填问卷**（腾讯问卷需登录）：
   - 登录：自动化浏览器打开问卷 → 截二维码给用户扫码（登录动作必须用户完成）
   - 预填：按确认后的文案自动填写全部字段
   - **提交按钮留给用户手动点**（提交交给人工）

## 技术备忘

- 底图：`assets/base_card.jpg`（1326×1280，空白卡照片）
- 已检测坐标（实际像素）：
  - To/From/日期 行横线 y=342；线段 x：To 285–459、From 557–731、日期 826–1098
  - BIA 复选框行 y≈398，框中心 x：合规≈453、担当≈633、贡献≈810、关爱≈986
  - 【Behaviour】区横线 y=476(标题行)、537、599
  - 【Impact】区横线 y=661(标题行)、722、784
  - 【Appreciation】区横线 y=846(标题行)、909、972
- 字体（用户要求：中性笔风格，弃用华文行楷/钢笔感）：
  - ✅ **已选定：`fonts/Yozai-Regular.ttf` 悠哉体 v0.868**（2026-11-05 用户确认，config 默认已指向）
  - 备选：`fonts/Xiaolai-Regular.ttf` 小赖体 v1.0.0（略潦草）、`fonts/LXGWWenKai-Regular.ttf` 霞鹜文楷（工整对照）
  - 对比图存档：`output/compare_fonts.jpg`；config 中 "font" 字段切换
- 下载渠道备忘：沙箱代理 8861 会断流（exit 56/502），GitHub release 走 `https://ghfast.top/https://github.com/...` 镜像直连更稳
- 渲染脚本：`tools/render_card.py`（配置驱动：`config_test.json` 是周跃样张的测试配置）
- 坐标检测脚本：`tools/detect_lines.py`、`tools/detect_to_row.py`
- 问卷：https://wj.qq.com/s2/28268428/3awq/ ，标题「"4C" 感谢卡线上登记」
  - **必须登录后作答**；腾讯问卷连接器只能管自己账号的问卷，读不了第三方问卷
  - 自动化：playwright-cli（已全局安装）+ 本机 Edge
  - ⚠️ 会话生命周期：浏览器会话**不跨 Bash 命令存活**（命令结束浏览器即关，续用会报 "no browsers"）。
    单条命令内 open→操作 要用 `;`/`&&` 串起来。登录扫码（耗时数分钟）需用 run_in_background 保活 + `--persistent`
    配置档，登录成功后 `state-save auth.json` 备份会话。【待登录时实测】
- 输出目录：`output/`（按 `card_<收卡人>_<日期>.jpg` 命名，不复写）

## 问卷结构（2026-11-05 登录后实测；登录账号：微信 Panda付）

标题：「"4C" 感谢卡线上登记」。规则：不可赠送给自己；线上提交后送卡才算有效；照片上传=手写卡照片（≤300MB，文字清晰即可）。

| # | 题目 | 类型 | 必填 | 选项/备注 |
|---|------|------|:---:|-----------|
| 01 | 发卡人部门 Issuer's Department | 单选 | ✓ | Production生产部 / IT / Purchasing采购部 / IE工程部 / **Quality质量部** / Logistics物流部 / GMO总经办 / Finance财务部 / Sales销售部 / HR人力资源部 / ME设备&设施部 |
| 02 | 发卡人职级 Issuer's Level | 单选 | ✓ | Employee员工 / **Supervisor主管** / Manager and above经理级及以上 |
| 03 | 发卡人姓名 Issuer's Name | 写入式文本 | ✓ | 用户确认：直接写入，非名单 |
| 04 | 收卡人部门 Recipient's Department | 单选 | ✓ | 同 01 |
| 05 | 收卡人姓名 Recipient's Name | 写入式文本 | ✓ | 用户确认：直接写入，非名单 |
| 06 | 送卡日期 Date of Giving | 日期 | ✓ | ⚠️ 说明写"默认当天"但**实际不会自动填**，占位符"请选择日期"、value 为空 → 预填时必须显式填写 |
| 07 | 感谢卡照片 | 文件上传 | ✓ | 放 render_card.py 产出的模拟手写卡照片 |
| 08 | 最想收到的文创产品 | 图片单选 | ✓ | 向日葵抱枕 / 帆布包 / 咖啡杯 / 笔记本 / 磁吸手机支架 / 背包 / 中性笔 / 暖手包 / U型枕（另有1项未识别） |
| 09 | 还想要哪些文创产品 | 长文本 | — | 可空 |

- 注册信息对齐结果：付立业=质量部 → 选项「Quality 质量部」✓、主管 → 「Supervisor 主管」✓，users.json 原文即规范写法。
- 08 文创产品：必答，用户默认「背包」（存 users.json），每次可改。

## 协同模式（2026-11-05 与用户确认）

| 模式 | 分工 | 优缺点 |
|------|------|--------|
| A. 自动化 Edge 窗口（**默认采用**） | 我在自动化 Edge 里预填全部字段并上传照片 → 用户在桌面上直接看这个真实窗口目检 → **用户亲手点提交** | 优：登录态现成、我填得快且能截图自检；缺：窗口是独立 Edge，不是 WorkBuddy 右边栏 |
| B. 右边栏人工填 | present_files 打开问卷链接到 WorkBuddy 右边栏 → 用户自己操作，我出全字段对照表 | 优：用户全程掌控；缺：面板登录态与自动化不互通，需在面板重新扫码；我读不到面板状态，只能出对照表 |

## 一条龙脚本（2026-11-05 v1 上线，dry 验证通过）

`python tools/send_card.py <spec.json> [--dry]`（真实跑用后台方式运行，脚本轮询提交、抓成功页）

- spec.json（LLM 每张卡只写这些）：to / category(合规|担当|贡献|关爱) / behaviour[≤2行] / impact[≤2行] / appreciation[≤1行] / date / recipient_dept(问卷选项原文) / product(默认背包)；可选 from_name、issuer_dept、issuer_level、seed
  - ⚠️ **分行规则（方案A）**：每段**首行 14–16 字**（写满行宽的关键，悠哉体字形窄，13 字撑不到边），**尾行自然**（人工样张的段尾行本来就留白）；渲染端对非末行自动摊字间距（≤9px/字）铺到横线右端
  - 铺行调试教训：PIL 的 `getbbox`/`getlength`/`getmask` 对 CJK 返回的都是**字幅框**(em宽≈56)，不是墨迹宽(实际仅~45)；且探针画布必须**黑底白字**（白底时 getbbox 把整张画布当非零区）。墨迹宽唯一可信来源 = 画布渲染后裁剪
- 脚本内部：渲染卡图（坐标/勾选位映射硬编码：担当633/贡献810/合规453/关爱986）→ 开 headed Edge（`.edge-profile` 持久档 + auth_state.json cookies）→ 登录检查(跳登录页则退出码2) → 预填全部字段 → **日期控件选择**（today-cell 策略）→ 上传照片 → DOM 读回核验（文字报告，替代视觉看图）→ 整页截图 → 轮询等用户点提交（检测"提交成功"等文案）→ 抓成功页 → 记 cards_log.jsonl → 退出
- 退出码：0 成功 / 2 需扫码 / 3 出错
- **LLM 每张卡只需 ~4 次交互**：选项卡提问 → 三句话文案+spec → 后台跑脚本读报告 → 交付（原来 ~15 次）
- 依赖备忘：`playwright` Python 库已装（**必须走用户 Clash 代理 7890 从官方 PyPI 装**；沙箱内/清华镜像均报 no matching distribution）；浏览器用系统 Edge，无需下载
- dry 模式：跳过上传与提交等待，用于验证管线

## playwright-cli 直操作备援（脚本失效时的人工兜底路线）

- **playwright-cli 默认无头！** 用户要看窗口必须 `open --browser=msedge --headed --persistent <url>`。
- 会话保活：`tools/login_watch.sh`（登录成功 → `state-save auth_state.json` → sleep 5400 常驻）。
  登录态丢失时：先 `open --headed --persistent` 试，仍跳登录页再走扫码；或 `state-load auth_state.json`。
- 表单 DOM 要点：
  - 单选 radio 是**隐藏 input**，`check()` 会超时 → 用 `page.locator('text=<选项文字>').click()` 点 label
  - 同名选项出现两次（发卡人/收卡人部门）：发卡人用 `.first()`，收卡人用 `.nth(1)`
  - 文本框全局序号：`input[type=text]` nth(0)=Q3发卡人姓名、nth(1)=Q5收卡人姓名（nth(2)=日期、nth(3)=Q9）
  - 08 文创选项是 div 卡片（非 input）→ `text=背包` 点击即可
  - ⚠️⚠️ Q6 日期**绝不能 fill()**：手输只改显示值，控件内部状态不更新（提交数据会缺日期）！
    正确做法：click 日期输入框 → 弹出日历控件 → 点击当天日期格（卡片#2 实测验证此路线）
  - 照片上传：`page.locator('input[type=file]').first().setInputFiles('<卡图路径>')`，实测可用
  - **同一微信账号可多次提交**（实测：提交后重新打开 URL 又是空白表单），无一人一卡限制 → 不用重复扫码
- 测试纪律：测试阶段**不传照片不提交**；提交永远由用户手动点击。
- 测试记录：filled_test.png（周跃/物流部测试数据，全部字段就位，未上传未提交）。
- 正式第一张（周跃）：filled_final.png = 提交前终态（质量部/主管/付立业/**质量部**/周跃/2026-11-05/照片已传/背包），提交由用户在 Edge 窗口手动完成。

## 待办

- [x] 用户注册信息（付立业/主管/质量部）
- [x] 字体选定（悠哉体）
- [x] 登录问卷读取题目结构
- [x] 08 文创产品默认选择（背包，已存 users.json）
- [x] 03/05 姓名字段确认（写入式，用户确认）
- [ ] 正式跑第一张卡
