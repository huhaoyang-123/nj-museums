# services/museum_service.py
import json
import logging
import os
import re

logger = logging.getLogger(__name__)

DISTRICT_COORDS = {
    "玄武区": {"lat": 32.048, "lng": 118.828},
    "秦淮区": {"lat": 32.022, "lng": 118.802},
    "建邺区": {"lat": 32.004, "lng": 118.742},
    "鼓楼区": {"lat": 32.066, "lng": 118.786},
    "栖霞区": {"lat": 32.086, "lng": 118.827},
    "雨花台区": {"lat": 31.989, "lng": 118.779},
    "江宁区": {"lat": 31.953, "lng": 118.857},
    "浦口区": {"lat": 32.059, "lng": 118.628},
    "六合区": {"lat": 32.350, "lng": 118.830},
    "溧水区": {"lat": 31.650, "lng": 119.020},
    "高淳区": {"lat": 31.327, "lng": 118.876}
}

CATEGORY_TYPE_MAP = {
    "综合类": "history",
    "历史类": "history",
    "纪念类": "history",
    "遗址类": "history",
    "专题类": "specialty",
    "民俗类": "specialty",
    "自然科学类": "science",
    "科学类": "science",
    "当代艺术": "art",
    "艺术": "art",
    "教育类": "science",
    "建筑类": "art",
    "革命史": "history"
}

def get_all_museums():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'museums.json')

    logger.info("读取文件: %s", file_path)

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        museums_raw = data.get('museums', []) if isinstance(data, dict) else data

        transformed_museums = []
        for idx, museum in enumerate(museums_raw, start=1):
            category = museum.get('category', '')
            museum_type = museum.get('type', '') or map_category_to_type(category)

            name = museum.get('name', '')
            district = museum.get('district', '')
            
            # 优先使用已有的精确坐标
            if 'lat' in museum and 'lng' in museum and museum['lat'] and museum['lng']:
                coords = {'lat': museum['lat'], 'lng': museum['lng']}
            else:
                # 只有在没有精确坐标时才使用基于区名的备用方案
                coords = get_district_coords(district, name)

            transformed = {
                'id': idx,
                'name': museum.get('name', ''),
                'desc': museum.get('intro_short', museum.get('desc', '')),
                'type': museum_type,
                'category': category,
                'address': museum.get('address', ''),
                'district': district,
                'lat': coords['lat'],
                'lng': coords['lng'],
                'open_time': museum.get('open_time', ''),
                'ticket_info': museum.get('ticket_info', ''),
                'phone': museum.get('phone', ''),
                'level': museum.get('level', ''),
                'alias': museum.get('alias', []),
                'wechat': museum.get('wechat', ''),
                'reserve_link': museum.get('reserve_link', ''),
                'website': museum.get('website', ''),
                'photo_url': museum.get('photo_url', ''),
                'intro_short': museum.get('intro_short', ''),
                'collections': museum.get('collections', []),
                'collections_note': museum.get('collections_note', ''),
                'news': museum.get('news', [])
            }
            transformed_museums.append(transformed)

        logger.info("读取成功，数据条数: %d", len(transformed_museums))
        return transformed_museums
    except FileNotFoundError:
        logger.error("文件不存在: %s", file_path)
        return []
    except json.JSONDecodeError as e:
        logger.error("JSON 解析失败: %s", e)
        return []

def map_category_to_type(category):
    if not category:
        return 'history'

    for key, value in CATEGORY_TYPE_MAP.items():
        if key in category:
            return value
    return 'history'

def get_district_coords(district, name=''):
    if not district:
        return {"lat": 32.04, "lng": 118.78}

    clean_district = re.sub(r'[^\u4e00-\u9fa5]', '', district)

    for d, coords in DISTRICT_COORDS.items():
        if d in clean_district:
            return {
                "lat": coords["lat"] + (hash(name) % 100 - 50) * 0.001,
                "lng": coords["lng"] + (hash(name) % 100 - 50) * 0.001
            }

    return {"lat": 32.04, "lng": 118.78}
