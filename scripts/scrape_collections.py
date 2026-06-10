#!/usr/bin/env python3
"""
博物馆展品文物数据批量爬取脚本
=================================
功能：为 museums.json 中缺失文物数据的博物馆，自动搜索并填充展品照片信息。
数据来源优先级：
  1. 百度百科 — 中文博物馆最全的结构化数据
  2. Wikipedia — 国际标准、CC 授权图片
  3. 博物馆官网 — 最准确的官方信息
  4. 通用搜索 — 权威媒体/文化网站

用法：
  python scripts/scrape_collections.py              # 处理所有缺失文物的博物馆
  python scripts/scrape_collections.py --limit 10   # 只处理前10个
  python scripts/scrape_collections.py --id 18,20   # 只处理指定ID
  python scripts/scrape_collections.py --dry-run    # 预览模式，不写文件
"""

import json
import os
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, urljoin

# 修复 Windows GBK 编码下 emoji 输出问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup

# ======================== 配置 ========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE_DIR, 'data', 'museums.json')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
REQUEST_TIMEOUT = 15
MAX_ARTIFACTS_PER_MUSEUM = 5
MAX_WORKERS = 4  # 并发请求数
DELAY_BETWEEN_REQUESTS = 1.5  # 请求间隔（秒），避免被封

PRIORITY_MUSEUMS = {
    # 南京最知名博物馆，优先处理
    '中山陵', '明孝陵', '总统府', '夫子庙', '南京博物院',
    '侵华日军南京大屠杀遇难同胞纪念馆', '南京中国科举博物馆',
    '南京城墙博物馆', '南京云锦博物馆', '南京古生物博物馆',
    '南京大报恩寺遗址博物馆', '郑和纪念馆',
    '中共代表团梅园新村纪念馆', '渡江胜利纪念馆',
    '南京市博物馆', '南京六朝博物馆', '南京民俗博物馆',
    '江宁织造博物馆', '太平天国历史博物馆',
    '南京奥林匹克博物馆', '南京抗日航空烈士纪念馆',
    '南京紫金山昆虫博物馆', '南京直立人化石遗址博物馆',
    '南京雨花石博物馆', '高淳陶瓷博物馆',
}


# ======================== 工具函数 ========================

def load_museums():
    with open(MUSEUMS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('museums', []) if isinstance(data, dict) else data


def save_museums(museums):
    os.makedirs(os.path.dirname(MUSEUMS_FILE), exist_ok=True)
    # 备份
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f'museums_backup_{int(time.time())}.json')
    if os.path.exists(MUSEUMS_FILE):
        import shutil
        shutil.copy2(MUSEUMS_FILE, backup_path)
        print(f'  已备份到: {backup_path}')

    with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)
    print(f'  ✅ 已保存到 {MUSEUMS_FILE}')


def safe_request(url, **kwargs):
    """带重试和错误处理的请求"""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, **kwargs)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return resp
        except requests.exceptions.Timeout:
            print(f'    ⚠️ 请求超时 (尝试 {attempt+1}/3): {url[:80]}')
            time.sleep(2)
        except requests.exceptions.ConnectionError:
            print(f'    ⚠️ 连接错误 (尝试 {attempt+1}/3): {url[:80]}')
            time.sleep(3)
        except Exception as e:
            print(f'    ⚠️ 请求失败 (尝试 {attempt+1}/3): {url[:80]} - {e}')
            time.sleep(2)
    return None


def validate_image_url(url, name=''):
    """快速验证图片URL有效性"""
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        return False
    try:
        resp = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if resp.status_code in (200, 301, 302, 304):
            content_type = resp.headers.get('Content-Type', '')
            if 'image' in content_type or url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                return True
            # 有些CDN不返回Content-Type，但URL以图片扩展名结尾
            if url.lower().split('?')[0].endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return True
        if resp.status_code == 403:
            # 很多网站防爬但浏览器可访问，保守接受
            if url.lower().split('?')[0].endswith(('.jpg', '.jpeg', '.png', '.webp')):
                print(f'    ⚠️ 图片403但保留: {name} - {url[:80]}')
                return True
        return False
    except Exception:
        return False


