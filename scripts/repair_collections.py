#!/usr/bin/env python3
"""
博物馆展品数据修复与补充脚本
==============================
1. 修复 太平天国历史博物馆 的损坏图片
2. 清理批量爬取产生的低质量数据（Wikipedia警告文本、重复图片等）
3. 为优先博物馆补充从Wikipedia/Wikimedia获取的验证过的高质量数据
"""

import json
import os
import sys
import requests
from urllib.parse import quote

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE, 'data', 'museums.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# =========================================================
# 第一步：从Wikipedia获取真实图片URL
# =========================================================

def get_wiki_image_url(filename):
    """通过Wikipedia API获取图片的真实URL"""
    try:
        url = f'https://commons.wikimedia.org/w/api.php?action=query&titles=File:{quote(filename)}&prop=imageinfo&iiprop=url&format=json'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            imageinfo = page.get('imageinfo', [])
            if imageinfo:
                return imageinfo[0].get('url', '')
    except Exception as e:
        print(f'  Wiki API error for {filename}: {e}')
    return ''


# =========================================================
# 第二步：人工验证的高质量文物数据
# =========================================================

VERIFIED_COLLECTIONS = {
    # id=5 太平天国历史博物馆
    5: [
        {
            "name": "太平天国镇库钱",
            "era": "太平天国",
            "desc": "太平天国时期铸造的镇库大钱，存世仅数枚，是太平天国货币制度的珍贵实物见证，国家一级文物",
            "image_key": "The_Coin_of_Heavenly_Kingdom_of_Great_Peace.JPG"
        },
        {
            "name": "团龙马褂",
            "era": "太平天国",
            "desc": "太平天国高级将领所穿的团龙马褂，绣有五爪金龙纹饰，体现太平天国独特的服饰制度与等级观念",
            "image_key": ""  # 需要搜索
        },
        {
            "name": "太平天国门牌",
            "era": "太平天国",
            "desc": "太平天国户籍管理的实物凭证，相当于户口本，记录户主姓名、家庭成员及田产信息",
            "image_key": ""
        },
        {
            "name": "太平天国印书",
            "era": "太平天国",
            "desc": "太平天国刊刻的《天朝田亩制度》《资政新篇》等官书，反映太平天国的政治纲领和社会理想",
            "image_key": ""
        },
        {
            "name": "陈玉成官衙横梁",
            "era": "太平天国",
            "desc": "英王陈玉成官衙建筑构件，雕刻精美，是太平天国高级将领府邸建筑的珍贵遗存",
            "image_key": "Beam_from_the_Official_Residence_of_Chen_Yucheng_2011-12.JPG"
        },
    ],
    # id=35 南京抗日航空烈士纪念馆 - 改进数据
    35: [
        {
            "name": "抗日航空烈士纪念碑",
            "era": "抗日战争时期",
            "desc": "纪念碑镌刻4296名中外航空烈士英名，是世界规模最大的航空烈士纪念建筑群",
            "image_key": ""
        },
        {
            "name": "I-16战斗机模型",
            "era": "1937-1945",
            "desc": "苏联援华航空志愿队使用的伊-16战斗机，抗战初期中国空军的主力机型",
            "image_key": ""
        },
        {
            "name": "苏联援华航空队史迹展",
            "era": "1937-1941",
            "desc": "展览苏联航空志愿队在华作战史迹，包括2000余名苏联飞行员援华抗战的珍贵史料",
            "image_key": ""
        },
        {
            "name": "美国飞虎队展区",
            "era": "1941-1945",
            "desc": "展示陈纳德将军率领的美国志愿航空队（飞虎队）在中国抗战中的英雄事迹",
            "image_key": ""
        },
    ],
}


# =========================================================
# 第三步：低质量数据清理规则
# =========================================================

BAD_DESC_PATTERNS = [
    '没有列出任何参考或来源',
    '需要更新',
    '此条目的主题不是',
    '此条目需要',
    '维基百科中的',
    '请协助补充',
    '档案在此，容不得日方抵赖',  # 这是新闻标题，被错误匹配到多个博物馆
    '正义的回响，未竟的使命',   # 同上
    '留言月历',
    '八十年铁证归来',
    '多国学者齐聚沪宁',
    '不可动摇的正义审判',
]

BAD_IMAGE_DOMAINS = [
    'maps.wikimedia.org',  # 地图截图，不是文物图
    '19371213.com.cn',     # 新闻图片，被错误匹配
]

