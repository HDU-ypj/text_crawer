import json
import os
from datetime import datetime
import glob


class JsonlWriter:
    """
    JSONL文件写入器，支持自动分割文件
    
    特性：
    1. 按指定条数自动分割文件
    2. 自动添加时间戳和序号后缀
    3. 提供简洁的写入接口
    4. 自动创建目录
    """
    
    def __init__(self, base_path, max_entries_per_file=5000, file_prefix="data"):
        """
        初始化JSONL写入器
        
        Args:
            base_path (str): 基础存储路径
            max_entries_per_file (int): 每个文件最大条数，默认5000
            file_prefix (str): 文件名前缀，默认为"data"
        """
        self.base_path = base_path
        self.max_entries_per_file = max_entries_per_file
        self.file_prefix = file_prefix
        self.current_file_path = None
        self.current_file = None
        self.current_file_entries = 0
        
        # 确保目录存在
        os.makedirs(base_path, exist_ok=True)
        
        # 初始化当前文件
        self._init_new_file()
    
    def _init_new_file(self):
        """初始化新的JSONL文件"""
        # 关闭当前文件（如果有）
        if self.current_file:
            self.current_file.close()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 查找现有文件数量以确定序号
        pattern = os.path.join(self.base_path, f"{self.file_prefix}_*.jsonl")
        existing_files = glob.glob(pattern)
        file_count = len(existing_files)
        
        # 生成新文件名
        if file_count == 0:
            filename = f"{self.file_prefix}_{timestamp}.jsonl"
        else:
            filename = f"{self.file_prefix}_{timestamp}_{file_count}.jsonl"
        
        self.current_file_path = os.path.join(self.base_path, filename)
        self.current_file = open(self.current_file_path, 'w', encoding='utf-8')
        self.current_file_entries = 0
        
        print(f"创建新的JSONL文件: {self.current_file_path}")
    
    def write(self, title, content, custom_time=None):
        """
        写入一条记录到JSONL文件
        
        Args:
            title (str): 标题
            content (str): 内容
            custom_time (str, optional): 自定义时间，默认为当前时间
        """
        # 如果达到最大条数，创建新文件
        if self.current_file_entries >= self.max_entries_per_file:
            self._init_new_file()
        
        # 使用自定义时间或当前时间
        if custom_time:
            timestamp = custom_time
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建记录
        record = {
            "title": title,
            "time": timestamp,
            "content": content
        }
        
        # 写入JSONL格式（每行一个JSON对象）
        json_line = json.dumps(record, ensure_ascii=False)
        self.current_file.write(json_line + '\n')
        self.current_file.flush()  # 确保立即写入磁盘
        
        self.current_file_entries += 1
        return self.current_file_path
    
    def write_batch(self, records):
        """
        批量写入记录
        
        Args:
            records (list): 记录列表，每个记录应包含title、content和可选的time字段
        """
        for record in records:
            title = record.get('title', '无标题')
            content = record.get('content', '')
            custom_time = record.get('time')
            self.write(title, content, custom_time)
    
    def close(self):
        """关闭当前文件"""
        if self.current_file:
            self.current_file.close()
            self.current_file = None
            print(f"已关闭文件: {self.current_file_path}")
    
    def __del__(self):
        """析构函数，确保文件被正确关闭"""
        self.close()
    
    @staticmethod
    def read_jsonl(file_path):
        """
        读取JSONL文件
        
        Args:
            file_path (str): JSONL文件路径
            
        Returns:
            list: 记录列表
        """
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception as e:
            print(f"读取JSONL文件失败: {e}")
        
        return records
    
    @staticmethod
    def read_all_jsonl(directory_path, file_prefix="data"):
        """
        读取目录下所有JSONL文件
        
        Args:
            directory_path (str): 目录路径
            file_prefix (str): 文件名前缀
            
        Returns:
            list: 所有记录列表
        """
        all_records = []
        pattern = os.path.join(directory_path, f"{file_prefix}_*.jsonl")
        file_paths = glob.glob(pattern)
        
        # 按文件名排序
        file_paths.sort()
        
        for file_path in file_paths:
            records = JsonlWriter.read_jsonl(file_path)
            all_records.extend(records)
            print(f"从 {file_path} 读取了 {len(records)} 条记录")
        
        return all_records


# 简化的工厂函数，提供更简洁的调用方式
def create_jsonl_writer(base_path, prefix="data", max_entries=5000):
    """
    创建JSONL写入器的简化函数
    
    Args:
        base_path (str): 基础存储路径
        max_entries (int): 每个文件最大条数，默认5000
        prefix (str): 文件名前缀，默认为"data"
        
    Returns:
        JsonlWriter: JSONL写入器实例
    """
    return JsonlWriter(base_path, max_entries, prefix)