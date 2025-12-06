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
        self.jsonl_config = config.get('jsonl_config', {})
        self.jsonl_file_prefix = self.jsonl_config.get('file_prefix', config.get('name', 'crawl_result'))
        self.jsonl_max_entries = self.jsonl_config.get('max_entries', 5000)
        self.jsonl_base_path = self.jsonl_config.get('base_path', 'output')
        
        if self.enable_jsonl:
            self.log(f"已配置JSONL写入器，输出目录: {self.jsonl_base_path}")
        
        # 添加停止标志位
        self.should_stop = False
        
    def _init_jsonl_writer(self):
        """初始化JSONL写入器"""
        if self.enable_jsonl and not self.jsonl_writer:
            self.jsonl_writer = JsonlWriter(
                base_path=self.jsonl_base_path,
                max_entries_per_file=self.jsonl_max_entries,
                file_prefix=self.jsonl_file_prefix
            )
            self.log(f"已初始化JSONL写入器，输出目录: {self.jsonl_base_path}")
    
    def log(self, message):
        """记录日志"""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
    def stop(self):
        """设置停止标志位，用于停止爬取任务"""
        self.should_stop = True
        self.log("收到停止请求，正在停止爬取任务...")
    
    def is_stopped(self):
        """检查是否应该停止爬取"""
        return self.should_stop

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
                
                if title_element:
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
    
    def extract_time_from_page(self, soup):
        """
        从页面中提取时间信息，不依赖外部配置
        
        Args:
            soup (BeautifulSoup): 页面对象
            
        Returns:
            str: 提取到的时间字符串，如果未找到则返回当前时间
        """
        try:
            # 导入正则表达式模块
            import re
            
            # 常见的时间格式正则表达式
            time_patterns = [
                # YYYY-MM-DD HH:MM:SS
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
                # YYYY-MM-DD HH:MM
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
                # YYYY-MM-DD
                r'(\d{4}-\d{2}-\d{2})',
                # YYYY/MM/DD HH:MM:SS
                r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',
                # YYYY/MM/DD HH:MM
                r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})',
                # YYYY/MM/DD
                r'(\d{4}/\d{2}/\d{2})',
                # YYYY年MM月DD日 HH:MM:SS
                r'(\d{4}年\d{1,2}月\d{1,2}日\s+\d{2}:\d{2}:\d{2})',
                # YYYY年MM月DD日 HH:MM
                r'(\d{4}年\d{1,2}月\d{1,2}日\s+\d{2}:\d{2})',
                # YYYY年MM月DD日
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                # MM-DD HH:MM
                r'(\d{2}-\d{2}\s+\d{2}:\d{2})',
                # MM/DD HH:MM
                r'(\d{2}/\d{2}\s+\d{2}:\d{2})',
                # MM月DD日
                r'(\d{1,2}月\d{1,2}日)',
                # MM月DD日 HH:MM
                r'(\d{1,2}月\d{1,2}日\s+\d{2}:\d{2})',
                # ISO 8601 格式
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
                # 带毫秒的格式
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})'
            ]
            
            # 常见的时间元素选择器
            time_selectors = [
                'time', '.time', '.date', '.publish-time', 
                '.publish_date', '.article-time', '.post-date',
                '[datetime]', '.entry-date', '.published',
                '.news-time', '.article-date', '.post-time',
                '.release-time', '.update-time', '.create-time',
                '.meta-time', '.timestamp', 'span[class*="time"]',
                'span[class*="date"]', 'div[class*="time"]',
                'div[class*="date"]', 'p[class*="time"]',
                'p[class*="date"]'
            ]
            
            # 首先尝试从常见的时间元素中提取
            for selector in time_selectors:
                elements = soup.select(selector)
                for element in elements:
                    # 优先从datetime属性获取
                    if element.has_attr('datetime'):
                        time_text = element['datetime']
                        # 尝试解析时间
                        parsed_time = self._parse_time_text(time_text)
                        if parsed_time:
                            self.log(f"从datetime属性提取时间: {parsed_time}")
                            return parsed_time
                    
                    # 从元素文本中提取
                    time_text = element.get_text(strip=True)
                    if time_text:
                        # 使用正则表达式从文本中提取时间
                        for pattern in time_patterns:
                            match = re.search(pattern, time_text)
                            if match:
                                time_str = match.group(1)
                                parsed_time = self._parse_time_text(time_str)
                                if parsed_time:
                                    self.log(f"从元素文本提取时间: {parsed_time}")
                                    return parsed_time
            
            # 如果没有从特定元素中找到时间，尝试从整个页面文本中搜索
            page_text = soup.get_text()
            for pattern in time_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # 取第一个匹配的时间
                    time_str = matches[0]
                    parsed_time = self._parse_time_text(time_str)
                    if parsed_time:
                        self.log(f"从页面文本提取时间: {parsed_time}")
                        return parsed_time
            
            # 如果没有找到时间，返回当前时间
            self.log("未找到时间元素，使用当前时间")
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            self.log(f"提取时间信息失败: {str(e)}")
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _parse_time_text(self, time_text):
        """
        解析时间文本并标准化为统一格式
        
        Args:
            time_text (str): 时间文本
            
        Returns:
            str: 标准化后的时间字符串，解析失败返回None
        """
        try:
            # 导入正则表达式模块
            import re
            
            # 预处理中文格式的月份和日期
            # 将"2023年5月15日"转换为"2023年05月15日"
            time_text = re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(1)}年{m.group(2).zfill(2)}月{m.group(3).zfill(2)}日", time_text)
            
            # 常见的时间格式
            time_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d',
                '%Y年%m月%d日 %H:%M:%S',
                '%Y年%m月%d日 %H:%M',
                '%Y年%m月%d日',
                '%m-%d %H:%M',
                '%m/%d %H:%M',
                '%m月%d日',
                '%m月%d日 %H:%M',
                '%Y-%m-%dT%H:%M:%S',  # ISO 8601
                '%Y-%m-%d %H:%M:%S.%f'  # 带毫秒
            ]
            
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_text, fmt)
                    # 如果解析成功但没有时间部分，添加当前时间
                    if fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日', '%m月%d日']:
                        now = datetime.now()
                        parsed_time = parsed_time.replace(hour=now.hour, minute=now.minute, second=now.second)
                    return parsed_time.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            
            # 如果标准格式无法解析，尝试使用正则表达式提取
            # 尝试提取年月日
            year_month_day_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', time_text)
            if year_month_day_match:
                year = int(year_month_day_match.group(1))
                month = int(year_month_day_match.group(2))
                day = int(year_month_day_match.group(3))
                
                # 尝试提取时分秒
                hour_min_sec_match = re.search(r'(\d{1,2})[时:](\d{1,2})(?:[分:](\d{1,2}))?', time_text)
                if hour_min_sec_match:
                    hour = int(hour_min_sec_match.group(1))
                    minute = int(hour_min_sec_match.group(2))
                    second = int(hour_min_sec_match.group(3)) if hour_min_sec_match.group(3) else 0
                else:
                    now = datetime.now()
                    hour, minute, second = now.hour, now.minute, now.second
                
                try:
                    parsed_time = datetime(year, month, day, hour, minute, second)
                    return parsed_time.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            
            return None
        except Exception as e:
            self.log(f"解析时间文本失败: {str(e)}")
            return None

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

            # 提取文章时间
            article_time = self.extract_time_from_page(soup)

            article_data = {
                'url': url,
                'content': content,
                'time': article_time
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
            article_data (dict): 包含标题、URL、内容和时间的文章数据
        """
        if not article_data:
            self.log("没有数据需要保存")
            return
            
        try:
            # 确保有标题
            title = article_data.get('title', '无标题')
            content = article_data.get('content', '')
            url = article_data.get('url', '')
            article_time = article_data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 如果内容为空，不保存
            if not content.strip():
                self.log(f"文章内容为空，跳过保存: {title}")
                return
                
            # 如果启用了JSONL写入器，使用它保存数据
            if self.enable_jsonl:
                # 确保JSONL写入器已初始化
                if not self.jsonl_writer:
                    self._init_jsonl_writer()
                
                # 写入到JSONL文件，使用从页面中提取的时间
                file_path = self.jsonl_writer.write(title, content, article_time)
                self.log(f"已保存文章到JSONL文件: {title}, 时间: {article_time}")
                
        except Exception as e:
            self.log(f"保存结果失败: {str(e)}")
    
    def close(self):
        """关闭爬虫资源，包括JSONL写入器"""
        if self.jsonl_writer:
            self.jsonl_writer.close()
            self.log("JSONL写入器已关闭")
    
    def test_config(self, max_pages=2, max_articles=3):
        """测试配置是否正确，只爬取少量页面和文章
        
        Args:
            max_pages (int): 最大测试页数，默认为2页
            max_articles (int): 最大测试文章数，默认为3篇
            
        Returns:
            dict: 测试结果，包含链接提取和文章解析的信息
        """
        self.log(f"开始测试配置，最多测试 {max_pages} 页和 {max_articles} 篇文章")
        
        # 保存原始JSONL启用状态，在测试模式下禁用JSONL文件创建
        original_enable_jsonl = self.enable_jsonl
        self.enable_jsonl = False
        self.log("测试模式：已禁用JSONL文件创建")
        
        test_results = {
            'success': False,
            'pages_tested': 0,
            'links_found': 0,
            'articles_tested': 0,
            'articles_parsed': 0,
            'errors': [],
            'sample_links': [],
            'sample_articles': []
        }
        
        try:
            # 获取配置
            config = {
                'url_onepage': self.config.get('url_onepage', ''),
                'url_multi_page': self.config.get('url_multi_page', ''),
                'url_multi_page_start': self.config.get('url_multi_page_start', 1),
                'url_multi_page_stop': self.config.get('url_multi_page_stop', 9999999),
                'process_articles': self.config.get('process_articles', True)
            }
            
            # 验证必要配置
            if not config['url_onepage'] or not config['url_multi_page']:
                error_msg = "缺少必要的URL配置"
                self.log(error_msg)
                test_results['errors'].append(error_msg)
                return test_results
            
            # 限制测试页数
            original_stop = config['url_multi_page_stop']
            config['url_multi_page_stop'] = min(
                config['url_multi_page_start'] + max_pages - 1,
                original_stop
            )
            
            self.log(f"测试模式：限制页数从 {config['url_multi_page_start']} 到 {config['url_multi_page_stop']}")
            
            # 测试链接收集
            all_url_data = []
            
            for page_index in range(config['url_multi_page_start'], config['url_multi_page_stop'] + 1):
                # 检查是否应该停止
                if self.is_stopped():
                    self.log("测试过程中收到停止请求")
                    break
                    
                # 构建页面URL
                if page_index == config['url_multi_page_start']:
                    page_url = config['url_onepage']
                else:
                    page_url = config['url_multi_page'].format(page_index)
                
                self.log(f"正在测试第 {page_index} 页: {page_url}")
                
                # 获取页面内容
                page_content = self.get_page(page_url)
                if not page_content:
                    error_msg = f"获取页面内容失败: {page_url}"
                    self.log(error_msg)
                    test_results['errors'].append(error_msg)
                    continue
                
                # 解析链接列表
                url_data = self.parse_url_lists(page_content)
                if url_data:
                    all_url_data.extend(url_data)
                    self.log(f"第 {page_index} 页找到 {len(url_data)} 个链接")
                    
                    # 保存样本链接
                    for i, item in enumerate(url_data[:3]):  # 每页最多保存3个样本
                        test_results['sample_links'].append({
                            'page': page_index,
                            'title': item['title'],
                            'url': item['url']
                        })
                else:
                    error_msg = f"第 {page_index} 页没有找到任何链接"
                    self.log(error_msg)
                    test_results['errors'].append(error_msg)
                
                test_results['pages_tested'] += 1
            
            # 去重
            unique_urls = []
            seen_urls = set()
            for item in all_url_data:
                url = item['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_urls.append(item)
            
            test_results['links_found'] = len(unique_urls)
            
            if not unique_urls:
                error_msg = "所有测试页面都没有找到任何链接"
                self.log(error_msg)
                test_results['errors'].append(error_msg)
                return test_results
            
            # 测试文章解析
            self.log(f"开始测试文章解析，最多测试 {min(max_articles, len(unique_urls))} 篇文章")
            
            for i, item in enumerate(unique_urls[:max_articles]):
                # 检查是否应该停止
                if self.is_stopped():
                    self.log("测试过程中收到停止请求")
                    break
                    
                url = item['url']
                title = item['title']
                
                self.log(f"正在测试文章: {url}")
                
                try:
                    # 获取页面内容
                    page_content = self.get_page(url)
                    if not page_content:
                        error_msg = f"获取文章页面内容失败: {url}"
                        self.log(error_msg)
                        test_results['errors'].append(error_msg)
                        continue
                    
                    # 解析文章内容
                    article_data = self.parse_article(page_content, url)
                    
                    if article_data and article_data.get('content'):
                        test_results['articles_parsed'] += 1
                        article_time = article_data.get('time', '未知')
                        
                        # 打印解析出的时间信息
                        self.log(f"解析出文章时间: {article_time}")
                        
                        # 保存样本文章
                        test_results['sample_articles'].append({
                            'title': title,
                            'url': url,
                            'content_length': len(article_data['content']),
                            'content_preview': article_data['content'][:100] + "..." if len(article_data['content']) > 100 else article_data['content'],
                            'time': article_time
                        })
                        
                        self.log(f"成功解析文章: {title}, 时间: {article_time}")
                    else:
                        error_msg = f"无法解析文章内容: {url}"
                        self.log(error_msg)
                        test_results['errors'].append(error_msg)
                    
                    test_results['articles_tested'] += 1
                    
                    # 测试模式下减少延迟
                    if i < max_articles - 1:  # 最后一篇文章不需要延迟
                        # 临时设置较短的延迟时间
                        original_delay_min = self.delay_min
                        original_delay_max = self.delay_max
                        self.delay_min = 0.5
                        self.delay_max = 1.0
                        self.random_delay()
                        # 恢复原始延迟时间
                        self.delay_min = original_delay_min
                        self.delay_max = original_delay_max
                        
                except Exception as e:
                    error_msg = f"测试文章 {url} 时出错: {str(e)}"
                    self.log(error_msg)
                    test_results['errors'].append(error_msg)
                    continue
            
            # 判断测试是否成功
            test_results['success'] = (
                test_results['pages_tested'] > 0 and 
                test_results['links_found'] > 0 and 
                test_results['articles_parsed'] > 0
            )
            
            self.log(f"配置测试完成: 测试了 {test_results['pages_tested']} 页，找到 {test_results['links_found']} 个链接，成功解析 {test_results['articles_parsed']}/{test_results['articles_tested']} 篇文章")
            
            return test_results
            
        except Exception as e:
            error_msg = f"测试配置时发生异常: {str(e)}"
            self.log(error_msg)
            test_results['errors'].append(error_msg)
            return test_results
        finally:
            # 恢复原始JSONL设置
            self.enable_jsonl = original_enable_jsonl
            self.log(f"测试完成：已恢复JSONL文件创建设置为 {original_enable_jsonl}")
            # 测试模式下不关闭JSONL写入器，因为可能继续执行正式爬取
    
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
            # 初始化JSONL写入器（如果需要）
            if self.enable_jsonl:
                self._init_jsonl_writer()
                
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
            if self.is_stopped():
                self.log("爬取任务已被用户停止")
                return False
                
            if not all_url_data:
                self.log("所有页面都没有找到任何链接，爬取任务终止")
                return False
            
            # 爬取文章内容
            self._crawl_articles(all_url_data, config)
            
            if self.is_stopped():
                self.log("爬取任务已被用户停止")
                return False
                
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
            # 检查是否应该停止
            if self.is_stopped():
                self.log("在收集链接过程中收到停止请求")
                break
                
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
            # 检查是否应该停止
            if self.is_stopped():
                self.log("在爬取文章内容过程中收到停止请求")
                break
                
            url = item['url']
            title = item['title']
            
            self.log(f"正在处理链接: {url}, 标题: {title}")
            
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
                
                self.log(f"已处理文章: {title}, 时间: {article_data.get('time', '未知')}")
                
                self.random_delay()
                    
            except Exception as e:
                self.log(f"处理链接 {url} 时出错: {str(e)}")
                continue