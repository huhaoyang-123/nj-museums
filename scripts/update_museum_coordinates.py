import os
import sys
import json
import requests
import time
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
load_dotenv(os.path.join(project_root, '.env'))

AMAP_KEY = os.environ.get('AMAP_KEY', '')

def get_coordinates_from_amap(address):
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        'key': AMAP_KEY,
        'address': address,
        'output': 'JSON'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get('status') == '1' and data.get('geocodes'):
            location = data['geocodes'][0]['location']
            lng, lat = location.split(',')
            return {
                'lat': float(lat),
                'lng': float(lng),
                'formatted_address': data['geocodes'][0].get('formatted_address', '')
            }
        else:
            print(f"  警告: 无法解析地址 '{address}': {data.get('info', '未知错误')}", flush=True)
            return None
    except Exception as e:
        print(f"  错误: 请求失败 '{address}': {e}", flush=True)
        return None

def update_museums_coordinates():
    if not AMAP_KEY:
        print("错误: 未配置 AMAP_KEY", flush=True)
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'museums.json')

    with open(file_path, 'r', encoding='utf-8') as f:
        museums = json.load(f)

    updated_count = 0
    failed_count = 0
    skipped_count = 0

    print(f"\n开始更新博物馆坐标，共 {len(museums)} 个...", flush=True)
    print("-" * 60, flush=True)

    for museum in museums:
        museum_id = museum.get('id', 'N/A')
        name = museum.get('name', '未知')
        current_lat = museum.get('lat', 0)
        current_lng = museum.get('lng', 0)
        address = museum.get('address', '')

        has_real_coords = (
            museum.get('data_source') == 'manual+official' and current_lat in [
                32.062000000000005, 32.021, 31.971999999999998, 32.061, 32.12, 32.016, 32.064, 32.379000000000005, 31.947, 32.379000000000005
            ]
        )

        if has_real_coords:
            print(f"[{museum_id}] {name}: 已有精确坐标，跳过", flush=True)
            skipped_count += 1
            continue

        if not address:
            print(f"[{museum_id}] {name}: 无地址，跳过", flush=True)
            skipped_count += 1
            continue

        print(f"[{museum_id}] {name}", flush=True)
        print(f"    地址: {address}", flush=True)

        result = get_coordinates_from_amap(address)
        time.sleep(0.5)

        if result:
            museum['lat'] = result['lat']
            museum['lng'] = result['lng']
            museum['coordinates_source'] = 'amap_geocoding'
            if 'formatted_address' not in museum:
                museum['formatted_address'] = result['formatted_address']
            print(f"    新坐标: lat={result['lat']}, lng={result['lng']}", flush=True)
            updated_count += 1
        else:
            print(f"    保留原坐标: lat={current_lat}, lng={current_lng}", flush=True)
            failed_count += 1

        print(flush=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    print("-" * 60, flush=True)
    print(f"更新完成！", flush=True)
    print(f"  - 成功更新: {updated_count} 个", flush=True)
    print(f"  - 跳过: {skipped_count} 个", flush=True)
    print(f"  - 失败: {failed_count} 个", flush=True)
    print(f"\n数据已保存到: {file_path}", flush=True)

if __name__ == '__main__':
    update_museums_coordinates()
