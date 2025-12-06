import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crawler import WebCrawler
from config.manager import ConfigManager
from ui.config_window import ConfigWindow

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python爬虫UI框架")
        self.root.geometry("900x600")
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化日志记录器
        self.setup_logger()
        
        # 当前爬虫实例
        self.current_crawler = None
        self.crawl_thread = None
        self.is_crawling = False
        
        # 创建UI
        self.create_widgets()
        
        # 加载配置列表
        self.refresh_config_list()
    
    def setup_logger(self):
        """设置日志记录器"""
        # 创建日志目录
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 创建日志记录器
        self.logger = logging.getLogger('crawler_ui')
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        log_file = os.path.join('logs', f'crawler_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器到记录器
        self.logger.addHandler(file_handler)
        
        # 创建自定义处理器，用于在UI中显示日志
        self.ui_handler = UILogHandler(self.log_callback)
        self.ui_handler.setLevel(logging.INFO)
        self.ui_handler.setFormatter(formatter)
        self.logger.addHandler(self.ui_handler)
    
    def log_callback(self, message):
        """日志回调函数，用于在UI中显示日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def create_widgets(self):
        """创建UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建配置选择区域
        config_frame = ttk.LabelFrame(main_frame, text="配置选择", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 配置选择下拉框
        ttk.Label(config_frame, text="选择配置:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.config_var = tk.StringVar()
        self.config_combo = ttk.Combobox(config_frame, textvariable=self.config_var, state="readonly")
        self.config_combo.grid(row=0, column=1, sticky=tk.EW, padx=(0, 5))
        
        # 配置管理按钮
        ttk.Button(config_frame, text="新建配置", command=self.create_config).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(config_frame, text="导入配置", command=self.import_config).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(config_frame, text="编辑配置", command=self.edit_config).grid(row=0, column=4, padx=(0, 5))
        ttk.Button(config_frame, text="删除配置", command=self.delete_config).grid(row=0, column=5)
        
        # 配置网格权重
        config_frame.columnconfigure(1, weight=1)
        
        # 创建控制区域
        control_frame = ttk.LabelFrame(main_frame, text="爬虫控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 控制按钮
        self.start_button = ttk.Button(control_frame, text="开始爬取", command=self.start_crawl)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="停止爬取", command=self.stop_crawl, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT)
        
        # 创建状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(control_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 创建日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加初始日志
        self.log_callback("爬虫UI框架已启动")
    
    def refresh_config_list(self):
        """刷新配置列表"""
        config_list = self.config_manager.get_config_list()
        self.config_combo['values'] = config_list
        if config_list:
            self.config_combo.current(0)
        self.log_callback(f"已加载 {len(config_list)} 个配置")
    
    def import_config(self):
        """导入配置文件"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 获取配置名称
            config_name = config_data.get('name', os.path.basename(file_path).split('.')[0])
            
            # 检查配置是否已存在
            if config_name in self.config_manager.get_config_list():
                if not messagebox.askyesno("确认", f"配置 '{config_name}' 已存在，是否覆盖？"):
                    return
            
            # 保存配置
            if self.config_manager.save_config(config_name, config_data):
                self.refresh_config_list()
                self.log_callback(f"已导入配置: {config_name}")
                messagebox.showinfo("成功", f"配置 '{config_name}' 已导入")
            else:
                messagebox.showerror("错误", f"导入配置失败: {config_name}")
        except Exception as e:
            messagebox.showerror("错误", f"导入配置文件失败: {str(e)}")
    
    def create_config(self):
        """创建新配置"""
        config_window = ConfigWindow(self.root, self.config_manager, self.refresh_config_list)
        self.root.wait_window(config_window.dialog)
    
    def edit_config(self):
        """编辑选中的配置"""
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请先选择一个配置")
            return
            
        config_data = self.config_manager.load_config(config_name)
        if config_data:
            config_window = ConfigWindow(self.root, self.config_manager, self.refresh_config_list, config_name, config_data)
            self.root.wait_window(config_window.dialog)
        else:
            messagebox.showerror("错误", f"无法加载配置: {config_name}")
    
    def delete_config(self):
        """删除选中的配置"""
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请先选择一个配置")
            return
            
        if messagebox.askyesno("确认", f"确定要删除配置 '{config_name}' 吗？"):
            if self.config_manager.delete_config(config_name):
                self.refresh_config_list()
                self.log_callback(f"已删除配置: {config_name}")
            else:
                messagebox.showerror("错误", f"删除配置失败: {config_name}")
    
    def start_crawl(self):
        """开始爬取"""
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请先选择一个配置")
            return
            
        config_data = self.config_manager.load_config(config_name)
        if not config_data:
            messagebox.showerror("错误", f"无法加载配置: {config_name}")
            return
            
        # 创建爬虫实例
        self.current_crawler = WebCrawler(config_data, self.logger)
        
        # 更新UI状态
        self.is_crawling = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("正在爬取...")
        
        # 在新线程中运行爬虫
        self.crawl_thread = threading.Thread(target=self.run_crawler)
        self.crawl_thread.daemon = True
        self.crawl_thread.start()
    
    def stop_crawl(self):
        """停止爬取"""
        self.is_crawling = False
        self.status_var.set("正在停止...")
        self.log_callback("正在停止爬取任务...")
    
    def run_crawler(self):
        """运行爬虫"""
        try:
            if self.current_crawler:
                success = self.current_crawler.crawl()
                
                # 在主线程中更新UI
                self.root.after(0, self.crawl_finished, success)
        except Exception as e:
            self.root.after(0, self.crawl_error, str(e))
    
    def crawl_finished(self, success):
        """爬取完成回调"""
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if success:
            self.status_var.set("爬取完成")
            self.log_callback("爬取任务已完成")
        else:
            self.status_var.set("爬取失败")
            self.log_callback("爬取任务失败")
    
    def crawl_error(self, error_msg):
        """爬取错误回调"""
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("爬取出错")
        self.log_callback(f"爬取出错: {error_msg}")
        messagebox.showerror("错误", f"爬取出错: {error_msg}")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_callback("日志已清空")
    
    def open_output_dir(self):
        """打开输出目录"""
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请先选择一个配置")
            return
            
        config_data = self.config_manager.load_config(config_name)
        if not config_data:
            messagebox.showerror("错误", f"无法加载配置: {config_name}")
            return
            
        output_dir = config_data.get('output_dir', 'output')
        
        # 创建输出目录（如果不存在）
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 打开目录
        os.startfile(output_dir)
    
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