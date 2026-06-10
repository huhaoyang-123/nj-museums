#!/usr/bin/env python3
"""
通过 Wikipedia/Wikimedia API 精确获取博物馆文物数据
完全走API，不用HTML解析，数据质量高
"""

import json, os, sys, time, re, shutil
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE, 'data', 'museums.json')
BACKUP_DIR = os.path.join(BASE, 'data', 'backups')

HEADERS = {'User-Agent': 'MuseumNanjing/3.0 (educational project; contact@example.com)'}
MAX_WORKERS = 5

# 已知在Wikipedia上有条目的博物馆（通过搜索确认）
WIKI_MUSEUMS = {}


def wiki_api(params):
    """通用Wikipedia API调用"""
    try:
        resp = requests.get('https://zh.wikipedia.org/w/api.php',
                          params=params, headers=HEADERS, timeout=15)
        return resp.json()
    except Exception as e:
        print(f'  Wiki API error: {e}')
        return None


def commons_api(params):
    """通用Wikimedia Commons API调用"""
    try:
        resp = requests.get('https://commons.wikimedia.org/w/api.php',
                          params=params, headers=HEADERS, timeout=15)
        return resp.json()
    except Exception as e:
        print(f'  Commons API error: {e}')
        return None


def search_wiki_page(museum_name):
    """搜索Wikipedia页面"""
    data = wiki_api({
        'action': 'query',
        'list': 'search',
        'srsearch': museum_name,
        'srlimit': 1,
        'format': 'json',
    })
    if not data or 'query' not in data:
        return None

    results = data['query']['search']
    if not results:
        return None

    return results[0]['pageid'], results[0]['title']


def get_page_images(pageid):
    """获取Wikipedia页面中的所有图片文件名"""
    data = wiki_api({
        'action': 'query',
        'pageids': str(pageid),
        'prop': 'images',
        'imlimit': 30,
        'format': 'json',
    })
    if not data or 'query' not in data:
        return []

    pages = data['query']['pages']
    for pid, page in pages.items():
        images = page.get('images', [])
        return [img['title'] for img in images if not img['title'].lower().endswith(('.svg', '.gif'))]

    return []


def get_image_urls(filenames, limit=5):
    """批量获取图片真实URL"""
    if not filenames:
        return {}

    urls = {}
    # 过滤掉图标、logo等
    filtered = [f for f in filenames
                if not any(kw in f.lower() for kw in
                          ['icon', 'logo', 'map', 'flag', 'commons-logo',
                           'wikidata', 'question', 'symbol', 'disambig',
                           'magnify', 'stub', 'silk', 'button'])]

    for fname in filtered[:limit * 2]:  # 请求2倍数量，后面再筛选
        data = commons_api({
            'action': 'query',
            'titles': fname,
            'prop': 'imageinfo',
            'iiprop': 'url|size|extmetadata',
            'format': 'json',
        })
        if data and 'query' in data:
            for page in data['query']['pages'].values():
                info = page.get('imageinfo', [])
                if info:
                    url = info[0].get('url', '')
                    size = info[0].get('size', 0)
                    meta = info[0].get('extmetadata', {})
                    desc = meta.get('ImageDescription', {}).get('value', '')
                    obj_name = meta.get('ObjectName', {}).get('value', '')

                    if url and size > 5000:  # 过滤太小的图片
                        # 提取文件名作为候选名称
                        clean_name = fname.replace('File:', '').replace('_', ' ').split('.')[0]
                        urls[fname] = {
                            'url': url,
                            'size': size,
                            'desc': desc or obj_name or clean_name,
                            'name': obj_name or clean_name,
                        }
                        if len(urls) >= limit:
                            return urls

    return urls


def get_page_extract(pageid):
    """获取页面摘要文本"""
    data = wiki_api({
        'action': 'query',
        'pageids': str(pageid),
        'prop': 'extracts',
        'exintro': 1,
        'explaintext': 1,
        'exchars': 2000,
        'format': 'json',
    })
    if data and 'query' in data:
        for page in data['query']['pages'].values():
            return page.get('extract', '')
    return ''


def extract_artifacts_from_text(text, museum_name):
    """从文本中提取文物名称和年代"""
    artifacts = []

    # 常见文物提及模式
    patterns = [
        r'《([^》]{2,20})》',      # 《文物名》
        r'「([^」]{2,20})」',      # 「文物名」
        r'馆藏([^，。,\s]{2,15})', # 馆藏XXX
        r'收藏([^，。,\s]{2,15})', # 收藏XXX
    ]

    found = set()
    for pat in patterns:
        matches = re.findall(pat, text)
        for m in matches:
            m = m.strip()
            if 2 <= len(m) <= 20 and m not in found and m != museum_name:
                found.add(m)
                era = ''
                # 尝试提取年代
                era_match = re.search(rf'{re.escape(m)}.*?([\u4e00-\u9fa5]{{1,4}}(?:代|朝|时期))', text)
                if era_match:
                    era = era_match.group(1)
                artifacts.append({'name': m, 'era': era, 'desc': '', 'image': ''})

            if len(artifacts) >= 5:
                break
        if len(artifacts) >= 5:
            break

    return artifacts[:5]


