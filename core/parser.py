from bs4 import BeautifulSoup
import re

class PageParser:
    @staticmethod
    def extract_text(soup, selector, attribute=None):
        """
        从页面中提取文本或属性值
        
        Args:
            soup (BeautifulSoup): 页面对象
            selector (str): CSS选择器
            attribute (str, optional): 要提取的属性名，如果为None则提取文本
            
        Returns:
            str: 提取的内容
        """
        try:
            element = soup.select_one(selector)
            if element:
                if attribute:
                    return element.get(attribute, '')
                else:
                    return element.get_text(strip=True)
            return ''
        except Exception as e:
            print(f"提取内容失败: {str(e)}")
            return ''
    
    @staticmethod
    def extract_list(soup, selector, attribute=None):
        """
        从页面中提取多个元素的文本或属性值
        
        Args:
            soup (BeautifulSoup): 页面对象
            selector (str): CSS选择器
            attribute (str, optional): 要提取的属性名，如果为None则提取文本
            
        Returns:
            list: 提取的内容列表
        """
        try:
            elements = soup.select(selector)
            result = []
            for element in elements:
                if attribute:
                    result.append(element.get(attribute, ''))
                else:
                    result.append(element.get_text(strip=True))
            return result
        except Exception as e:
            print(f"提取列表失败: {str(e)}")
            return []
    
    @staticmethod
    def extract_by_regex(text, pattern):
        """
        使用正则表达式提取文本
        
        Args:
            text (str): 要搜索的文本
            pattern (str): 正则表达式模式
            
        Returns:
            list: 匹配的结果列表
        """
        try:
            matches = re.findall(pattern, text)
            return matches
        except Exception as e:
            print(f"正则提取失败: {str(e)}")
            return []
    
    @staticmethod
    def clean_text(text):
        """
        清理文本，移除多余的空白字符
        
        Args:
            text (str): 要清理的文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ''
            
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白
        text = text.strip()
        return text