# -*- coding: utf-8 -*-
"""login.py — 弹出浏览器扫码登录腾讯问卷（每台电脑只需一次）
用法: python tools/login.py
流程: 打开有头 Edge → 若跳登录页则在窗口里扫码（或截二维码到 output/login_qr.png 用手机扫）
     → 登录成功自动保存会话(auth_state.json) → 之后 send_card.py 自动复用
"""
import os, sys, time, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://wj.qq.com/s2/28268428/3awq/"
STATE = os.path.join(ROOT, "auth_state.json")
PROFILE = os.path.join(ROOT, ".edge-profile")
QR = os.path.join(ROOT, "output", "login_qr.png")


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(os.path.dirname(QR), exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, channel="msedge", headless=False,
            viewport={"width": 1280, "height": 940})
        if os.path.exists(STATE):
            try:
                with open(STATE, encoding="utf-8") as f:
                    ctx.add_cookies(json.load(f).get("cookies", []))
            except Exception:
                pass
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4500)

        if "/r/login" not in page.url:
            print("已经是登录状态, 无需扫码")
            ctx.storage_state(path=STATE)
            print("STATE_SAVED:", STATE)
            ctx.close()
            return

        # 勾选用户协议(若存在)
        try:
            page.evaluate(
                "() => { const c = document.querySelector('input[type=checkbox]');"
                " if (c && !c.checked) c.click(); }")
        except Exception:
            pass
        try:
            page.screenshot(path=QR)
            print("QR_SAVED:", QR, "(也可直接在弹出的窗口里扫码)")
        except Exception:
            pass

        print("请在弹出的窗口中扫码登录（微信/QQ），最长等待 10 分钟...")
        deadline = time.time() + 600
        while time.time() < deadline:
            time.sleep(4)
            url = page.url
            if "/r/login" not in url:
                page.wait_for_timeout(3000)
                ctx.storage_state(path=STATE)
                print("LOGGED_IN")
                print("STATE_SAVED:", STATE)
                ctx.close()
                return
        print("TIMEOUT: 10 分钟未检测到登录, 请重跑本命令")
        ctx.close()
        sys.exit(2)


if __name__ == "__main__":
    main()
