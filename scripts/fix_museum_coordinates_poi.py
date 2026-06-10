#!/usr/bin/env python3
"""
博物馆坐标修正脚本 v2 — 通过高德 POI 名称搜索获取精确坐标

核心策略（保守优先）：
1. 用博物馆名称在高德 POI API 搜索
2. 仅在 POI 名称精确匹配或高度相似时才采用
3. 距离校验：新坐标与原坐标偏差超过 5km 时拒绝（防止张冠李戴）
4. 匹配失败时保持原坐标不变
"""

import os
import sys
import json
import time
import math
import requests
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
load_dotenv(os.path.join(project_root, '.env'))

AMAP_KEY = os.environ.get('AMAP_KEY', '')
POI_URL = 'https://restapi.amap.com/v3/place/text'

# 最大允许的坐标偏移（km），超出的视为错误匹配
MAX_DISTANCE_KM = 5.0

# 名称修正映射（博物馆名称 → POI 搜索关键词）
NAME_FIX_MAP = {
    "国民政府主席官邸旧址": "美龄宫",
    "南京国防园": "南京国防园景区",
    "东吴大帝孙权纪念馆": "孙权纪念馆",
    "南京市江宁区博物馆": "江宁博物馆",
    "江苏药学博物馆": "中国药科大学药学博物馆",
    "南京市溧水区博物馆": "溧水博物馆",
    "南京市高淳区博物馆": "高淳博物馆",
    "南京市现代陶瓷博物馆": "高淳陶瓷博物馆",
    "南京直立人化石遗址博物馆": "南京汤山方山国家地质公园博物馆",
    "南京金都金箔技艺博物馆": "金陵金箔博物馆",
    "南京市六合区博物馆": "六合博物馆",
    "江苏警官学院博物馆": "江苏警官学院民国警察史博物馆",
    "南京师范大学珍稀动植物博物馆": "南京师范大学珍稀动物标本馆",
    "雨花台烈士纪念馆": "雨花台烈士陵园纪念馆",
    "南京雨花石博物馆": "雨花石博物馆",
    "南京奥林匹克博物馆": "南京奥林匹克博物馆",
    "求雨山文化名人纪念馆": "求雨山名人纪念馆",
    "陶行知纪念馆": "陶行知纪念馆",
    "南京指纹博物馆": "南京指纹博物馆",
    "南京税收博物馆": "南京税收博物馆",
    "南京静海寺纪念馆": "静海寺纪念馆",
    "南京颜真卿纪念馆": "颜真卿纪念馆",
    "鼓楼医院历史纪念馆": "鼓楼医院",
    "南京鲁迅纪念馆": "南京鲁迅纪念馆",
    "傅抱石纪念馆": "傅抱石纪念馆",
    "南京市手语博物馆": "手语博物馆",
}


def geocode_address(address):
    """地址地理编码兜底"""
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        'key': AMAP_KEY,
        'address': address,
        'city': '南京',
        'output': 'JSON'
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get('status') == '1' and data.get('geocodes'):
            location = data['geocodes'][0]['location']
            lng, lat = location.split(',')
            return {
                'lat': float(lat),
                'lng': float(lng),
                'formatted_address': data['geocodes'][0].get('formatted_address', '')
            }
    except Exception:
        pass
    return None


def search_poi_by_name(name):
    """按名称搜索高德 POI"""
    params = {
        'key': AMAP_KEY,
        'keywords': name,
        'city': '南京',
        'citylimit': 'true',
        'offset': 5,
        'page': 1,
        'extensions': 'all',
        'output': 'JSON',
    }
    try:
        resp = requests.get(POI_URL, params=params, timeout=15)
        data = resp.json()
        if data.get('status') != '1':
            print(f"    API 异常: {data.get('info', '')}", flush=True)
            return None
        return data.get('pois', [])
    except Exception as e:
        print(f"    请求失败: {e}", flush=True)
        return None


