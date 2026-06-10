#!/usr/bin/env python3
"""
博物馆元数据填充脚本
对 data_source=formal_catalog 的博物馆，通过网页抓取 + 规则生成补充基础信息。

填充字段：
  intro_short, open_time, ticket_info, website, wechat, phone, photo_url, photo_source

策略：
  1. 百度百科抓取 → 获取开放时间、门票、电话、官网、摘要
  2. Bing 搜索引擎抓取 → 兜底获取信息
  3. 高德 POI 搜索 → 兜底获取图片、电话
  4. 规则生成 → 完全搜不到时根据名称/类别/地区生成合理描述
"""

import json
import os
import re
import time
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

# ========== 配置 ==========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE_DIR, 'data', 'museums.json')
BACKUP_FILE = MUSEUMS_FILE + '.bak_fill'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 批量搜索时的请求间隔（秒）
REQUEST_DELAY = 2

BAIDU_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://baike.baidu.com/',
    'Connection': 'keep-alive',
}

_baidu_session = None


def _get_baidu_session():
    """获取带 cookie 的百度会话（首次访问建立 cookie）"""
    global _baidu_session
    if _baidu_session is None:
        _baidu_session = requests.Session()
        _baidu_session.headers.update(BAIDU_HEADERS)
        try:
            _baidu_session.get('https://www.baidu.com', timeout=10)
        except Exception:
            pass
    return _baidu_session


# ========== 百度百科抓取 ==========
def fetch_baidu_baike(name):
    """抓取百度百科页面获取结构化信息"""
    result = {
        'intro': '',
        'open_time': '',
        'ticket_info': '',
        'phone': '',
        'website': '',
        'photo_url': '',
    }
    try:
        session = _get_baidu_session()
        encoded = quote(name)
        url = f'https://baike.baidu.com/item/{encoded}'
        resp = session.get(url, timeout=15, allow_redirects=True)
        if resp.status_code != 200 or '抱歉，您所访问的页面不存在' in resp.text:
            return result

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 摘要
        summary_el = soup.select_one('.lemma-summary')
        if summary_el:
            text = summary_el.get_text(strip=True)
            if len(text) > 120:
                text = text[:120].rsplit('。', 1)[0] + '。'
            result['intro'] = text

        # 基本信息表格
        for dt_el in soup.select('.basicInfo-item.name'):
            label = dt_el.get_text(strip=True)
            dd_el = dt_el.find_next_sibling('dd')
            if not dd_el:
                continue
            value = dd_el.get_text(strip=True)

            if '开放时间' in label or '参观时间' in label:
                result['open_time'] = value
            elif '门票' in label or '票价' in label:
                result['ticket_info'] = value
            elif '电话' in label or '联系方式' in label:
                result['phone'] = value
            elif '官网' in label or '网址' in label:
                # 提取链接
                link = dd_el.select_one('a')
                if link and link.get('href'):
                    result['website'] = link['href']

        # 图片
        img_el = soup.select_one('.summary-pic img')
        if img_el and img_el.get('src'):
            src = img_el['src']
            if src.startswith('//'):
                src = 'https:' + src
            result['photo_url'] = src

    except Exception:
        pass
    return result


# ========== 通用搜索引擎 ==========
def _is_result_relevant(title, snippet, name):
    """检查搜索结果是否与目标博物馆相关"""
    # 提取博物馆名称中的关键词（去掉"南京""市""博物馆"等通用词）
    core_name = name
    for w in ['南京市', '南京', '博物馆', '陈列馆', '纪念馆', '展示馆']:
        core_name = core_name.replace(w, '')
    core_name = core_name.strip()

    combined = (title or '') + ' ' + (snippet or '')

    # 必须包含核心名称（至少2个字）或完整名称
    if len(core_name) >= 2 and core_name in combined:
        return True
    if len(name) >= 4 and name in combined:
        return True

    # 排除明显不相关的结果（南京市概况、南京旅游等）
    blacklist_patterns = [
        r'^南京市[（(]',           # "南京市（Nanjing City）"
        r'南京市[^博陈纪展]',        # "南京市"后不是博物馆相关字
    ]
    for pat in blacklist_patterns:
        if re.search(pat, title or ''):
            return False

    # 标题中包含博物馆名称为准
    if core_name in (title or '') or name in (title or ''):
        return True

    return False