# ======================== 数据来源：百度百科 ========================

def scrape_baidu_baike(museum_name):
    """从百度百科获取博物馆展品信息（增强版）"""
    url = f'https://baike.baidu.com/item/{quote(museum_name)}'
    resp = safe_request(url)
    if not resp or resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, 'lxml')
    artifacts = []
    seen_artifacts = set()

    # 先从 infobox 提取基础信息（建立年代/分类等上下文）
    basic_info = {}
    for dt in soup.find_all('dt', class_='basicInfo-item'):
        name_tag = dt.find('span', class_='name')
        value_tag = dt.find_next('dd', class_='basicInfo-item')
        if name_tag and value_tag:
            k = name_tag.get_text(strip=True)
            v = value_tag.get_text(strip=True)
            basic_info[k] = v

    # 方法1: 查找"馆藏文物"相关标题段落
    target_headings = ['馆藏文物', '代表文物', '镇馆之宝', '重要藏品',
                       '馆藏精品', '文物藏品', '珍藏', '精品文物',
                       '展品陈列', '陈列展览', '藏品', '基本陈列']

    heading_elements = []
    for tag_name in ['h2', 'h3', 'h4', 'div']:
        for elem in soup.find_all(tag_name):
            text = elem.get_text(strip=True)
            if any(kw in text for kw in target_headings):
                heading_elements.append(elem)

    if not heading_elements:
        # 没找到文物章节，尝试找table中的文物列表
        return _scrape_baike_tables(soup, museum_name, basic_info, MAX_ARTIFACTS_PER_MUSEUM)

    for heading in heading_elements[:2]:  # 最多处理2个相关章节
        # 找后续的段落容器
        container = heading.find_parent(['div', 'section'])
        if not container:
            continue

        # 在这个区域找文物条目
        current_artifact = {'name': '', 'era': '', 'desc': '', 'image': ''}
        text_buffer = []

        # 遍历标题后的内容
        for sibling in heading.find_all_next(['p', 'div', 'table', 'ul']):
            # 如果遇到下一个h2/h3，停止
            prev_h = sibling.find_previous(['h2', 'h3'])
            if prev_h and prev_h != heading:
                if prev_h.find_previous(['h2', 'h3']) == heading:
                    break

            sibling_text = sibling.get_text(strip=True)
            sibling_text = re.sub(r'\[\d+\]', '', sibling_text)  # 去掉引用标记

            # 检测是否是新文物开始（常见模式：粗体名称 + 描述）
            bold = sibling.find(['b', 'strong'])
            imgs = sibling.find_all('img')

            if bold and len(bold.get_text(strip=True)) >= 2:
                # 可能是新文物开始
                name = bold.get_text(strip=True)[:30]
                if name not in seen_artifacts and 2 <= len(name) <= 30:
                    # 保存上一个文物
                    if current_artifact['name'] and current_artifact['image']:
                        if current_artifact['name'] not in seen_artifacts:
                            seen_artifacts.add(current_artifact['name'])
                            artifacts.append(current_artifact)
                            if len(artifacts) >= MAX_ARTIFACTS_PER_MUSEUM:
                                return artifacts

                    current_artifact = {'name': name, 'era': '', 'desc': '', 'image': ''}
                    text_buffer = [sibling_text]

                    # 从此段落提取年代
                    era = _extract_era(sibling_text)
                    if era:
                        current_artifact['era'] = era

            # 提取图片
            for img in imgs:
                src = img.get('src') or img.get('data-src') or ''
                if src and not src.startswith('data:') and len(src) > 20:
                    # 跳过百度内部图
                    if 'baidu' in src.lower() and ('logo' in src.lower() or 'icon' in src.lower()):
                        continue
                    if not src.startswith('http'):
                        src = 'https:' + src if src.startswith('//') else 'https://baike.baidu.com' + src if src.startswith('/') else ''
                    current_artifact['image'] = src

            # 累积描述文本
            if len(sibling_text) > 15:
                text_buffer.append(sibling_text)

        # 保存最后一个文物
        if current_artifact['name']:
            # 如果没有图片但名称有意义，也保存（后续可以通过其他来源补图）
            desc = ' '.join(text_buffer)[:150]
            if desc and desc != current_artifact['name']:
                current_artifact['desc'] = desc
            if current_artifact['name'] not in seen_artifacts:
                seen_artifacts.add(current_artifact['name'])
                artifacts.append(current_artifact)

    # 方法2: 如果没找到，尝试解析百科图册
    if not artifacts:
        artifacts = _scrape_baike_gallery(soup, museum_name)

    # 方法3: 解析表格中的文物列表
    if not artifacts:
        artifacts = _scrape_baike_tables(soup, museum_name, basic_info, MAX_ARTIFACTS_PER_MUSEUM)

    return artifacts


