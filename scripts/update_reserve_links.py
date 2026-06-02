#!/usr/bin/env python3
"""批量更新博物馆预约网址"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'museums.json')

RESERVE_LINKS = {
    # ========== 有独立官网/预约平台的博物馆 ==========
    "南京博物院": "https://www.njmuseum.com/zh/visitIndex",
    "侵华日军南京大屠杀遇难同胞纪念馆": "https://exhibit.19371213.com.cn/yuyue/",
    "南京中国科举博物馆（江南贡院）": "https://www.njiemuseum.com/",
    "南京城墙博物馆": "https://www.njcitywall.com/",
    "南京古生物博物馆": "http://nmp.ac.cn/",
    "南京云锦博物馆": "http://www.yjmuseum.com/",
    "南京大报恩寺遗址博物馆": "https://www.dahepiao.com/jingqulvyou1/2019082386361.html",
    "南京中国近代史遗址博物馆": "https://www.njztf.cn/",
    "南京地质博物馆": "http://www.njgeo.cn/",

    # ========== 南京市博物总馆旗下（统一通过博物南京公众号预约）==========
    "南京市博物馆（朝天宫）": "https://www.njmuseumadmin.com/Stadium/index",
    "六朝博物馆": "https://www.njmuseumadmin.com/Stadium/index/id/6",
    "江宁织造博物馆": "https://www.njmuseumadmin.com/Stadium/index/id/3",
    "太平天国历史博物馆（瞻园）": "https://www.njmuseumadmin.com/Stadium/index/id/5",
    "中国共产党代表团梅园新村纪念馆": "https://www.njmuseumadmin.com/Stadium/index/id/4",
    "渡江胜利纪念馆": "https://www.njmuseumadmin.com/Stadium/index/id/7",
    "南京市民俗博物馆（甘熙宅第）": "https://www.njmuseumadmin.com/Stadium/index/id/2",

    # ========== 高校博物馆 ==========
    "南京大学校史博物馆": "https://www.nju.edu.cn/",
    "东南大学校史馆": "https://www.seu.edu.cn/",
    "南京理工大学兵器博物馆": "https://www.njust.edu.cn/",
    "南京航空航天博物馆": "https://www.nuaa.edu.cn/",
    "南京林业大学博物馆": "https://www.njfu.edu.cn/",
    "南京审计大学货币博物馆": "https://www.nau.edu.cn/",
    "江苏警官学院校史馆": "https://www.jspi.cn/",
    "江苏警官学院近代警察史博物馆": "https://www.jspi.cn/",
    "南京森林警察学院珍稀动物标本馆": "https://www.forestpolice.net/",

    # ========== 其他专题博物馆 ==========
    "南京抗日航空烈士纪念馆": "https://www.nj1937.org/",
    "明孝陵博物馆": "https://zschina.nanjing.gov.cn/",
    "南京十朝历史文化陈列馆": "https://www.nj10d.com/",
    "江苏省中医药博物馆": "https://www.njucm.edu.cn/",
    "南京国防园": "https://www.njgf.gov.cn/",
    "紫金山天文历史博物馆": "https://www.pmo.ac.cn/",
    "南京中山植物园": "https://www.cnbg.net/",
    "南京永银钱币博物馆": "http://www.yybwg.com/",
    "郑和纪念馆": "http://www.zhjng.com/",
    "孙中山纪念馆": "http://www.szsjng.com/",
    "德基艺术博物馆": "https://www.dejiplaza.com/",
    "德基美术馆": "https://www.dejiplaza.com/",
    "南京近代建筑博物馆": "https://www.njgjz.com/",
    "南京江南丝绸文化博物馆": "http://www.silkmuseum.cn/",
}

WEBSITE_LINKS = {
    "南京博物院": "https://www.njmuseum.com",
    "南京市博物馆（朝天宫）": "https://www.njmuseumadmin.com",
    "侵华日军南京大屠杀遇难同胞纪念馆": "https://www.19371213.com.cn",
    "南京中国科举博物馆（江南贡院）": "https://www.njiemuseum.com",
    "南京城墙博物馆": "https://www.njcitywall.com",
    "南京古生物博物馆": "http://nmp.ac.cn",
    "南京云锦博物馆": "http://www.yjmuseum.com",
    "南京中国近代史遗址博物馆": "https://www.njztf.cn",
    "南京地质博物馆": "http://www.njgeo.cn",
    "六朝博物馆": "https://www.njmuseumadmin.com/Stadium/index/id/6",
    "江宁织造博物馆": "https://www.njmuseumadmin.com/Stadium/index/id/3",
}


def update_museums():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated_count = 0
    http_count = 0

    for m in data:
        name = m.get('name', '')

        # 精确匹配
        if name in RESERVE_LINKS:
            m['reserve_link'] = RESERVE_LINKS[name]
            updated_count += 1
            if RESERVE_LINKS[name].startswith('http'):
                http_count += 1
        elif m.get('reserve_link') and not m['reserve_link'].startswith('http'):
            # 已是文本描述，保持不变（如"公众号「博物南京」预约"）
            pass

        if name in WEBSITE_LINKS:
            m['website'] = WEBSITE_LINKS[name]

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {updated_count} 个博物馆的预约链接")
    print(f"其中 HTTP 可跳转链接: {http_count} 个")
    print(f"共 {len(data)} 个博物馆")

    # 统计
    http_count = sum(1 for m in data if m.get('reserve_link', '').startswith('http'))
    text_count = sum(1 for m in data if m.get('reserve_link') and not m['reserve_link'].startswith('http'))
    website_count = sum(1 for m in data if m.get('website', '').startswith('http'))
    print(f"\n汇总: HTTP预约={http_count}, 文本预约={text_count}, 有官网={website_count}")


if __name__ == '__main__':
    update_museums()
