# scripts/crawl_news_quick.py
"""快速爬取博物馆新闻 - 精简版"""
import json
import os
import re
import time
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE_DIR, 'data', 'museums.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 只处理这些有独立官网的博物馆
TARGET_IDS = [1, 6, 7, 8, 9, 10, 11, 17, 19, 35, 44, 47, 86, 88, 89, 90, 103, 105, 137, 138, 139, 145, 146, 147]
SKIP_DOMAINS = ['njmuseumadmin.com', 'zq.jspi.cn', 'njgl.gov.cn']


def crawl_site(url):
    """爬取单个网站首页，提取新闻/展览链接"""
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if resp.status_code != 200:
            logger.warning(f"  HTTP {resp.status_code}")
            return results
        
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        seen = set()

        for a in soup.find_all('a', href=True):
            title = a.get_text(strip=True)
            if not title or len(title) < 4 or len(title) > 80:
                title = a.get('title', '').strip()
            if not title or len(title) < 4 or title in seen:
                continue
            
            # 排除纯导航
            skip = ['首页', '关于我们', '联系我们', '友情链接', '回到顶部', '返回首页', 
                    '版权', '隐私', '登录', '注册', 'English', '更多', '查看详情']
            if title in skip:
                continue

            seen.add(title)
            href = a['href']
            full_url = urljoin(url, href)
            date_str = ''
            m = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', title)
            if m:
                date_str = m.group(1)

            results.append({
                'title': title,
                'desc': title,
                'link': full_url,
                'date': date_str
            })

        return results[:6]
    except Exception as e:
        logger.warning(f"  异常: {e}")
        return []


def main():
    logger.info("=" * 50)
    logger.info("快速爬取博物馆新闻")
    logger.info("=" * 50)

    with open(MUSEUMS_FILE, 'r', encoding='utf-8-sig') as f:
        museums = json.load(f)
    
    logger.info(f"加载 {len(museums)} 个博物馆")

    updated = 0
    total_news = 0

    for museum in museums:
        mid = museum.get('id', 0)
        if mid not in TARGET_IDS:
            continue
        
        website = museum.get('website', '')
        if not website or not website.startswith('http'):
            continue
        
        # 跳过管理后台
        skip = False
        for d in SKIP_DOMAINS:
            if d in website:
                skip = True
                break
        if skip:
            continue
        
        # 跳过已有 news
        if museum.get('news') and len(museum.get('news', [])) > 0:
            continue

        name = museum.get('name', '?')
        logger.info(f"[{mid}] {name} <- {website}")
        
        news_list = crawl_site(website)
        if news_list:
            museum['news'] = news_list
            museum['last_updated'] = '2026-06-09'
            updated += 1
            total_news += len(news_list)
            logger.info(f"  -> {len(news_list)} 条")
            for n in news_list:
                logger.info(f"    {n['title'][:50]} | {n['link'][:80]}")
        else:
            logger.info(f"  -> 0 条")
        
        time.sleep(1.5)

    if updated > 0:
        with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(museums, f, ensure_ascii=False, indent=4)
        logger.info("=" * 50)
        logger.info(f"保存完成: {updated} 馆, {total_news} 条")
    else:
        logger.info("无新数据")

if __name__ == '__main__':
    main()
