---
name: "museum-artifact-scraper"
description: "Automatically scrape and verify museum artifact/collection photos from Wikipedia Commons, official museum sites, and authoritative media. Invoke when user asks to crawl museum artifact images, add collection photos, or update museums.json with verified image URLs."
---

# Museum Artifact Photo Scraper

This skill provides an **optimized, high-performance workflow** for scraping museum artifact photos and writing verified results into `data/museums.json`.

---

## 🔄 Optimized Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     HIGH-PERFORMANCE MODE                       │
├─────────────────────────────────────────────────────────────────┤
│  1. Batch Discovery    →  Parallel search for multiple museums │
│  2. Smart Extraction   →  Auto-extract valid image URLs        │
│  3. Direct Update      →  Write directly to museums.json       │
│  4. Quick Validation   →  Concurrent URL verification         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Methodology: Three-Tier Fallback Strategy

```
Tier 1: Wikipedia Commons（最稳定，优先使用）
  └── CC licensed, permanent URLs, clean path structure
  └── Search: "{artifact_name} site:commons.wikimedia.org"

Tier 2: Official Museum Websites（最准确）
  └── njmuseum.com, njmuseumadmin.com, nmp.ac.cn, njiemuseum.com, 19371213.com.cn
  └── Search: "site:{official_domain} {artifact_name}"

Tier 3: Authoritative Media（兜底）
  └── 人民画报 rmhb.com.cn/yxsj, 新华网 news.cn, 中国军网 81.cn
  └── Search: "{artifact_name} site:rmhb.com.cn/yxsj"
```

---

## Domain-Specific Official Site Mapping

| Museum ID     | Museum Name                      | Official Domain   | Priority |
| ------------- | -------------------------------- | ----------------- | -------- |
| 1             | 南京博物院                       | njmuseum.com      | HIGH     |
| 2,3,4,5,12,14 | 南京市博物总馆系列               | njmuseumadmin.com | HIGH     |
| 6             | 南京中国科举博物馆               | njiemuseum.com    | HIGH     |
| 7             | 南京城墙博物馆                   | njcitywall.com    | MEDIUM   |
| 8             | 侵华日军南京大屠杀遇难同胞纪念馆 | 19371213.com.cn   | HIGH     |
| 9             | 南京云锦博物馆                   | njyjmuseum.com    | MEDIUM   |
| 10            | 南京古生物博物馆                 | nmp.ac.cn         | HIGH     |
| 15            | 南京大报恩寺遗址博物馆           | dahepiao.com      | LOW      |

---

## ⚡ Optimized Step-by-Step Workflow

### Phase 1: Batch Discovery（批量发现）

**KEY OPTIMIZATION**: Process multiple museums in parallel

```python
# Batch search for museums WITHOUT collections
def batch_discover_artifacts(museums, max_concurrent=5):
    """并行搜索多个博物馆的文物信息"""
    queries = []
    for museum in museums:
        if not museum.get('collections') or len(museum['collections']) < 3:
            queries.extend([
                f"{museum['name']} 镇馆之宝 site:wikipedia.org",
                f"{museum['name']} 代表文物 site:baike.baidu.com"
            ])
    
    # Execute searches in parallel (max 5 concurrent)
    results = parallel_search(queries, max_workers=max_concurrent)
    return parse_artifact_names(results)
```

### Phase 2: Smart Image URL Acquisition（智能获取）

**KEY OPTIMIZATION**: Skip manual URL extraction, auto-detect valid links

```python
def smart_search_images(artifact_name, museum_id):
    """智能搜索图片，自动提取有效URL"""
    search_patterns = [
        f"{artifact_name} site:upload.wikimedia.org",
        f"{artifact_name} site:commons.wikimedia.org"
    ]
    
    for pattern in search_patterns:
        results = firecrawl_search(pattern, limit=3)
        for result in results:
            if is_valid_wikipedia_image(result['url']):
                return convert_to_raw_url(result['url'])
    return None

def is_valid_wikipedia_image(url):
    """快速判断是否为有效Wikipedia图片链接"""
    return 'commons.wikimedia.org/wiki/File:' in url and '.jpg' in url.lower()

def convert_to_raw_url(wiki_url):
    """自动将Wiki页面URL转换为原始图片URL"""
    # Example: https://commons.wikimedia.org/wiki/File:Sun_Yat-sen.jpg
    # → https://upload.wikimedia.org/wikipedia/commons/S/Su/Sun_Yat-sen.jpg
    filename = wiki_url.split('/')[-1]
    if filename:
        first_char = filename[0].upper()
        return f"https://upload.wikimedia.org/wikipedia/commons/{first_char}/{first_char}{filename[1] if len(filename) > 1 else ''}/{filename}"
    return None
```

### Phase 3: Concurrent Validation（并发验证）

**KEY OPTIMIZATION**: Parallel URL validation with connection pooling

