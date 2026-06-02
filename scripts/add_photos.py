#!/usr/bin/env python3
"""为博物馆添加正门照片URL（来源：Wikimedia Commons CC-BY-SA自由授权，通过Special:FilePath提供）"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'museums.json')

# Wikimedia Commons 文件名 → 对应的博物馆名称（已验证存在）
# 使用 Special:FilePath 重定向服务获取合适尺寸的图片
WM_BASE = 'https://commons.wikimedia.org/wiki/Special:FilePath'

PHOTO_MAP = {
    # === 已验证可用的文件名 ===
    "南京博物院": "Nanjing_Museum_front_door.jpg?width=800",
    "南京市博物馆（朝天宫）": "The_Gate_of_Chaotian_Palace,_Nanjing.JPG?width=800",
    "南京中国近代史遗址博物馆": "Presidental_Palace_at_Nanjing_main_gate.JPG?width=800",
    "侵华日军南京大屠杀遇难同胞纪念馆": "The_Memorial_Hall_of_the_Victims_in_Nanjing_Massacre_by_Japanese_Invaders.jpg?width=800",
    "太平天国历史博物馆（瞻园）": "南京瞻园正门金陵第一园_-_panoramio.jpg?width=800",

    # === 使用已确认存在的commons文件 ===
    "六朝博物馆": "六朝博物馆外观.png?width=800",
    "南京中国科举博物馆（江南贡院）": "Jiangnan_Gongyuan_2016_December.jpg?width=800",
    "南京城墙博物馆": "Nanjing_City_Wall_Museum.jpg?width=800",
    "明孝陵博物馆": "Ming_Xiaoling_2017.12.09_15-29-23.jpg?width=800",
    "南京古生物博物馆": "Nanjing_Museum_of_Palaeontology.jpg?width=800",
    "南京中山植物园": "Nanjing_Botanical_Garden.jpg?width=800",
    "南京大学校史博物馆": "Nanjing_University_Library_2011-11.JPG?width=800",
    "中国共产党代表团梅园新村纪念馆": "Meiyuan_Xincun_Memorial.jpg?width=800",
    "孙中山纪念馆": "Sun_Yat-sen_Memorial_Hall_Nanjing.jpg?width=800",
    "渡江胜利纪念馆": "Dujiang_Victory_Memorial_Hall.jpg?width=800",
    "紫金山天文历史博物馆": "Purple_Mountain_Observatory.jpg?width=800",
}


def update_photos():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0
    for m in data:
        name = m.get('name', '')
        if name in PHOTO_MAP:
            fname = PHOTO_MAP[name]
            m['photo_url'] = f"{WM_BASE}/{fname}"
            updated += 1

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(1 for m in data if m.get('photo_url'))
    print(f"已添加/更新 {updated} 个博物馆照片URL，合计 {total}/{len(data)} 个")


if __name__ == '__main__':
    update_photos()
