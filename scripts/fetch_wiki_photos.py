#!/usr/bin/env python3
"""通过 Wikipedia API 批量获取博物馆主图（CC自由授权）"""
import json
import os
import ssl
import time
import urllib.request
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'museums.json')

# Wikipedia 搜索关键词映射（部分博物馆名与百科条目名不同）
WIKI_OVERRIDES = {
    "南京博物院": "南京博物院",
    "南京市博物馆（朝天宫）": "南京市博物馆",
    "南京中国近代史遗址博物馆": "南京总统府",
    "太平天国历史博物馆（瞻园）": "太平天国历史博物馆",
    "南京中国科举博物馆（江南贡院）": "南京中国科举博物馆",
    "南京市民俗博物馆（甘熙宅第）": "甘熙故居",
    "国民政府主席官邸旧址": "美龄宫",
    "东吴大帝孙权纪念馆": "孙权纪念馆",
    "南京抗日航空烈士纪念馆": "南京抗日航空烈士纪念馆",
    "南京十朝历史文化陈列馆": "南京十朝历史文化园",
    "中国共产党代表团梅园新村纪念馆": "中国共产党代表团梅园新村纪念馆",
    "中国共产党代表团梅园新村纪念馆": "梅园新村纪念馆",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch_wiki_image(page_title):
    """查询 Wikipedia 页面主图"""
    encoded = urllib.parse.quote(page_title)
    url = f'https://zh.wikipedia.org/api/rest_v1/page/summary/{encoded}'
    req = urllib.request.Request(url, headers={'User-Agent': 'MuseumGuide/1.0 (Nanjing)'})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=12)
        data = json.loads(resp.read().decode())
        # 优先原图，其次缩略图
        img = data.get('originalimage', {}).get('source', '')
        if not img:
            img = data.get('thumbnail', {}).get('source', '')
        # 去掉缩略图尺寸限制以获得大图
        if '/thumb/' in img:
            img = img.rsplit('/', 1)[0]  # 去 /330px-xxx.jpg
            img = img.replace('/thumb/', '/')  # 用原图
        if img and 'upload.wikimedia.org' in img:
            return img
    except urllib.error.HTTPError as e:
        if e.code == 404:
            pass  # 百科无此条目
    except Exception:
        pass
    return None


def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        museums = json.load(f)

    found = 0
    not_found = 0

    for i, m in enumerate(museums):
        name = m.get('name', '')
        # 跳过已有有效 URL 的
        existing = m.get('photo_url', '')
        if existing and 'Special:FilePath' in existing:
            continue  # 保留已验证的3个

        # 确定搜索关键词
        search_name = WIKI_OVERRIDES.get(name, name)

        print(f'[{i+1}/{len(museums)}] {name} ...', end=' ', flush=True)

        img_url = fetch_wiki_image(search_name)
        if img_url:
            m['photo_url'] = img_url
            found += 1
            print(f'OK {img_url[:80]}')
        else:
            not_found += 1
            print('NO WIKI PAGE')

        time.sleep(0.25)  # 礼貌限速

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    total = sum(1 for m in museums if m.get('photo_url'))
    print(f'\n======= 完成 =======')
    print(f'新增照片: {found} 个')
    print(f'无百科页面: {not_found} 个')
    print(f'合计有照片: {total}/{len(museums)} 个博物馆')


if __name__ == '__main__':
    main()
