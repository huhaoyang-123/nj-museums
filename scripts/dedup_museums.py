#!/usr/bin/env python3
"""
比较 new_museums_candidates.json 与 museums.json，
1. 删除名称完全一致的条目
2. 提取核心名称（剥离公共前缀后缀）后比较相似度
3. 检测子串包含关系
"""

import json
import os
import re
import sys
from difflib import SequenceMatcher

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

MUSEUMS_FILE = os.path.join(DATA_DIR, 'museums.json')
CANDIDATES_FILE = os.path.join(DATA_DIR, 'new_museums_candidates.json')
# 如果原始文件不存在，使用去重后的文件
if not os.path.exists(CANDIDATES_FILE):
    CANDIDATES_FILE = os.path.join(DATA_DIR, 'new_museums_candidates_deduped.json')
    if not os.path.exists(CANDIDATES_FILE):
        raise FileNotFoundError('找不到候选文件')
OUTPUT_FILE = os.path.join(DATA_DIR, 'new_museums_candidates_deduped.json')
# 如果输入就是 deduped 文件，输出到不同文件避免冲突
if CANDIDATES_FILE.endswith('new_museums_candidates_deduped.json'):
    OUTPUT_FILE = os.path.join(DATA_DIR, 'new_museums_candidates_deduped_v2.json')
REPORT_FILE = os.path.join(DATA_DIR, 'similar_name_report.txt')

# 原始名称相似度阈值
RAW_SIMILARITY_THRESHOLD = 0.80
# 核心名称相似度阈值（剥离城市前缀和机构后缀后）
CORE_SIMILARITY_THRESHOLD = 0.72
# 子串匹配阈值（一个核心是另一个核心的至少这么多比例）
SUBSTR_RATIO_THRESHOLD = 0.70


# 常见的城市/区域前缀
CITY_PREFIXES = [
    '南京市', '南京', '中国南京', '中国南京市',
    '中国', '江苏省', '江苏',
    '南京中国', '金陵',
]

# 常见的机构类型后缀
VENUE_SUFFIXES = [
    '博物馆', '艺术博物馆', '历史博物馆',
    '艺术馆', '美术馆', '展览馆', '科技馆',
    '纪念馆', '陈列馆', '展示馆', '文化馆',
    '故居', '旧居', '遗址',
    '自然科学博物馆', '自然博物馆',
    '地质博物馆', '地质公园博物馆',
    '国家地质公园博物馆',
]

# 人工确认保留：虽然名称相似但实际是不同博物馆
KEEP_SIMILAR_NAMES = {
    '南京雨花茶博物馆',         # ≠ 南京雨花石博物馆
    '江宁博物馆',               # ≠ 江宁织造博物馆
    '六朝荟博物馆',             # ≠ 六朝博物馆
    '六朝荟茶博物馆',           # ≠ 六朝博物馆
    '横梁雨花石博物馆',         # 横梁镇独立小博物馆
    '雨花石地质博物馆',         # 偏地质专题，可能不同
    '六合国家地质公园博物馆',    # 地质公园博物馆 ≠ 六合区综合博物馆
}


def normalize(text):
    """基础规范化：去空格、转小写"""
    t = text.strip()
    t = re.sub(r'\s+', '', t)
    return t.lower()


def strip_prefix(name, prefixes):
    """剥离第一个匹配的前缀，返回 (剥离后的名称, 被剥离的前缀)"""
    n = normalize(name)
    for p in sorted(prefixes, key=len, reverse=True):
        pn = normalize(p)
        if n.startswith(pn):
            return name[len(p):], p
    return name, ''


def strip_suffix(name, suffixes):
    """剥离第一个匹配的后缀"""
    n = normalize(name)
    for s in sorted(suffixes, key=len, reverse=True):
        sn = normalize(s)
        if n.endswith(sn) and len(n) > len(sn) + 1:
            return name[:len(name)-len(s)], s
    return name, ''


def extract_core(name):
    """提取核心名称：剥离城市前缀和机构后缀"""
    name, _pref = strip_prefix(name, CITY_PREFIXES)
    name, _suff = strip_suffix(name, VENUE_SUFFIXES)
    return name.strip()