def search_web(name, query_type='general'):
    """通过 Bing 搜索获取信息"""
    results = {'intro': '', 'open_time': '', 'ticket_info': '', 'phone': '', 'website': '', 'photo_url': ''}

    try:
        if query_type == 'general':
            query = f'"{name}" 博物馆 开放时间 门票 简介'
        elif query_type == 'baike':
            query = f'site:baike.baidu.com "{name}" 博物馆'
        elif query_type == 'hours':
            query = f'"{name}" 开放时间 门票 电话'
        else:
            query = f'"{name}" 博物馆 官网'

        encoded = quote(query)
        url = f'https://www.bing.com/search?q={encoded}&setlang=zh-cn'
        resp = requests.get(url, headers=HEADERS, timeout=15)

        if resp.status_code != 200:
            return results

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 获取搜索结果列表（标题 + 摘要），仅保留与博物馆名称相关的结果
        algo_items = soup.select('.b_algo')
        relevant_snippets = []

        for algo in algo_items:
            h2 = algo.select_one('h2')
            title = h2.get_text(strip=True) if h2 else ''
            caption = algo.select_one('.b_caption')
            snippet_text = caption.get_text(strip=True) if caption else ''

            if _is_result_relevant(title, snippet_text, name):
                relevant_snippets.append(snippet_text)

        # 没有相关结果就直接返回空，交给规则生成兜底
        if not relevant_snippets:
            return results

        for text in relevant_snippets[:5]:
            if len(text) < 10:
                continue

            # 查找开放时间
            if not results['open_time']:
                time_patterns = [
                    r'(\d{1,2}[:：]\d{2}\s*[-–—~至到]\s*\d{1,2}[:：]\d{2})',
                    r'(周[一二三四五六日]\s*[-–—~至到]\s*周[一二三四五六日]\s*\d{1,2}[:：]\d{2}\s*[-–—~至到]\s*\d{1,2}[:：]\d{2})',
                    r'(开放时间[：:]\s*.{0,30}?\d{1,2}[:：]\d{2})',
                ]
                for pat in time_patterns:
                    m = re.search(pat, text)
                    if m:
                        results['open_time'] = m.group(0)
                        break

            # 查找电话
            if not results['phone']:
                phone_patterns = [
                    r'(0\d{2,3}[-–—]?\d{7,8})',
                    r'(电话[：:]\s*\d{3,4}[-–—]?\d{7,8})',
                ]
                for pat in phone_patterns:
                    m = re.search(pat, text)
                    if m:
                        phone_val = m.group(0)
                        if '电话' in phone_val:
                            phone_val = re.sub(r'电话[：:]', '', phone_val).strip()
                        results['phone'] = phone_val
                        break

            # 查找门票
            if not results['ticket_info']:
                ticket_keywords = ['免费参观', '免费开放', '免费不免票', '票价', '门票', '收费']
                if any(kw in text for kw in ticket_keywords):
                    if len(text) < 80:
                        results['ticket_info'] = text
                    else:
                        for sent in re.split(r'[。！；;]', text):
                            if any(kw in sent for kw in ticket_keywords):
                                results['ticket_info'] = sent.strip()
                                break

            # 收集简介文本（必须包含博物馆名称关键词）
            if not results['intro'] and len(text) > 25:
                intro_text = text
                if len(intro_text) > 120:
                    intro_text = intro_text[:120].rsplit('。', 1)[0] + '。'
                results['intro'] = intro_text

        # 查找官网链接
        if not results['website']:
            for link in soup.select('a[href^="http"]'):
                href = link.get('href', '')
                text_lower = link.get_text(strip=True).lower()
                if any(kw in href for kw in ['museum', 'gov.cn', 'edu.cn']):
                    results['website'] = href
                    break
                if '官网' in text_lower or '官方网站' in text_lower:
                    results['website'] = href
                    break

    except Exception:
        pass

    return results


# ========== Amap POI 搜索（获取图片等） ==========
def search_amap_poi(name, district=''):
    """通过高德 POI 搜索获取图片"""
    result = {'photo_url': '', 'phone': ''}
    try:
        amap_key = os.environ.get('AMAP_KEY', '')
        if not amap_key:
            # 尝试从 .env 加载
            from dotenv import load_dotenv
            load_dotenv(os.path.join(BASE_DIR, '.env'))
            amap_key = os.environ.get('AMAP_KEY', '')

        if not amap_key:
            return result

        url = 'https://restapi.amap.com/v3/place/text'
        params = {
            'key': amap_key,
            'keywords': name,
            'city': '南京',
            'citylimit': 'true',
            'offset': 3,
            'page': 1,
            'extensions': 'all',
            'output': 'JSON',
        }
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if data.get('status') == '1' and data.get('pois'):
            poi = data['pois'][0]
            # 图片
            photos = poi.get('photos', [])
            if photos:
                photo = photos[0]
                url_part = photo.get('url', '')
                if url_part:
                    result['photo_url'] = url_part if url_part.startswith('http') else f'https://store.is.autonavi.com/showpic/{url_part}'
            # 电话
            tel = poi.get('tel', '')
            if tel:
                result['phone'] = tel
    except Exception:
        pass
    return result


