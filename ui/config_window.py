import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

class ConfigWindow:
    def __init__(self, parent, config_manager, refresh_callback, config_name=None, config_data=None):
        """
        初始化配置窗口
        
        Args:
            parent: 父窗口
            config_manager: 配置管理器实例
            refresh_callback: 刷新配置列表的回调函数
            config_name: 配置名称（编辑模式）
            config_data: 配置数据（编辑模式）
        """
        self.parent = parent
        self.config_manager = config_manager
        self.refresh_callback = refresh_callback
        self.config_name = config_name
        self.is_edit_mode = config_name is not None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑配置" if self.is_edit_mode else "新建配置")
        self.dialog.geometry("700x750")  # 进一步增加高度以确保按钮完全可见
        self.dialog.resizable(True, True)  # 允许调整大小
        self.dialog.transient(parent)
        self.dialog.grab_set()
        # 设置最小高度，确保按钮可见
        self.dialog.minsize(700, 700)
        
        # 创建变量
        self.name_var = tk.StringVar()
        self.base_url_var = tk.StringVar()
        self.url_onepage_var = tk.StringVar()
        self.url_multi_page_var = tk.StringVar()
        self.url_multi_page_start_var = tk.IntVar(value=2)  # 默认从第2页开始
        self.url_multi_page_stop_var = tk.IntVar(value=9999999)  # 默认到9999999页
        self.delay_min_var = tk.StringVar(value="1000")
        self.delay_max_var = tk.StringVar(value="3000")
        
        # URL列表配置变量
        self.list_container_name_var = tk.StringVar(value="div")
        self.list_container_class_var = tk.StringVar()
        self.list_container_id_var = tk.StringVar()
        self.list_item_name_var = tk.StringVar(value="li")
        self.list_item_title_name_var = tk.StringVar(value="a")
        self.list_item_title_attr_var = tk.StringVar(value="text")
        self.list_item_link_name_var = tk.StringVar(value="a")
        self.list_item_link_attr_var = tk.StringVar(value="href")
        
        # 文章配置变量
        self.article_container_name_var = tk.StringVar(value="div")
        self.article_container_class_var = tk.StringVar()
        self.article_container_id_var = tk.StringVar()
        self.article_text_item_name_var = tk.StringVar(value="p")
        self.article_text_item_attr_var = tk.StringVar(value="text")
        
        # 请求头变量
        self.user_agent_var = tk.StringVar(value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # JSONL写入器变量
        self.use_jsonl_var = tk.BooleanVar(value=False)
        self.jsonl_file_prefix_var = tk.StringVar()
        self.jsonl_max_entries_var = tk.StringVar(value="1000")
        self.jsonl_base_path_var = tk.StringVar()
        
        # 多页爬取变量已移除，不再需要
        
        # 如果是编辑模式，加载数据
        if self.is_edit_mode and config_data:
            self.load_config_data(config_data)
        # 如果是新建模式，加载默认配置
        elif not self.is_edit_mode:
            self.load_default_config()
        
        # 创建UI
        self.create_widgets()
        
        # 居中显示
        self.center_window()
    
    def load_config_data(self, config_data):
        """加载配置数据到表单"""
        self.name_var.set(config_data.get('name', ''))
        self.base_url_var.set(config_data.get('base_url', ''))
        # 加载URL配置
        self.url_onepage_var.set(config_data.get('url_onepage', ''))
        self.url_multi_page_var.set(config_data.get('url_multi_page', ''))
        self.url_multi_page_start_var.set(config_data.get('url_multi_page_start', 2))
        self.url_multi_page_stop_var.set(config_data.get('url_multi_page_stop', 9999999))
        # output_dir已移除，不再加载
        self.delay_min_var.set(str(config_data.get('delay_min', 1000)))
        self.delay_max_var.set(str(config_data.get('delay_max', 3000)))
        
        # URL列表配置
        url_list_config = config_data.get('url_list_config', {})
        target_list_container = url_list_config.get('target_list_container', {})
        self.list_container_name_var.set(target_list_container.get('name', 'div'))
        self.list_container_class_var.set(target_list_container.get('class', ''))
        self.list_container_id_var.set(target_list_container.get('id', ''))
        
        target_list_item = url_list_config.get('target_list_item', {})
        self.list_item_name_var.set(target_list_item.get('name', 'li'))
        
        title_config = target_list_item.get('title', {})
        self.list_item_title_name_var.set(title_config.get('name', 'a'))
        self.list_item_title_attr_var.set(title_config.get('attr', 'text'))
        
        link_config = target_list_item.get('link', {})
        self.list_item_link_name_var.set(link_config.get('name', 'a'))
        self.list_item_link_attr_var.set(link_config.get('attr', 'href'))
        
        # 文章配置
        article_config = config_data.get('article_config', {})
        target_container = article_config.get('target_container', {})
        self.article_container_name_var.set(target_container.get('name', 'div'))
        self.article_container_class_var.set(target_container.get('class', ''))
        self.article_container_id_var.set(target_container.get('id', ''))
        
        target_text_item = article_config.get('target_text_item', {})
        self.article_text_item_name_var.set(target_text_item.get('name', 'p'))
        self.article_text_item_attr_var.set(target_text_item.get('attr', 'text'))
        
        # 请求头
        headers = config_data.get('headers', {})
        self.user_agent_var.set(headers.get('User-Agent', ''))
        
        # JSONL写入器配置
        self.use_jsonl_var.set(config_data.get('use_jsonl', False))
        jsonl_config = config_data.get('jsonl_config', {})
        self.jsonl_file_prefix_var.set(jsonl_config.get('file_prefix', ''))
        self.jsonl_max_entries_var.set(str(jsonl_config.get('max_entries', 1000)))
        self.jsonl_base_path_var.set(jsonl_config.get('base_path', ''))
        
        # 多页爬取配置已移除，不再加载
    
    def load_default_config(self):
        """加载默认配置"""
        try:
            # 获取default.json的路径
            default_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'default.json')
            
            # 如果文件存在，加载并应用默认配置
            if os.path.exists(default_config_path):
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    default_config = json.load(f)
                self.load_config_data(default_config)
        except Exception as e:
            print(f"加载默认配置失败: {e}")
    
    def create_widgets(self):
        """创建UI组件"""
        # 使用网格布局确保按钮区域始终可见
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # 创建主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 创建笔记本（选项卡）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本设置选项卡
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="基本设置")
        self.create_basic_tab(basic_frame)
        
        # URL列表配置选项卡
        url_list_frame = ttk.Frame(notebook, padding="10")
        notebook.add(url_list_frame, text="URL列表配置")
        self.create_url_list_tab(url_list_frame)
        
        # 文章配置选项卡
        article_frame = ttk.Frame(notebook, padding="10")
        notebook.add(article_frame, text="文章配置")
        self.create_article_tab(article_frame)
        
        # 高级设置选项卡
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="高级设置")
        self.create_advanced_tab(advanced_frame)
        
        # 添加分隔线使按钮区域更明显
        separator = ttk.Separator(self.dialog, orient='horizontal')
        separator.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # 按钮区域 - 使用网格布局确保完全可见
        button_frame = ttk.Frame(self.dialog, padding="15")
        button_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # 使用更明显的按钮样式
        save_btn = ttk.Button(button_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 将次要按钮放在左侧
        ttk.Button(button_frame, text="导入配置", command=self.import_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出配置", command=self.export_config).pack(side=tk.LEFT, padx=(0, 5))
    
    def create_basic_tab(self, parent):
        """创建基本设置选项卡"""
        # 配置名称
        ttk.Label(parent, text="配置名称:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(parent, textvariable=self.name_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=(0, 10))
        
        # 基础URL
        ttk.Label(parent, text="基础URL:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(parent, textvariable=self.base_url_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=(0, 10))
        
        # 单页URL
        ttk.Label(parent, text="单页URL:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(parent, textvariable=self.url_onepage_var, width=50).grid(row=2, column=1, sticky=tk.EW, pady=(0, 10))
        
        # 多页URL模板
        ttk.Label(parent, text="多页URL模板:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(parent, textvariable=self.url_multi_page_var, width=50).grid(row=3, column=1, sticky=tk.EW, pady=(0, 10))
        
        # 多页URL起始页码
        ttk.Label(parent, text="多页URL起始页码:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(parent, textvariable=self.url_multi_page_start_var, width=50).grid(row=4, column=1, sticky=tk.EW, pady=(0, 10))
        
        # 多页URL结束页码
        ttk.Label(parent, text="多页URL结束页码:").grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Entry(parent, textvariable=self.url_multi_page_stop_var, width=50).grid(row=5, column=1, sticky=tk.EW, pady=(0, 10))
        
        # 输出目录已移除，因为输出路径在jsonl_config中配置
        
        # 延迟设置
        delay_frame = ttk.Frame(parent)
        delay_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        ttk.Label(delay_frame, text="最小延迟(ms):").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(delay_frame, textvariable=self.delay_min_var, width=10).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(delay_frame, text="最大延迟(ms):").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(delay_frame, textvariable=self.delay_max_var, width=10).pack(side=tk.LEFT)
        
        # 配置说明
        info_frame = ttk.LabelFrame(parent, text="配置说明", padding="10")
        info_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        info_text = """基本设置说明：
1. 配置名称：用于标识不同的爬虫配置
2. 基础URL：要爬取的网站基础URL
3. 单页URL：单页爬取的URL（可选）
4. 多页URL模板：多页爬取的URL模板，使用{}作为页码占位符（可选）
5. 多页URL起始页码：多页爬取的起始页码
6. 多页URL结束页码：多页爬取的结束页码（可选，默认为9999999）
7. 延迟设置：请求之间的延迟时间范围（毫秒）"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # 设置列权重
        parent.columnconfigure(1, weight=1)
    
    def create_url_list_tab(self, parent):
        """创建URL列表配置选项卡"""
        # 列表容器配置
        container_frame = ttk.LabelFrame(parent, text="列表容器配置", padding="10")
        container_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(container_frame, text="容器标签名:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(container_frame, textvariable=self.list_container_name_var, width=30).grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(container_frame, text="容器CSS类名:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(container_frame, textvariable=self.list_container_class_var, width=30).grid(row=1, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(container_frame, text="容器ID:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(container_frame, textvariable=self.list_container_id_var, width=30).grid(row=2, column=1, sticky=tk.EW, pady=(0, 5))
        
        container_frame.columnconfigure(1, weight=1)
        
        # 列表项配置
        item_frame = ttk.LabelFrame(parent, text="列表项配置", padding="10")
        item_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(item_frame, text="列表项标签名:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(item_frame, textvariable=self.list_item_name_var, width=30).grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))
        
        # 标题配置
        ttk.Label(item_frame, text="标题标签名:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(item_frame, textvariable=self.list_item_title_name_var, width=30).grid(row=1, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(item_frame, text="标题属性:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        title_attr_frame = ttk.Frame(item_frame)
        title_attr_frame.grid(row=2, column=1, sticky=tk.EW, pady=(0, 5))
        title_attr_frame.columnconfigure(0, weight=1)
        
        title_attr_combo = ttk.Combobox(title_attr_frame, textvariable=self.list_item_title_attr_var, width=27)
        title_attr_combo['values'] = ('text', 'href', 'title', 'alt')
        title_attr_combo.grid(row=0, column=0, sticky=tk.EW)
        
        # 链接配置
        ttk.Label(item_frame, text="链接标签名:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(item_frame, textvariable=self.list_item_link_name_var, width=30).grid(row=3, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(item_frame, text="链接属性:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        link_attr_frame = ttk.Frame(item_frame)
        link_attr_frame.grid(row=4, column=1, sticky=tk.EW, pady=(0, 5))
        link_attr_frame.columnconfigure(0, weight=1)
        
        link_attr_combo = ttk.Combobox(link_attr_frame, textvariable=self.list_item_link_attr_var, width=27)
        link_attr_combo['values'] = ('href', 'text', 'title', 'alt')
        link_attr_combo.grid(row=0, column=0, sticky=tk.EW)
        
        item_frame.columnconfigure(1, weight=1)
        
        # 配置说明
        info_frame = ttk.LabelFrame(parent, text="配置说明", padding="10")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = """URL列表配置说明：
1. 列表容器配置：包含链接列表的容器元素
   - 容器标签名：容器的HTML标签（如div、ul等）
   - 容器CSS类名：容器的CSS类名（可选）
   - 容器ID：容器的ID属性（可选）
   
2. 列表项配置：每个列表项的配置
   - 列表项标签名：列表项的HTML标签（如li、div等）
   - 标题标签名：标题元素的HTML标签（通常是a）
   - 标题属性：标题的属性（text表示文本内容，href表示链接地址）
   - 链接标签名：链接元素的HTML标签（通常是a）
   - 链接属性：链接的属性（通常是href）"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def create_article_tab(self, parent):
        """创建文章配置选项卡"""
        # 文章容器配置
        container_frame = ttk.LabelFrame(parent, text="文章容器配置", padding="10")
        container_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(container_frame, text="容器标签名:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(container_frame, textvariable=self.article_container_name_var, width=30).grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(container_frame, text="容器CSS类名:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(container_frame, textvariable=self.article_container_class_var, width=30).grid(row=1, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(container_frame, text="容器ID:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(container_frame, textvariable=self.article_container_id_var, width=30).grid(row=2, column=1, sticky=tk.EW, pady=(0, 5))
        
        container_frame.columnconfigure(1, weight=1)
        
        # 文本项配置
        text_frame = ttk.LabelFrame(parent, text="文本项配置", padding="10")
        text_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(text_frame, text="文本项标签名:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(text_frame, textvariable=self.article_text_item_name_var, width=30).grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(text_frame, text="文本项属性:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        text_attr_frame = ttk.Frame(text_frame)
        text_attr_frame.grid(row=1, column=1, sticky=tk.EW, pady=(0, 5))
        text_attr_frame.columnconfigure(0, weight=1)
        
        text_attr_combo = ttk.Combobox(text_attr_frame, textvariable=self.article_text_item_attr_var, width=27)
        text_attr_combo['values'] = ('text', 'href', 'title', 'alt')
        text_attr_combo.grid(row=0, column=0, sticky=tk.EW)
        
        text_frame.columnconfigure(1, weight=1)
        
        # 配置说明
        info_frame = ttk.LabelFrame(parent, text="配置说明", padding="10")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = """文章配置说明：
1. 文章容器配置：包含文章内容的容器元素
   - 容器标签名：容器的HTML标签（如div、section等）
   - 容器CSS类名：容器的CSS类名（可选）
   - 容器ID：容器的ID属性（可选）
   
2. 文本项配置：要提取的文本元素
   - 文本项标签名：文本元素的HTML标签（如p、span等）
   - 文本项属性：文本的属性（text表示文本内容，其他表示属性值）"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def create_advanced_tab(self, parent):
        """创建高级设置选项卡"""
        # JSONL写入器配置
        jsonl_frame = ttk.LabelFrame(parent, text="JSONL写入器配置", padding="10")
        jsonl_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(jsonl_frame, text="启用JSONL写入器", variable=self.use_jsonl_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(jsonl_frame, text="文件前缀:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(jsonl_frame, textvariable=self.jsonl_file_prefix_var, width=30).grid(row=1, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(jsonl_frame, text="文件最大条目数:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(jsonl_frame, textvariable=self.jsonl_max_entries_var, width=30).grid(row=2, column=1, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(jsonl_frame, text="输出路径:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        jsonl_path_frame = ttk.Frame(jsonl_frame)
        jsonl_path_frame.grid(row=3, column=1, sticky=tk.EW, pady=(0, 5))
        jsonl_path_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(jsonl_path_frame, textvariable=self.jsonl_base_path_var).grid(row=0, column=0, sticky=tk.EW)
        ttk.Button(jsonl_path_frame, text="浏览", command=self.browse_jsonl_path).grid(row=0, column=1, padx=(5, 0))
        
        jsonl_frame.columnconfigure(1, weight=1)
        
        # 请求头配置
        headers_frame = ttk.LabelFrame(parent, text="请求头配置", padding="10")
        headers_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(headers_frame, text="User-Agent:").grid(row=0, column=0, sticky=tk.NW, pady=(0, 5))
        user_agent_text = tk.Text(headers_frame, height=4, width=50)
        user_agent_text.grid(row=0, column=1, sticky=tk.EW, pady=(0, 5))
        user_agent_text.insert(tk.END, self.user_agent_var.get())
        user_agent_text.bind("<KeyRelease>", lambda e: self.user_agent_var.set(user_agent_text.get("1.0", tk.END).strip()))
        
        headers_frame.columnconfigure(1, weight=1)
        
        # 配置说明
        info_frame = ttk.LabelFrame(parent, text="配置说明", padding="10")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = """高级设置说明：
1. JSONL写入器配置：
   - 启用JSONL写入器：是否启用JSONL格式输出
   - 文件前缀：输出文件的前缀名称
   - 文件最大条目数：每个JSONL文件的最大条目数，超过会创建新文件
   - 输出路径：JSONL文件的保存路径
   
2. 请求头配置：
   - User-Agent：浏览器标识，用于模拟浏览器访问"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def browse_jsonl_path(self):
        """浏览JSONL输出路径"""
        directory = filedialog.askdirectory(initialdir=self.jsonl_base_path_var.get() or self.output_dir_var.get())
        if directory:
            self.jsonl_base_path_var.set(directory)
    
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
            
            self.load_config_data(config_data)
            messagebox.showinfo("成功", "配置文件导入成功")
        except Exception as e:
            messagebox.showerror("错误", f"导入配置文件失败: {str(e)}")
    
    def export_config(self):
        """导出配置文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            config_data = self.get_config_data()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "配置文件导出成功")
        except Exception as e:
            messagebox.showerror("错误", f"导出配置文件失败: {str(e)}")
    
    def get_config_data(self):
        """获取表单中的配置数据"""
        # URL列表配置
        url_list_config = {
            "target_list_container": {
                "name": self.list_container_name_var.get(),
                "class": self.list_container_class_var.get(),
                "id": self.list_container_id_var.get()
            },
            "target_list_item": {
                "name": self.list_item_name_var.get(),
                "title": {
                    "name": self.list_item_title_name_var.get(),
                    "attr": self.list_item_title_attr_var.get()
                },
                "link": {
                    "name": self.list_item_link_name_var.get(),
                    "attr": self.list_item_link_attr_var.get()
                }
            }
        }
        
        # 文章配置
        article_config = {
            "target_container": {
                "name": self.article_container_name_var.get(),
                "class": self.article_container_class_var.get(),
                "id": self.article_container_id_var.get()
            },
            "target_text_item": {
                "name": self.article_text_item_name_var.get(),
                "attr": self.article_text_item_attr_var.get()
            }
        }
        
        # 请求头
        headers = {
            "User-Agent": self.user_agent_var.get()
        }
        
        # JSONL写入器配置
        jsonl_config = {}
        if self.use_jsonl_var.get():
            jsonl_config = {
                "file_prefix": self.jsonl_file_prefix_var.get() or self.name_var.get(),
                "max_entries": int(self.jsonl_max_entries_var.get()) if self.jsonl_max_entries_var.get() else 1000,
                "base_path": self.jsonl_base_path_var.get() or self.output_dir_var.get()
            }
        
        # 多页爬取配置 - 已移除，不再包含在配置中
        
        # 完整配置
        config_data = {
            "name": self.name_var.get(),
            "base_url": self.base_url_var.get(),
            "url_onepage": self.url_onepage_var.get(),
            "url_multi_page": self.url_multi_page_var.get(),
            "url_multi_page_start": self.url_multi_page_start_var.get(),
            "url_multi_page_stop": self.url_multi_page_stop_var.get(),
            "url_list_config": url_list_config,
            "article_config": article_config,
            "delay_min": int(self.delay_min_var.get()) if self.delay_min_var.get() else 1000,
            "delay_max": int(self.delay_max_var.get()) if self.delay_max_var.get() else 3000,
            "headers": headers,
            "use_jsonl": self.use_jsonl_var.get(),
            "jsonl_config": jsonl_config
        }
        
        return config_data
    
    def save_config(self):
        """保存配置"""
        config_name = self.name_var.get().strip()
        if not config_name:
            messagebox.showerror("错误", "请输入配置名称")
            return
            
        config_data = self.get_config_data()
        
        if self.config_manager.save_config(config_name, config_data):
            messagebox.showinfo("成功", f"配置 '{config_name}' 已保存")
            self.refresh_callback()
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", f"保存配置失败: {config_name}")
    
    def center_window(self):
        """居中显示窗口"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")