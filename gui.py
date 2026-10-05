import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import re
import subprocess
import sys
import threading

try:
    import winsound
except ImportError:
    winsound = None

class TwitterDownloadGUI:
    TRANSLATIONS = {
        "Twitter Download GUI": "Twitter Download GUI",
        "下载": "Download", "同步管理": "Sync", "日志": "Logs",
        "Twitter 下载工具": "Twitter Download", "批量下载、筛选和同步管理": "Batch download, filtering and sync management",
        "基本设置": "Basic Settings", "保存路径:": "Save path:", "浏览": "Browse",
        "用户列表:": "Users:", "(多用户用英文逗号分隔)": "(Separate multiple users with commas)",
        "Cookie 中的 auth_token 值": "auth_token value from Cookie", "Cookie 中的 ct0 值": "ct0 value from Cookie",
        "保存配置": "Save Settings", "开始下载": "Start Download", "下载选项": "Download Options",
        "下载类型:": "Download type:", "默认(仅用户自己的媒体)": "Default (user's own media)",
        "包含转推": "Include reposts", "仅亮点内容": "Highlights only", "仅点赞内容": "Likes only",
        "时间范围:": "Date range:", "(格式: 1990-01-01:2030-01-01)": "(Format: 1990-01-01:2030-01-01)",
        "其他选项": "Other Options", "开启下载日志(避免重复下载)": "Enable download log (avoid duplicates)",
        "自动同步最新内容": "Auto-sync latest content", "下载视频": "Download videos",
        "显示下载过程日志": "Show download log", "任务完成时播放提示音": "Play sound when finished",
        "提示音路径:": "Sound path:", "试听": "Preview", "留空使用系统提示音，仅支持 WAV": "Leave empty for system sound; WAV only",
        "生成 Markdown 文件": "Generate Markdown file", "图片格式:": "Image format:",
        "媒体数量限制:": "Media limit:", "(0 为不限制)": "(0 means unlimited)", "网络设置": "Network Settings",
        "最大并发请求:": "Max concurrent requests:", "请求间隔(秒):": "Request interval (seconds):",
        "代理:": "Proxy:", "(格式: http://localhost:port)": "(Format: http://localhost:port)",
        "同步管理": "Sync Management", "查看本地用户状态并更新已选内容": "View local users and update selected content",
        "扫描路径": "Scan Path", "存储路径:": "Storage path:", "开始检测文件夹": "Detect folders",
        "扫描用户": "Scan users", "全选": "Select all", "全不选": "Deselect all", "更新选中": "Update selected",
        "用户名": "Username", "昵称": "Display name", "文件数": "Files", "最后下载": "Last download",
        "日志中心": "Log Center", "查看下载与同步执行过程的实时输出": "View live download and sync output",
        "运行日志": "Runtime Log", "清空日志": "Clear log", "提示音文件:": "Sound file:",
        "语言:": "Language:", "中文": "Chinese", "英文": "English",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Twitter Download GUI")
        self.root.geometry("920x700")
        self.root.minsize(760, 560)
        self.root.resizable(True, True)
        self.root.configure(bg="#edf3fb")

        self._apply_theme()
        self._check_dependencies()

        settings_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
        self.settings_file = os.path.join(settings_dir, "settings.json")
        self.load_settings()
        self.language = self.settings.get("language", "zh-CN")

        self.main_frame = ttk.Frame(root, padding="14")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        language_frame = ttk.Frame(self.main_frame)
        language_frame.grid(row=0, column=0, sticky=tk.EW, pady=(0, 8))
        ttk.Label(language_frame, text="语言:").pack(side=tk.LEFT)
        self.language_var = tk.StringVar(value="中文" if self.language == "zh-CN" else "英文")
        self.language_combo = ttk.Combobox(language_frame, textvariable=self.language_var, values=["中文", "英文"], state="readonly", width=10)
        self.language_combo.pack(side=tk.LEFT, padx=(6, 0))
        self.language_var.trace_add("write", self._on_language_changed)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=0, sticky=tk.NSEW)

        self.create_download_tab()
        self.create_sync_tab()
        self.create_log_tab()
        self._apply_language()

    def _on_language_changed(self, *_):
        self.language = "zh-CN" if self.language_var.get() in ("中文", "Chinese") else "en-US"
        self.settings["language"] = self.language
        try:
            with open(self.settings_file, "w", encoding="utf8") as settings_file:
                json.dump(self.settings, settings_file, indent=2, ensure_ascii=False)
        except OSError:
            pass
        self._apply_language()

    def _translate(self, text):
        if self.language == "zh-CN":
            reverse_translations = {value: key for key, value in self.TRANSLATIONS.items()}
            return reverse_translations.get(text, text)
        return self.TRANSLATIONS.get(text, text)

    def _apply_language(self):
        self.root.title(self._translate("Twitter Download GUI"))
        language_options = ["中文", "英文"] if self.language == "zh-CN" else ["Chinese", "English"]
        self.language_combo.configure(values=language_options)
        selected_language = language_options[0 if self.language == "zh-CN" else 1]
        if self.language_var.get() != selected_language:
            self.language_var.set(selected_language)
        for widget in self.root.winfo_children():
            self._translate_widget_tree(widget)
        for tab_id in self.notebook.tabs():
            tab_text = self.notebook.tab(tab_id, "text")
            self.notebook.tab(tab_id, text=self._translate(tab_text))

    def _translate_widget_tree(self, widget):
        if isinstance(widget, (tk.Label, ttk.Label, ttk.Button, ttk.Checkbutton, ttk.Radiobutton, ttk.LabelFrame)):
            current_text = widget.cget("text")
            widget.configure(text=self._translate(current_text))
        if isinstance(widget, ttk.Treeview):
            for column in widget["columns"]:
                heading = widget.heading(column, "text")
                widget.heading(column, text=self._translate(heading))
        for child in widget.winfo_children():
            self._translate_widget_tree(child)
    
    def _check_dependencies(self):
        missing_deps = []
        try:
            import httpx
        except ImportError:
            missing_deps.append("httpx")
        
        if missing_deps:
            messagebox.showwarning(
                "依赖缺失",
                f"检测到缺少以下依赖:\n{', '.join(missing_deps)}\n\n请运行:\npip install {' '.join(missing_deps)}"
            )
    
    def _on_mousewheel(self, event, canvas):
        if event.num == 5 or event.delta < 0:
            amount = 1
        elif event.num == 4 or event.delta > 0:
            amount = -1
        else:
            return
        canvas.yview_scroll(amount, "units")
        return "break"
    
    def _is_descendant(self, widget, ancestor):
        while widget is not None:
            if widget == ancestor:
                return True
            parent = widget.winfo_parent()
            if not parent:
                return False
            widget = widget.nametowidget(parent)
        return False

    def _bind_mousewheel(self, widget, canvas, include_children=False):
        widget.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))
        widget.bind("<Button-4>", lambda e: self._on_mousewheel(e, canvas))
        widget.bind("<Button-5>", lambda e: self._on_mousewheel(e, canvas))
        if include_children:
            def on_mousewheel(event):
                if self._is_descendant(event.widget, widget):
                    return self._on_mousewheel(event, canvas)

            self.root.bind_all("<MouseWheel>", on_mousewheel, add="+")
            self.root.bind_all("<Button-4>", on_mousewheel, add="+")
            self.root.bind_all("<Button-5>", on_mousewheel, add="+")

    def _apply_theme(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#edf3fb")
        style.configure("TLabel", background="#edf3fb", foreground="#162033", font=("Microsoft YaHei", 10))
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#1f2a3d", padding=6)
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#1f2a3d", padding=6)
        style.configure("TButton", padding=(14, 8), font=("Microsoft YaHei", 10, "bold"))
        style.configure("Accent.TButton", background="#2d7ff9", foreground="#ffffff", padding=(16, 9), relief="flat")
        style.map("Accent.TButton", background=[("active", "#1f6fe8"), ("pressed", "#1b62d6")], foreground=[("disabled", "#dfe9ff")])
        style.configure("Card.TLabelframe", background="#ffffff", foreground="#1d2b42", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background="#ffffff", foreground="#1d2b42", font=("Microsoft YaHei", 10, "bold"))
        style.configure("TLabelframe", background="#edf3fb")
        style.configure("TLabelframe.Label", background="#edf3fb", foreground="#1d2b42", font=("Microsoft YaHei", 10, "bold"))
        style.configure("TNotebook", background="#edf3fb")
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Microsoft YaHei", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#ffffff"), ("active", "#eaf2ff")], foreground=[("selected", "#0d1f40")])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", rowheight=28, font=("Microsoft YaHei", 9))
        style.map("Treeview", background=[("selected", "#2d7ff9")], foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"), background="#dfeaff", foreground="#1d2b42")
        style.map("Treeview.Heading", background=[("active", "#cfe0ff")])

    def build_header(self, parent, title, subtitle=""):
        header = tk.Frame(parent, bg="#ffffff", padx=18, pady=16, highlightthickness=1, highlightbackground="#d8e3f5")
        header.grid(row=0, column=0, sticky=tk.NSEW, pady=(0, 12))
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_columnconfigure(0, weight=1)

        title_label = tk.Label(header, text=title, bg="#ffffff", fg="#102a52", font=("Microsoft YaHei", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)

        if subtitle:
            subtitle_label = tk.Label(header, text=subtitle, bg="#ffffff", fg="#63779a", font=("Microsoft YaHei", 10))
            subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(4, 0))

        return header

    def load_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf8') as f:
                self.settings = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            self.settings = {
                "save_path": "",
                "user_lst": "",
                "cookie": "",
                "has_retweet": False,
                "high_lights": False,
                "likes": False,
                "time_range": "",
                "down_log": False,
                "autoSync": False,
                "image_format": "orig",
                "has_video": False,
                "log_output": False,
                "max_concurrent_requests": 8,
                "request_interval": 0.5,
                "proxy": "",
                "md_output": False,
                "media_count_limit": 0
            }

    @staticmethod
    def _split_cookie(cookie):
        values = dict(re.findall(r'(auth_token|ct0)=([^;]*)', cookie or ''))
        return values.get("auth_token", ""), values.get("ct0", "")
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {e}")
    
    def create_download_tab(self):
        download_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(download_tab, text="下载")

        download_tab.grid_rowconfigure(1, weight=1)
        download_tab.grid_columnconfigure(0, weight=1)

        self.build_header(download_tab, "Twitter 下载工具", "批量下载、筛选和同步管理")

        scroll_frame = ttk.Frame(download_tab)
        scroll_frame.grid(row=1, column=0, sticky=tk.NSEW)
        
        canvas = tk.Canvas(scroll_frame, highlightthickness=0, borderwidth=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        self._bind_mousewheel(canvas, canvas, include_children=True)
        
        content_frame = ttk.Frame(canvas)
        content_window = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

        def resize_content(event):
            canvas.itemconfigure(content_window, width=event.width)
            canvas.configure(scrollregion=canvas.bbox('all'))

        canvas.bind('<Configure>', resize_content)
        content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        content_frame.grid_columnconfigure(0, weight=1)
        
        basic_frame = ttk.LabelFrame(content_frame, text="基本设置", padding="12", style="Card.TLabelframe")
        basic_frame.pack(fill=tk.X, pady=6)
        
        ttk.Label(basic_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.save_path_var = tk.StringVar(value=self.settings.get("save_path", ""))
        basic_frame.grid_columnconfigure(1, weight=1)
        ttk.Entry(basic_frame, textvariable=self.save_path_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        ttk.Button(basic_frame, text="浏览", command=self.browse_save_path).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(basic_frame, text="用户列表:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.user_lst_var = tk.StringVar(value=self.settings.get("user_lst", ""))
        ttk.Entry(basic_frame, textvariable=self.user_lst_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=5)
        ttk.Label(basic_frame, text="(多用户用英文逗号分隔)").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        auth_token, ct0 = self._split_cookie(self.settings.get("cookie", ""))
        ttk.Label(basic_frame, text="auth_token:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.auth_token_var = tk.StringVar(value=auth_token)
        ttk.Entry(basic_frame, textvariable=self.auth_token_var, width=50).grid(row=2, column=1, sticky=tk.EW, pady=5)
        ttk.Label(basic_frame, text="Cookie 中的 auth_token 值").grid(row=2, column=2, sticky=tk.W, pady=5)

        ttk.Label(basic_frame, text="ct0:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ct0_var = tk.StringVar(value=ct0)
        ttk.Entry(basic_frame, textvariable=self.ct0_var, width=50).grid(row=3, column=1, sticky=tk.EW, pady=5)
        ttk.Label(basic_frame, text="Cookie 中的 ct0 值").grid(row=3, column=2, sticky=tk.W, pady=5)
        
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config, style="TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="开始下载", command=self.start_download, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)

        download_frame = ttk.LabelFrame(content_frame, text="下载选项", padding="12", style="Card.TLabelframe")
        download_frame.pack(fill=tk.X, pady=6)
        
        ttk.Label(download_frame, text="下载类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.download_type_var = tk.StringVar(value="default")
        if self.settings.get("has_retweet", False):
            self.download_type_var.set("retweet")
        elif self.settings.get("high_lights", False):
            self.download_type_var.set("highlights")
        elif self.settings.get("likes", False):
            self.download_type_var.set("likes")
        
        ttk.Radiobutton(download_frame, text="默认(仅用户自己的媒体)", variable=self.download_type_var, value="default").grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(download_frame, text="包含转推", variable=self.download_type_var, value="retweet").grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(download_frame, text="仅亮点内容", variable=self.download_type_var, value="highlights").grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(download_frame, text="仅点赞内容", variable=self.download_type_var, value="likes").grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(download_frame, text="时间范围:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.time_range_var = tk.StringVar(value=self.settings.get("time_range", ""))
        download_frame.grid_columnconfigure(1, weight=1)
        ttk.Entry(download_frame, textvariable=self.time_range_var, width=30).grid(row=5, column=1, sticky=tk.EW, pady=5)
        ttk.Label(download_frame, text="(格式: 1990-01-01:2030-01-01)").grid(row=5, column=2, sticky=tk.W, pady=5)
        
        other_frame = ttk.LabelFrame(content_frame, text="其他选项", padding="12", style="Card.TLabelframe")
        other_frame.pack(fill=tk.X, pady=6)
        
        self.down_log_var = tk.BooleanVar(value=self.settings.get("down_log", False))
        ttk.Checkbutton(other_frame, text="开启下载日志(避免重复下载)", variable=self.down_log_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.auto_sync_var = tk.BooleanVar(value=self.settings.get("autoSync", False))
        ttk.Checkbutton(other_frame, text="自动同步最新内容", variable=self.auto_sync_var).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        self.has_video_var = tk.BooleanVar(value=self.settings.get("has_video", False))
        ttk.Checkbutton(other_frame, text="下载视频", variable=self.has_video_var).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.log_output_var = tk.BooleanVar(value=self.settings.get("log_output", False))
        ttk.Checkbutton(other_frame, text="显示下载过程日志", variable=self.log_output_var).grid(row=1, column=1, sticky=tk.W, pady=5)

        self.completion_sound_var = tk.BooleanVar(value=self.settings.get("completion_sound", False))
        ttk.Checkbutton(other_frame, text="任务完成时播放提示音", variable=self.completion_sound_var).grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(other_frame, text="提示音路径:").grid(row=3, column=0, sticky=tk.W, pady=5)
        default_sound_path = self.settings.get("completion_sound_path", "") or "sounds"
        if default_sound_path.replace('\\', '/') == "sounds/default.wav":
            default_sound_path = "sounds"
        self.completion_sound_path_var = tk.StringVar(value=default_sound_path)
        ttk.Entry(other_frame, textvariable=self.completion_sound_path_var, width=30).grid(row=3, column=1, sticky=tk.EW, pady=5)
        ttk.Button(other_frame, text="浏览", command=self.browse_completion_sound).grid(row=3, column=2, padx=5, pady=5)
        ttk.Button(other_frame, text="试听", command=self.preview_completion_sound).grid(row=3, column=3, padx=5, pady=5)
        ttk.Label(other_frame, text="留空使用系统提示音，仅支持 WAV").grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        
        self.md_output_var = tk.BooleanVar(value=self.settings.get("md_output", False))
        ttk.Checkbutton(other_frame, text="生成 Markdown 文件", variable=self.md_output_var).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(other_frame, text="图片格式:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.image_format_var = tk.StringVar(value=self.settings.get("image_format", "orig"))
        format_values = ["orig", "jpg", "png"]
        ttk.Combobox(other_frame, textvariable=self.image_format_var, values=format_values, width=10).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(other_frame, text="媒体数量限制:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.media_count_limit_var = tk.StringVar(value=str(self.settings.get("media_count_limit", 0)))
        ttk.Entry(other_frame, textvariable=self.media_count_limit_var, width=10).grid(row=6, column=1, sticky=tk.W, pady=5)
        ttk.Label(other_frame, text="(0 为不限制)").grid(row=6, column=2, sticky=tk.W, pady=5)
        
        network_frame = ttk.LabelFrame(content_frame, text="网络设置", padding="12", style="Card.TLabelframe")
        network_frame.pack(fill=tk.X, pady=6)
        
        ttk.Label(network_frame, text="最大并发请求:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_concurrent_var = tk.StringVar(value=str(self.settings.get("max_concurrent_requests", 8)))
        ttk.Entry(network_frame, textvariable=self.max_concurrent_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(network_frame, text="请求间隔(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.request_interval_var = tk.StringVar(value=str(self.settings.get("request_interval", 0.5)))
        ttk.Entry(network_frame, textvariable=self.request_interval_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(network_frame, text="代理:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.proxy_var = tk.StringVar(value=self.settings.get("proxy", ""))
        network_frame.grid_columnconfigure(1, weight=1)
        ttk.Entry(network_frame, textvariable=self.proxy_var, width=30).grid(row=2, column=1, sticky=tk.EW, pady=5)
        ttk.Label(network_frame, text="(格式: http://localhost:port)").grid(row=2, column=2, sticky=tk.W, pady=5)
    
    def create_sync_tab(self):
        sync_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(sync_tab, text="同步管理")

        sync_tab.grid_rowconfigure(1, weight=0)
        sync_tab.grid_rowconfigure(2, weight=0)
        sync_tab.grid_rowconfigure(3, weight=1)
        sync_tab.grid_columnconfigure(0, weight=1)

        self.build_header(sync_tab, "同步管理", "查看本地用户状态并更新已选内容")

        path_frame = ttk.LabelFrame(sync_tab, text="扫描路径", padding="12", style="Card.TLabelframe")
        path_frame.grid(row=1, column=0, sticky=tk.EW, pady=(0, 10))

        ttk.Label(path_frame, text="存储路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sync_path_var = tk.StringVar(value=self.settings.get("save_path", ""))
        path_frame.grid_columnconfigure(1, weight=1)
        ttk.Entry(path_frame, textvariable=self.sync_path_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        ttk.Button(path_frame, text="浏览", command=self.sync_browse_path).grid(row=0, column=2, padx=5, pady=5)

        button_frame = ttk.Frame(sync_tab, height=42)
        button_frame.grid(row=2, column=0, sticky=tk.EW, pady=(0, 10))
        button_frame.grid_propagate(False)

        ttk.Button(button_frame, text="开始检测文件夹", command=self.sync_scan_users, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="扫描用户", command=self.sync_scan_users, style="TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全选", command=self.sync_select_all, style="TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全不选", command=self.sync_deselect_all, style="TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新选中", command=self.sync_update_selected, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)

        tree_frame = ttk.Frame(sync_tab)
        tree_frame.grid(row=3, column=0, sticky=tk.NSEW)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.sync_tree = ttk.Treeview(tree_frame, columns=('screen_name', 'name', 'file_count', 'last_download'), 
                                      show='headings', selectmode='extended')
        self.sync_tree.heading('screen_name', text='用户名')
        self.sync_tree.heading('name', text='昵称')
        self.sync_tree.heading('file_count', text='文件数')
        self.sync_tree.heading('last_download', text='最后下载')
        
        self.sync_tree.column('screen_name', width=120)
        self.sync_tree.column('name', width=150)
        self.sync_tree.column('file_count', width=80, anchor=tk.CENTER)
        self.sync_tree.column('last_download', width=120, anchor=tk.CENTER)
        self.sync_tree.tag_configure('selected', background='#2d7ff9', foreground='#ffffff')
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.sync_tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.sync_tree.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.sync_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.sync_tree.pack(fill=tk.BOTH, expand=True)
        
        self._bind_mousewheel(self.sync_tree, self.sync_tree)
        
        self.sync_users = []
    
    def create_log_tab(self):
        log_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_tab, text="日志")

        log_tab.grid_rowconfigure(0, weight=1)
        log_tab.grid_columnconfigure(0, weight=1)

        self.build_header(log_tab, "日志中心", "查看下载与同步执行过程的实时输出")

        log_panel = ttk.LabelFrame(log_tab, text="运行日志", padding="12", style="Card.TLabelframe")
        log_panel.grid(row=1, column=0, sticky=tk.NSEW)

        scroll_frame = ttk.Frame(log_panel)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(scroll_frame, wrap=tk.WORD, font=('Consolas', 10), height=18)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self._bind_mousewheel(self.log_text, self.log_text)

        ttk.Button(log_panel, text="清空日志", command=self.clear_log).pack(side=tk.BOTTOM, pady=(10, 0))
    
    def browse_save_path(self):
        path = filedialog.askdirectory()
        if path:
            path = path.replace('\\', '/')
            self.save_path_var.set(path)

    def browse_completion_sound(self):
        path = filedialog.askopenfilename(
            title="选择完成提示音",
            filetypes=[("WAV 音频", "*.wav"), ("所有文件", "*.*")]
        )
        if path:
            self.completion_sound_path_var.set(path.replace('\\', '/'))
    
    def save_config(self):
        save_path = self.save_path_var.get().strip()
        if not save_path:
            messagebox.showerror("缺少下载地址", "请先点击“浏览”选择下载文件夹")
            return False
        if not os.path.isdir(save_path):
            messagebox.showerror("下载地址无效", "请选择一个已存在的文件夹")
            return False

        self.settings["save_path"] = save_path.replace('\\', '/')
        self.settings["user_lst"] = self.user_lst_var.get()
        auth_token = self.auth_token_var.get().strip()
        ct0 = self.ct0_var.get().strip()
        self.settings["cookie"] = f"auth_token={auth_token};ct0={ct0};" if auth_token or ct0 else ""
        
        download_type = self.download_type_var.get()
        self.settings["has_retweet"] = (download_type == "retweet")
        self.settings["high_lights"] = (download_type == "highlights")
        self.settings["likes"] = (download_type == "likes")
        
        self.settings["time_range"] = self.time_range_var.get()
        self.settings["down_log"] = self.down_log_var.get()
        self.settings["autoSync"] = self.auto_sync_var.get()
        self.settings["has_video"] = self.has_video_var.get()
        self.settings["log_output"] = self.log_output_var.get()
        self.settings["completion_sound"] = self.completion_sound_var.get()
        self.settings["completion_sound_path"] = self.completion_sound_path_var.get().strip()
        self.settings["md_output"] = self.md_output_var.get()
        self.settings["image_format"] = self.image_format_var.get()
        
        try:
            self.settings["media_count_limit"] = int(self.media_count_limit_var.get())
            self.settings["max_concurrent_requests"] = int(self.max_concurrent_var.get())
            self.settings["request_interval"] = float(self.request_interval_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        
        self.settings["proxy"] = self.proxy_var.get()
        
        self.save_settings()
        return True
    
    def start_download(self):
        if not self.save_config():
            return

        if not self.settings["user_lst"]:
            messagebox.showerror("错误", "请输入用户列表")
            return

        if not self.settings["cookie"].strip() and not os.environ.get("TWITTER_COOKIE", "").strip():
            messagebox.showerror("错误", "请输入 Cookie，或设置环境变量 TWITTER_COOKIE")
            return

        self.clear_log()

        self.log_text.insert(tk.END, "开始下载...\n")
        self.log_text.see(tk.END)
        self.root.update()

        try:
            self._disable_buttons()

            if getattr(sys, "frozen", False):
                self.output_thread = threading.Thread(target=self._run_frozen_download, daemon=True)
            else:
                python_exe = os.path.abspath(sys.executable)
                self.process = subprocess.Popen(
                    [python_exe, "main.py"],
                    cwd=os.path.dirname(__file__),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1
                )
                self.output_thread = threading.Thread(target=self._read_process_output, daemon=True)
            self.output_thread.start()

        except Exception as e:
            self.log_text.insert(tk.END, f"\n启动下载失败: {e}\n")
            self._enable_buttons()

    def sync_browse_path(self):
        path = filedialog.askdirectory()
        if path:
            path = path.replace('\\', '/')
            self.sync_path_var.set(path)
    
    def sync_scan_users(self):
        save_path = self.sync_path_var.get().strip()
        
        if not save_path:
            messagebox.showerror("错误", "请先选择扫描路径")
            return
        
        if not os.path.exists(save_path):
            messagebox.showerror("错误", f"路径不存在: {save_path}")
            return
        
        self.log_text.insert(tk.END, f"正在扫描路径: {save_path}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
        try:
            from sync_manager import scan_users
            self.sync_users = scan_users(save_path)
            
            for item in self.sync_tree.get_children():
                self.sync_tree.delete(item)
            
            if not self.sync_users:
                self.log_text.insert(tk.END, "未发现任何用户\n")
                return
            
            for user in self.sync_users:
                last_download = user.last_download_date if user.last_download_date else "未知"
                self.sync_tree.insert('', tk.END, values=(
                    f"@{user.screen_name}",
                    user.name,
                    user.file_count,
                    last_download
                ), tags=(user.screen_name,))
            
            self.log_text.insert(tk.END, f"扫描完成，发现 {len(self.sync_users)} 个用户\n")
            
        except PermissionError:
            self.log_text.insert(tk.END, f"扫描失败: 没有权限访问该路径\n")
            messagebox.showerror("错误", "没有权限访问该路径，请选择其他路径")
        except Exception as e:
            self.log_text.insert(tk.END, f"扫描失败: {e}\n")
    
    def sync_select_all(self):
        for item in self.sync_tree.get_children():
            self.sync_tree.selection_add(item)
    
    def sync_deselect_all(self):
        self.sync_tree.selection_remove(self.sync_tree.selection())
    
    def sync_update_selected(self):
        if not self.save_config():
            return
        
        if not self.settings["cookie"].strip() and not os.environ.get("TWITTER_COOKIE", "").strip():
            messagebox.showerror("错误", "请输入 Cookie，或设置环境变量 TWITTER_COOKIE")
            return
        
        selected_items = self.sync_tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要更新的用户")
            return
        
        selected_screen_names = []
        for item in selected_items:
            values = self.sync_tree.item(item, 'values')
            screen_name = values[0].replace('@', '')
            selected_screen_names.append(screen_name)
        
        self.log_text.insert(tk.END, f"\n即将更新 {len(selected_screen_names)} 个用户:\n")
        for name in selected_screen_names:
            self.log_text.insert(tk.END, f"  - @{name}\n")
        self.log_text.see(tk.END)
        
        confirm = messagebox.askyesno("确认", f"确定要更新选中的 {len(selected_screen_names)} 个用户吗？")
        if not confirm:
            return
        
        self._disable_buttons()
        
        def run_update():
            try:
                if getattr(sys, "frozen", False):
                    self._run_frozen_sync(selected_screen_names)
                    return

                python_exe = os.path.abspath(sys.executable)
                users_str = ','.join(selected_screen_names)
                self.process = subprocess.Popen(
                    [python_exe, "sync_manager.py", "--users", users_str],
                    cwd=os.path.dirname(__file__),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1
                )
                
                for line in self.process.stdout:
                    if line:
                        self.root.after(0, lambda l=line: self._append_log(l))
                
                self.process.wait()
                self.root.after(0, self._on_process_complete)
                
            except Exception as e:
                self.root.after(0, lambda: self.log_text.insert(tk.END, f"\n更新失败: {e}\n"))
                self.root.after(0, self._enable_buttons)
        
        self.output_thread = threading.Thread(target=run_update, daemon=True)
        self.output_thread.start()

    def _run_frozen_sync(self, screen_names):
        try:
            from sync_manager import update_users
            update_users(screen_names, log_callback=lambda message: self.root.after(
                0, lambda: self._append_log(f"{message}\n")
            ))
            self.root.after(0, self._on_frozen_process_complete)
        except Exception as error:
            self.root.after(0, lambda: self._append_log(f"\n更新失败: {error}\n"))
            self.root.after(0, self._enable_buttons)

    def _run_frozen_download(self):
        try:
            from user_info import User_info
            from main import main as download_main

            users = [user.strip() for user in self.settings["user_lst"].replace("\n", ",").split(",") if user.strip()]
            for screen_name in users:
                self.root.after(0, lambda name=screen_name: self._append_log(f"正在下载 @{name}...\n"))
                result = download_main(User_info(screen_name))
                if result is False:
                    raise RuntimeError(f"@{screen_name} 下载失败")
            self.root.after(0, self._on_frozen_process_complete)
        except Exception as error:
            self.root.after(0, lambda: self._append_log(f"\n下载失败: {error}\n"))
            self.root.after(0, self._enable_buttons)

    def _on_frozen_process_complete(self):
        self._enable_buttons()
        self._append_log("\n下载完成！\n")
        self._play_completion_sound()

    def _read_process_output(self):
        try:
            for line in self.process.stdout:
                if line:
                    self.root.after(0, lambda l=line: self._append_log(l))
            self.process.wait()
            self.root.after(0, self._on_process_complete)
        except Exception as e:
            self.root.after(0, lambda: self.log_text.insert(tk.END, f"\n读取输出失败: {e}\n"))

    def _append_log(self, line):
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)

    def _on_process_complete(self):
        self._enable_buttons()
        if self.process.returncode == 0:
            self.log_text.insert(tk.END, "\n操作完成！\n")
            self._play_completion_sound()
        else:
            self.log_text.insert(tk.END, f"\n操作失败，返回码: {self.process.returncode}\n")

    def _resolve_completion_sound_path(self):
        sound_path = self.completion_sound_path_var.get().strip()
        if sound_path.replace('\\', '/').rstrip('/') == "sounds":
            sound_path = os.path.join(sound_path, "default.wav")
        if sound_path and not os.path.isabs(sound_path):
            external_path = os.path.join(os.path.dirname(self.settings_file), sound_path)
            bundled_path = os.path.join(getattr(sys, "_MEIPASS", ""), sound_path)
            sound_path = external_path if os.path.isfile(external_path) else bundled_path
        return sound_path

    def _play_sound(self, show_error=False):
        if winsound is None:
            return

        sound_path = self._resolve_completion_sound_path()
        try:
            if sound_path and os.path.isfile(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif not sound_path:
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            elif show_error:
                messagebox.showerror("试听失败", f"提示音文件不存在:\n{sound_path}")
            else:
                self._append_log(f"提示音文件不存在: {sound_path}\n")
        except RuntimeError as error:
            if show_error:
                messagebox.showerror("试听失败", f"播放提示音失败:\n{error}")
            else:
                self._append_log(f"播放提示音失败: {error}\n")

    def preview_completion_sound(self):
        self._play_sound(show_error=True)

    def _play_completion_sound(self):
        if self.completion_sound_var.get():
            self._play_sound()

    def _disable_buttons(self):
        self._find_and_disable_buttons(self.root)

    def _enable_buttons(self):
        self._find_and_enable_buttons(self.root)

    def _find_and_disable_buttons(self, widget):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='disabled')
            else:
                self._find_and_disable_buttons(child)

    def _find_and_enable_buttons(self, widget):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='normal')
            else:
                self._find_and_enable_buttons(child)
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = TwitterDownloadGUI(root)
    root.mainloop()