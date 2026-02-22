# main.py
# B站账号注册时间计算器 v0.1
# Code and Scripting by sauta73

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import sys
import requests
from api import extract_uid, get_uid_info
from calculator import calculate_join_time, format_result

# ── 颜色主题（B站粉）──────────────────────────────
BG_COLOR      = "#1a1a2e"
CARD_COLOR    = "#16213e"
ACCENT_COLOR  = "#fb7299"
TEXT_COLOR    = "#ffffff"
SUBTLE_COLOR  = "#a0a0b0"
SUCCESS_COLOR = "#23d18b"
DIM_COLOR     = "#6a6a7a"


def get_readme_path():
    """获取 README.txt 路径，兼容打包后的 exe"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "README.txt")


def open_readme():
    path = get_readme_path()
    if not os.path.exists(path):
        messagebox.showwarning("找不到文件", f"未找到 README.txt\n路径：{path}")
        return
    try:
        os.startfile(path)          # Windows 默认记事本打开
    except Exception as e:
        messagebox.showerror("打开失败", str(e))


class BilibiliCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("B站账号注册时间计算器  v0.1")
        self.root.geometry("640x580")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        self._build_ui()

    def _build_ui(self):

        # ══ 顶部栏：署名 + 关于按钮 ══════════════════
        topbar = tk.Frame(self.root, bg=BG_COLOR)
        topbar.pack(fill="x", padx=20, pady=(10, 0))

        tk.Label(
            topbar,
            text="Code and Scripting by sauta73",
            font=("Microsoft YaHei", 8),
            fg=DIM_COLOR, bg=BG_COLOR
        ).pack(side="left")

        tk.Button(
            topbar,
            text="关于 / README",
            font=("Microsoft YaHei", 8),
            bg="#2a2a4a", fg=SUBTLE_COLOR,
            activebackground="#3a3a5a",
            activeforeground=TEXT_COLOR,
            relief="flat", bd=0, padx=10, pady=3,
            cursor="hand2",
            command=open_readme
        ).pack(side="right")

        # ══ 标题区 ════════════════════════════════════
        title_frame = tk.Frame(self.root, bg=BG_COLOR)
        title_frame.pack(pady=(8, 6))

        tk.Label(
            title_frame,
            text="🎵  B站注册时间计算器",
            font=("Microsoft YaHei", 18, "bold"),
            fg=ACCENT_COLOR, bg=BG_COLOR
        ).pack()
        tk.Label(
            title_frame,
            text="输入 UID 或主页 URL，估算账号注册时间",
            font=("Microsoft YaHei", 10),
            fg=SUBTLE_COLOR, bg=BG_COLOR
        ).pack()

        # ══ 单个查询区域 ══════════════════════════════
        input_frame = tk.Frame(self.root, bg=CARD_COLOR)
        input_frame.pack(padx=32, pady=(6, 0), fill="x", ipady=12)

        tk.Label(
            input_frame,
            text="请输入 UID 或 B站主页链接：",
            font=("Microsoft YaHei", 10),
            fg=TEXT_COLOR, bg=CARD_COLOR
        ).pack(anchor="w", padx=16, pady=(8, 4))

        entry_row = tk.Frame(input_frame, bg=CARD_COLOR)
        entry_row.pack(fill="x", padx=16, pady=(0, 8))

        self.entry = tk.Entry(
            entry_row,
            font=("Consolas", 12),
            bg="#0f3460", fg=TEXT_COLOR,
            insertbackground=ACCENT_COLOR,
            relief="flat", bd=0
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.insert(0, "例：24474955 或 https://space.bilibili.com/24474955")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<Return>",  lambda e: self._start_calc())

        self.calc_btn = tk.Button(
            entry_row,
            text="计算 🚀",
            font=("Microsoft YaHei", 10, "bold"),
            bg=ACCENT_COLOR, fg="white",
            activebackground="#e05a80",
            relief="flat", bd=0, padx=16,
            cursor="hand2",
            command=self._start_calc
        )
        self.calc_btn.pack(side="right", ipady=8)

        # ══ 批量查询区域 ══════════════════════════════
        batch_frame = tk.Frame(self.root, bg=CARD_COLOR)
        batch_frame.pack(padx=32, pady=(2, 0), fill="x")

        tk.Label(
            batch_frame,
            text="批量查询（每行一个 UID / URL）：",
            font=("Microsoft YaHei", 9),
            fg=SUBTLE_COLOR, bg=CARD_COLOR
        ).pack(anchor="w", padx=16, pady=(6, 2))

        self.batch_text = tk.Text(
            batch_frame,
            height=3,
            font=("Consolas", 10),
            bg="#0f3460", fg=TEXT_COLOR,
            insertbackground=ACCENT_COLOR,
            relief="flat", bd=0
        )
        self.batch_text.pack(fill="x", padx=16, pady=(0, 6))

        batch_btn = tk.Button(
            batch_frame,
            text="批量计算 📋",
            font=("Microsoft YaHei", 9),
            bg="#4a4e69", fg="white",
            activebackground="#6b6f9a",
            relief="flat", bd=0, padx=12,
            cursor="hand2",
            command=self._start_batch_calc
        )
        batch_btn.pack(anchor="e", padx=16, pady=(0, 8))

        # ══ 进度条 ════════════════════════════════════
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "pink.Horizontal.TProgressbar",
            troughcolor="#0f3460",
            background=ACCENT_COLOR,
            thickness=4
        )
        self.progress = ttk.Progressbar(
            self.root, mode="indeterminate",
            style="pink.Horizontal.TProgressbar"
        )
        self.progress.pack(padx=32, fill="x", pady=4)

        # ══ 结果输出框 ════════════════════════════════
        result_frame = tk.Frame(self.root, bg=CARD_COLOR)
        result_frame.pack(padx=32, pady=(0, 4), fill="both", expand=True)

        self.result_box = scrolledtext.ScrolledText(
            result_frame,
            font=("Consolas", 11),
            bg="#0a0a1a", fg=SUCCESS_COLOR,
            insertbackground="white",
            relief="flat", bd=0,
            wrap="word", state="disabled"
        )
        self.result_box.pack(fill="both", expand=True)

        # ══ 底部提示 ══════════════════════════════════
        tk.Label(
            self.root,
            text="⚡ 估算基于 UID 线性插值，仅供参考，误差约 ±1 个月   |   v0.1",
            font=("Microsoft YaHei", 8),
            fg=SUBTLE_COLOR, bg=BG_COLOR
        ).pack(pady=(2, 8))

    # ── 事件处理 ──────────────────────────────────────

    def _clear_placeholder(self, event=None):
        if "例：" in self.entry.get():
            self.entry.delete(0, "end")

    def _set_result(self, text: str):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.configure(state="disabled")

    def _start_calc(self):
        raw = self.entry.get().strip()
        if not raw or "例：" in raw:
            self._set_result("⚠️  请先输入 UID 或主页链接！")
            return
        threading.Thread(target=self._do_calc, args=(raw,), daemon=True).start()

    def _do_calc(self, raw: str):
        self.calc_btn.configure(state="disabled")
        self.progress.start(10)
        self._set_result("⏳ 正在计算中...")

        uid = extract_uid(raw)
        if uid is None:
            self._set_result("❌ 无法识别输入，请检查 UID 或 URL 格式")
            self._done()
            return

        username = None
        try:
            info = get_uid_info(uid)
            if info:
                username = info.get("name")
        except (requests.RequestException, ValueError, KeyError):
            pass

        result = calculate_join_time(uid)
        output = format_result(result, username)
        self._set_result(output)
        self._done()

    def _start_batch_calc(self):
        raw_text = self.batch_text.get("1.0", "end").strip()
        if not raw_text:
            self._set_result("⚠️  批量输入为空！")
            return
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        threading.Thread(target=self._do_batch_calc, args=(lines,), daemon=True).start()

    def _do_batch_calc(self, lines: list):
        self.progress.start(10)
        self._set_result(f"⏳ 批量计算 {len(lines)} 个账号中...\n")
        outputs = []
        for raw in lines:
            uid = extract_uid(raw)
            if uid is None:
                outputs.append(f"❌ 无法识别: {raw}")
                continue
            result = calculate_join_time(uid)
            outputs.append(
                f"UID {result['uid']:>12,} │ "
                f"注册时间: {result['estimated_date']} │ "
                f"置信度: {result['confidence']}"
            )
        self._set_result("\n".join(outputs))
        self._done()

    def _done(self):
        self.progress.stop()
        self.calc_btn.configure(state="normal")


def main():
    root = tk.Tk()
    BilibiliCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
