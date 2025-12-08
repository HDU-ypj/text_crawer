import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
import sys
import shutil
from datetime import datetime

# 添加项目根目录到路径
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(application_path)

from config.manager import ConfigManager
from ui.config_window import ConfigWindow

class ConfigManagerWindow:
    def __init__(self, parent):
        self.parent = parent
        self.config_manager = ConfigManager()
        self.current_config_name = None
        self.config_files = []
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("配置管理器")
        self.window.geometry("900x600")
        self.window.resizable(True, True)
        
        # 设置窗口样式
        self.window.overrideredirect(False)  # 确保窗口有系统标题栏
        self.window.wm_attributes('-toolwindow', False)  # 确保有最大化按钮
        self.window.wm_attributes('-alpha', 1.0)  # 确保窗口完全不透明
        
        # 设置窗口协议
        self.window.wm_protocol("WM_DELETE_WINDOW", self.on_close)  # 处理窗口关闭事件
        
        # 创建UI组件
        self.create_widgets()
        
        # 加载配置文件列表
        self.load_config_files()
        
        # 居中显示窗口
        self.center_window()
    
    def create_widgets(self):
        """创建UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 左侧：配置文件列表
        ttk.Label(left_frame, text="配置文件列表", font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 5))
        
        # 配置文件列表框
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 列表框
        self.config_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.config_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.config_listbox.yview)
        
        # 绑定选择事件
        self.config_listbox.bind('<<ListboxSelect>>', self.on_config_select)
        
        # 配置文件操作按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="新建", command=self.new_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="编辑", command=self.edit_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导入", command=self.import_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出", command=self.export_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除", command=self.delete_config).pack(side=tk.LEFT)
        
        # 右侧：配置编辑区
        ttk.Label(right_frame, text="配置内容", font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 5))
        
        # 配置名称输入
        name_frame = ttk.Frame(right_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(name_frame, text="配置名称:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 配置内容编辑区
        self.content_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 底部按钮
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(bottom_frame, text="保存", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text="重置", command=self.reset_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text="格式化", command=self.format_json).pack(side=tk.LEFT)
    
    def load_config_files(self):
        """加载配置文件列表"""
        self.config_files = []
        self.config_listbox.delete(0, tk.END)
        
        config_dir = os.path.join(application_path, 'config')
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith('.json'):
                    self.config_files.append(file)
                    self.config_listbox.insert(tk.END, file[:-5])  # 去掉.json后缀
    
    def on_config_select(self, event):
        """配置文件选择事件处理"""
        selection = self.config_listbox.curselection()
        if selection:
            index = selection[0]
            config_name = self.config_listbox.get(index)
            self.load_config(config_name)
    
    def load_config(self, config_name):
        """加载配置文件内容"""
        try:
            config_path = os.path.join(application_path, 'config', f"{config_name}.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.current_config_name = config_name
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, config_name)
            
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, content)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
    
    def new_config(self):
        """新建配置文件"""
        config_window = ConfigWindow(self.window, ConfigManager(), self.load_config_files)
        self.window.wait_window(config_window.dialog)
    
    def edit_config(self):
        """编辑选中的配置文件"""
        selection = self.config_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个配置文件")
            return
        
        index = selection[0]
        config_name = self.config_listbox.get(index)
        
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config_name)
        
        if config_data:
            config_window = ConfigWindow(self.window, config_manager, self.load_config_files, config_name, config_data)
            self.window.wait_window(config_window.dialog)
        else:
            messagebox.showerror("错误", f"无法加载配置: {config_name}")
    
    def import_config(self):
        """导入配置文件"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 验证JSON格式
                json.loads(content)
                
                # 获取文件名作为配置名
                filename = os.path.basename(file_path)
                config_name = os.path.splitext(filename)[0]
                
                # 检查是否已存在
                if f"{config_name}.json" in self.config_files:
                    result = messagebox.askyesno(
                        "确认", 
                        f"配置文件 '{config_name}' 已存在，是否覆盖？"
                    )
                    if not result:
                        return
                
                # 保存配置
                config_path = os.path.join(application_path, 'config', f"{config_name}.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 更新列表
                if f"{config_name}.json" not in self.config_files:
                    self.config_files.append(f"{config_name}.json")
                    self.config_listbox.insert(tk.END, config_name)
                
                # 加载配置
                self.load_config(config_name)
                
                messagebox.showinfo("成功", f"配置文件 '{config_name}' 导入成功")
            except Exception as e:
                messagebox.showerror("错误", f"导入配置文件失败: {str(e)}")
    
    def export_config(self):
        """导出配置文件"""
        if not self.current_config_name:
            messagebox.showwarning("警告", "请先选择一个配置文件")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialfile=f"{self.current_config_name}.json"
        )
        
        if file_path:
            try:
                content = self.content_text.get(1.0, tk.END).strip()
                
                # 验证JSON格式
                json.loads(content)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo("成功", f"配置文件导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出配置文件失败: {str(e)}")
    
    def delete_config(self):
        """删除配置文件"""
        selection = self.config_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个配置文件")
            return
        
        index = selection[0]
        config_name = self.config_listbox.get(index)
        
        result = messagebox.askyesno("确认", f"确定要删除配置文件 '{config_name}' 吗？")
        if result:
            try:
                config_path = os.path.join(application_path, 'config', f"{config_name}.json")
                if os.path.exists(config_path):
                    os.remove(config_path)
                
                # 从列表中移除
                self.config_files.remove(f"{config_name}.json")
                self.config_listbox.delete(index)
                
                # 清空编辑区
                if self.current_config_name == config_name:
                    self.current_config_name = None
                    self.name_entry.delete(0, tk.END)
                    self.content_text.delete(1.0, tk.END)
                
                messagebox.showinfo("成功", f"配置文件 '{config_name}' 已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除配置文件失败: {str(e)}")
    
    def save_config(self):
        """保存配置文件"""
        if not self.current_config_name:
            messagebox.showwarning("警告", "请先选择或创建一个配置文件")
            return
        
        try:
            content = self.content_text.get(1.0, tk.END).strip()
            
            # 验证JSON格式
            json.loads(content)
            
            # 获取配置名称
            new_name = self.name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("警告", "配置名称不能为空")
                return
            
            # 如果名称改变了，需要重命名文件
            if new_name != self.current_config_name:
                if f"{new_name}.json" in self.config_files:
                    messagebox.showwarning("警告", f"配置文件 '{new_name}' 已存在")
                    return
                
                old_path = os.path.join(application_path, 'config', f"{self.current_config_name}.json")
                new_path = os.path.join(application_path, 'config', f"{new_name}.json")
                
                # 重命名文件
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                # 更新列表
                index = self.config_files.index(f"{self.current_config_name}.json")
                self.config_files[index] = f"{new_name}.json"
                self.config_listbox.delete(index)
                self.config_listbox.insert(index, new_name)
                self.config_listbox.selection_set(index)
                
                self.current_config_name = new_name
            else:
                # 直接保存
                config_path = os.path.join(application_path, 'config', f"{self.current_config_name}.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            messagebox.showinfo("成功", f"配置文件 '{self.current_config_name}' 保存成功")
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"JSON格式错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")
    
    def reset_config(self):
        """重置配置内容"""
        if self.current_config_name:
            self.load_config(self.current_config_name)
        else:
            self.name_entry.delete(0, tk.END)
            self.content_text.delete(1.0, tk.END)
    
    def format_json(self):
        """格式化JSON内容"""
        try:
            content = self.content_text.get(1.0, tk.END).strip()
            if not content:
                return
            
            # 解析并重新格式化JSON
            data = json.loads(content)
            formatted_content = json.dumps(data, indent=2, ensure_ascii=False)
            
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, formatted_content)
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"JSON格式错误: {str(e)}")
    
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_close(self):
        """处理窗口关闭事件"""
        self.window.destroy()