# ========== 规则生成 ==========
def generate_by_rules(museum):
    """根据博物馆名称、类别、地区生成合理描述"""
    name = museum.get('name', '')
    category = museum.get('category', '')
    district = museum.get('district', '')
    address = museum.get('address', '')
    grade = museum.get('grade', '')

    # 基础开放时间推测（南京大多数博物馆的常见模式）
    open_time = '9:00-17:00（16:00停止入馆），周一闭馆（法定节假日除外）'
    ticket_info = '免费参观，需预约'
    phone = ''

    # 根据名称中的关键词微调
    is_university = any(kw in name for kw in ['大学', '学院', '师范', '警官', '药学'])
    is_memorial = any(kw in name for kw in ['纪念', '烈士'])
    is_small = any(kw in name for kw in ['社区', '陈列馆', '史料馆', '馆藏'])

    if is_university:
        open_time = '工作日上午9:00-11:30，下午14:00-16:30，周末及节假日需预约'
        ticket_info = '免费，需提前预约'
    elif is_memorial:
        open_time = '9:00-17:00（16:00停止入馆），周一闭馆'
        ticket_info = '免费参观'
    elif is_small:
        open_time = '9:00-17:00，建议提前电话确认'
        ticket_info = '免费参观'

    # 生成简介
    intro = generate_intro(name, category, district, is_university, is_memorial)

    return {
        'intro_short': intro,
        'open_time': open_time,
        'ticket_info': ticket_info,
        'phone': phone,
    }


def generate_intro(name, category, district, is_university, is_memorial):
    """为博物馆生成简介"""
    # 提取核心名称（去掉"南京市""区"等前缀）
    short_name = name
    for prefix in ['南京市', '南京']:
        if short_name.startswith(prefix):
            short_name = short_name[len(prefix):]
            break
    for suffix in ['市', '区']:
        if district.endswith(suffix):
            district = district[:-1]

    templates = []

    if is_university:
        univ_name = ''
        for kw in ['南京师范大学', '中国药科大学', '南京林业大学', '南京大学', '江苏警官学院', '江苏海事职业技术学院']:
            if kw in name:
                univ_name = kw
                break
        if univ_name:
            templates.append(f'{name}隶属于{univ_name}，是以{category.replace("类","")}为主题的专题博物馆。')
        else:
            templates.append(f'{name}是南京地区高校系统内的{category}主题博物馆。')
    elif is_memorial:
        if '烈士' in name or '抗日' in name:
            templates.append(f'{name}是南京市{district}重要的爱国主义教育基地，展示革命历史与英雄事迹。')
        else:
            templates.append(f'{name}位于南京市{district}区，是以纪念历史名人为主题的专题纪念馆。')
    elif '专题' in category or '自然科学' in category or '民俗' in category or '艺术' in category:
        templates.append(f'{name}位于南京市{district}区，是以{category.replace("类","")}为主的专题博物馆。')
    else:
        templates.append(f'{name}位于南京市{district}区，是展示地方历史文化与特色的{category}博物馆。')

    return templates[0] if templates else f'{name}是南京市{district}区的综合性博物馆。'


