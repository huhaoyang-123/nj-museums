# Scripts 目录说明

本目录包含博物馆数据维护脚本，用于数据更新和修复。

## 脚本列表

### 1. update_museum_coordinates.py
**用途**：通过高德地图API更新博物馆的经纬度坐标

**功能**：
- 根据博物馆地址调用高德地理编码API
- 更新museums.json中的lat和lng字段
- 标记坐标数据来源

**使用场景**：
- 新增博物馆需要补充坐标
- 坐标数据不准确需要修正
- 地址变更后需要更新坐标

**运行命令**：
```bash
python scripts/update_museum_coordinates.py
```

---

### 2. update_museums_address.py
**用途**：更新博物馆的地址信息

**功能**：
- 从高德POI API获取准确的地址信息
- 更新museums.json中的address字段
- 补充formatted_address字段

**使用场景**：
- 地址信息不完整或不准确
- 需要标准化地址格式
- 新增博物馆需要补充地址

**运行命令**：
```bash
python scripts/update_museums_address.py
```

---

### 3. update_reserve_links.py
**用途**：更新博物馆的预约链接和官网信息

**功能**：
- 补充官方预约链接
- 更新官方网站URL
- 修复错误的预约链接

**使用场景**：
- 预约链接失效或错误
- 新增博物馆需要补充预约信息
- 官网地址变更

**运行命令**：
```bash
python scripts/update_reserve_links.py
```

---

### 4. reindex_museums.py
**用途**：重新索引博物馆ID

**功能**：
- 重新分配博物馆ID（按顺序）
- 确保ID连续无缺失
- 修复ID重复或错乱问题

**使用场景**：
- 删除博物馆后ID不连续
- ID数据混乱需要重建
- 数据迁移后需要重新索引

**运行命令**：
```bash
python scripts/reindex_museums.py
```

---

## 使用注意事项

1. **运行前备份**：建议在运行任何脚本前备份 `data/museums.json`
2. **API密钥**：部分脚本需要高德地图API密钥，请确保 `.env` 文件中配置了 `AMAP_KEY`
3. **网络连接**：调用高德API的脚本需要稳定的网络连接
4. **数据验证**：脚本运行后建议检查数据准确性

## 依赖环境

所有脚本依赖以下Python包：
- `requests` - HTTP请求
- `python-dotenv` - 环境变量加载

安装依赖：
```bash
pip install -r requirements.txt
```

## 维护建议

- 定期检查预约链接的有效性（建议每月一次）
- 新增博物馆时先运行 `update_museums_address.py` 获取准确地址
- 地址变更后运行 `update_museum_coordinates.py` 更新坐标
- 图片失效时运行 `apply_amap_photos.py` 重新获取