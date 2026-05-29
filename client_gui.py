"""
ATM客户端 GUI — 符合 RFC-20242024 协议
基于 Tkinter 的图形界面版本
用法: py -3 client_gui.py
"""

import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ==================== 常量 ====================
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 17685
BUFFER_SIZE = 1024


# ==================== ATM 客户端逻辑 ====================
class ATMClient:
    def __init__(self):
        self.sock = None

    def ensure_connected(self, host, port):
        """如果未连接则建立连接，如果连接已断开则重连"""
        if self.sock:
            try:
                # 检查连接是否仍然有效
                self.sock.getpeername()
                return
            except (socket.error, OSError):
                self.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((host, port))

    def send(self, message):
        data = (message + "\n").encode("utf-8")
        self.sock.sendall(data)

    def recv(self):
        data = self.sock.recv(BUFFER_SIZE)
        return data.decode("utf-8").strip() if data else ""

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None


# ==================== GUI 应用 ====================
class ATMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ATM 银行客户端")
        self.root.geometry("540x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#eef1f5")

        self.client = ATMClient()

        self._setup_styles()
        self._build_top_bar()
        self._build_login_page()
        self._build_main_page()
        self._show_page("login")

    # ---------- 样式 ----------
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"),
                        background="white", foreground="#1a1a2e")
        style.configure("Hint.TLabel", font=("Microsoft YaHei", 9),
                        background="white", foreground="#999")

    # ---------- 顶部栏 ----------
    def _build_top_bar(self):
        bar = tk.Frame(self.root, bg="#e8ecf1", height=42)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="服务器地址", bg="#e8ecf1", fg="#888",
                 font=("Microsoft YaHei", 8)).pack(side="left", padx=(16, 6))

        self.host_var = tk.StringVar(value=DEFAULT_HOST)
        tk.Entry(bar, textvariable=self.host_var, width=14,
                 font=("Consolas", 10), relief="flat", bg="white",
                 borderwidth=0).pack(side="left", pady=8)

        tk.Label(bar, text=" : ", bg="#e8ecf1", fg="#888",
                 font=("Consolas", 10)).pack(side="left")

        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        vcmd = (self.root.register(lambda p: p == "" or p.isdigit()), "%P")
        tk.Entry(bar, textvariable=self.port_var, width=6,
                 font=("Consolas", 10), relief="flat", bg="white",
                 borderwidth=0, validate="key", validatecommand=vcmd
                 ).pack(side="left", pady=8)

        self.conn_dot = tk.Label(bar, text="●", bg="#e8ecf1", fg="#bbb",
                                 font=("", 11))
        self.conn_dot.pack(side="right", padx=(0, 4))

        self.conn_label = tk.Label(bar, text="未连接", bg="#e8ecf1", fg="#999",
                                   font=("Microsoft YaHei", 9))
        self.conn_label.pack(side="right", padx=(0, 16))

    # ---------- 登录页 ----------
    def _build_login_page(self):
        self.login_page = tk.Frame(self.root, bg="#eef1f5")

        card = tk.Frame(self.login_page, bg="white",
                        highlightbackground="#e0e0e0", highlightthickness=1)
        card.place(relx=0.5, rely=0.42, anchor="center", width=450, height=400)

        ttk.Label(card, text="欢迎使用 ATM", style="Title.TLabel"
                  ).pack(pady=(30, 8))
        ttk.Label(card, text="请输入卡号和口令登录", style="Hint.TLabel").pack()

        # 卡号
        tk.Label(card, text="卡号", bg="white", fg="#555",
                 font=("Microsoft YaHei", 10)).pack(anchor="w", padx=52, pady=(24, 4))
        self.card_entry = tk.Entry(card, font=("Consolas", 14), relief="solid",
                                   bg="#f7f8fa", fg="#333", borderwidth=1)
        self.card_entry.pack(fill="x", padx=52, ipady=7)
        self.card_entry.bind("<Return>", lambda e: self.pass_entry.focus())

        # 口令
        tk.Label(card, text="口令", bg="white", fg="#555",
                 font=("Microsoft YaHei", 10)).pack(anchor="w", padx=52, pady=(16, 4))
        self.pass_entry = tk.Entry(card, font=("Consolas", 14), relief="solid",
                                   bg="#f7f8fa", fg="#333", borderwidth=1, show="●")
        self.pass_entry.pack(fill="x", padx=52, ipady=7)
        self.pass_entry.bind("<Return>", lambda e: self._do_login())

        self.login_btn = tk.Button(card, text="登  录", command=self._do_login,
                                   font=("Microsoft YaHei", 14, "bold"),
                                   bg="#4a6cf7", fg="white", relief="flat",
                                   activebackground="#3b5de7", cursor="hand2")
        self.login_btn.pack(fill="x", padx=52, pady=(24, 36), ipady=14)

        self.login_page.place(relwidth=1, relheight=1)

    # ---------- 主菜单页 ----------
    def _build_main_page(self):
        self.main_page = tk.Frame(self.root, bg="#eef1f5")

        card = tk.Frame(self.main_page, bg="white",
                        highlightbackground="#e0e0e0", highlightthickness=1)
        card.place(relx=0.5, rely=0.42, anchor="center", width=450, height=370)

        self.welcome_label = ttk.Label(card, text="", style="Title.TLabel")
        self.welcome_label.pack(pady=(40, 10))

        btn = {"font": ("Microsoft YaHei", 13), "relief": "flat",
               "cursor": "hand2", "borderwidth": 0}

        self.bala_btn = tk.Button(card, text="查询余额", command=self._do_balance,
                                  bg="#e8f4fd", fg="#1a73e8",
                                  activebackground="#d2e8fc", **btn)
        self.bala_btn.pack(fill="x", padx=52, pady=(30, 0), ipady=14)

        self.wdra_btn = tk.Button(card, text="取    款", command=self._do_withdraw,
                                  bg="#fef3e2", fg="#e67e22",
                                  activebackground="#fdebd0", **btn)
        self.wdra_btn.pack(fill="x", padx=52, pady=(14, 0), ipady=14)

        self.quit_btn = tk.Button(card, text="退出服务", command=self._do_quit,
                                  bg="#f0f0f0", fg="#888",
                                  activebackground="#e0e0e0", **btn)
        self.quit_btn.pack(fill="x", padx=52, pady=(14, 0), ipady=14)

        self.main_page.place(relwidth=1, relheight=1)

    # ---------- 页面切换 ----------
    def _show_page(self, name):
        for page in [self.login_page, self.main_page]:
            page.place_forget()
        if name == "login":
            self.login_page.place(relwidth=1, relheight=1)
        else:
            self.main_page.place(relwidth=1, relheight=1)

    # ---------- 异步执行 ----------
    def _run_async(self, target, on_done=None):
        def worker():
            try:
                result = target()
            except Exception as e:
                result = e
            self.root.after(0, lambda: on_done(result) if on_done else None)
        threading.Thread(target=worker, daemon=True).start()

    def _set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in [self.login_btn, self.bala_btn, self.wdra_btn, self.quit_btn]:
            btn.configure(state=state)

    def _set_connected(self, connected, label=""):
        if connected:
            self.conn_dot.configure(fg="#27ae60")
            self.conn_label.configure(text=label or "已连接", fg="#27ae60")
        else:
            self.conn_dot.configure(fg="#bbb")
            self.conn_label.configure(text="未连接", fg="#999")

    # ---------- 登录 ----------
    def _do_login(self):
        card = self.card_entry.get().strip()
        passwd = self.pass_entry.get().strip()
        if not card:
            messagebox.showwarning("提示", "请输入卡号")
            return
        if not passwd:
            messagebox.showwarning("提示", "请输入口令")
            return

        host = self.host_var.get().strip()
        port_str = self.port_var.get().strip()
        if not host or not port_str:
            messagebox.showwarning("提示", "请填写服务器地址和端口")
            return
        port = int(port_str)

        self._set_buttons(False)
        self.login_btn.configure(text="正在连接...")
        self._set_connected(True, "连接中...")
        self.conn_dot.configure(fg="#e67e22")

        def do_auth():
            self.client.ensure_connected(host, port)
            self.client.send(f"HELO {card}")
            resp = self.client.recv()
            if not resp.startswith("500"):
                raise RuntimeError(f"服务器返回异常: {resp}")
            self.client.send(f"PASS {passwd}")
            resp = self.client.recv()
            if resp != "525 OK!":
                raise RuntimeError(f"认证失败: {resp}")
            return card

        def on_done(result):
            self.login_btn.configure(text="登  录")
            if isinstance(result, Exception):
                self._set_buttons(True)
                self._set_connected(False)
                self.client.close()
                err_msg = str(result)
                messagebox.showerror("登录失败", err_msg)
            else:
                self._set_connected(True, "已连接")
                self.welcome_label.configure(text=f"欢迎，{result}")
                self._show_page("main")
                self._set_buttons(True)

        self._run_async(do_auth, on_done)

    # ---------- 查询余额 ----------
    def _do_balance(self):
        self._set_buttons(False)

        def query():
            self.client.send("BALA")
            resp = self.client.recv()
            if resp.startswith("AMNT:"):
                return resp[5:]
            raise RuntimeError(resp)

        def on_done(result):
            self._set_buttons(True)
            if isinstance(result, Exception):
                self._handle_conn_error(result)
                messagebox.showerror("查询失败", str(result))
            else:
                messagebox.showinfo("账户余额", f"当前余额: {result} 元")

        self._run_async(query, on_done)

    # ---------- 取款 ----------
    def _do_withdraw(self):
        host = self.host_var.get().strip()
        port = int(self.port_var.get().strip())

        # 使用 simpledialog 弹窗输入金额，比自定义 Toplevel 更稳定
        amount = simpledialog.askstring(
            "取款", "请输入取款金额:",
            parent=self.root
        )
        if not amount:
            return
        amount = amount.strip()
        try:
            float(amount)
        except ValueError:
            messagebox.showwarning("提示", "金额格式不正确")
            return

        self._set_buttons(False)

        def withdraw():
            self.client.ensure_connected(host, port)
            self.client.send(f"WDRA {amount}")
            resp = self.client.recv()
            if resp == "525 OK!":
                return amount
            raise RuntimeError(resp)

        def on_done(result):
            self._set_buttons(True)
            if isinstance(result, Exception):
                self._handle_conn_error(result)
                err_msg = str(result)
                if "401" in err_msg:
                    err_msg = "取款失败（余额不足或金额无效）"
                messagebox.showerror("取款失败", err_msg)
            else:
                messagebox.showinfo("取款成功", f"成功取出: {result} 元")

        self._run_async(withdraw, on_done)

    # ---------- 退出 ----------
    def _do_quit(self):
        self._set_buttons(False)

        def quit_proc():
            self.client.send("QUIT")
            return self.client.recv()

        def on_done(_result):
            self.client.close()
            self._set_connected(False)
            self.welcome_label.configure(text="")
            self._set_buttons(True)
            self.card_entry.delete(0, "end")
            self.pass_entry.delete(0, "end")
            self._show_page("login")

        self._run_async(quit_proc, on_done)

    # ---------- 连接错误处理 ----------
    def _handle_conn_error(self, error):
        if isinstance(error, (socket.error, OSError, ConnectionError)):
            self._set_connected(False)
            self.client.close()


# ==================== 入口 ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = ATMApp(root)
    root.mainloop()