def _extract_era(text):
    """从文本中提取年代/朝代信息"""
    era_patterns = [
        r'([\u4e00-\u9fa5]{1,4}(?:代|朝|时期|年间))',
        r'((?:新石器|旧石器|青铜|铁器|陶器|玉器)时代)',
        r'((?:公元前|公元)[\d]+年)',
        r'([\u4e00-\u9fa5]{2}(?:早期|晚期|中期|前期|后期))',
    ]
    for pat in era_patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ''


def _scrape_baike_gallery(soup, museum_name):
    """解析百度百科图片相册"""
    artifacts = []
    galleries = soup.find_all(['div', 'ul'], class_=re.compile(r'gallery|album|picture|pic', re.I))
    for gallery in galleries:
        items = gallery.find_all('li') or gallery.find_all('div')
        for item in items[:MAX_ARTIFACTS_PER_MUSEUM]:
            img = item.find('img')
            caption_tag = item.find(['span', 'div', 'p'], class_=re.compile(r'caption|title|desc|text', re.I))
            if not img:
                continue
            src = img.get('src') or img.get('data-src') or ''
            if not src:
                continue
            caption = caption_tag.get_text(strip=True)[:30] if caption_tag else ''
            if src:
                artifacts.append({
                    'name': caption or museum_name + '藏品',
                    'era': '',
                    'desc': caption[:120],
                    'image': src,
                })
        if artifacts:
            break
    return artifacts


def _scrape_baike_tables(soup, museum_name, basic_info, limit):
    """从百科页面的表格中提取文物信息"""
    artifacts = []
    seen = set()

    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue

        # 检查表头是否包含文物相关关键词
        header_text = ' '.join(td.get_text(strip=True) for td in rows[0].find_all(['th', 'td']))
        if not any(kw in header_text for kw in ['名称', '文物', '藏品', '器物', '年代', '时代']):
            continue

        for row in rows[1:limit + 1]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            name = ''
            era = ''
            desc = ''
            image = ''

            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                img = cell.find('img')
                if img:
                    src = img.get('src') or img.get('data-src') or ''
                    if src and not src.startswith('data:'):
                        image = src
                if i == 0:
                    name = text[:30]
                elif i == 1:
                    era = _extract_era(text) or text[:20]
                else:
                    if not desc:
                        desc = text[:120]

            if name and 2 <= len(name) <= 30 and name not in seen:
                seen.add(name)
                # 用basic_info补充年代
                if not era:
                    era = basic_info.get('始建年代', basic_info.get('年代', ''))
                artifacts.append({
                    'name': name,
                    'era': era,
                    'desc': desc,
                    'image': image if image.startswith('http') else ('https:' + image if image.startswith('//') else ''),
                })
        if artifacts:
            break

    return artifacts


# ======================== 数据来源：Wikipedia ========================

