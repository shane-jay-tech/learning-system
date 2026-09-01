"""桌面应用启动器 - PyWebView 套壳 Streamlit。

启动流程：
  1. 单例锁 + 找空闲端口 + 启动 Streamlit 后台
  2. 创建窗口显示 splash（紫色渐变 + 转圈）
  3. 后台线程：Python 端轮询 /_stcore/health（不走浏览器，避开 CORS）
  4. health=200 -> window.load_url 切到主界面
  5. 关窗口 -> 优雅终止 Streamlit

注意：曾尝试用 GET / 做"预热"，但 streamlit 主页 GET / 只返 5KB SPA 壳，
不会触发后端 home 真实渲染（那要等 webview 建 WebSocket）。所以预热无效，删了。
真正的启动加速在 app.py 顶层：4 个 ui.pages 改成 lazy import，省 ~2.6s。

开发模式仍然可用：streamlit run app.py（直接浏览器，热重载）。
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

try:
    import webview
except ImportError:
    webview = None  # 缺 pywebview 时在 main() 里给友好提示，而不是模块级崩溃


HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
ICON = str(ASSETS / "app.ico")
LOG_FILE = HERE / "data" / "launcher.log"
SINGLETON_LOCK_PORT = 49281
STARTUP_TIMEOUT_SEC = 60


# ---------- 日志（滚动 3×1MB，避免无限增长）----------
logger = logging.getLogger("launcher")


def _setup_logging() -> None:
    """在 main() 里调用：import 本模块不产生建目录/写日志副作用（测试友好）。"""
    if getattr(_setup_logging, "_done", False):
        return
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _handler = logging.handlers.RotatingFileHandler(
        str(LOG_FILE), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.setLevel(logging.INFO)
    logger.addHandler(_handler)
    _setup_logging._done = True


# ---------- 单例 ----------
_lock_socket = None


def acquire_singleton_lock() -> bool:
    global _lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        s.bind(("127.0.0.1", SINGLETON_LOCK_PORT))
        s.listen(1)
        _lock_socket = s
        return True
    except OSError:
        s.close()
        return False


# ---------- 端口 ----------
def find_free_port(preferred: int = 8501, max_tries: int = 20) -> int:
    for offset in range(max_tries):
        p = preferred + offset
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError(f"找不到空闲端口（{preferred}-{preferred + max_tries}）")


def terminate_backend(proc) -> None:
    """优雅终止 streamlit：terminate → 等 4s → kill。幂等，任何异常都不外抛。"""
    if proc is None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception:
        logger.exception("Failed to terminate streamlit cleanly")


# ---------- Streamlit 子进程 ----------
def start_streamlit_backend(port: int) -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(HERE / "app.py"),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]
    logger.info("Starting streamlit: %s", " ".join(cmd))
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW
    log_handle = open(str(LOG_FILE.parent / "streamlit.log"), "ab")
    proc = subprocess.Popen(
        cmd,
        cwd=str(HERE),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    log_handle.close()  # 子进程持有自己的句柄，父进程立即关闭避免泄漏
    return proc


# ---------- 健康检查（Python 端 - 不受浏览器跨域限制）----------
def is_health_ready(port: int, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/_stcore/health", timeout=timeout
        ) as r:
            return r.status == 200  # 4xx 不是就绪（此前 <500 会把 404 当成功）
    except Exception:
        return False


# ---------- splash HTML ----------
def splash_html() -> str:
    # 注意：纯静态。所有进度文本由 Python 通过 evaluate_js 更新。
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>编程学习平台</title>
<style>
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100%;
    font-family: -apple-system, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    color: white; overflow: hidden;
    user-select: none;
  }
  .center {
    height: 100%; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 28px;
  }
  .logo {
    font-size: 96px; font-weight: 700; line-height: 1;
    background: rgba(255,255,255,0.18); border-radius: 28px;
    width: 144px; height: 144px;
    display: flex; align-items: center; justify-content: center;
    backdrop-filter: blur(8px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.25);
  }
  h1 { margin: 0; font-size: 32px; font-weight: 600; }
  p#status { margin: 0; font-size: 15px; opacity: 0.85; min-height: 22px; }
  .spinner {
    width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.25);
    border-top-color: white; border-radius: 50%;
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .hint { position: absolute; bottom: 24px; font-size: 12px; opacity: 0.65; }
</style>
</head>
<body>
<div class="center">
  <div class="logo">学</div>
  <h1>编程学习平台</h1>
  <div class="spinner"></div>
  <p id="status">正在启动后端…</p>
</div>
<div class="hint">© 2026 · Python · SQL · C++ · R · Agent 开发</div>
</body>
</html>
"""


# ---------- 错误对话框 ----------
def show_error_box(title: str, message: str) -> None:
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
            return
        except Exception:
            pass
    # pythonw 下 sys.stderr 可能为 None，直接 print 会 AttributeError
    if sys.stderr is not None:
        try:
            print(f"[{title}] {message}", file=sys.stderr)
        except Exception:
            pass


def _set_splash_status(window, text: str) -> None:
    """安全地更新 splash 文字（webview 可能已经切走，evaluate_js 会抛错）。"""
    try:
        # 用 JSON 编码避免引号注入
        import json as _json
        window.evaluate_js(
            f"var s=document.getElementById('status');"
            f"if(s) s.textContent={_json.dumps(text)};"
        )
    except Exception:
        pass


