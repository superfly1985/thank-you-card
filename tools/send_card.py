# -*- coding: utf-8 -*-
"""send_card.py — 4C 感谢卡一条龙：渲染 → 预填 → 日期控件 → 上传 → DOM核验 → 等提交

用法:
  python tools/send_card.py <spec.json> [--dry]     # spec 模式（AI/模板）
  python tools/send_card.py --interactive [--dry]   # 问答模式（无需 AI）
  python tools/send_card.py --register              # 登记发卡人信息到 users.json

首次使用: 先 `python tools/login.py` 扫码登录一次（之后会话自动复用）。
退出码: 0=成功  2=需扫码登录(先跑 tools/login.py)  3=出错
"""
import json, sys, os, time, random, traceback
from datetime import date as _date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 仓库根(任意克隆位置可用)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import render_card as rc
from PIL import Image

CAT_X = {"合规": 453, "担当": 633, "贡献": 810, "关爱": 986}
SECTION_Y = {"behaviour": [537, 599], "impact": [722, 784], "appreciation": [909, 972]}
X_BODY = 260
FIT_RIGHT = 1115                      # 正文铺行目标右端
MAX_LINE = 16                         # 每行字数上限(首行14-16字最佳)
URL = "https://wj.qq.com/s2/28268428/3awq/"
STATE = os.path.join(ROOT, "auth_state.json")
PROFILE = os.path.join(ROOT, ".edge-profile")
OUT = os.path.join(ROOT, "output")
LOG = os.path.join(ROOT, "cards_log.jsonl")
USERS = os.path.join(ROOT, "users.json")

SURVEY_DEPTS = ["Production 生产部", "IT 信息技术部", "Purchasing 采购部", "IE 工程部",
                "Quality 质量部", "Logistics 物流部", "GMO 总经办", "Finance 财务部",
                "Sales 销售部", "HR 人力资源部", "ME 设备&设施部"]
DEPT_MAP = {"生产部": "Production 生产部", "质量部": "Quality 质量部", "质保部": "Quality 质量部",
            "物流部": "Logistics 物流部", "IT": "IT 信息技术部", "采购部": "Purchasing 采购部",
            "工程部": "IE 工程部", "总经办": "GMO 总经办", "财务部": "Finance 财务部",
            "销售部": "Sales 销售部", "人力资源部": "HR 人力资源部", "设备部": "ME 设备&设施部",
            "设备&设施部": "ME 设备&设施部"}
LEVEL_MAP = {"员工": "Employee 员工", "主管": "Supervisor 主管", "经理": "Manager and above 经理级及以上",
             "经理级及以上": "Manager and above 经理级及以上"}


def load_me():
    """从 users.json 读第一个注册用户, 映射为问卷选项文字; 没有则返回 None"""
    try:
        with open(USERS, encoding="utf-8") as f:
            users = json.load(f).get("users", [])
        if not users:
            return None
        u = users[0]
        return {
            "from_name": u.get("姓名", ""),
            "issuer_dept": DEPT_MAP.get(u.get("部门", ""), u.get("部门", "")),
            "issuer_level": LEVEL_MAP.get(u.get("职级", ""), u.get("职级", "")),
        }
    except Exception:
        return None


def split2(text, maxlen=MAX_LINE):
    """把一句话拆成 ≤2 行: 优先在标点处断, 否则按字数断。超长返回 None。"""
    text = text.strip()
    if len(text) <= maxlen:
        return [text]
    if len(text) > maxlen * 2:
        return None
    window = text[:maxlen]
    best = -1
    for p in "，。！？、；：":
        idx = window.rfind(p)
        if idx >= maxlen - 5:
            best = max(best, idx)
    if best >= 0:
        return [text[:best + 1], text[best + 1:]]
    return [text[:maxlen], text[maxlen:]]


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    for k in ("to", "category", "behaviour", "impact", "appreciation", "recipient_dept"):
        if k not in spec:
            raise SystemExit("spec 缺少必填字段: " + k)
    me = load_me() or {"from_name": "", "issuer_dept": "", "issuer_level": ""}
    spec.setdefault("date", _date.today().isoformat())
    spec.setdefault("product", "背包")
    spec.setdefault("from_name", me["from_name"])
    spec.setdefault("issuer_dept", me["issuer_dept"])
    spec.setdefault("issuer_level", me["issuer_level"])
    spec.setdefault("font", rc.FONT_PATH)
    for k in ("behaviour", "impact"):
        if len(spec[k]) > 2:
            raise SystemExit(k + " 最多2行")
    if len(spec["appreciation"]) > 1:
        raise SystemExit("appreciation 最多1行")
    return spec


def check_coverage(spec):
    """渲染前检查所有文字是否在子集字体里有墨迹(生僻字提示补字)"""
    from PIL import ImageFont, Image, ImageDraw
    f = ImageFont.truetype(spec.get("font", rc.FONT_PATH), 48)
    missing = set()
    texts = [spec["to"], spec["from_name"], spec["date"].replace("-", ".")]
    for key in ("behaviour", "impact", "appreciation"):
        texts += spec[key]
    for t in texts:
        for ch in t:
            if ch in missing or ch.strip() == "" or (ch.isascii() and ch.isalnum()):
                continue
            img = Image.new("L", (80, 80), 0)
            ImageDraw.Draw(img).text((10, 10), ch, font=f, fill=255)
            if not img.getbbox():
                missing.add(ch)
    if missing:
        raise SystemExit("以下字符在子集字体中缺字: {} \n请运行: python tools/make_subset.py {}".format(
            " ".join(sorted(missing)), " ".join(sorted(missing))))


