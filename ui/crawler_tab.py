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
from ui.config_window import ConfigWindow

class CrawlerTab:
    """爬虫标签页类，封装单个爬虫的所有UI元素和功能"""
    
    def __init__(self, parent, tab_name, config_manager, on_close_callback=None):
        """
        初始化爬虫标签页
        
        Args:
            parent: 父级Notebook控件
            tab_name: 标签页名称
            config_manager: 配置管理器实例
            on_close_callback: 标签页关闭回调函数
        """
        self.parent = parent
        self.tab_name = tab_name
        self.config_manager = config_manager
        self.on_close_callback = on_close_callback
        
        # 创建标签页框架
        self.frame = ttk.Frame(parent)
        
        # 当前爬虫实例
        self.current_crawler = None
        self.crawl_thread = None
        self.is_crawling = False
        
        # 创建UI组件
        self.create_widgets()
        
        # 初始化日志记录器
        self.setup_logger()
        
        # 加载配置列表
        self.refresh_config_list()
    
    def setup_logger(self):
        """设置日志记录器"""
        # 创建日志记录器，使用标签页名称作为标识
        self.logger = logging.getLogger(f'crawler_ui_{self.tab_name}')
        self.logger.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
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
        main_frame = ttk.Frame(self.frame, padding="10")
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
        
        self.test_button = ttk.Button(control_frame, text="测试配置", command=self.test_config)
        self.test_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加关闭标签页按钮
        ttk.Button(control_frame, text="关闭标签页", command=self.close_tab).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 创建进度条区域
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        # 初始化进度为0
        self.progress_var.set(0)
        
        # 创建日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加初始日志
        self.log_callback(f"爬虫标签页 '{self.tab_name}' 已启动")
    
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
        config_window = ConfigWindow(self.frame, self.config_manager, self.refresh_config_list)
        self.frame.wait_window(config_window.dialog)
    
    def edit_config(self):
        """编辑选中的配置"""
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请先选择一个配置")
            return
            
        config_data = self.config_manager.load_config(config_name)
        if config_data:
            config_window = ConfigWindow(self.frame, self.config_manager, self.refresh_config_list, config_name, config_data)
            self.frame.wait_window(config_window.dialog)
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
    
    def update_progress(self, current, total, message=""):
        """更新进度条"""
        if total > 0:
            # 计算百分比
            percentage = int((current / total) * 100)
            # 更新进度条
            self.progress_var.set(percentage)
    
    def test_config(self):
        """测试配置是否正确"""
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请先选择一个配置")
            return
            
        config_data = self.config_manager.load_config(config_name)
        if not config_data:
            messagebox.showerror("错误", f"无法加载配置: {config_name}")
            return
            
        # 创建爬虫实例，传入进度回调函数
        def progress_callback(current, total, message):
            # 在主线程中更新进度
            self.frame.after(0, self.update_progress, current, total, message)
            
        self.current_crawler = WebCrawler(config_data, self.logger, progress_callback)
        
        # 更新UI状态
        self.is_crawling = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.test_button.config(state=tk.DISABLED)
        # 开始测试配置，进度条初始化为0
        self.progress_var.set(0)
        
        # 在新线程中运行测试
        self.crawl_thread = threading.Thread(target=self.run_test)
        self.crawl_thread.daemon = True
        self.crawl_thread.start()
    
    def run_test(self):
        """运行配置测试"""
        try:
            if self.current_crawler and self.is_crawling:
                test_results = self.current_crawler.test_config()
                
                # 在主线程中更新UI
                self.frame.after(0, self.test_finished, test_results)
        except Exception as e:
            self.frame.after(0, self.test_error, str(e))
    
    def test_finished(self, test_results):
        """测试完成回调"""
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.test_button.config(state=tk.NORMAL)
        
        # 检查是否是因为停止而结束的
        if self.current_crawler and self.current_crawler.is_stopped():
            self.progress_var.set(0)
            self.log_callback("配置测试已停止")
        elif test_results['success']:
            self.progress_var.set(100)
            self.log_callback("配置测试成功")
            
            # 显示测试结果
            self.show_test_results(test_results)
        else:
            self.progress_var.set(0)
            self.log_callback("配置测试失败")
            
            # 显示测试结果
            self.show_test_results(test_results)
    
    def test_error(self, error_msg):
        """测试错误回调"""
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.test_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.log_callback(f"配置测试出错: {error_msg}")
        messagebox.showerror("错误", f"配置测试出错: {error_msg}")
    
    def show_test_results(self, test_results):
        """显示测试结果"""
        # 创建测试结果窗口
        result_window = tk.Toplevel(self.frame)
        result_window.title("配置测试结果")
        result_window.geometry("800x600")
        result_window.resizable(True, True)
        
        # 创建笔记本控件
        notebook = ttk.Notebook(result_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 概要标签页
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="概要")
        
        # 测试概要
        summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, state=tk.DISABLED)
        summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 构建概要内容
        summary_content = f"测试状态: {'成功' if test_results['success'] else '失败'}\n\n"
        summary_content += f"测试页数: {test_results['pages_tested']}\n"
        summary_content += f"找到链接数: {test_results['links_found']}\n"
        summary_content += f"测试文章数: {test_results['articles_tested']}\n"
        summary_content += f"成功解析文章数: {test_results['articles_parsed']}\n\n"
        
        if test_results['errors']:
            summary_content += "错误信息:\n"
            for error in test_results['errors']:
                summary_content += f"- {error}\n"
        
        summary_text.config(state=tk.NORMAL)
        summary_text.insert(tk.END, summary_content)
        summary_text.config(state=tk.DISABLED)
        
        # 样本链接标签页
        if test_results['sample_links']:
            links_frame = ttk.Frame(notebook)
            notebook.add(links_frame, text="样本链接")
            
            links_text = scrolledtext.ScrolledText(links_frame, wrap=tk.WORD, state=tk.DISABLED)
            links_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            links_content = ""
            for i, link in enumerate(test_results['sample_links'], 1):
                links_content += f"{i}. 页面 {link['page']}: {link['title']}\n"
                links_content += f"   URL: {link['url']}\n\n"
            
            links_text.config(state=tk.NORMAL)
            links_text.insert(tk.END, links_content)
            links_text.config(state=tk.DISABLED)
        
        # 样本文章标签页
        if test_results['sample_articles']:
            articles_frame = ttk.Frame(notebook)
            notebook.add(articles_frame, text="样本文章")
            
            articles_text = scrolledtext.ScrolledText(articles_frame, wrap=tk.WORD, state=tk.DISABLED)
            articles_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            articles_content = ""
            for i, article in enumerate(test_results['sample_articles'], 1):
                articles_content += f"{i}. 标题: {article['title']}\n"
                articles_content += f"   URL: {article['url']}\n"
                articles_content += f"   时间: {article['time']}\n"
                articles_content += f"   内容长度: {article['content_length']} 字符\n"
                articles_content += f"   内容预览: {article['content_preview']}\n\n"
            
            articles_text.config(state=tk.NORMAL)
            articles_text.insert(tk.END, articles_content)
            articles_text.config(state=tk.DISABLED)
        
        # 关闭按钮
        close_button = ttk.Button(result_window, text="关闭", command=result_window.destroy)
        close_button.pack(pady=10)
    
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
            
        # 创建爬虫实例，传入进度回调函数
        def progress_callback(current, total, message):
            # 在主线程中更新进度
            self.frame.after(0, self.update_progress, current, total, message)
            
        self.current_crawler = WebCrawler(config_data, self.logger, progress_callback)
        
        # 更新UI状态
        self.is_crawling = True
        self.stop_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)
        # 开始爬取，进度条初始化为0
        self.progress_var.set(0)
        
        # 在新线程中运行爬虫
        self.crawl_thread = threading.Thread(target=self.run_crawler)
        self.crawl_thread.daemon = True
        self.crawl_thread.start()
    
    def stop_crawl(self):
        """停止爬取"""
        if not self.is_crawling:
            return
            
        self.is_crawling = False
        self.log_callback("正在停止爬取任务...")
        
        # 调用爬虫的停止方法
        if self.current_crawler:
            self.current_crawler.stop()
    
    def run_crawler(self):
        """运行爬虫"""
        try:
            if self.current_crawler and self.is_crawling:
                success = self.current_crawler.crawl()
                
                # 在主线程中更新UI
                self.frame.after(0, self.crawl_finished, success)
        except Exception as e:
            self.frame.after(0, self.crawl_error, str(e))
    
    def crawl_finished(self, success):
        """爬取完成回调"""
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 检查是否是因为停止而结束的
        if self.current_crawler and self.current_crawler.is_stopped():
            self.progress_var.set(0)
            self.log_callback("爬取任务已停止")
        elif success:
            self.progress_var.set(100)
            self.log_callback("爬取任务已完成")
        else:
            self.progress_var.set(0)
            self.log_callback("爬取任务失败")
    
    def crawl_error(self, error_msg):
        """爬取错误回调"""
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
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
    
    def close_tab(self):
        """关闭当前标签页"""
        # 如果正在爬取，先询问用户是否确认关闭
        if self.is_crawling:
            if not messagebox.askyesno("确认", "当前标签页正在爬取数据，确定要关闭吗？"):
                return
        
        # 调用停止方法进行清理
        self.stop()
        
        # 从父级Notebook中移除当前标签页
        self.parent.forget(self.frame)
    
    def stop(self):
        """停止标签页，用于关闭时的清理工作"""
        # 如果正在爬取，先停止
        if self.is_crawling:
            self.stop_crawl()
            # 等待爬虫线程结束
            if self.crawl_thread and self.crawl_thread.is_alive():
                self.crawl_thread.join(timeout=2)  # 最多等待2秒
        
        # 调用关闭回调
        if self.on_close_callback:
            self.on_close_callback(self.tab_name)


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