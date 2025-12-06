import json
import os
import glob
import sys

def resource_path(relative_path):
    """获取资源的绝对路径，支持开发环境和PyInstaller打包后的环境"""
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        # 正常的开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ConfigManager:
    def __init__(self, config_dir='config'):
        """
        初始化配置管理器
        
        Args:
            config_dir (str): 配置文件目录
        """
        # 在打包环境中，将配置目录设置为可执行文件所在目录下的config目录
        if getattr(sys, 'frozen', False):
            # 获取可执行文件所在目录
            exe_dir = os.path.dirname(sys.executable)
            self.config_dir = os.path.join(exe_dir, config_dir)
        else:
            # 开发环境中，使用相对路径
            self.config_dir = config_dir
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
    
    def get_config_list(self):
        """
        获取所有配置文件列表
        
        Returns:
            list: 配置文件名列表（不含扩展名）
        """
        config_files = glob.glob(os.path.join(self.config_dir, '*.json'))
        return [os.path.basename(f).replace('.json', '') for f in config_files]
    
    def load_config(self, config_name):
        """
        加载配置文件
        
        Args:
            config_name (str): 配置文件名（不含扩展名）
            
        Returns:
            dict: 配置数据，失败返回None
        """
        # 尝试从用户目录加载配置
        user_config_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        # 如果是打包后的环境，先尝试从打包的资源中加载默认配置
        if getattr(sys, 'frozen', False) and config_name == 'default':
            bundled_config_path = resource_path(os.path.join('config', f"{config_name}.json"))
            try:
                with open(bundled_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass  # 如果从打包资源中加载失败，继续尝试从用户目录加载
        
        # 尝试从用户目录加载配置
        if os.path.exists(user_config_path):
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {str(e)}")
                return None
        
        # 如果是default配置且不存在，创建默认配置
        if config_name == 'default':
            return self.create_default_config()
        
        return None
    
    def save_config(self, config_name, config_data):
        """
        保存配置文件
        
        Args:
            config_name (str): 配置文件名（不含扩展名）
            config_data (dict): 配置数据
            
        Returns:
            bool: 是否保存成功
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False
    
    def delete_config(self, config_name):
        """
        删除配置文件
        
        Args:
            config_name (str): 配置文件名（不含扩展名）
            
        Returns:
            bool: 是否删除成功
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        try:
            if os.path.exists(config_path):
                os.remove(config_path)
                return True
            return False
        except Exception as e:
            print(f"删除配置失败: {str(e)}")
            return False
    
    def create_default_config(self):
        """
        创建默认配置文件
        
        Returns:
            bool: 是否创建成功
        """
        default_config = {
            "name": "默认配置",
            "base_url": "https://example.com",
            "url_list_config": {
                "target_class": "list-container",
                "target_tag": "li",
                "link_selector": "a",
                "link_attr": "href"
            },
            "article_config": {
                "target_class": "article-content",
                "target_tag": "p"
            },
            "output_dir": "output",
            "delay": 1,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }
        
        # 保存到用户目录
        if self.save_config("default", default_config):
            return default_config
        return default_config  # 即使保存失败也返回配置，以便程序可以继续运行