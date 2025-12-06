import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径，以便导入其他模块
if getattr(sys, 'frozen', False):
    # 打包后的环境
    application_path = os.path.dirname(sys.executable)
else:
    # 开发环境
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(application_path)

from config.manager import ConfigManager
from ui.crawler_tab import CrawlerTab

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文本爬虫UI框架")
        self.root.geometry("1000x700")
        
        # 设置工作目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境，确保在exe所在目录工作
            os.chdir(os.path.dirname(sys.executable))
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 标签页计数器，用于生成唯一的标签页名称
        self.tab_counter = 1
        
        # 存储所有爬虫标签页的字典 {tab_name: CrawlerTab}
        self.crawler_tabs = {}
        
        # 创建UI
        self.create_widgets()
        
        # 创建第一个默认标签页
        self.add_new_tab("爬虫 1")
    
    def create_widgets(self):
        """创建UI组件"""
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建爬虫标签页", command=self.add_new_tab_from_menu)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加新标签页按钮
        ttk.Button(toolbar, text="添加新爬虫标签页", command=self.add_new_tab_from_menu).pack(side=tk.LEFT, padx=(0, 5))
        
        # 创建标签页(Notebook)控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 绑定右键菜单事件
        self.notebook.bind("<Button-3>", self.show_tab_context_menu)
    
    def add_new_tab_from_menu(self):
        """从菜单添加新标签页"""
        self.tab_counter += 1
        tab_name = f"爬虫 {self.tab_counter}"
        self.add_new_tab(tab_name)
    
    def add_new_tab(self, tab_name):
        """添加新的爬虫标签页
        
        Args:
            tab_name: 标签页名称
        """
        # 检查标签页名称是否已存在
        if tab_name in self.crawler_tabs:
            messagebox.showwarning("警告", f"标签页 '{tab_name}' 已存在")
            return
        
        # 创建新的爬虫标签页
        crawler_tab = CrawlerTab(
            self.notebook, 
            tab_name, 
            self.config_manager,
            on_close_callback=self.on_tab_close
        )
        
        # 将标签页添加到Notebook控件
        self.notebook.add(crawler_tab.frame, text=tab_name)
        
        # 存储标签页引用
        self.crawler_tabs[tab_name] = crawler_tab
        
        # 切换到新创建的标签页
        self.notebook.select(crawler_tab.frame)
        
    
    def on_tab_changed(self, event):
        """标签页切换事件处理"""
        # 获取当前选中的标签页索引
        current_tab_index = self.notebook.index("current")
        
        # 获取当前选中的标签页文本
        current_tab_text = self.notebook.tab(current_tab_index, "text")
        
        # 如果当前标签页是爬虫标签页，记录日志
        if current_tab_text in self.crawler_tabs:
            crawler_tab = self.crawler_tabs[current_tab_text]
    
    def show_tab_context_menu(self, event):
        """显示标签页右键菜单"""
        # 获取点击位置对应的标签页
        tab_index = self.notebook.index(f"@{event.x},{event.y}")
        tab_text = self.notebook.tab(tab_index, "text")
        
        # 只对爬虫标签页显示右键菜单
        if tab_text in self.crawler_tabs:
            # 创建右键菜单
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="关闭标签页", command=lambda: self.close_tab(tab_text))
            context_menu.add_command(label="重命名标签页", command=lambda: self.rename_tab(tab_text))
            
            # 显示菜单
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def close_tab(self, tab_name):
        """关闭指定的标签页"""
        if tab_name in self.crawler_tabs:
            crawler_tab = self.crawler_tabs[tab_name]
            crawler_tab.close_tab()
    
    def rename_tab(self, tab_name):
        """重命名指定的标签页"""
        if tab_name not in self.crawler_tabs:
            return
        
        # 创建输入对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("重命名标签页")
        dialog.geometry("300x100")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # 创建输入框
        ttk.Label(dialog, text="新名称:").pack(pady=(10, 5))
        entry_var = tk.StringVar(value=tab_name)
        entry = ttk.Entry(dialog, textvariable=entry_var, width=30)
        entry.pack(pady=5, padx=10, fill=tk.X)
        entry.select_range(0, tk.END)
        entry.focus()
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def on_ok():
            new_name = entry_var.get().strip()
            if not new_name:
                messagebox.showwarning("警告", "标签页名称不能为空")
                return
            
            if new_name == tab_name:
                dialog.destroy()
                return
                
            if new_name in self.crawler_tabs:
                messagebox.showwarning("警告", f"标签页 '{new_name}' 已存在")
                return
                
            # 重命名标签页
            crawler_tab = self.crawler_tabs[tab_name]
            crawler_tab.tab_name = new_name
            
            # 更新字典键
            self.crawler_tabs[new_name] = self.crawler_tabs.pop(tab_name)
            
            # 更新标签页文本
            self.notebook.tab(crawler_tab.frame, text=new_name)
            
            # 记录日志
            crawler_tab.log_callback(f"标签页已重命名为: {new_name}")
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        entry.bind("<Return>", lambda e: on_ok())
    
    def on_tab_close(self, tab_name):
        """标签页关闭事件处理
        
        Args:
            tab_name: 要关闭的标签页名称
        """
        # 从字典中移除标签页引用
        if tab_name in self.crawler_tabs:
            del self.crawler_tabs[tab_name]
    
    def run(self):
        """运行主窗口"""
        self.root.mainloop()


class UILogHandler(logging.Handler):
    """自定义日志处理器，用于在UI中显示日志"""
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    def emit(self, record):
        """发送日志记录"""
        try:
            msg = self.format(record)
            self.callback(msg)
        except Exception:
            self.handleError(record)