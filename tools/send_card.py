# -*- coding: utf-8 -*-
"""send_card.py — 4C 感谢卡一条龙：渲染 → 预填 → 日期控件 → 上传 → DOM核验 → 等提交

用法:
  python send_card.py <spec.json> [--dry]

spec.json (LLM 只需提供这些):
  to            收卡人姓名 (必填)
  category      合规/担当/贡献/关爱 (必填, 渲染勾选框)
  behaviour     [行1, 行2] 每段最多2行 (必填)
  impact        [行1, 行2] (必填)
  appreciation  [行1] (必填)
  date          "YYYY-MM-DD" (默认今天)
  recipient_dept 问卷选项原文, 如 "Quality 质量部" (必填)
  product       文创产品, 默认 "背包"
  可选覆盖: from_name(默认付立业), issuer_dept(默认 Quality 质量部),
            issuer_level(默认 Supervisor 主管), seed

退出码: 0=成功(或dry完成)  2=需扫码登录  3=出错(看输出)
"""
import json, sys, os, time, random, traceback
from datetime import date as _date

ROOT = r"D:\03.其他应用\01.感谢卡"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import render_card as rc
from PIL import Image

CAT_X = {"合规": 453, "担当": 633, "贡献": 810, "关爱": 986}
SECTION_Y = {"behaviour": [537, 599], "impact": [722, 784], "appreciation": [909, 972]}
X_BODY = 260
URL = "https://wj.qq.com/s2/28268428/3awq/"
STATE = os.path.join(ROOT, "auth_state.json")
PROFILE = os.path.join(ROOT, ".edge-profile")
OUT = os.path.join(ROOT, "output")
FONT_DEFAULT = os.path.join(ROOT, "fonts", "Yozai-Regular.ttf")
LOG = os.path.join(ROOT, "cards_log.jsonl")


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    for k in ("to", "category", "behaviour", "impact", "appreciation", "recipient_dept"):
        if k not in spec:
            raise SystemExit("spec 缺少必填字段: " + k)
    for k in ("behaviour", "impact", "appreciation"):
        if len(spec[k]) > 2:
            raise SystemExit(k + " 最多2行")
        if not spec[k]:
            raise SystemExit(k + " 至少1行")
    spec.setdefault("date", _date.today().isoformat())
    spec.setdefault("product", "背包")
    spec.setdefault("from_name", "付立业")
    spec.setdefault("issuer_dept", "Quality 质量部")
    spec.setdefault("issuer_level", "Supervisor 主管")
    spec.setdefault("font", FONT_DEFAULT)
    return spec


def render(spec):
    base = Image.open(rc.BASE).convert("RGBA")
    random.seed(spec.get("seed", 11))
    rc.FONT_PATH = spec["font"]
    rc.write_line(base, 295, 342, spec["to"], size=58)
    rc.write_line(base, 565, 342, spec["from_name"], size=52)
    rc.write_line(base, 840, 342, spec["date"].replace("-", "."), size=46)
    for key, ys in SECTION_Y.items():
        lines = spec[key]
        for i, ln in enumerate(lines):
            # 方案A: 非末行自适应铺满行宽(铺到横线右端), 段尾行保持自然(与人工书写一致)
            fit = 1115 if i < len(lines) - 1 else None
            rc.write_line(base, X_BODY, ys[i], ln, size=56, fit_right=fit)
    rc.check_mark(base, CAT_X[spec["category"]], 398)
    photo = os.path.join(OUT, "card_{}_{}.jpg".format(spec["to"], spec["date"].replace("-", "")))
    base.convert("RGB").save(photo, quality=92)
    print("RENDER:", photo)
    return photo


