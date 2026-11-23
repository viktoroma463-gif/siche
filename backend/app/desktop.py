"""思拆桌面启动器：启动本地服务、弹出控制窗口，并打开浏览器。"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


def _ensure_streams() -> None:
    """--noconsole 打包后 sys.stdout/stderr 可能为 None，uvent 日志会因此崩溃。"""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


_ensure_streams()


if not getattr(sys, "frozen", False):
    backend = Path(__file__).resolve().parents[1]
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))


def exe_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def find_port(start: int = 8010, span: int = 30) -> int:
    for port in range(start, start + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("找不到可用端口（8010 起已全部被占用）。")


def wait_until_up(url: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.2)
    return False


def write_log(text: str) -> None:
    try:
        (exe_dir() / "siche.log").write_text(text, encoding="utf-8")
    except OSError:
        pass


def main() -> None:
    import tkinter as tk
    from tkinter import messagebox

    import uvicorn

    from app.main import app

    port = find_port()
    url = f"http://127.0.0.1:{port}/"
    health = f"http://127.0.0.1:{port}/api/health"
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()

    if not wait_until_up(health):
        raise RuntimeError("服务启动超时，请查看同目录下的 siche.log。")

    webbrowser.open(url)

    root = tk.Tk()
    root.title("思拆")
    root.geometry("400x220")
    root.resizable(False, False)
    try:
        root.attributes("-topmost", True)
        root.after(800, lambda: root.attributes("-topmost", False))
    except tk.TclError:
        pass

    bg = "#f6f1e8"
    ink = "#2b261f"
    root.configure(bg=bg)
    tk.Label(root, text="思拆已在本机启动", font=("Microsoft YaHei UI", 16), bg=bg, fg=ink).pack(pady=(28, 8))
    tk.Label(root, text=url, font=("Microsoft YaHei UI", 11), bg=bg, fg="#7a2e2e").pack()
    tk.Label(
        root,
        text="浏览器会自动打开界面。关闭本窗口即退出。",
        font=("Microsoft YaHei UI", 9),
        bg=bg,
        fg="#5c564c",
    ).pack(pady=(12, 8))

    def on_close() -> None:
        server.should_exit = True
        root.destroy()

    bar = tk.Frame(root, bg=bg)
    bar.pack(pady=12)
    tk.Button(bar, text="打开界面", command=lambda: webbrowser.open(url), width=12).pack(side="left", padx=8)
    tk.Button(bar, text="退出", command=on_close, width=12).pack(side="left", padx=8)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    server.should_exit = True


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        write_log(err)
        try:
            import tkinter as tk
            from tkinter import messagebox

            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("思拆启动失败", err[-1500:])
        except Exception:
            sys.stderr.write(err)
        sys.exit(1)