def scrape_wikipedia(museum_name):
    """从Wikipedia获取博物馆展品信息（优化版）"""
    search_url = f'https://zh.wikipedia.org/w/api.php?action=opensearch&search={quote(museum_name)}&limit=3&format=json'
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        data = resp.json()
        if len(data) > 3 and data[3]:
            page_url = data[3][0]
        else:
            # 尝试英文Wikipedia
            en_search = f'https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(museum_name)}&limit=3&format=json'
            en_resp = requests.get(en_search, headers=HEADERS, timeout=10)
            en_data = en_resp.json()
            if len(en_data) > 3 and en_data[3]:
                page_url = en_data[3][0]
            else:
                return None
    except Exception:
        return None

    resp = safe_request(page_url)
    if not resp or resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, 'lxml')
    artifacts = []
    content = soup.find('div', id='mw-content-text')
    if not content:
        return artifacts

    # 先查找 infobox —— 可能有结构化数据
    infobox_data = {}
    infobox = soup.find('table', class_='infobox')
    if infobox:
        for row in infobox.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)[:200]
                if key and val:
                    infobox_data[key] = val

    # 查找"Collections"/"馆藏"相关section
    collections_section = None
    for heading in content.find_all(['h2', 'h3', 'span', 'div']):
        heading_text = heading.get_text(strip=True).lower()
        if any(kw in heading_text for kw in ['collection', '馆藏', 'exhibit', '藏品', 'gallery']):
            collections_section = heading.find_parent(['div', 'section'])
            break

    seen_names = set()
    imgs_processed = 0

    # 如果找到了collection section，优先从中提取
    search_area = collections_section if collections_section else content

    for img in search_area.find_all('img'):
        if imgs_processed >= MAX_ARTIFACTS_PER_MUSEUM:
            break

        src = img.get('src') or img.get('data-src') or ''
        if not src or 'wiki' not in src.lower() and 'wikimedia' not in src.lower():
            continue
        if any(kw in src.lower() for kw in ['icon', 'flag', 'pixel', '15px', '20px', '25px', '30px', '/static/', 'edit', 'magnify']):
            continue

        # 转为原始图片URL
        original_src = src
        if 'thumb/' in src:
            original_src = re.sub(r'/thumb/(.+?)/\d+px-.+', r'/\1', src)
            if not original_src.startswith('http'):
                original_src = 'https:' + original_src

        # 提取caption
        caption = ''
        parent = img.find_parent(['figure', 'div', 'li'])
        if parent:
            figcaption = parent.find('figcaption')
            if figcaption:
                caption = figcaption.get_text(strip=True)[:100]
            if not caption:
                # 看看父元素的文本
                parent_text = parent.get_text(strip=True)
                if parent_text:
                    # 从图片alt也提取
                    alt = img.get('alt', '')
                    if alt and len(alt) > 2:
                        caption = alt[:100]
                    elif len(parent_text) > 5:
                        caption = parent_text[:100]

        # 清理caption：去掉无意义内容
        caption = re.sub(r'\s+', ' ', caption).strip()
        caption = re.sub(r'^[：:，,\s]+', '', caption)

        # 生成名称：优先从caption提取
        name = ''
        if caption:
            # 尝试提取文物名称模式
            name_match = re.search(r'[《「](.+?)[》」]', caption)
            if name_match:
                name = name_match.group(1)
            else:
                # 取caption的前几个有意义词
                words = caption.replace('，', ',').replace('。', '.').split(',')
                for w in words:
                    w = w.strip()
                    if 3 <= len(w) <= 25 and not w.startswith(('File', 'Image', 'http')):
                        name = w
                        break
                if not name:
                    name = caption[:30]

        if not name or len(name) < 2:
            name = museum_name + ' 藏品 ' + str(imgs_processed + 1)

        if name in seen_names:
            continue
        seen_names.add(name)

        artifacts.append({
            'name': name,
            'era': infobox_data.get('年代', infobox_data.get('Established', '')),
            'desc': caption[:150] if caption else '',
            'image': original_src,
        })
        imgs_processed += 1

    return artifacts


# ======================== 数据来源：通用网页抓取 ========================