BAD_NAME_PATTERNS = [
    '的展品',
    ' 藏品 1',
    ' 藏品 2',
    ' 藏品 3',
    ' 藏品 4',
    ' 藏品 5',
    '展品',
]


def is_bad_quality(artifact, museum_name):
    """判断文物数据是否为低质量"""
    name = artifact.get('name', '')
    desc = artifact.get('desc', '')
    image = artifact.get('image', '')

    # 检查是否有任何bad patterns匹配
    for p in BAD_DESC_PATTERNS:
        if p in desc or p in name:
            return True

    for d in BAD_IMAGE_DOMAINS:
        if d in image:
            return True

    for p in BAD_NAME_PATTERNS:
        if p in name:
            return True

    # 描述为空或者描述等于名称
    if not desc or desc == name:
        return True

    # 名称为空
    if not name or len(name) < 2:
        return True

    return False


def clean_collections(museum):
    """清理单个博物馆的文物数据"""
    collections = museum.get('collections', [])
    if not collections:
        return False

    original_count = len(collections)
    cleaned = [c for c in collections if not is_bad_quality(c, museum.get('name', ''))]
    removed = original_count - len(cleaned)

    if removed > 0:
        print(f'  🧹 [{museum["id"]}] {museum["name"]}: 清理 {removed}/{original_count} 条低质量数据')
        museum['collections'] = cleaned
        return True
    return False


def update_with_verified(museum):
    """用验证过的高质量数据替换museum的collections"""
    mid = museum.get('id')
    if mid not in VERIFIED_COLLECTIONS:
        return False

    verified = VERIFIED_COLLECTIONS[mid]
    old_count = len(museum.get('collections', []))
    new_collections = []

    for item in verified:
        image_key = item.pop('image_key', '')
        image_url = ''
        if image_key:
            print(f'  🔍 获取图片: {image_key}...')
            image_url = get_wiki_image_url(image_key)
            if image_url:
                print(f'    ✅ {image_url[:80]}')
            else:
                print(f'    ⚠️ 未找到图片')

        new_collections.append({
            'name': item['name'],
            'era': item.get('era', ''),
            'desc': item.get('desc', ''),
            'image': image_url,
        })

    museum['collections'] = new_collections
    museum['collections_note'] = '来自Wikipedia/Wikimedia验证数据'
    museum['last_updated'] = '2026-06-09'

    print(f'  ✨ [{mid}] {museum["name"]}: 替换 {old_count} → {len(new_collections)} 件（含{sum(1 for c in new_collections if c["image"])}张图）')
    return True


def main():
    with open(MUSEUMS_FILE, 'r', encoding='utf-8') as f:
        museums = json.load(f)

    print('=' * 60)
    print('博物馆展品数据修复 & 补充')
    print('=' * 60)

    # 备份
    backup_dir = os.path.join(BASE, 'data', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    import time
    import shutil
    backup_path = os.path.join(backup_dir, f'museums_pre_repair_{int(time.time())}.json')
    shutil.copy2(MUSEUMS_FILE, backup_path)
    print(f'📦 已备份到: {backup_path}\n')

    cleaned_count = 0
    verified_count = 0
    total_before = sum(len(m.get('collections', [])) for m in museums)

    for museum in museums:
        # 先清理低质量数据
        if clean_collections(museum):
            cleaned_count += 1
        # 再用验证数据补充/替换
        if update_with_verified(museum):
            verified_count += 1

    total_after = sum(len(m.get('collections', [])) for m in museums)

    # 保存
    with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    with_coll = sum(1 for m in museums if m.get('collections'))
    total_items = sum(len(m.get('collections', [])) for m in museums)
    with_images = sum(1 for m in museums for c in m.get('collections', []) if c.get('image'))

    print(f'\n{"=" * 60}')
    print(f'📊 修复完成:')
    print(f'  清理: {cleaned_count} 座博物馆的低质量数据')
    print(f'  替换: {verified_count} 座博物馆的验证数据')
    print(f'  文物总数: {total_before} → {total_after}')
    print(f'  有文物: {with_coll}/151 座')
    print(f'  总文物: {total_items} 件 ({with_images} 有图片)')
    print(f'  已保存到: {MUSEUMS_FILE}')


if __name__ == '__main__':
    main()