def is_similar(candidate_name, existing_name):
    """
    判断候选名称与已有名称是否高度相似（同一博物馆）
    返回 (is_match, match_type, ratio)
    """
    c_norm = normalize(candidate_name)
    e_norm = normalize(existing_name)

    # 策略1：原始名称相似度
    raw_ratio = SequenceMatcher(None, c_norm, e_norm).ratio()
    if raw_ratio >= RAW_SIMILARITY_THRESHOLD:
        return True, 'raw', round(raw_ratio, 4)

    # 策略2：核心名称相似度
    c_core = normalize(extract_core(candidate_name))
    e_core = normalize(extract_core(existing_name))

    if c_core and e_core and len(c_core) >= 2 and len(e_core) >= 2:
        core_ratio = SequenceMatcher(None, c_core, e_core).ratio()
        if core_ratio >= CORE_SIMILARITY_THRESHOLD:
            return True, 'core', round(core_ratio, 4)

        # 策略3：子串包含关系
        if len(c_core) >= 2 and len(e_core) >= 2 and c_core != e_core:
            shorter = c_core if len(c_core) <= len(e_core) else e_core
            longer = e_core if len(c_core) <= len(e_core) else c_core
            if len(shorter) > 0:
                substr_ratio = len(shorter) / len(longer)
                if substr_ratio >= SUBSTR_RATIO_THRESHOLD and shorter in longer:
                    return True, 'substr', round(substr_ratio, 4)

    return False, '', 0.0


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    museums = load_json(MUSEUMS_FILE)
    candidates = load_json(CANDIDATES_FILE)

    existing_names = {}
    for m in museums:
        name = m['name']
        existing_names[normalize(name)] = name
        for alias in m.get('alias', []):
            existing_names[normalize(alias)] = m['name']

    print(f"museums.json 中有 {len(museums)} 个博物馆")
    print(f"（含别名）共 {len(existing_names)} 个名称")
    print(f"new_museums_candidates.json 中有 {len(candidates)} 个候选\n")

    # ---- 第1步：完全匹配 ----
    exact_matches = []
    remaining = []
    for c in candidates:
        if c['name'] in existing_names or normalize(c['name']) in existing_names:
            exact_matches.append(c['name'])
        else:
            remaining.append(c)

    print(f"=== 第1步：名称完全一致，已删除 {len(exact_matches)} 个 ===")
    for name in exact_matches:
        print(f"  [删除] {name}")

    # ---- 第2步：多维相似度匹配 ----
    similar_matches = []
    truly_new = []

    for c in remaining:
        c_name = c['name']
        found_similar = None

        for norm_name, original_name in existing_names.items():
            if normalize(c_name) == norm_name:
                continue

            is_match, match_type, ratio = is_similar(c_name, original_name)
            if is_match:
                found_similar = {
                    'candidate_name': c_name,
                    'existing_name': original_name,
                    'match_type': match_type,
                    'similarity': ratio,
                }
                break

        if found_similar:
            similar_matches.append(found_similar)
        else:
            truly_new.append(c)

    # ---- 第3步：人工确认规则 ----
    auto_deleted_similar = []
    kept_similar = []
    final_candidates = []

    for c in truly_new:
        final_candidates.append(c)

    for sm in similar_matches:
        c_name = sm['candidate_name']
        if c_name in KEEP_SIMILAR_NAMES:
            kept_similar.append(c_name)
            for c in remaining:
                if c['name'] == c_name:
                    final_candidates.append(c)
                    break
        else:
            auto_deleted_similar.append(c_name)

    # ---- 输出结果 ----
    print(f"\n=== 第2步：多维相似度检测，共 {len(similar_matches)} 组 ===")
    if similar_matches:
        for sm in similar_matches:
            tag = "[保留]" if sm['candidate_name'] in KEEP_SIMILAR_NAMES else "[删除]"
            print(f"  {tag} ({sm['match_type']}={sm['similarity']}) 候选「{sm['candidate_name']}」↔ 已有「{sm['existing_name']}」")

    print(f"\n   保留（确认不同）: {len(kept_similar)} 个")
    print(f"   删除（确认重复）: {len(auto_deleted_similar)} 个")

    save_json(OUTPUT_FILE, final_candidates)
    print(f"\n清洗后剩余 {len(final_candidates)} 个候选，已保存至:")
    print(f"  {OUTPUT_FILE}")

    # ---- 生成报告 ----
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("博物馆候选去重报告")
    report_lines.append("=" * 70)
    report_lines.append(f"原始候选数: {len(candidates)}")
    report_lines.append(f"完全一致(已删除): {len(exact_matches)}")
    report_lines.append(f"多维相似检测: {len(similar_matches)}")
    report_lines.append(f"  - 人工确认删除: {len(auto_deleted_similar)}")
    report_lines.append(f"  - 人工确认保留: {len(kept_similar)}")
    report_lines.append(f"最终新候选: {len(final_candidates)}")
    report_lines.append("")
    report_lines.append(f"检测策略:")
    report_lines.append(f"  - 原始名称相似度 >= {RAW_SIMILARITY_THRESHOLD}")
    report_lines.append(f"  - 核心名称相似度 >= {CORE_SIMILARITY_THRESHOLD}")
    report_lines.append(f"  - 核心名称子串包含 >= {SUBSTR_RATIO_THRESHOLD}")
    report_lines.append("")

    if exact_matches:
        report_lines.append("-" * 70)
        report_lines.append(f"一、名称完全一致（已自动删除，共 {len(exact_matches)} 个）")
        report_lines.append("-" * 70)
        for name in exact_matches:
            report_lines.append(f"  - {name}")
        report_lines.append("")

    if similar_matches:
        report_lines.append("-" * 70)
        report_lines.append(f"二、多维相似度检测结果（共 {len(similar_matches)} 组）")
        report_lines.append("-" * 70)
        report_lines.append("  [已删除]：")
        for sm in similar_matches:
            if sm['candidate_name'] not in KEEP_SIMILAR_NAMES:
                report_lines.append(
                    f"    - ({sm['match_type']}={sm['similarity']}) "
                    f"候选「{sm['candidate_name']}」↔ 已有「{sm['existing_name']}」"
                )
        report_lines.append("")
        report_lines.append("  [已保留]：")
        for sm in similar_matches:
            if sm['candidate_name'] in KEEP_SIMILAR_NAMES:
                report_lines.append(
                    f"    - ({sm['match_type']}={sm['similarity']}) "
                    f"候选「{sm['candidate_name']}」↔ 已有「{sm['existing_name']}」"
                    f"，原因：判断为不同博物馆"
                )
        report_lines.append("")

    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append(f"三、最终新候选（共 {len(final_candidates)} 个）")
    report_lines.append("-" * 70)
    for c in final_candidates:
        report_lines.append(f"  - {c['name']}")

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n详细报告已保存至:")
    print(f"  {REPORT_FILE}")


if __name__ == '__main__':
    main()
