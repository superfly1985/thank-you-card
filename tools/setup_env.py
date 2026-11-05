# -*- coding: utf-8 -*-
"""setup_env.py — 环境一键自检与安装（克隆仓库后先跑我）
用法: python tools/setup_env.py
做四件事: 1)检查Python版本 2)安装依赖(清华源→官方源自动回退) 3)检查Edge 4)检查字体
"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSET = os.path.join(ROOT, "fonts", "Yozai-Subset.ttf")

DEPS = ["pillow", "playwright"]


def pip_install(pkg):
    sources = [
        ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        [],  # 官方源(有代理的环境用环境变量)
    ]
    for src in sources:
        cmd = [sys.executable, "-m", "pip", "install", pkg] + src
        print("安装", pkg, "..." if src else "(官方源)...")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return True
        print("  该源失败, 换下一个")
    return False


def main():
    print("== 1/5 Python版本 ==")
    v = sys.version_info
    print("  Python {}.{}.{} {}".format(v.major, v.minor, v.micro, "✓" if v >= (3, 9) else "✗ 需要 3.9+"))
    if v < (3, 9):
        sys.exit(1)

    print("== 2/5 依赖 ==")
    for pkg in DEPS:
        mod = "PIL" if pkg == "pillow" else pkg
        try:
            __import__(mod)
            print("  {} 已安装 ✓".format(pkg))
        except ImportError:
            ok = pip_install(pkg)
            print("  {} {}".format(pkg, "安装成功 ✓" if ok else "安装失败 ✗ (检查网络/代理后重跑)"))
            if not ok:
                sys.exit(1)

    print("== 3/5 Edge 浏览器 ==")
    edge = False
    if sys.platform == "win32":
        for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
            if os.path.exists(p):
                edge = True
        if not edge:
            import winreg
            try:
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe")
                edge = True
            except OSError:
                pass
    print("  Edge {}".format("找到 ✓ (无需额外下载浏览器)" if edge else
                           "未找到 ⚠ Windows请装Edge; Mac/Linux改用chrome: 把脚本中 channel='msedge' 改为 'chrome'"))
    if edge:
        print("  Edge 启动冒烟测试...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch(channel="msedge", headless=True)
                pg = b.new_page()
                pg.goto("about:blank")
                b.close()
            print("  playwright 可正常驱动 Edge ✓")
        except Exception as e:
            print("  Edge 启动失败 ✗:", str(e)[:120])
            print("  处理: python -m playwright install chromium 后, 把脚本中 channel='msedge' 改为 'chromium'")

    print("== 4/5 联网与账号状态 ==")
    import urllib.request
    try:
        urllib.request.urlopen("https://wj.qq.com", timeout=10)
        print("  wj.qq.com 可达 ✓")
    except Exception as e:
        print("  wj.qq.com 不可达 ⚠ 检查网络/代理:", str(e)[:80])
    users_file = os.path.join(ROOT, "users.json")
    registered = False
    try:
        import json as _json
        with open(users_file, encoding="utf-8") as f:
            registered = bool(_json.load(f).get("users"))
    except Exception:
        pass
    print("  发卡人注册: {}".format("已注册 ✓" if registered else "未注册 → python tools/send_card.py --register"))
    print("  问卷登录态: {}".format("已保存 ✓ (若失效重跑 tools/login.py)"
                                  if os.path.exists(os.path.join(ROOT, "auth_state.json"))
                                  else "未登录 → python tools/login.py"))

    print("== 5/5 字体 ==")
    if os.path.exists(SUBSET):
        print("  子集字体 ✓ {} ({:.2f} MB)".format(SUBSET, os.path.getsize(SUBSET) / 1048576))
    else:
        print("  子集字体缺失, 尝试生成(需要完整字体或联网下载)...")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "make_subset.py")])
        if r.returncode != 0:
            print("  生成失败 ✗ — 可手动下载 Yozai-Regular.ttf 放入 fonts/ 后运行 tools/make_subset.py")

    print("== 完成 ==")
    print("下一步:")
    print("  1. 登记发卡人信息:  python tools/send_card.py --register")
    print("  2. 扫码登录问卷:    python tools/login.py")
    print("  3. 生成一张卡:      python tools/send_card.py --interactive")


if __name__ == "__main__":
    main()