# ========== 主流程 ==========
def fill_museum(museum, idx, total):
    """填充单个博物馆的元数据"""
    name = museum['name']
    print(f'\n[{idx}/{total}] {name}', flush=True)

    # Step 1: 百度百科（主数据源）
    baidu_info = fetch_baidu_baike(name)

    # Step 2: Bing 搜索（兜底）
    bing_info = search_web(name, 'general')

    # 合并信息，从博物馆现有数据开始，逐层覆盖
    # 优先级：百度百科 > Bing 搜索 > 已有数据 > 规则生成
    final = {
        'intro_short': museum.get('intro_short', ''),
        'open_time': museum.get('open_time', ''),
        'ticket_info': museum.get('ticket_info', ''),
        'website': museum.get('website', ''),
        'wechat': museum.get('wechat', ''),
        'phone': museum.get('phone', ''),
        'photo_url': museum.get('photo_url', ''),
        'photo_source': museum.get('photo_source', ''),
    }

    # 百度百科日志
    if baidu_info.get('intro'):
        print(f'  [百度百科] 获取到摘要', flush=True)
    if baidu_info.get('open_time'):
        print(f'  [百度百科] 获取到开放时间: {baidu_info["open_time"]}', flush=True)
    if baidu_info.get('ticket_info'):
        print(f'  [百度百科] 获取到门票信息', flush=True)
    if baidu_info.get('phone'):
        print(f'  [百度百科] 获取到电话', flush=True)
    if baidu_info.get('website'):
        print(f'  [百度百科] 获取到官网', flush=True)
    if baidu_info.get('photo_url'):
        print(f'  [百度百科] 获取到图片', flush=True)

    # Bing 搜索日志
    if bing_info.get('intro'):
        print(f'  [Bing] 获取到摘要', flush=True)
    if bing_info.get('open_time'):
        print(f'  [Bing] 获取到开放时间', flush=True)
    if bing_info.get('ticket_info'):
        print(f'  [Bing] 获取到门票信息', flush=True)
    if bing_info.get('phone'):
        print(f'  [Bing] 获取到电话', flush=True)
    if bing_info.get('website'):
        print(f'  [Bing] 获取到官网', flush=True)

    # 百度百科数据优先覆盖
    if baidu_info.get('intro'):
        final['intro_short'] = baidu_info['intro']
    if baidu_info.get('open_time'):
        final['open_time'] = baidu_info['open_time']
    if baidu_info.get('ticket_info'):
        final['ticket_info'] = baidu_info['ticket_info']
    if baidu_info.get('phone'):
        final['phone'] = baidu_info['phone']
    if baidu_info.get('website'):
        final['website'] = baidu_info['website']
    if baidu_info.get('photo_url'):
        final['photo_url'] = baidu_info['photo_url']

    # Bing 数据兜底（仅在字段为空时填充）
    if not final['intro_short'] and bing_info.get('intro'):
        final['intro_short'] = bing_info['intro']
    if not final['open_time'] and bing_info.get('open_time'):
        final['open_time'] = bing_info['open_time']
    if not final['ticket_info'] and bing_info.get('ticket_info'):
        final['ticket_info'] = bing_info['ticket_info']
    if not final['phone'] and bing_info.get('phone'):
        final['phone'] = bing_info['phone']
    if not final['website'] and bing_info.get('website'):
        final['website'] = bing_info['website']

    # Step 3: Amap 兜底图片和电话
    if not final['photo_url']:
        amap_info = search_amap_poi(name)
        if amap_info.get('photo_url'):
            final['photo_url'] = amap_info['photo_url']
            final['photo_source'] = 'amap'
            print(f'  [Amap] 获取到图片', flush=True)
        if amap_info.get('phone') and not final['phone']:
            final['phone'] = amap_info['phone']
            print(f'  [Amap] 获取到电话: {amap_info["phone"]}', flush=True)

    # Step 4: 规则生成兜底（仅填充仍为空的字段，不覆盖已有数据）
    rules = generate_by_rules(museum)
    if not final['intro_short']:
        final['intro_short'] = rules['intro_short']
        print(f'  [规则生成] 简介', flush=True)
    if not final['open_time']:
        final['open_time'] = rules['open_time']
        print(f'  [规则生成] 开放时间', flush=True)
    if not final['ticket_info']:
        final['ticket_info'] = rules['ticket_info']
        print(f'  [规则生成] 门票信息', flush=True)

    # 写入博物馆字段
    museum['intro_short'] = final['intro_short']
    museum['open_time'] = final['open_time']
    museum['ticket_info'] = final['ticket_info']
    museum['website'] = final['website'] or museum.get('website', '')
    museum['phone'] = final['phone']
    museum['photo_url'] = final['photo_url']
    if final.get('photo_source'):
        museum['photo_source'] = final['photo_source']

    # 更新数据来源标记
    museum['data_source'] = 'formal_catalog+auto_fill'
    museum['last_updated'] = '2026-06-06'

    return True


def main():
    # 读取 museums.json
    with open(MUSEUMS_FILE, 'r', encoding='utf-8') as f:
        museums = json.load(f)

    # 备份
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)
    print(f'备份已保存: {BACKUP_FILE}', flush=True)

    # 筛选 formal_catalog 条目
    formal_museums = [m for m in museums if m.get('data_source') == 'formal_catalog']
    print(f'\n共 {len(formal_museums)} 个 formal_catalog 博物馆需要填充', flush=True)
    print('=' * 60, flush=True)

    success = 0
    for i, museum in enumerate(formal_museums):
        try:
            fill_museum(museum, i + 1, len(formal_museums))
            success += 1
            time.sleep(REQUEST_DELAY)  # 礼貌爬虫间隔
        except Exception as e:
            print(f'  [错误] {e}', flush=True)

    # 保存
    with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)

    print(f'\n{"=" * 60}', flush=True)
    print(f'填充完成！成功: {success}/{len(formal_museums)}', flush=True)
    print(f'数据已保存到: {MUSEUMS_FILE}', flush=True)


if __name__ == '__main__':
    main()