def scrape_general_search(museum_name):
    """通用搜索：从权威网站获取展品信息"""
    artifacts = []

    # 搜索关键字
    search_queries = [
        f'{museum_name} 镇馆之宝',
        f'{museum_name} 馆藏精品',
        f'{museum_name} 代表文物',
    ]

    for query in search_queries[:1]:  # 只搜一次，避免太多请求
        try:
            # 使用 Bing 搜索（百度有反爬）
            search_url = f'https://www.bing.com/search?q={quote(query)}&setlang=zh-cn'
            resp = safe_request(search_url)
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, 'lxml')

            # 提取搜索结果摘要
            results = soup.find_all('li', class_=re.compile(r'b_algo'))
            for result in results[:3]:
                title_tag = result.find('h2')
                desc_tag = result.find('p')
                title = title_tag.get_text(strip=True) if title_tag else ''
                desc = desc_tag.get_text(strip=True) if desc_tag else ''

                if any(kw in (title + desc) for kw in ['镇馆', '馆藏', '文物', '珍品', '藏品', '国宝']):
                    # 提取文物名称（在标题或描述中）
                    artifact_names = re.findall(r'《(.+?)》|"(.+?)"|「(.+?)」', title + desc)
                    for match in artifact_names:
                        name = next((m for m in match if m), '')
                        if 2 <= len(name) <= 20 and name not in {'馆', '博物馆'}:
                            artifacts.append({
                                'name': name,
                                'era': '',
                                'desc': desc[:120] if desc else title[:120],
                                'image': '',  # 通用搜索不太容易获得可靠图片URL
                            })
                            if len(artifacts) >= MAX_ARTIFACTS_PER_MUSEUM:
                                break
                if len(artifacts) >= MAX_ARTIFACTS_PER_MUSEUM:
                    break

        except Exception as e:
            print(f'    搜索失败: {query} - {e}')
            continue

    return artifacts


# ======================== 数据来源：博物馆官网 ========================

OFFICIAL_SITES = {
    '南京博物院': 'https://www.njmuseum.com/zh/collection?type=',
    '南京市博物馆': 'https://www.njmuseumadmin.com/Exhibition/index',
    '南京六朝博物馆': 'https://www.njmuseumadmin.com/Exhibition/index/id/2',
    '南京中国科举博物馆': 'https://www.njiemuseum.com/collection',
    '南京云锦博物馆': 'https://www.njyjmuseum.com',
    '南京古生物博物馆': 'http://www.nmp.ac.cn/?list/26/',
    '南京城墙博物馆': 'https://www.njcitywall.com',
    '南京大报恩寺遗址博物馆': 'https://www.dahepiao.com',
    '侵华日军南京大屠杀遇难同胞纪念馆': 'https://www.19371213.com.cn',
    '南京抗日航空烈士纪念馆': 'https://www.nj1937.org',
    '江宁织造博物馆': 'https://www.njmuseumadmin.com/Exhibition/index/id/3',
}


def scrape_official_site(museum_name):
    """从博物馆官网获取展品信息"""
    # 先尝试精确匹配
    url = None
    for name, site_url in OFFICIAL_SITES.items():
        if name in museum_name or museum_name in name:
            url = site_url
            break

    if not url:
        # 模糊匹配
        for name, site_url in OFFICIAL_SITES.items():
            overlap = len(set(museum_name) & set(name))
            if overlap >= 3:
                url = site_url
                break

    if not url:
        return None

    resp = safe_request(url)
    if not resp or resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, 'lxml')
    artifacts = []
    seen_names = set()

    # 查找页面中的图片和标题
    # 常见模式：文物列表/卡片 > 图片 + 标题 + 描述
    for item in soup.find_all(['li', 'div'], class_=re.compile(r'item|card|collection|artifact|exhibit', re.I)):
        imgs = item.find_all('img')
        titles = item.find_all(['h3', 'h4', 'h5', 'span', 'p'], class_=re.compile(r'title|name', re.I))
        descs = item.find_all(['p', 'span', 'div'], class_=re.compile(r'desc|intro|text', re.I))

        for img in imgs[:MAX_ARTIFACTS_PER_MUSEUM]:
            src = img.get('src') or img.get('data-src') or img.get('data-original') or ''
            if not src or src in ('/favicon.ico', '/logo.png'):
                continue
            if not src.startswith('http'):
                src = urljoin(url, src)

            title = titles[0].get_text(strip=True)[:30] if titles else ''
            desc = descs[0].get_text(strip=True)[:120] if descs else ''

            name = title if title else museum_name + ' 展品'
            if name not in seen_names:
                seen_names.add(name)
                artifacts.append({
                    'name': name,
                    'era': '',
                    'desc': desc,
                    'image': src,
                })
                if len(artifacts) >= MAX_ARTIFACTS_PER_MUSEUM:
                    return artifacts

    return artifacts


