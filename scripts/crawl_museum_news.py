# scripts/crawl_museum_news.py
"""
从博物馆官网上爬取最新展览、活动、新闻等动态信息。
填充到 museums.json 的 news 字段中。
"""
import json
import os
import re
import time
import logging
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE_DIR, 'data', 'museums.json')

# 新闻/展览相关的关键词（中文）
NEWS_KEYWORDS = ['展览', '活动', '新闻', '公告', '通知', '临时展', '特展',
                 '新展', '临展', '巡展', '讲座', '社教', '研学', '体验',
                 '展览预告', '正在展出', '即将展出', '最新展览',
                 'event', 'exhibition', 'news', 'activity']

# 排除的非新闻链接关键词
EXCLUDE_KEYWORDS = ['首页', '关于我们', '联系我们', '友情链接', '网站地图',
                    '版权', '隐私', '登录', '注册', '回到顶部', '返回首页',
                    'english', '会员', '志愿者', '捐赠']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
SESSION.timeout = 15


def load_museums():
    """加载 museums.json"""
    with open(MUSEUMS_FILE, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def save_museums(data):
    """保存 museums.json"""
    with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def is_news_like(text):
    """判断文本是否像新闻/展览标题"""
    if not text:
        return False
    text = text.strip()
    # 太短或太长都不像新闻标题
    if len(text) < 4 or len(text) > 80:
        return False
    # 排除纯导航文字
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            return False
    # 包含新闻关键词
    for kw in NEWS_KEYWORDS:
        if kw in text:
            return True
    # 或者看起来像一个标题（包含日期、书名号等）
    if re.search(r'《.+》', text):
        return True
    if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', text):
        return True
    return False


def extract_date(text):
    """从文本中提取日期"""
    patterns = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(\d{4}年\d{1,2}月\d{1,2}日)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return ''


def clean_text(text):
    """清洗文本"""
    if not text:
        return ''
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    # 截断过长文本
    if len(text) > 150:
        text = text[:147] + '...'
    return text


def crawl_website(url, museum_name):
    """
    爬取博物馆官网，提取新闻/展览链接。
    返回 list[dict]: [{"title": ..., "desc": ..., "link": ..., "date": ...}]
    """
    results = []
    try:
        logger.info(f"  正在请求: {url}")
        resp = SESSION.get(url, timeout=15, verify=False)
        resp.encoding = resp.apparent_encoding or 'utf-8'

        if resp.status_code != 200:
            logger.warning(f"  HTTP {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 策略1: 查找所有 <a> 标签，看文字是否包含新闻关键词
        all_links = soup.find_all('a', href=True)
        seen_titles = set()

        for a in all_links:
            # 获取链接文字
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                # 尝试从 title 属性获取
                title = a.get('title', '').strip()

            if not is_news_like(title):
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            href = a['href']
            full_link = urljoin(url, href)

            # 尝试获取描述（从父元素的后续文本或 data-content 等属性）
            parent = a.parent
            desc = ''
            if parent:
                # 尝试获取相邻的 p/span/div 中的文本
                for sibling in parent.find_all(['p', 'span', 'div', 'li']):
                    sibling_text = sibling.get_text(strip=True)
                    if sibling_text and sibling_text != title and len(sibling_text) > 10:
                        desc = clean_text(sibling_text)
                        break
                # 如果没找到，尝试父元素的其他子元素
                if not desc:
                    all_text = parent.get_text(separator=' ', strip=True)
                    # 去掉 title 部分
                    remaining = all_text.replace(title, '', 1).strip()
                    if len(remaining) > 10:
                        desc = clean_text(remaining)

            date_str = extract_date(title + ' ' + desc)

            results.append({
                'title': title,
                'desc': desc if desc else title,
                'link': full_link,
                'date': date_str
            })

        # 策略2: 查找特定的新闻列表结构（常见的 class/id 模式）
        news_selectors = [
            {'class_': re.compile(r'news|exhibit|event|activity|notice|bulletin', re.I)},
            {'id': re.compile(r'news|exhibit|event|activity|notice|bulletin', re.I)},
        ]

        for selector in news_selectors:
            for container in soup.find_all(['div', 'ul', 'section', 'article'], **selector):
                for a in container.find_all('a', href=True):
                    title = a.get_text(strip=True)
                    if not title or len(title) < 4:
                        title = a.get('title', '').strip()
                    if title and title not in seen_titles and len(title) >= 4:
                        seen_titles.add(title)
                        href = a['href']
                        full_link = urljoin(url, href)
                        date_str = extract_date(title)
                        results.append({
                            'title': title,
                            'desc': title,
                            'link': full_link,
                            'date': date_str
                        })

        # 去重、限制每馆最多 6 条
        unique = []
        seen = set()
        for item in results:
            key = item['title']
            if key not in seen:
                seen.add(key)
                unique.append(item)
        unique = unique[:6]

        return unique

    except requests.Timeout:
        logger.warning(f"  请求超时: {url}")
    except requests.ConnectionError:
        logger.warning(f"  连接失败: {url}")
    except Exception as e:
        logger.warning(f"  爬取异常: {e}")

    return results


def crawl_museum(museum):
    """爬取单个博物馆"""
    website = museum.get('website', '')
    name = museum.get('name', '')

    if not website or not website.startswith('http'):
        return []

    # 某些网站是管理后台或预约系统，不适合爬首页
    skip_domains = ['njmuseumadmin.com', 'booking', 'reserve', 'ticket']
    for d in skip_domains:
        if d in website:
            logger.info(f"跳过 [{name}] - 网站({website})为管理/预约系统")
            return []

    # 对于 sub-page URL（如 /Stadium/index/id/3），尝试用根域名
    if '/Stadium/' in website or '/index/id/' in website:
        logger.info(f"跳过 [{name}] - 网址({website})为子页面")
        return []

    return crawl_website(website, name)


def main():
    logger.info("=" * 60)
    logger.info("开始爬取博物馆新闻/展览信息")
    logger.info("=" * 60)

    museums = load_museums()

    # 按有计划官网的博物馆进行爬取
    eligible = [m for m in museums if m.get('website', '').startswith('http')]
    logger.info(f"共 {len(museums)} 个博物馆，其中 {len(eligible)} 个有官网链接")

    updated_count = 0
    total_news = 0

    for i, museum in enumerate(eligible):
        name = museum.get('name', '?')
        website = museum.get('website', '')
        logger.info(f"[{i+1}/{len(eligible)}] {name}")

        # 跳过已有 news 数据的
        if museum.get('news') and len(museum['news']) > 0:
            logger.info(f"  已有 {len(museum['news'])} 条新闻，跳过")
            continue

        news_items = crawl_museum(museum)

        if news_items:
            museum['news'] = news_items
            museum['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            updated_count += 1
            total_news += len(news_items)
            logger.info(f"  ✅ 获取到 {len(news_items)} 条动态")
            
            for item in news_items:
                logger.info(f"    - {item['title'][:50]}")
        else:
            logger.info(f"  ❌ 未获取到动态")

        # 礼貌延迟
        time.sleep(1.5)

    # 保存
    save_museums(museums)
    logger.info("=" * 60)
    logger.info(f"完成！共更新 {updated_count} 个博物馆，{total_news} 条新闻/展览")
    logger.info("=" * 60)


if __name__ == '__main__':
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