# ---------- 高 DPI 感知 ----------
def _enable_dpi_awareness() -> None:
    """声明进程为高 DPI 感知，避免 Windows 在缩放 >100% 时把窗口位图拉伸（界面发虚/像素化）。
    必须在创建任何窗口之前调用。按优先级尝试三种 API，全失败也不影响启动。"""
    if os.name != "nt":
        return
    import ctypes
    # 1) Per-Monitor-Aware v2（Win10 1703+，最佳：每屏独立、字体最锐利）
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            logger.info("DPI awareness: Per-Monitor-v2")
            return
    except Exception:
        pass
    # 2) Per-Monitor（Win8.1+）
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        logger.info("DPI awareness: Per-Monitor (shcore)")
        return
    except Exception:
        pass
    # 3) System-DPI-Aware（Vista+，兜底）
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        logger.info("DPI awareness: System (legacy)")
    except Exception:
        logger.warning("DPI awareness: all attempts failed")


# ---------- 主流程 ----------
def main() -> int:
    _setup_logging()
    _enable_dpi_awareness()  # 必须最先调用，且在任何窗口创建之前
    if webview is None:
        logger.error("pywebview is not installed")
        show_error_box("缺少依赖", "未安装 pywebview，桌面模式无法启动。\n\n"
                                    "请在本项目目录执行：\n  pip install pywebview\n\n"
                                    "或改用开发模式：start.bat")
        return 1
    if not acquire_singleton_lock():
        logger.info("Another instance is running; exit.")
        show_error_box("已在运行", "编程学习平台已经在运行中。\n\n"
                                   "如果看不到窗口，请在任务管理器结束\n"
                                   "pythonw.exe 后重试。")
        return 0

    # 用 8511 起步,跟心理系统(8501)完全错开
    # —— 避免 webview 把同一个 url(127.0.0.1:8501) 的旧缓存当成新页面渲染
    try:
        port = find_free_port(preferred=8511)
    except Exception as e:
        logger.exception("Port scan failed")
        show_error_box("启动失败", f"找不到空闲端口：{e}\n\n详细日志：{LOG_FILE}")
        return 1

    try:
        proc = start_streamlit_backend(port)
    except Exception as e:
        logger.exception("Streamlit start failed")
        show_error_box("启动失败",
                       f"无法启动 Streamlit：{e}\n\n请确保依赖完整安装：\n"
                       f"  pip install -r requirements.txt\n\n日志：{LOG_FILE}")
        return 1

    target_url = f"http://127.0.0.1:{port}"
    logger.info("Streamlit backend launching at %s (pid=%s)", target_url, proc.pid)

    window = webview.create_window(
        "编程学习平台",
        html=splash_html(),
        width=1400,
        height=900,
        min_size=(960, 640),
        background_color="#6366F1",
        easy_drag=False,
        confirm_close=False,
        # 独立持久 profile：既不串心理系统缓存，又能跨启动缓存 Streamlit
        # 前端静态资源（~10MB），后续启动明显更快。private_mode 每次全新
        # profile 会丢掉缓存，冷启动每次都重新下载全部资源。
        storage_path=str(HERE / "data" / "webview_profile"),
    )

    def on_closed():
        logger.info("Window closed; terminating streamlit.")
        terminate_backend(proc)

    # 兜底：launcher 被强杀/崩溃时也尽量带走 streamlit，避免僵尸进程
    # 累积占端口、持有 progress.db
    import atexit
    atexit.register(lambda: terminate_backend(proc))

    window.events.closed += on_closed

    # 后台线程:health 200 -> 切 URL
    def wait_and_switch():
        deadline = time.time() + STARTUP_TIMEOUT_SEC
        t0 = time.perf_counter()
        progress_hints = [
            (3.0, "正在加载题库…"),
            (8.0, "首次启动稍慢,请再等几秒…"),
        ]
        next_hint = 0
        while time.time() < deadline:
            if proc.poll() is not None:
                logger.error("Streamlit exited prematurely (rc=%s)", proc.returncode)
                show_error_box("启动失败",
                               f"Streamlit 进程意外退出(exit code {proc.returncode})。\n"
                               f"详细日志:{LOG_FILE.parent / 'streamlit.log'}")
                _safe_destroy()
                return
            if is_health_ready(port):
                elapsed = time.perf_counter() - t0
                logger.info("Streamlit ready in %.2fs; switching to %s", elapsed, target_url)
                _set_splash_status(window, "就绪,正在打开…")
                time.sleep(0.15)
                try:
                    window.load_url(target_url)
                except Exception:
                    logger.exception("load_url failed")
                return
            elapsed = time.perf_counter() - t0
            if next_hint < len(progress_hints) and elapsed >= progress_hints[next_hint][0]:
                _set_splash_status(window, progress_hints[next_hint][1])
                next_hint += 1
            time.sleep(0.2)

        logger.error("Startup timeout")
        show_error_box("启动超时", f"Streamlit 后端启动超过 {STARTUP_TIMEOUT_SEC} 秒。\n日志:{LOG_FILE}")
        _safe_destroy()

    def _safe_destroy():
        # 后台线程直接操作 UI 窗口可能抛异常（窗口已关/事件循环退出），吞掉即可
        try:
            window.destroy()
        except Exception:
            logger.debug("window.destroy failed (already closed?)")

    def on_window_ready():
        # webview.start 在事件循环准备好后调用此函数，启动后台线程才安全
        threading.Thread(target=wait_and_switch, daemon=True).start()

    try:
        webview.start(
            on_window_ready,
            icon=ICON if os.path.exists(ICON) else None,
        )
    except Exception:
        logger.exception("webview.start failed")
        show_error_box("启动失败",
                       f"GUI 初始化失败。请确保已装 WebView2（Win10/11 一般预装）。\n"
                       f"日志：{LOG_FILE}")
        on_closed()
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Unhandled exception in launcher")
        show_error_box("严重错误",
                       f"未预料的错误：{e}\n\n详细堆栈：\n{traceback.format_exc()}\n\n"
                       f"日志：{LOG_FILE}")
        sys.exit(1)