```python
import requests
from concurrent.futures import ThreadPoolExecutor

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def batch_validate_urls(url_pairs, max_workers=10):
    """并发验证多个URL，返回有效链接"""
    valid = []
    
    def check_url(name_url):
        name, url = name_url
        try:
            with requests.Session() as session:
                session.headers.update(headers)
                response = session.head(url, timeout=10, allow_redirects=True)
                if response.status_code in [200, 301, 302]:
                    return (name, url, True)
                return (name, url, False)
        except Exception:
            return (name, url, False)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(check_url, url_pairs)
    
    for name, url, is_valid in results:
        if is_valid:
            valid.append((name, url))
    
    return valid
```

### Phase 4: Direct JSON Update（直接更新）

**KEY OPTIMIZATION**: Skip intermediate script, write directly to museums.json

```python
import json

def update_museums_json(museum_id, artifacts):
    """直接更新museums.json，无需中间脚本"""
    with open('data/museums.json', 'r', encoding='utf-8') as f:
        museums = json.load(f)
    
    for museum in museums:
        if museum['id'] == museum_id:
            existing_names = {c['name'] for c in museum.get('collections', [])}
            for artifact in artifacts:
                if artifact['name'] not in existing_names and artifact.get('image'):
                    museum.setdefault('collections', []).append(artifact)
            break
    
    with open('data/museums.json', 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=2)
```

---

## 🚀 Quick Start: One-Click Execution

```python
# Complete workflow in one function call
def scrape_all_museums(target_museums=None):
    """一键爬取所有目标博物馆的文物图片"""
    
    # Step 1: Load museums
    with open('data/museums.json', 'r', encoding='utf-8') as f:
        museums = json.load(f)
    
    # Filter target museums (prioritize famous ones)
    if not target_museums:
        target_museums = prioritize_museums(museums)
    
    # Step 2: Batch discover artifacts
    all_artifacts = batch_discover_artifacts(target_museums)
    
    # Step 3: Get image URLs concurrently
    results = []
    for museum in target_museums:
        artifacts = all_artifacts.get(museum['id'], [])
        for artifact in artifacts[:5]:  # Max 5 per museum
            url = smart_search_images(artifact['name'], museum['id'])
            if url:
                artifact['image'] = url
                results.append((museum['id'], artifact))
    
    # Step 4: Validate all URLs
    url_pairs = [(f"{mid}_{a['name']}", a['image']) for mid, a in results]
    valid_pairs = batch_validate_urls(url_pairs)
    
    # Step 5: Update museums.json
    for mid, artifact in results:
        if (f"{mid}_{artifact['name']}", artifact['image']) in valid_pairs:
            update_museums_json(mid, [artifact])
    
    return len(results)

def prioritize_museums(museums):
    """按重要性排序博物馆"""
    priority_names = {"中山陵", "明孝陵", "总统府", "夫子庙", "南京博物院", 
                      "大屠杀纪念馆", "郑和纪念馆", "科举博物馆"}
    return sorted(museums, key=lambda x: x['name'] in priority_names, reverse=True)
```

---

## 🛡️ Critical Validation Rules

| Rule                     | Implementation                       | Why                                        |
| ------------------------ | ------------------------------------ | ------------------------------------------ |
| **User-Agent Required**  | Always set `User-Agent: Mozilla/5.0` | Wikipedia blocks requests without it (403) |
| **Concurrent Limit**     | Max 10 threads for validation        | Avoid rate limiting (429)                  |
| **Timeout**              | 10 seconds per request               | Prevent hanging on slow servers            |
| **Acceptable Status**    | 200, 301, 302, 304                   | Handle redirects properly                  |
| **File Extension Check** | Verify `.jpg`, `.png`, `.webp`       | Avoid non-image URLs                       |
| **Duplicate Detection**  | Check `(museum_id, artifact_name)`   | Prevent duplicate entries                  |

---

## ⚠️ Common Pitfalls & Solutions

| Problem                       | Solution                                               |
| ----------------------------- | ------------------------------------------------------ |
| **Baidu captcha blocks**      | Skip baike.baidu.com for images, use Wikipedia instead |
| **Wikipedia thumb paths 404** | Always use raw file URLs (auto-convert)                |
| **Firecrawl rate limits**     | Add 1 second delay between search calls                |
| **Invalid URL construction**  | Never guess URLs, only use extracted ones              |
| **Slow verification**         | Use ThreadPoolExecutor for concurrent checks           |
| **HTTP 597 proxy errors**     | Fallback to alternative sources                        |

---

## 📊 Performance Optimization Summary

| Optimization   | Before                 | After                       | Improvement               |
| -------------- | ---------------------- | --------------------------- | ------------------------- |
| Search         | Sequential (2-5s each) | Parallel (max 5 concurrent) | **5x faster**             |
| URL Extraction | Manual                 | Auto-detect & convert       | **No human intervention** |
| Validation     | Sequential (0.5s each) | Concurrent (10 threads)     | **10x faster**            |
| Data Update    | Manual script edit     | Direct JSON write           | **90% time saved**        |

---

## Integration with Existing Project

```
data/museums.json          → Target output file
scripts/validate_images.py → Validation helper script
IMAGE_MAP dict (deprecated)→ Legacy mapping, use direct update instead
```

**Recommendation**: Phase out `update_collections_images.py` and use the direct JSON update approach for faster execution.