# ======================== 主流程 ========================

def process_museum(museum):
    """处理单个博物馆，获取展品数据"""
    name = museum.get('name', '')
    museum_id = museum.get('id', '')
    print(f'\n📍 [{museum_id}] {name}')

    # 跳过已有足够文物的
    existing = museum.get('collections', [])
    if len(existing) >= 3:
        print(f'  ✅ 已有 {len(existing)} 件文物，跳过')
        return museum_id, existing, 'skipped'

    all_artifacts = []

    # Tier 1: 博物馆官网（最准确）
    print(f'  🔍 尝试官网...')
    official = scrape_official_site(name)
    if official:
        print(f'    获取到 {len(official)} 件（官网）')
        all_artifacts.extend(official)

    time.sleep(DELAY_BETWEEN_REQUESTS)

    # Tier 2: 百度百科（中文博物馆结构化数据最好）
    if len(all_artifacts) < MAX_ARTIFACTS_PER_MUSEUM:
        print(f'  🔍 尝试百度百科...')
        baike = scrape_baidu_baike(name)
        if baike:
            print(f'    获取到 {len(baike)} 件（百度百科）')
            all_artifacts.extend(baike)

    time.sleep(DELAY_BETWEEN_REQUESTS)

    # Tier 3: Wikipedia
    if len(all_artifacts) < MAX_ARTIFACTS_PER_MUSEUM:
        print(f'  🔍 尝试Wikipedia...')
        wiki = scrape_wikipedia(name)
        if wiki:
            print(f'    获取到 {len(wiki)} 件（Wikipedia）')
            all_artifacts.extend(wiki)

    time.sleep(DELAY_BETWEEN_REQUESTS)

    # Tier 4: 通用搜索（获取文物名称和描述，不一定有图）
    if len(all_artifacts) < MAX_ARTIFACTS_PER_MUSEUM:
        print(f'  🔍 尝试通用搜索...')
        general = scrape_general_search(name)
        if general:
            print(f'    获取到 {len(general)} 件（通用搜索）')
            all_artifacts.extend(general)

    # 去重（按名称）
    seen = set()
    unique_artifacts = []
    for a in all_artifacts:
        if a['name'] not in seen:
            seen.add(a['name'])
            if a.get('description'):
                a['desc'] = a.pop('description')  # 统一字段名
            unique_artifacts.append(a)
    all_artifacts = unique_artifacts[:MAX_ARTIFACTS_PER_MUSEUM]

    # 验证图片URL
    valid_artifacts = []
    for a in all_artifacts:
        if a.get('image'):
            if validate_image_url(a['image'], a['name']):
                valid_artifacts.append(a)
                print(f'    ✅ 图片有效: {a["name"][:20]} → {a["image"][:60]}')
            else:
                # 图片无效，只保留文字信息
                a['image'] = ''
                valid_artifacts.append(a)
                print(f'    ⚠️ 图片无效: {a["name"][:20]}，保留文字信息')
        else:
            valid_artifacts.append(a)

    if valid_artifacts:
        print(f'  🎉 最终获取 {len(valid_artifacts)} 件展品')
    else:
        print(f'  ❌ 未能获取展品数据')

    return museum_id, valid_artifacts, 'updated' if valid_artifacts else 'failed'


