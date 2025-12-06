import json
import os
import glob

class ConfigManager:
    def __init__(self, config_dir='config'):
        """
        初始化配置管理器
        
        Args:
            config_dir (str): 配置文件目录
        """
        self.config_dir = config_dir
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
    
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
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
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
        
        return self.save_config("default", default_config)