#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Python爬虫UI框架 - 主程序入口
"""

import os
import sys

# 添加项目根目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ui.main_window import MainWindow

def main():
    """主函数"""
    try:
        print("正在启动爬虫UI框架...")
        # 创建并运行主窗口
        app = MainWindow()
        print("主窗口已创建，正在运行...")
        app.run()
    except Exception as e:
        import traceback
        error_msg = f"程序启动失败: {str(e)}\n\n详细信息:\n{traceback.format_exc()}"
        print(error_msg)
        
        import tkinter as tk
        from tkinter import messagebox
        
        # 如果主窗口初始化失败，显示错误信息
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("错误", error_msg)
        root.destroy()

if __name__ == "__main__":
    main()