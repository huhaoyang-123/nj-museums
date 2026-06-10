#!/usr/bin/env python3
"""
博物馆发现脚本 — 通过高德 POI API 搜索南京博物馆/美术馆/展览馆/科技馆/纪念馆/名人故居，
与现有 museums.json 交叉比对，生成：
  1. data/new_museums_candidates.json  — 数据库中不存在的新场馆候选
  2. data/existing_museums_updates.json — 已有博物馆可补充的字段（电话、地址等）
"""

import os
import sys
import json
import time
import re
import requests
from dotenv import load_dotenv

# ---- 配置 ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

AMAP_KEY = os.environ.get('AMAP_KEY', '')
POI_URL = 'https://restapi.amap.com/v3/place/text'

# 搜索关键词列表（每行一个，比大类代码更精准）
SEARCH_QUERIES = [
    '博物馆',
    '美术馆',
    '展览馆',
    '科技馆',
    '纪念馆',
    '名人故居',
    '陈列馆',
    '艺术馆',
    '旧址纪念馆',
]

# 明确要排除的名称关键词（即使 type 是对的，名字决定它不是博物馆）
EXCLUDE_NAME_KEYWORDS = [
    '超市', '酒店', '宾馆', '餐厅', '饭店', '停车场', '厕所', '公厕',
    'KTV', '网吧', '洗浴', '足疗', '按摩', '棋牌室',
    '美容', '美发', '理发', '照相', '打印',
    '药店', '诊所', '医院',
    '银行', '保险',
    '驾校', '加油站', '4S店',
    '五金', '建材', '装修',
    '开市客', '麦德龙', '山姆', '盒马', 'Costco',
    '肯德基', '麦当劳', '星巴克', '必胜客',
    '烟酒', '茶叶', '蛋糕', '小吃', '早点',
]

PAGE_SIZE = 25
DELAY_SECONDS = 1.5


def poi_keyword_search(keyword, page=1):
    """按关键词搜索 POI"""
    params = {
        'key': AMAP_KEY,
        'keywords': keyword,
        'city': '南京',
        'citylimit': 'true',
        'offset': PAGE_SIZE,
        'page': page,
        'extensions': 'all',
        'output': 'JSON',
    }
    try:
        resp = requests.get(POI_URL, params=params, timeout=30)
        data = resp.json()
        if data.get('status') != '1':
            print(f"  [警告] API 返回异常: {data.get('info', '未知')}", flush=True)
            return None
        return data
    except Exception as e:
        print(f"  [错误] 请求失败: {e}", flush=True)
        return None


