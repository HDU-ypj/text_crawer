import requests
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from .jsonl_writer import JsonlWriter
import random

class WebCrawler:
    def __init__(self, config, logger=None):
        """
        初始化爬虫
        
        Args:
            config (dict): 爬虫配置
            logger: 日志记录器
        """
        self.config = config
        self.base_url = config.get('base_url', '')
        self.url_list_config = config.get('url_list_config', {})
        self.article_config = config.get('article_config', {})
        self.delay_min = config.get('delay_min', 1000) / 1000  # 转换为秒
        self.delay_max = config.get('delay_max', 3000) / 1000  # 转换为秒
        self.headers = config.get('headers', {})
        self.enable_jsonl = config.get('use_jsonl', False)
        if self.enable_jsonl:
            self.output_dir = config.get('jsonl_config', {}).get('base_path', 'output')
        
        # 设置日志
        self.logger = logger or logging.getLogger(__name__)
        
        # 创建输出目录

        if self.enable_jsonl:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
        # 创建会话
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 初始化JSONL写入器
        self.jsonl_writer = None
        if self.enable_jsonl:
            jsonl_config = config.get('jsonl_config', {})
            jsonl_file_prefix = jsonl_config.get('file_prefix', config.get('name', 'crawl_result'))
            max_entries = jsonl_config.get('max_entries', 5000)
            jsonl_base_path = jsonl_config.get('base_path', 'output')
            
            self.jsonl_writer = JsonlWriter(
                base_path=jsonl_base_path,
                max_entries_per_file=max_entries,
                file_prefix=jsonl_file_prefix
            )
            self.log(f"已初始化JSONL写入器，输出目录: {jsonl_base_path}")
        
    def log(self, message):
        """记录日志"""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def random_delay(self):
        """随机延迟"""
        delay = random.uniform(self.delay_min, self.delay_max)
        self.log(f"随机延迟 {delay:.2f} 秒")
        time.sleep(delay)
    
    def get_page(self, url):
        """
        获取页面内容
        
        Args:
            url (str): 页面URL
            
        Returns:
            BeautifulSoup: 解析后的页面对象，失败返回None
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 自动处理编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
                
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            self.log(f"获取页面失败: {url}, 错误: {str(e)}")
            return None
    
    def parse_url_lists(self, soup):
        """
        解析页面中的链接列表
        
        Args:
            soup (BeautifulSoup): 页面对象
            
        Returns:
            list: 包含标题和链接的字典列表 [{'title': '标题', 'url': '链接'}, ...]
        """
        url_data = []
        try:
            # 从新的配置格式中获取参数
            list_container_config = self.url_list_config.get('target_list_container', {})
            list_item_config = self.url_list_config.get('target_list_item', {})
            
            container_tag = list_container_config.get('name', 'div')
            container_class = list_container_config.get('class', '')
            container_id = list_container_config.get('id', '')
            
            item_tag = list_item_config.get('name', 'li')
            item_class = list_item_config.get('class', '')
            item_id = list_item_config.get('id', '')
            
            title_config = list_item_config.get('title', {})
            link_config = list_item_config.get('link', {})
            
            title_tag = title_config.get('name', 'a')
            title_attr = title_config.get('attr', 'text')

            link_tag = link_config.get('name', 'a')
            link_attr = link_config.get('attr', 'href')
            
            # 查找容器元素
            if container_id:
                container = soup.find(container_tag, id=container_id)
            elif container_class:
                container = soup.find(container_tag, class_=container_class)
            else:
                container = soup
            
            # 查找列表项
            if item_id:
                target_elements = container.find_all(item_tag, id=item_id)
            elif item_class:
                target_elements = container.find_all(item_tag, class_=item_class)
            else:
                target_elements = container.find_all(item_tag)
            
            self.log(f"找到 {len(target_elements)} 个 {item_tag} 元素")
            
            # 提取链接和标题
            for element in target_elements:
                link_element = element.find(link_tag)
                title_element = element.find(title_tag)
                
                full_url = ''
                title = ''
                if link_element and link_element.has_attr(link_attr):
                    href = link_element[link_attr]

                    if not href.startswith('http'):
                        full_url = urljoin(self.base_url, href)
                    else:
                        full_url = href
                
                if title_element and title_element.has_attr(title_attr):
                    if title_attr == 'text':
                        title = title_element.get_text(strip=True)
                    else:
                        title = title_element.get(title_attr, '')
                    
                    if not title:
                        title = full_url
                    
                url_data.append({
                    'title': title,
                    'url': full_url
                })
                    
            self.log(f"成功提取 {len(url_data)} 个链接和标题")
            return url_data
        except Exception as e:
            self.log(f"解析链接列表失败: {str(e)}")
            return []
    
    def parse_article(self, soup, url):
        """
        解析文章内容
        
        Args:
            soup (BeautifulSoup): 页面对象
            url (str): 文章URL
            
        Returns:
            dict: 文章数据
        """
        try:
            # 从新的配置格式中获取参数
            container_config = self.article_config.get('target_container', {})
            text_item_config = self.article_config.get('target_text_item', {})
            
            container_tag = container_config.get('name', 'div')
            container_class = container_config.get('class', '')
            container_id = container_config.get('id', '')
            
            text_tag = text_item_config.get('name', 'p')
            text_attr = text_item_config.get('attr', 'text')
            
            # 查找容器元素
            if container_id:
                container = soup.find(container_tag, id=container_id)
            elif container_class:
                container = soup.find(container_tag, class_=container_class)
            else:
                container = soup
            
            # 查找文本元素
            content_elements = container.find_all(text_tag)
            
            # 提取文本内容
            if text_attr == 'text':
                content = '\n'.join([element.get_text(strip=True) for element in content_elements])
            else:
                # 如果指定了其他属性，则提取该属性值
                content = '\n'.join([element.get(text_attr, '') for element in content_elements if element.has_attr(text_attr)])

            article_data = {
                'url': url,
                'content': content
            }
            return article_data
        except Exception as e:
            self.log(f"解析文章失败: {url}, 错误: {str(e)}")

            error_data = {
                'url': url,
                'content': "",
                'error': str(e)
            }
            return error_data
    
    def save_results(self, article_data):
        """
        保存爬取结果到JSONL文件
        
        Args:
            article_data (dict): 包含标题、URL和内容的文章数据
        """
        if not article_data:
            self.log("没有数据需要保存")
            return
            
        try:
            # 确保有标题
            title = article_data.get('title', '无标题')
            content = article_data.get('content', '')
            url = article_data.get('url', '')
            
            # 如果内容为空，不保存
            if not content.strip():
                self.log(f"文章内容为空，跳过保存: {title}")
                return
                
            # 如果启用了JSONL写入器，使用它保存数据
            if self.enable_jsonl:
                # 写入到JSONL文件
                file_path = self.jsonl_writer.write(title, content)
                self.log(f"已保存文章到JSONL文件: {title}")
                
        except Exception as e:
            self.log(f"保存结果失败: {str(e)}")
    
    def close(self):
        """关闭爬虫资源，包括JSONL写入器"""
        if self.jsonl_writer:
            self.jsonl_writer.close()
            self.log("JSONL写入器已关闭")
    
    def crawl(self):
        """执行爬取任务"""
        self.log(f"开始爬取任务: {self.config.get('name', '未命名任务')}")
        self.log(f"第一页URL: {self.config.get('url_onepage', '')}")
        self.log(f"多页URL模板: {self.config.get('url_multi_page', '')}")
        
        # 只支持多页爬取模式
        return self.crawl_multi_pages()
    
    def crawl_multi_pages(self):
        """爬取多页内容"""
        try:
            # 获取配置
            config = {
                'url_onepage': self.config.get('url_onepage', ''),
                'url_multi_page': self.config.get('url_multi_page', ''),
                'url_multi_page_start': self.config.get('url_multi_page_start', 1),
                'url_multi_page_stop': self.config.get('url_multi_page_stop', 9999999),
                'process_articles': self.config.get('process_articles', True)
            }
            
            # 调试信息：打印原始配置中的值
            self.log(f"调试信息：原始配置中的url_multi_page_stop值: {self.config.get('url_multi_page_stop', '未设置')}")
            self.log(f"调试信息：config字典中的url_multi_page_stop值: {config['url_multi_page_stop']}")
            
            # 验证必要配置
            if not config['url_onepage'] or not config['url_multi_page']:
                self.log("缺少必要的URL配置，爬取任务终止")
                return False
                
            self.log(f"启用多页爬取模式，第一页: {config['url_onepage']}")
            self.log(f"多页URL模板: {config['url_multi_page']}")
            self.log(f"多页URL起始页码: {config['url_multi_page_start']}")
            self.log(f"多页URL结束页码: {config['url_multi_page_stop']}")
            
            # 收集所有URL数据（包含标题和URL）
            all_url_data = self._collect_all_urls(config)
            if not all_url_data:
                self.log("所有页面都没有找到任何链接，爬取任务终止")
                return False
            
            # 爬取文章内容
            self._crawl_articles(all_url_data, config)
            
            self.log(f"多页爬取任务完成，共处理 {len(all_url_data)} 个链接")
            return True
        finally:
            # 确保关闭JSONL写入器
            self.close()
    
    def _collect_all_urls(self, config):
        """收集所有页面的URL"""
        all_url_data = []
        
        page_start = config['url_multi_page_start']
        page_stop = config['url_multi_page_stop']
        
        for page_index in range(page_start, page_stop + 1):
            # 构建页面URL
            if page_index == page_start:
                page_url = config['url_onepage']
            else:
                page_url = config['url_multi_page'].format(page_index)
            
            self.log(f"正在处理第 {page_index} 页: {page_url}")
            
            # 获取页面内容
            page_content = self.get_page(page_url)
            if not page_content:
                self.log(f"获取页面内容失败: {page_url}")
                break
            
            # 解析链接列表
            url_data = self.parse_url_lists(page_content)
            if url_data:
                all_url_data.extend(url_data)
                self.log(f"第 {page_index} 页找到 {len(url_data)} 个链接")
            else:
                self.log(f"第 {page_index} 页没有找到任何链接")
            
            self.random_delay()
        
        # 去重
        unique_urls = []
        seen_urls = set()
        for item in all_url_data:
            url = item['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(item)
        
        self.log(f"总共收集到 {len(all_url_data)} 个链接，去重后剩余 {len(unique_urls)} 个链接")
        return unique_urls
    
    def _crawl_page(self, url, page_name):
        """爬取单个页面并返回URL列表"""
        self.log(f"正在获取{page_name}: {url}")
        
        page_soup = self.get_page(url)
        if not page_soup:
            self.log(f"无法获取{page_name}，可能已到最后一页")
            return []
        
        page_urls = self.parse_url_lists(page_soup)
        if not page_urls:
            self.log(f"{page_name}没有找到任何链接")
            return []
            
        self.log(f"{page_name}找到 {len(page_urls)} 个链接")
        return page_urls
    
    def _crawl_articles(self, url_data, config):
        """爬取文章内容"""
        if not url_data:
            self.log("没有找到任何链接，跳过文章爬取")
            return
            
        self.log(f"开始爬取文章内容，共 {len(url_data)} 个链接")
        
        for item in url_data:
            url = item['url']
            title = item['title']
            
            self.log(f"正在处理链接: {url}")
            
            try:
                # 获取页面内容
                page_content = self.get_page(url)
                if not page_content:
                    self.log(f"获取页面内容失败: {url}")
                    continue
                
                # 解析文章内容
                article_data = self.parse_article(page_content, url)

                if not article_data.get('content'):
                    continue
                
                # 使用从链接列表中提取的标题
                article_data['title'] = title
                
                # 保存结果
                self.save_results(article_data)
                
                self.random_delay()
                    
            except Exception as e:
                self.log(f"处理链接 {url} 时出错: {str(e)}")
                continue