def run_browser(spec, photo, dry):
    from playwright.sync_api import sync_playwright
    filled_shot = os.path.join(OUT, "filled_{}.png".format(spec["to"]))
    success_shot = os.path.join(OUT, "success_{}_{}.png".format(spec["to"], spec["date"].replace("-", "")))
    issues = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, channel="msedge", headless=False,
            viewport={"width": 1280, "height": 940})
        if os.path.exists(STATE):
            try:
                with open(STATE, encoding="utf-8") as f:
                    ctx.add_cookies(json.load(f).get("cookies", []))
                print("COOKIES: auth_state.json 已载入")
            except Exception as e:
                print("COOKIES: 载入失败(继续):", e)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4500)
        if "/r/login" in page.url:
            print("NEED_LOGIN: 会话失效, 请重新扫码后重试")
            ctx.close()
            sys.exit(2)
        page.wait_for_selector('input[type="radio"]', timeout=25000)

        def ct(text, nth=0):
            page.locator("text={}".format(text)).nth(nth).click(timeout=12000)

        ct(spec["issuer_dept"], 0)
        page.locator('input[type="text"]').nth(0).fill(spec["from_name"], timeout=12000)
        ct(spec["recipient_dept"], 1)
        page.locator('input[type="text"]').nth(1).fill(spec["to"], timeout=12000)
        ct(spec["issuer_level"], 0)
        ct(spec["product"], 0)
        print("FILL: 单选/文本/文创 完成")

        # 日期: 点输入框打开控件, 点"今天"或指定日的格子
        page.locator('input[type="text"]').nth(2).click(timeout=12000, force=True)
        page.wait_for_selector('[class*="date-picker__panel"]', timeout=12000)
        today = _date.today().isoformat()
        picked = page.evaluate(
            """(want) => {
              const cells = [...document.querySelectorAll('[class*="date-picker__cell"]')];
              let c = null, how = '';
              if (want.today) {
                c = cells.find(x => /--now|today/.test(x.className));
                how = 'today-cell';
              }
              if (!c) {
                const d = String(want.day);
                c = cells.find(x => x.textContent.trim() === d && !/(disabled|other|prefix|suffix)/i.test(x.className));
                how = 'daynum:' + d;
              }
              if (c) { c.click(); return how; }
              return 'NOT_FOUND';
            }""",
            {"today": spec["date"] == today, "day": int(spec["date"][8:10])},
        )
        page.wait_for_timeout(800)
        date_val = page.locator('input[type="text"]').nth(2).input_value()
        print("DATE: 策略={} 输入框值={}".format(picked, date_val))
        if date_val.replace("/", "-") != spec["date"]:
            issues.append("日期不符: {} != {}".format(date_val, spec["date"]))

        # 上传照片
        if not dry:
            page.locator('input[type="file"]').first.set_input_files(photo, timeout=25000)
            page.wait_for_timeout(4000)
            print("UPLOAD:", photo)
        else:
            print("DRY: 跳过照片上传")

        # DOM 读回核验
        st = page.evaluate(
            """() => {
              const rs = [...document.querySelectorAll('input[type=radio]')].map(r => ({
                checked: r.checked,
                label: ((r.closest('label') || r.parentElement || {}).innerText || '').trim().slice(0, 30)
              }));
              const ts = [...document.querySelectorAll('input[type=text]')].map(t => t.value);
              const f = document.querySelector('input[type=file]');
              return {radios: rs, texts: ts, file: f ? f.value : null};
            }"""
        )
        rs = st["radios"]

        def checked_in(rng):
            for r in rng:
                if r["checked"]:
                    return r["label"]
            return "(空)"

        report = [
            ("01 发卡人部门", checked_in(rs[0:11]), spec["issuer_dept"]),
            ("02 发卡人职级", checked_in(rs[11:14]), spec["issuer_level"]),
            ("03 发卡人姓名", st["texts"][0], spec["from_name"]),
            ("04 收卡人部门", checked_in(rs[14:25]), spec["recipient_dept"]),
            ("05 收卡人姓名", st["texts"][1], spec["to"]),
            ("06 送卡日期", st["texts"][2], spec["date"]),
            ("07 照片", (st["file"] or "").split("\\")[-1], photo.split("\\")[-1] if not dry else "(dry跳过)"),
            ("08 文创产品", spec["product"], spec["product"]),
        ]
        print("== 核验报告 ==")
        for name, actual, expect in report:
            if name == "08 文创产品":
                okmark = "✓"  # 文创为 div 卡片, 点击即选中, 以点击成功为准
            elif dry and name == "07 照片":
                okmark = "✓(dry跳过)"
            else:
                okmark = "✓" if expect in (actual or "") or actual == expect else "✗"
            print("  {} 实际[{}] 期望[{}] {}".format(name, actual, expect, okmark))
            if okmark == "✗":
                issues.append(name + " 不符")
        page.screenshot(path=filled_shot, full_page=True)
        print("SHOT:", filled_shot)

        if dry:
            print("DRY_DONE: 全流程(除上传)验证通过" if not issues else "DRY_DONE_WITH_ISSUES")
            ctx.close()
            return

        # 轮询等待用户提交
        print("WAIT_SUBMIT: 请在 Edge 窗口核对并点提交 (脚本持续监听)")
        while True:
            txt = page.evaluate("document.body.innerText.slice(0, 2500)")
            if ("提交成功" in txt) or ("投票到此结束" in txt) or ("您已提交" in txt) or ("已成功提交" in txt):
                page.wait_for_timeout(2500)
                page.screenshot(path=success_shot, full_page=True)
                print("SUBMITTED: 提交成功")
                print("SHOT:", success_shot)
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "to": spec["to"], "category": spec["category"], "date": spec["date"],
                        "photo": photo, "recipient_dept": spec["recipient_dept"],
                        "product": spec["product"], "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }, ensure_ascii=False) + "\n")
                print("LOG: cards_log.jsonl 已记录")
                break
            time.sleep(5)
        ctx.close()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    if not args:
        raise SystemExit("用法: python send_card.py <spec.json> [--dry]")
    spec = load_spec(args[0])
    photo = render(spec)
    try:
        run_browser(spec, photo, dry)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("ERROR: 流程中断, 退出码3")
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
