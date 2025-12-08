import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
from urllib.parse import urlparse

# 尝试导入win32gui模块
try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

class RequestTestWindow:
    def __init__(self, parent):
        """初始化请求测试窗口
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Request测试工具")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # 设置窗口样式
        self.window.overrideredirect(False)  # 确保窗口有系统标题栏
        
        # 尝试使用wm_attributes设置窗口样式
        self.window.wm_attributes('-toolwindow', False)  # 确保有最大化按钮
        self.window.wm_attributes('-alpha', 1.0)  # 确保窗口完全不透明
        
        # 设置窗口协议
        self.window.wm_protocol("WM_DELETE_WINDOW", self.on_close)  # 处理窗口关闭事件
        
        # 设置窗口在父窗口中心
        # self.window.transient(parent)  # 注释掉这行，可能会影响最大化按钮的显示
        # self.window.grab_set()  # 注释掉这行，可能会影响最大化按钮的显示
        
        # 创建UI组件
        self.create_widgets()
        
        # 居中显示窗口
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def on_close(self):
        """处理窗口关闭事件"""
        self.window.destroy()
    
    def _add_maximize_button(self):
        """添加最大化按钮"""
        try:
            # 尝试使用wm_attributes设置窗口样式
            self.window.wm_attributes('-toolwindow', False)
            
            # 尝试使用Windows API
            import ctypes
            # 获取窗口句柄
            hwnd = self.window.winfo_id()
            if hwnd:
                # 获取当前窗口样式
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE = -16
                # 添加最大化按钮样式 (WS_MAXIMIZEBOX)
                new_style = style | 0x00010000  # WS_MAXIMIZEBOX = 0x00010000
                # 设置新的窗口样式
                ctypes.windll.user32.SetWindowLongW(hwnd, -16, new_style)
                # 刷新窗口显示
                self.window.update()
        except Exception as e:
            # 如果Windows API调用失败，至少保持基本功能
            print(f"无法添加最大化按钮: {e}")
            pass
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="URL设置")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        # URL输入框
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.url_entry.bind("<Return>", lambda e: self.test_request())
        
        # 请求方法选择
        ttk.Label(url_frame, text="请求方法:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.method_var = tk.StringVar(value="GET")
        method_frame = ttk.Frame(url_frame)
        method_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD"]
        for method in methods:
            ttk.Radiobutton(method_frame, text=method, variable=self.method_var, 
                           value=method).pack(side=tk.LEFT, padx=5)
        
        # 配置列权重
        url_frame.columnconfigure(1, weight=1)
        
        # 请求头设置区域
        headers_frame = ttk.LabelFrame(main_frame, text="请求头设置 (可选)")
        headers_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 请求头输入框
        self.headers_text = scrolledtext.ScrolledText(headers_frame, height=5, width=80)
        self.headers_text.pack(fill=tk.X, padx=5, pady=5)
        self.headers_text.insert(tk.END, '{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}')
        
        # 请求体设置区域 (仅POST/PUT请求)
        self.body_frame = ttk.LabelFrame(main_frame, text="请求体设置 (仅POST/PUT请求)")
        self.body_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.body_text = scrolledtext.ScrolledText(self.body_frame, height=5, width=80)
        self.body_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="发送请求", command=self.test_request).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="响应结果")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(result_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 结果文本框
        self.result_text = scrolledtext.ScrolledText(result_frame, height=15, width=80)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定请求方法变化事件
        self.method_var.trace("w", self.on_method_change)
        
        # 初始状态下隐藏请求体设置区域
        self.on_method_change()
    
    def on_method_change(self, *args):
        """请求方法变化时的处理"""
        method = self.method_var.get()
        if method in ["POST", "PUT"]:
            self.body_frame.pack(fill=tk.X, pady=(0, 10), after=self.headers_frame.master.winfo_children()[1])
        else:
            self.body_frame.pack_forget()
    
    def test_request(self):
        """发送HTTP请求"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入URL")
            return
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            self.url_var.set(url)
        
        method = self.method_var.get()
        
        # 解析请求头
        headers = {}
        headers_text = self.headers_text.get(1.0, tk.END).strip()
        if headers_text:
            try:
                headers = json.loads(headers_text)
            except json.JSONDecodeError:
                messagebox.showerror("错误", "请求头格式错误，请输入有效的JSON格式")
                return
        
        # 解析请求体
        body = None
        if method in ["POST", "PUT"]:
            body_text = self.body_text.get(1.0, tk.END).strip()
            if body_text:
                try:
                    body = json.loads(body_text)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，则作为纯文本处理
                    body = body_text
        
        # 在新线程中发送请求，避免UI阻塞
        threading.Thread(target=self._send_request, args=(url, method, headers, body), daemon=True).start()
    
    def _send_request(self, url, method, headers, body):
        """在后台线程中发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            headers: 请求头
            body: 请求体
        """
        try:
            # 更新状态
            self.status_var.set(f"正在发送 {method} 请求到 {url}...")
            
            # 发送请求
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if not isinstance(body, dict) else None,
                timeout=30
            )
            
            # 更新状态
            self.status_var.set(f"请求完成 - 状态码: {response.status_code}")
            
            # 准备响应信息
            result_info = f"请求方法: {method}\n"
            result_info += f"请求URL: {url}\n"
            result_info += f"状态码: {response.status_code}\n"
            result_info += f"响应头:\n{json.dumps(dict(response.headers), indent=2, ensure_ascii=False)}\n\n"
            
            # 检查响应状态码
            if response.status_code >= 400:
                result_info += f"错误响应: {response.reason}\n\n"
            
            # 添加响应内容
            try:
                # 尝试解析为JSON
                content = response.json()
                result_info += f"响应内容 (JSON):\n{json.dumps(content, indent=2, ensure_ascii=False)}"
            except:
                # 如果不是JSON，则显示原始内容
                content = response.text
                result_info += f"响应内容 (文本):\n{content}"
            
            # 在主线程中更新UI
            self.window.after(0, self._update_result, result_info)
            
        except requests.exceptions.Timeout:
            self.window.after(0, self._update_error, "请求超时")
        except requests.exceptions.ConnectionError:
            self.window.after(0, self._update_error, "连接错误，请检查URL是否正确或网络是否正常")
        except requests.exceptions.RequestException as e:
            self.window.after(0, self._update_error, f"请求异常: {str(e)}")
        except Exception as e:
            self.window.after(0, self._update_error, f"未知错误: {str(e)}")
    
    def _update_result(self, result_info):
        """更新结果显示
        
        Args:
            result_info: 响应信息
        """
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_info)
    
    def _update_error(self, error_msg):
        """更新错误信息
        
        Args:
            error_msg: 错误信息
        """
        self.status_var.set("请求失败")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"错误: {error_msg}")
    
    def clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("准备就绪")