def calc_distance(lat1, lng1, lat2, lng2):
    """计算两点间距离（km），Haversine 公式"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def name_similarity(a, b):
    """简单的名称相似度 — 规范化后比较"""
    def norm(s):
        return s.replace('（', '(').replace('）', ')').replace('·', '').replace(' ', '').lower()
    na, nb = norm(a), norm(b)
    if na == nb:
        return 3  # 完全一致
    base_a = na.split('(')[0].strip()
    base_b = nb.split('(')[0].strip()
    if base_a == base_b:
        return 2  # 去括号后一致
    if len(base_a) >= 4 and len(base_b) >= 4 and (base_a in base_b or base_b in base_a):
        return 1  # 包含关系
    return 0


def match_best_poi(museum_name, search_name, pois):
    """从 POI 列表中选出最佳匹配，无可靠匹配返回 None
    同时用原始名称和搜索名称进行匹配（搜索名称可能是经过 FIX_MAP 修正的）
    """
    if not pois:
        return None

    best_poi = None
    best_score = -1

    for poi in pois:
        # 用原始名称和搜索名称分别尝试匹配，取最高分
        score1 = name_similarity(museum_name, poi['name'])
        score2 = name_similarity(search_name, poi['name']) if search_name != museum_name else -1
        score = max(score1, score2)
        if score > best_score:
            best_score = score
            best_poi = poi

    # 至少要包含关系才接受
    if best_score >= 1:
        return (best_poi, best_score)
    return (None, 0)


def main():
    if not AMAP_KEY:
        print("错误: 未配置 AMAP_KEY", flush=True)
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'museums.json')

    # 备份
    with open(file_path, 'r', encoding='utf-8') as f:
        museums = json.load(f)
    backup_path = file_path + '.bak2'
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    total = len(museums)
    updated = 0
    not_found = 0
    rejected_distance = 0

    print(f"开始 POI 搜索修正坐标，共 {total} 个博物馆", flush=True)
    print(f"距离校验阈值: {MAX_DISTANCE_KM}km", flush=True)
    print("=" * 70, flush=True)

    for i, museum in enumerate(museums):
        name = museum.get('name', '')
        old_lat = museum.get('lat', 0)
        old_lng = museum.get('lng', 0)

        print(f"\n[{i+1}/{total}] {name}", flush=True)

        search_name = NAME_FIX_MAP.get(name, name)
        pois = search_poi_by_name(search_name)

        if not pois:
            # 新条目：POI 名称搜索失败，用地址编码兜底
            if museum.get('coordinates_source') == 'pending_poi' and museum.get('address'):
                geo = geocode_address(museum['address'])
                if geo:
                    museum['lat'] = geo['lat']
                    museum['lng'] = geo['lng']
                    museum['coordinates_source'] = 'amap_geocoding_fallback'
                    museum['formatted_address'] = geo.get('formatted_address', '')
                    print(f"    地址编码兜底: ({geo['lat']:.6f}, {geo['lng']:.6f})", flush=True)
                    updated += 1
                else:
                    print(f"    无 POI 结果，地址编码也失败", flush=True)
                    not_found += 1
            else:
                print(f"    无 POI 结果，保留原坐标", flush=True)
                not_found += 1
            time.sleep(0.3)
            continue

        best, match_score = match_best_poi(name, search_name, pois)
        if not best:
            # 新条目：名称不匹配，用地址编码兜底
            if museum.get('coordinates_source') == 'pending_poi' and museum.get('address'):
                geo = geocode_address(museum['address'])
                if geo:
                    museum['lat'] = geo['lat']
                    museum['lng'] = geo['lng']
                    museum['coordinates_source'] = 'amap_geocoding_fallback'
                    museum['formatted_address'] = geo.get('formatted_address', '')
                    print(f"    名称不匹配，地址编码兜底: ({geo['lat']:.6f}, {geo['lng']:.6f})", flush=True)
                    updated += 1
                else:
                    print(f"    无可信名称匹配（候选: {', '.join(p['name'] for p in pois[:3])}），地址编码也失败", flush=True)
                    not_found += 1
            else:
                print(f"    无可信名称匹配（候选: {', '.join(p['name'] for p in pois[:3])}），保留原坐标", flush=True)
                not_found += 1
            time.sleep(0.3)
            continue

        location = best.get('location', '')
        lng_str, lat_str = location.split(',')
        new_lat, new_lng = float(lat_str), float(lng_str)

        # 距离校验：新条目（lat==0 占位符）跳过；精确名称匹配时放宽，弱匹配保留5km阈值
        is_new_entry = museum.get('coordinates_source') == 'pending_poi' or (old_lat == 0 and old_lng == 0)
        if not is_new_entry:
            dist = calc_distance(old_lat, old_lng, new_lat, new_lng)
            threshold = 50.0 if match_score >= 3 else MAX_DISTANCE_KM
            if dist > threshold:
                print(f"    距离 {dist:.1f}km > {threshold:.0f}km 阈值，拒绝: {best['name']} ({best.get('address','')})", flush=True)
                print(f"    保留原坐标: ({old_lat:.6f}, {old_lng:.6f})", flush=True)
                rejected_distance += 1
                time.sleep(0.3)
                continue
        else:
            dist = 0

        museum['lat'] = new_lat
        museum['lng'] = new_lng
        museum['coordinates_source'] = 'amap_poi_search'
        museum['amap_poi_name'] = best['name']
        museum['amap_poi_address'] = best.get('address', '')

        if is_new_entry:
            print(f"    新条目: ({new_lat:.6f}, {new_lng:.6f})", flush=True)
            print(f"    POI匹配: {best['name']} | {best.get('address','')}", flush=True)
        elif dist > 0.05:
            print(f"    修正: ({old_lat:.6f}, {old_lng:.6f}) -> ({new_lat:.6f}, {new_lng:.6f}) 偏移 {dist*1000:.0f}m", flush=True)
            print(f"    POI匹配: {best['name']}", flush=True)
        else:
            print(f"    确认: ({new_lat:.6f}, {new_lng:.6f}) 无显著变化", flush=True)
        updated += 1

        time.sleep(0.3)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"修正完成！")
    print(f"  - 总数: {total}")
    print(f"  - POI 更新: {updated}")
    print(f"  - 无匹配/保留: {not_found}")
    print(f"  - 距离超阈值拒绝: {rejected_distance}")
    print(f"  - 备份: {backup_path}")


if __name__ == '__main__':
    main()