def process_museum(museum):
    """处理单个博物馆"""
    name = museum.get('name', '')
    mid = museum.get('id', '')

    # 跳过已有足够高质量数据的
    existing = museum.get('collections', [])
    if len(existing) >= 3 and all(c.get('image') for c in existing[:3]):
        return mid, None, 'already_ok'

    print(f'\n📍 [{mid}] {name}')

    # 搜索Wikipedia
    pageid, title = search_wiki_page(name)
    if not pageid:
        print(f'  ❌ 无Wikipedia条目')
        return mid, None, 'no_wiki'

    print(f'  📄 找到: {title} (pageid={pageid})')

    # 获取页面图片
    filenames = get_page_images(pageid)
    if not filenames:
        print(f'  ❌ 页面无图片')
        return mid, None, 'no_images'

    print(f'  🖼️ 页面有 {len(filenames)} 张图')

    # 获取图片URL
    image_data = get_image_urls(filenames, 5)
    if not image_data:
        print(f'  ❌ 无法获取图片')
        return mid, None, 'no_valid_images'

    print(f'  ✅ 获取到 {len(image_data)} 张有效图片')

    # 获取页面文字
    extract = get_page_extract(pageid)
    text_artifacts = extract_artifacts_from_text(extract, name)

    # 构建文物数据
    collections = []
    # 先加入从图片提取的数据
    for fname, info in image_data.items():
        # 尝试匹配文本中的文物名
        matched = False
        for ta in text_artifacts:
            if ta['name'] in info['name'] or any(ch in info['name'] for ch in ta['name']):
                collections.append({
                    'name': ta['name'],
                    'era': ta['era'],
                    'desc': ta.get('desc', '') or info.get('desc', ''),
                    'image': info['url'],
                })
                matched = True
                text_artifacts.remove(ta)
                break

        if not matched:
            # 使用图片的描述作为名称
            clean_name = info.get('name', fname.split(':')[-1].split('.')[0].replace('_', ' '))[:30]
            collections.append({
                'name': clean_name,
                'era': '',
                'desc': info.get('desc', '')[:120],
                'image': info['url'],
            })

        if len(collections) >= 5:
            break

    # 去重
    seen = set()
    unique = []
    for c in collections:
        if c['name'] not in seen and c['image']:
            seen.add(c['name'])
            unique.append(c)
    collections = unique[:5]

    if not collections:
        print(f'  ❌ 无法构建文物数据')
        return mid, None, 'build_failed'

    print(f'  🎉 生成 {len(collections)} 件文物')
    return mid, collections, 'success'


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    with open(MUSEUMS_FILE, 'r', encoding='utf-8') as f:
        museums = json.load(f)

    # 备份
    shutil.copy2(MUSEUMS_FILE, os.path.join(BACKUP_DIR, f'museums_pre_wiki_{int(time.time())}.json'))
    print(f'📦 已备份\n')

    # 筛选目标: 文物<3件或无图
    targets = [m for m in museums
               if len(m.get('collections', [])) < 3
               or not any(c.get('image') for c in m.get('collections', []))]

    print(f'🎯 待处理: {len(targets)} 座\n{"="*60}')

    success = 0
    failed = 0
    already = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_museum, m): m for m in targets}
        for future in as_completed(futures):
            try:
                mid, colls, status = future.result()
                if status == 'success' and colls:
                    # 更新museum数据
                    for m in museums:
                        if m.get('id') == mid:
                            m['collections'] = colls
                            m['collections_note'] = 'Wikipedia API自动提取'
                            m['last_updated'] = time.strftime('%Y-%m-%d')
                            print(f'  ✅ [{mid}] {m["name"]}: {len(colls)}件')
                            break
                    success += 1
                elif status == 'already_ok':
                    already += 1
                else:
                    failed += 1
            except Exception as e:
                print(f'  ❌ Exception: {e}')
                failed += 1

    elapsed = time.time() - start

    # 保存
    with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    # 统计
    with_coll = sum(1 for m in museums if m.get('collections'))
    total_items = sum(len(m.get('collections', [])) for m in museums)
    with_images = sum(1 for m in museums for c in m.get('collections', []) if c.get('image'))

    print(f'\n{"="*60}')
    print(f'📊 完成 (耗时 {elapsed:.1f}s):')
    print(f'  ✅ 成功: {success} 座')
    print(f'  ❌ 失败: {failed} 座')
    print(f'  ⏭️ 已完善: {already} 座')
    print(f'  📚 有文物: {with_coll}/151 座')
    print(f'  🖼️ 总文物: {total_items} 件 ({with_images} 有图片)')
    print(f'  💾 已保存到: {MUSEUMS_FILE}')


if __name__ == '__main__':
    main()