def render(spec):
    base = Image.open(rc.BASE).convert("RGBA")
    random.seed(spec.get("seed", 11))
    rc.FONT_PATH = spec.get("font", rc.FONT_PATH)
    rc.write_line(base, 295, 342, spec["to"], size=58)
    rc.write_line(base, 565, 342, spec["from_name"], size=52)
    rc.write_line(base, 840, 342, spec["date"].replace("-", "."), size=46)
    for key, ys in SECTION_Y.items():
        lines = spec[key]
        for i, ln in enumerate(lines):
            fit = FIT_RIGHT if i < len(lines) - 1 else None
            rc.write_line(base, X_BODY, ys[i], ln, size=56, fit_right=fit)
    rc.check_mark(base, CAT_X[spec["category"]], 398)
    os.makedirs(OUT, exist_ok=True)   # 新克隆仓库没有 output/ 目录
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
                print("COOKIES: 已载入")
            except Exception as e:
                print("COOKIES: 载入失败(继续):", e)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4500)
        if "/r/login" in page.url:
            print("NEED_LOGIN: 会话失效, 请先运行  python tools/login.py  扫码后再试")
            ctx.close()
            sys.exit(2)
        # 未提交草稿会弹"继续填写/重新填写"对话框挡住表单, 本脚本总是全新填写 → 点重新填写
        try:
            page.locator("text=重新填写").first.click(timeout=4000)
            print("DRAFT: 检测到未提交草稿, 已选择重新填写")
            page.wait_for_timeout(2500)
        except Exception:
            pass
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

        if not dry:
            page.locator('input[type="file"]').first.set_input_files(photo, timeout=25000)
            page.wait_for_timeout(4000)
            print("UPLOAD:", photo)
        else:
            print("DRY: 跳过照片上传")

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
                okmark = "✓"
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


def interactive(dry):
    me = load_me()
    print("===== 4C 感谢卡生成 =====")
    if not me or not me.get("from_name"):
        print("首次使用请先登记发卡人信息: python tools/send_card.py --register")
        sys.exit(1)
    print("发卡人: {} / {} / {}".format(me["from_name"], me["issuer_dept"], me["issuer_level"]))
    to = input("收卡人姓名: ").strip()
    while not to:
        to = input("  收卡人姓名(必填): ").strip()
    print("收卡人部门:")
    for i, d in enumerate(SURVEY_DEPTS):
        print("  [{}] {}".format(i + 1, d))
    d_in = input("编号或直接输入: ").strip()
    if d_in.isdigit() and 1 <= int(d_in) <= len(SURVEY_DEPTS):
        dept = SURVEY_DEPTS[int(d_in) - 1]
    else:
        dept = DEPT_MAP.get(d_in, d_in)
    c_in = input("类别 [1]合规 [2]担当 [3]贡献 [4]关爱: ").strip()
    category = {"1": "合规", "2": "担当", "3": "贡献", "4": "关爱"}.get(c_in, "")
    while category not in CAT_X:
        c_in = input("  请输入 1-4: ").strip()
        category = {"1": "合规", "2": "担当", "3": "贡献", "4": "关爱"}.get(c_in, "")
    d = input("送卡日期 YYYY-MM-DD (回车=今天): ").strip() or _date.today().isoformat()
    product = input("文创产品 (回车=背包): ").strip() or "背包"

    def ask2(label):
        while True:
            raw = input(label + "（一句大白话，≤32字）: ").strip()
            lines = split2(raw)
            if lines:
                return lines
            print("  太长了，请压缩到 32 字以内")

    behaviour = ask2("【具体事件】")
    impact = ask2("【积极作用】")
    while True:
        app = input("【感谢与认可】（一句话）: ").strip()
        if app and len(app) <= MAX_LINE:
            break
        print("  请控制在 {} 字以内".format(MAX_LINE))

    spec = {
        "to": to, "category": category,
        "behaviour": behaviour, "impact": impact, "appreciation": [app],
        "date": d, "recipient_dept": dept, "product": product,
        "from_name": me["from_name"], "issuer_dept": me["issuer_dept"], "issuer_level": me["issuer_level"],
    }
    print("== 预览 ==")
    print(json.dumps(spec, ensure_ascii=False, indent=1))
    ok = input("确认生成并预填? (回车=确认 / n=取消): ").strip().lower()
    if ok == "n":
        print("已取消")
        return
    photo = render(spec)
    check_coverage(spec)
    run_browser(spec, photo, dry)


def register():
    me = load_me() or {}
    name = input("姓名: ").strip() or me.get("from_name", "")
    print("职级: [1]员工 [2]主管 [3]经理级及以上")
    lv = input("编号: ").strip()
    level = {"1": "员工", "2": "主管", "3": "经理级及以上"}.get(lv, lv)
    print("部门: 生产部/质量部(质保)/物流部/IT/采购/工程/总经办/财务/销售/HR/设备&设施部")
    dept = input("部门: ").strip() or me.get("issuer_dept", "")
    data = {"users": [], "_说明": "发卡人注册表(首次使用编辑或用 --register 生成)"}
    if os.path.exists(USERS):
        with open(USERS, encoding="utf-8") as f:
            old = json.load(f)
        data["users"] = old.get("users", [])
        data["_说明"] = old.get("_说明", data["_说明"])
    data["users"].append({"姓名": name, "职级": level, "部门": dept,
                          "登记时间": time.strftime("%Y-%m-%d"), "默认文创产品": "背包"})
    with open(USERS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("已登记:", name, level, dept, "→", USERS)


def main():
    argv = sys.argv[1:]
    dry = "--dry" in argv
    if "--register" in argv:
        return register()
    if "--interactive" in argv or "-i" in argv:
        return interactive(dry)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    spec = load_spec(args[0])
    check_coverage(spec)
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
