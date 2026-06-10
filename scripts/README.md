# Scripts 目录说明

本目录包含博物馆数据维护脚本，用于发现新场馆、去重、补充元数据、修正坐标、爬取文物、获取新闻及数据质量检查（共 10 个脚本）。

## 脚本列表

### 1. discover_new_museums.py
**用途**：通过高德 POI API 搜索南京地区博物馆/美术馆/展览馆/科技馆/纪念馆/名人故居

**功能**：
- 按关键词（博物馆、美术馆、展览馆、科技馆、纪念馆、名人故居、陈列馆、艺术馆、旧址纪念馆）分页搜索高德 POI
- 与现有 `museums.json` 交叉比对，自动排除名称含无关关键词的 POI（超市、酒店、餐厅等）
- 生成两个输出文件：
  - `data/new_museums_candidates.json` — 数据库中不存在的新场馆候选
  - `data/existing_museums_updates.json` — 已有博物馆可补充的字段（电话、地址等）

**运行命令**：
```bash
python scripts/discover_new_museums.py
```

**依赖**：`.env` 中配置 `AMAP_KEY`

---

### 2. dedup_museums.py
**用途**：比较 `new_museums_candidates.json` 与 `museums.json`，去除重复场馆

**功能**：
- 删除名称完全一致的条目
- 剥离城市前缀（南京、江苏省等）和机构后缀（博物馆、美术馆等）后计算核心名称相似度
- 检测子串包含关系
- 设有白名单 `KEEP_SIMILAR_NAMES`，保留名称相似但实际不同的博物馆
- 生成 `data/new_museums_candidates_deduped.json`

**运行命令**：
```bash
python scripts/dedup_museums.py
```

---

### 3. fill_museum_metadata.py
**用途**：为博物馆批量补充基础元数据

**功能**：
- 通过百度百科抓取开放时间、门票信息、电话、官网、摘要
- Bing 搜索引擎兜底获取信息
- 高德 POI 搜索兜底获取图片、电话
- 规则生成：完全搜不到时根据名称/类别/地区生成合理描述

**填充字段**：`intro_short`、`open_time`、`ticket_info`、`website`、`wechat`、`phone`、`photo_url`、`photo_source`

**运行命令**：
```bash
python scripts/fill_museum_metadata.py
```

**依赖**：网络连接，部分功能需要 `AMAP_KEY`

---

### 4. fix_museum_coordinates_poi.py
**用途**：通过高德 POI 名称搜索获取精确坐标

**功能**：
- 用博物馆名称在高德 POI API 搜索
- 仅在 POI 名称精确匹配或高度相似时才采用
- 距离校验：新坐标与原坐标偏差超过 5km 时拒绝，防止张冠李戴
- 内置名称修正映射表 `NAME_FIX_MAP`（如"国民政府主席官邸旧址" → "美龄宫"）
- 匹配失败时保持原坐标不变

**运行命令**：
```bash
python scripts/fix_museum_coordinates_poi.py
```

**依赖**：`.env` 中配置 `AMAP_KEY`

---

### 5. fill_candidates_address.py
**用途**：为 `new_museums_candidates_deduped.json` 补充详细地址信息

**功能**：
- 通过高德 POI 搜索获取 `formatted_address`、完整地址
- 仅补充地址相关字段，不动坐标等其他信息
- 自动备份原文件

**运行命令**：
```bash
python scripts/fill_candidates_address.py
```

**依赖**：`.env` 中配置 `AMAP_KEY`

---

### 6. scrape_collections.py
**用途**：为缺失文物数据的博物馆自动搜索并填充展品照片信息

**功能**：
- 多源搜索（百度百科 → 博物馆官网 → 通用搜索）
- 支持限流、并发控制、自动备份
- 支持命令行参数：`--limit`、`--id`、`--dry-run`（预览模式）