def fetch_all_pois(keyword, max_pages=10):
    """分页拉取某关键词下所有 POI（最多 max_pages 页以控制总量）"""
    all_pois = []
    page = 1
    while page <= max_pages:
        data = poi_keyword_search(keyword, page)
        if data is None:
            break

        pois = data.get('pois', [])
        if not pois:
            break

        for p in pois:
            location = p.get('location', '')
            lng, lat = None, None
            if location and ',' in location:
                parts = location.split(',')
                lng, lat = float(parts[0]), float(parts[1])

            # 排除名称含无关关键词的
            name = p.get('name', '')
            if any(kw in name for kw in EXCLUDE_NAME_KEYWORDS):
                continue

            all_pois.append({
                'name': name,
                'address': p.get('address', ''),
                'pname': p.get('pname', ''),
                'cityname': p.get('cityname', ''),
                'adname': p.get('adname', ''),
                'tel': p.get('tel', ''),
                'type': p.get('type', ''),
                'typecode': p.get('typecode', ''),
                'lat': lat,
                'lng': lng,
                'biz_ext': p.get('biz_ext', {}),
                'deep_info': p.get('deep_info', {}),
                'photos': [ph.get('url', '') for ph in (p.get('photos', []) or [])[:1]],
            })

        count = int(data.get('count', 0))
        total_pages = min((count + PAGE_SIZE - 1) // PAGE_SIZE, max_pages)
        print(f"    [{keyword}] 第 {page}/{total_pages} 页, 已获取 {len(all_pois)}/{count}", flush=True)

        if page >= total_pages:
            break
        page += 1
        time.sleep(DELAY_SECONDS)

    return all_pois


def distance(lat1, lng1, lat2, lng2):
    """经纬度距离（米），南京纬度约 32 度"""
    if None in (lat1, lng1, lat2, lng2):
        return float('inf')
    dlat = (lat1 - lat2) * 111320
    dlng = (lng1 - lng2) * 111320 * 0.847
    return (dlat ** 2 + dlng ** 2) ** 0.5


def normalize_name(name):
    """去除括号内容、空格"""
    name = re.sub(r'[（(].*?[）)]', '', name)
    name = re.sub(r'\s+', '', name)
    return name.upper()


def load_existing_museums():
    """加载现有博物馆数据"""
    file_path = os.path.join(PROJECT_ROOT, 'data', 'museums.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_poi_to_existing(poi, existing_museums):
    """将 POI 匹配到已有博物馆。仅按名称精确匹配，不做坐标匹配。"""
    poi_name = normalize_name(poi['name'])

    # 名称完全相等
    for m in existing_museums:
        db_name = normalize_name(m.get('name', ''))
        if poi_name and db_name and poi_name == db_name:
            return m, 'exact({} == {})'.format(poi['name'], m['name'])

    # 别名完全相等
    for m in existing_museums:
        for alias in (m.get('alias') or []):
            a_norm = normalize_name(alias)
            if a_norm and poi_name == a_norm:
                return m, 'alias({} == {})'.format(poi['name'], alias)

    return None, ''


def extract_district(poi):
    adname = poi.get('adname', '')
    if adname and '区' in adname:
        return adname
    addr = poi.get('address', '')
    m = re.search(r'(玄武|秦淮|建邺|鼓楼|栖霞|雨花台|江宁|浦口|六合|溧水|高淳)区', addr)
    return m.group(0) if m else ''


def determine_category(poi):
    code = poi.get('typecode', '')
    if '060400' in code:
        return '综合类'
    if '060300' in code:
        return '纪念类'
    if '060600' in code:
        return '艺术'
    if '060700' in code:
        return '教育类'
    if '060500' in code:
        return '专题类'
    if '060200' in code:
        return '历史类'
    return '综合类'


def check_missing_fields(museum, poi):
    updates = {}
    if not museum.get('phone') and poi.get('tel'):
        updates['phone'] = poi['tel']
    poi_addr = poi.get('address', '')
    if poi_addr and (not museum.get('address') or len(museum.get('address', '')) < 10):
        updates['address'] = poi_addr
    # 营业时间
    biz = poi.get('biz_ext', {})
    if biz and biz.get('opentime'):
        if not museum.get('open_time'):
            updates['open_time'] = biz['opentime']
    return updates if updates else None


def main():
    if not AMAP_KEY:
        print('[ERROR] 未配置 AMAP_KEY', flush=True)
        sys.exit(1)

    print('=' * 60)
    print('博物金陵 - POI 发现脚本')
    print('=' * 60)

    # ---- 1. 加载现有数据 ----
    print('\n[1/4] 加载现有博物馆数据...', flush=True)
    existing = load_existing_museums()
    print(f'  已加载 {len(existing)} 个博物馆', flush=True)

    # ---- 2. 拉取高德 POI ----
    print('\n[2/4] 从高德 POI API 拉取数据（关键词搜索）...', flush=True)
    all_pois = []
    for kw in SEARCH_QUERIES:
        print(f'\n  搜索: {kw}', flush=True)
        pois = fetch_all_pois(kw)
        print(f'  有效条目: {len(pois)}', flush=True)
        all_pois.extend(pois)
        time.sleep(1)

    # 去重（同坐标 + 同名）
    seen = {}
    for p in all_pois:
        key = '{:.5f},{:.5f}|{}'.format(p.get('lat', 0), p.get('lng', 0), p['name'])
        if key not in seen:
            seen[key] = p
    all_pois = list(seen.values())
    print(f'\n  去重后共 {len(all_pois)} 条唯一 POI', flush=True)

    # ---- 3. 交叉比对 ----
    print('\n[3/4] 交叉比对...', flush=True)
    new_candidates = []
    existing_updates = []
    matched_ids = set()

    for poi in all_pois:
        cityname = poi.get('cityname', '')
        if cityname and cityname != '南京市' and '南京' not in cityname:
            continue

        matched_museum, match_info = match_poi_to_existing(poi, existing)

        if matched_museum:
            matched_ids.add(matched_museum['id'])
            updates = check_missing_fields(matched_museum, poi)
            if updates:
                existing_updates.append({
                    'museum_id': matched_museum['id'],
                    'museum_name': matched_museum['name'],
                    'poi_name': poi['name'],
                    'match_method': match_info,
                    'updates': updates,
                })
            continue

        # 未匹配 → 候选
        # 按 amap_type 过滤，只保留文化场馆相关类型
        poi_type = poi.get('type', '')
        allowed_types = [
            '博物馆', '纪念馆', '展览馆', '美术馆', '科技馆', '文化宫',
            '科教文化场所', '红色景区', '旅游景点', '风景名胜',
            '图书馆', '文艺团体',
        ]
        if not any(t in poi_type for t in allowed_types):
            continue

        # 名称后缀过滤：只保留以"博物馆/博物院/艺术馆/旧居/故居"结尾的
        if not re.search(r'(博物[馆院]|艺术[馆宫]|旧居|故居)$', poi['name']):
            continue

        district = extract_district(poi)
        category = determine_category(poi)
        photo_url = poi.get('photos', [''])[0] if poi.get('photos') else ''

        candidate = {
            'name': poi['name'],
            'address': poi.get('address', ''),
            'district': district,
            'lat': poi['lat'],
            'lng': poi['lng'],
            'phone': poi.get('tel', ''),
            'category': category,
            'amap_typecode': poi.get('typecode', ''),
            'amap_type': poi.get('type', ''),
            'photo_url': photo_url,
            'photo_source': 'amap_poi' if photo_url else '',
            'data_source': 'amap_poi_discovery',
            'last_updated': time.strftime('%Y-%m-%d'),
            'alias': [],
            'intro_short': '',
            'open_time': '',
            'ticket_info': '',
            'reserve_link': '',
            'website': '',
            'wechat': '',
            'level': '',
            'collections': [],
            'collections_note': '待人工补充',
        }
        new_candidates.append(candidate)

    # 输出前对 updates 去重（同一 museum_id 只保留一条，合并字段）
    deduped_updates = {}
    for u in existing_updates:
        mid = u['museum_id']
        if mid in deduped_updates:
            deduped_updates[mid]['updates'].update(u['updates'])
        else:
            deduped_updates[mid] = u
    existing_updates = list(deduped_updates.values())

    print(f'\n  对比完成:', flush=True)
    print(f'  - 新场馆候选: {len(new_candidates)}', flush=True)
    print(f'  - 已有场馆可更新: {len(existing_updates)}', flush=True)

    # ---- 4. 输出 ----
    print('\n[4/4] 保存结果...', flush=True)
    data_dir = os.path.join(PROJECT_ROOT, 'data')

    if new_candidates:
        path = os.path.join(data_dir, 'new_museums_candidates.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(new_candidates, f, ensure_ascii=False, indent=2)
        print(f'\n  [OK] 新场馆候选: data/new_museums_candidates.json ({len(new_candidates)} 个)', flush=True)
        print('  ---- 预览 ----')
        for i, c in enumerate(new_candidates[:15], 1):
            print(f'  {i:3d}. {c["name"]}')
            print(f'       {c["district"]} | {c["address"][:40]}', flush=True)
        if len(new_candidates) > 15:
            print(f'  ... 还有 {len(new_candidates) - 15} 个', flush=True)
    else:
        print('\n  (i) 未发现新场馆候选', flush=True)

    if existing_updates:
        path = os.path.join(data_dir, 'existing_museums_updates.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing_updates, f, ensure_ascii=False, indent=2)
        print(f'\n  [OK] 已有场馆更新建议: data/existing_museums_updates.json ({len(existing_updates)} 个)', flush=True)
        print('  ---- 预览 ----')
        for u in existing_updates[:15]:
            fields = ', '.join(u['updates'].keys())
            print(f'  [{u["museum_id"]}] {u["museum_name"]}: {fields}', flush=True)
        if len(existing_updates) > 15:
            print(f'  ... 还有 {len(existing_updates) - 15} 个', flush=True)

    print('\n' + '=' * 60)
    print('汇总:', flush=True)
    print(f'  现有博物馆:   {len(existing)}', flush=True)
    print(f'  高德 POI:     {len(all_pois)}', flush=True)
    print(f'  已匹配:       {len(matched_ids)}', flush=True)
    print(f'  新候选:       {len(new_candidates)}', flush=True)
    print(f'  可更新:       {len(existing_updates)}', flush=True)
    print('=' * 60)
    print('\n下一步:', flush=True)
    print('  1. 审核 data/new_museums_candidates.json，移除不需要的，补充详细信息', flush=True)
    print('  2. 审核 data/existing_museums_updates.json，确认字段补充正确', flush=True)
    print('  3. 确认后可手动将候选并入 museums.json 或开发合并脚本', flush=True)


if __name__ == '__main__':
    main()