def main():
    import argparse
    parser = argparse.ArgumentParser(description='博物馆展品数据爬取')
    parser.add_argument('--limit', type=int, default=0, help='限制处理数量')
    parser.add_argument('--id', type=str, default='', help='指定博物馆ID（逗号分隔）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不写文件')
    parser.add_argument('--priority-only', action='store_true', help='仅处理知名博物馆')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='并发数')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认')
    args = parser.parse_args()

    museums = load_museums()
    print(f'📚 总博物馆数: {len(museums)}')

    # 筛选需要处理的博物馆
    target_ids = None
    if args.id:
        target_ids = set(int(x.strip()) for x in args.id.split(',') if x.strip().isdigit())
        targets = [m for m in museums if m.get('id') in target_ids]
    elif args.priority_only:
        targets = [m for m in museums
                   if not m.get('collections') and m.get('name', '') in PRIORITY_MUSEUMS]
    else:
        targets = [m for m in museums if not m.get('collections') or len(m.get('collections', [])) < 3]

    # 按优先级排序：知名博物馆优先
    def priority(m):
        name = m.get('name', '')
        return (0 if name in PRIORITY_MUSEUMS else 1, name)

    targets.sort(key=priority)

    if args.limit > 0:
        targets = targets[:args.limit]

    print(f'🎯 待处理（缺失/不足文物）: {len(targets)} 座')
    for t in targets[:20]:
        existing = len(t.get('collections', []))
        flag = '⭐' if t.get('name', '') in PRIORITY_MUSEUMS else '  '
        print(f'  {flag} [{t["id"]:>3}] {t["name"]} (现有 {existing} 件)')
    if len(targets) > 20:
        print(f'  ... 还有 {len(targets)-20} 座')

    if args.dry_run:
        print('\n🔍 [DRY RUN] 预览模式，不会写文件')
        return

    if not targets:
        print('✅ 没有需要处理的博物馆')
        return

    # 确认
    if not args.yes:
        print(f'\n⚠️  即将为 {len(targets)} 座博物馆搜索展品数据')
        print('    这将发送大量网络请求，预计耗时 5-15 分钟')
        print('    处理前会自动备份 museums.json')
        response = input('    确认继续? [y/N]: ').strip().lower()
        if response != 'y':
            print('❌ 已取消')
            return

    # 并行处理
    results = {}
    start_time = time.time()
    success_count = 0
    failed_count = 0
    skipped_count = 0

    print(f'\n🚀 开始处理（{args.workers} 线程并发）...\n{"="*60}')

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_museum, m): m for m in targets}
        for future in as_completed(futures):
            try:
                museum_id, artifacts, status = future.result()
                if status == 'updated' and artifacts:
                    results[museum_id] = artifacts
                    success_count += 1
                elif status == 'skipped':
                    skipped_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f'  ❌ 处理异常: {e}')
                traceback.print_exc()
                failed_count += 1

    elapsed = time.time() - start_time
    print(f'\n{"="*60}')
    print(f'📊 完成统计 (耗时 {elapsed:.1f}s):')
    print(f'  ✅ 成功获取: {success_count} 座')
    print(f'  ❌ 获取失败: {failed_count} 座')
    print(f'  ⏭️ 已有数据: {skipped_count} 座')

    # 更新数据
    if results and not args.dry_run:
        museums = load_museums()
        updated = 0
        for museum in museums:
            mid = museum.get('id')
            if mid in results:
                existing_names = {c['name'] for c in museum.get('collections', [])}
                new_items = [a for a in results[mid] if a['name'] not in existing_names]
                if new_items:
                    museum.setdefault('collections', [])
                    museum['collections'].extend(new_items)
                    museum['collections_note'] = '自动采集自百度百科/Wikipedia/博物馆官网'
                    museum['last_updated'] = time.strftime('%Y-%m-%d')
                    updated += 1
                    print(f'  ✅ [{mid}] {museum["name"]}: +{len(new_items)} 件文物')

        if updated > 0:
            save_museums(museums)
            print(f'\n🎉 更新完成！共为 {updated} 座博物馆补充了展品数据')
        else:
            print('\n⚠️ 没有新数据需要写入（可能都已存在）')

    # 汇总报告
    if failed_count > 0:
        print('\n💡 提示：部分博物馆未能获取数据，可能原因：')
        print('   - 官网有反爬机制（可尝试手动补充）')
        print('   - 百度百科无反爬但页面结构变化')
        print('   - 小型博物馆在线资料较少')


if __name__ == '__main__':
    main()