**运行命令**：
```bash
python scripts/scrape_collections.py              # 处理所有缺失文物的博物馆
python scripts/scrape_collections.py --limit 10   # 只处理前 10 个
python scripts/scrape_collections.py --id 18,20   # 只处理指定 ID
python scripts/scrape_collections.py --dry-run    # 预览模式，不写文件
```

**依赖**：`requests`、`beautifulsoup4`

---

### 7. repair_collections.py
**用途**：修复与清理博物馆文物数据

**功能**：
- 修复损坏的文物图片链接
- 清理批量爬取产生的低质量数据（重复图片、无效文本等）
- 为优先博物馆补充验证过的高质量文物数据

**运行命令**：
```bash
python scripts/repair_collections.py
```

---

### 8. crawl_museum_news.py
**用途**：从博物馆官网首页自动抓取最新展览、活动、新闻等动态信息

**功能**：
- 遍历 `museums.json` 中有 `website` 字段的博物馆
- 用 `requests` + `BeautifulSoup` 解析官网首页 HTML
- 通过中英文关键词（展览、活动、新闻、特展、讲座、event 等）匹配新闻/展览链接
- 自动排除导航链接（首页、关于我们、版权声明等）
- 跳过管理后台/预约系统类网站（`njmuseumadmin.com` 等）
- 自动去重、每馆限制最多 6 条
- 写入 `museums.json` 的 `news` 字段

**运行命令**：
```bash
python scripts/crawl_museum_news.py
```

**依赖**：`requests`、`beautifulsoup4`

**适用场景**：HTML 直出的静态官网。JS 渲染的网站需配合 firecrawl 等工具。

---

### 9. crawl_news_quick.py
**用途**：精简版新闻爬虫，聚焦有独立官网的重点博物馆

**功能**：
- 只处理 `TARGET_IDS` 中列出的 24 个重点博物馆
- 跳过管理后台、预约系统等不适合爬取的域名
- 跳过已有 `news` 数据的博物馆，避免重复爬取
- 更宽松的链接提取策略（不限关键词），抓取首页所有非导航链接
- 写入 `museums.json` 的 `news` 字段

**运行命令**：
```bash
python scripts/crawl_news_quick.py
```

**依赖**：`requests`、`beautifulsoup4`

**与 crawl_museum_news.py 的区别**：更精简更快速，不做关键词过滤，适合对已筛选过的重点博物馆批量采集。

---

### 10. update_news_data.py
**用途**：将通过 firecrawl 等工具采集到的精选新闻/展览数据写入 `museums.json`

**功能**：
- 内置 `NEWS_DATA` 字典，按博物馆 ID 组织精选新闻
- 每条数据包含 `title`（标题）、`desc`（描述）、`link`（链接）、`date`（日期）
- 自动更新对应博物馆的 `news` 字段和 `last_updated` 时间戳
- 覆盖已有 news 数据

**运行命令**：
```bash
python scripts/update_news_data.py
```

**数据格式**：
```python
NEWS_DATA = {
    1: [  # 博物馆 ID
        {
            "title": "展览/活动标题",
            "desc": "简短描述",
            "link": "https://...",
            "date": "2026-06-09"
        },
    ],
}
```

---

### 11. check_status.py
**用途**：快速查看博物馆文物覆盖情况

**功能**：
- 统计有文物的博物馆数量和占比
- 列出文物较少的博物馆（<5 件）
- 列出完全无文物的博物馆

**运行命令**：
```bash
python scripts/check_status.py
```

---

## 使用注意事项

1. **运行前备份**：建议在运行任何脚本前备份 `data/museums.json`
2. **API 密钥**：坐标和地址脚本需要高德地图 API 密钥，确保 `.env` 中配置了 `AMAP_KEY`
3. **网络连接**：调用外部 API 的脚本需要稳定的网络连接
4. **脚本执行顺序**：新场馆处理建议按以下顺序执行：
   - `discover_new_museums.py` → `dedup_museums.py` → `fill_candidates_address.py`

## 依赖环境

```bash
pip install -r requirements.txt
```
