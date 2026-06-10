#!/usr/bin/env python3
"""
为 new_museums_candidates_deduped.json 补充详细地址信息
- 通过高德 POI 搜索获取 formatted_address、完整地址
- 仅补充地址相关字段，不动坐标等其他信息
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
load_dotenv(os.path.join(project_root, '.env'))

AMAP_KEY = os.environ.get('AMAP_KEY', '')
POI_URL = 'https://restapi.amap.com/v3/place/text'
GEO_URL = 'https://restapi.amap.com/v3/geocode/geo'


def search_poi(name):
    """按名称搜索高德 POI，返回最佳匹配"""
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
            return None
        return data.get('pois', [])
    except Exception as e:
        print(f"    POI 请求失败: {e}", flush=True)
        return None


def geocode(address):
    """地址地理编码，获取 formatted_address"""
    params = {
        'key': AMAP_KEY,
        'address': address,
        'city': '南京',
        'output': 'JSON'
    }
    try:
        resp = requests.get(GEO_URL, params=params, timeout=10)
        data = resp.json()
        if data.get('status') == '1' and data.get('geocodes'):
            geo = data['geocodes'][0]
            return {
                'formatted_address': geo.get('formatted_address', ''),
                'province': geo.get('province', ''),
                'city': geo.get('city', ''),
                'district': geo.get('district', ''),
            }
    except Exception:
        pass
    return None


def name_match(a, b):
    """简单的名称相似度"""
    def norm(s):
        return s.replace('（', '(').replace('）', ')').replace('·', '').replace(' ', '').lower()
    na, nb = norm(a), norm(b)
    if na == nb:
        return 3
    base_a = na.split('(')[0].strip()
    base_b = nb.split('(')[0].strip()
    if base_a == base_b:
        return 2
    if len(base_a) >= 4 and len(base_b) >= 4 and (base_a in base_b or base_b in base_a):
        return 1
    return 0


def main():
    if not AMAP_KEY:
        print("错误: 未配置 AMAP_KEY", flush=True)
        sys.exit(1)

    input_path = os.path.join(project_root, 'data', 'new_museums_candidates_deduped.json')
    output_path = input_path  # 原地更新

    with open(input_path, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    # 备份
    backup_path = input_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    total = len(candidates)
    updated_poi = 0
    updated_geo = 0
    skipped = 0

    print(f"开始补充地址信息，共 {total} 个候选博物馆", flush=True)
    print("=" * 70, flush=True)

    for i, c in enumerate(candidates):
        name = c.get('name', '')
        old_address = c.get('address', '')
        old_formatted = c.get('formatted_address', '')

        print(f"\n[{i+1}/{total}] {name}", flush=True)
        print(f"    原地址: {old_address}", flush=True)

        # 策略1: POI 搜索
        pois = search_poi(name)
        if pois:
            # 找最佳名称匹配
            best_poi = None
            best_score = -1
            for poi in pois:
                score = name_match(name, poi['name'])
                if score > best_score:
                    best_score = score
                    best_poi = poi

            if best_poi and best_score >= 1:
                poi_address = best_poi.get('address', '')
                # POI address 字段有时很简略，尝试用 geocode 获取 formatted_address
                geo = geocode(poi_address)
                if geo:
                    c['formatted_address'] = geo['formatted_address']
                    # 如果原有 address 太简略（< 6 个字符），用 POI 地址替换
                    if len(old_address) < 6 and len(poi_address) >= 6:
                        c['address'] = poi_address
                    if not c.get('district') and geo.get('district'):
                        c['district'] = geo['district']
                    print(f"    POI匹配: {best_poi['name']} (score={best_score})", flush=True)
                    print(f"    详细地址: {geo['formatted_address']}", flush=True)
                    updated_poi += 1
                else:
                    # geocode 失败，直接用 POI 地址
                    if len(old_address) < 6 and len(poi_address) >= 6:
                        c['address'] = poi_address
                    print(f"    POI匹配: {best_poi['name']} (score={best_score})", flush=True)
                    print(f"    POI地址: {poi_address}", flush=True)
                    updated_poi += 1
                time.sleep(0.3)
                continue
            else:
                # 名称不匹配，用现有 address 做 geocode
                pass

        # 策略2: 地理编码兜底（用已有的 address）
        if old_address:
            geo = geocode(old_address)
            if geo:
                c['formatted_address'] = geo['formatted_address']
                if not c.get('district') and geo.get('district'):
                    c['district'] = geo['district']
                print(f"    地理编码: {geo['formatted_address']}", flush=True)
                updated_geo += 1
                time.sleep(0.3)
                continue

        print(f"    跳过（无地址可补充）", flush=True)
        skipped += 1
        time.sleep(0.2)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"完成！")
    print(f"  - 总数: {total}")
    print(f"  - POI 匹配补充: {updated_poi}")
    print(f"  - 地理编码补充: {updated_geo}")
    print(f"  - 跳过: {skipped}")
    print(f"  - 备份: {backup_path}")


if __name__ == '__main__':
    main()
