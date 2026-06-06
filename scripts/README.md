# Scripts 目录说明

本目录包含博物馆数据维护脚本。

## 脚本列表

### 1. update_museum_coordinates.py
**用途**：通过高德地图API更新博物馆的经纬度坐标

**功能**：
- 根据博物馆地址调用高德地理编码API
- 更新museums.json中的lat和lng字段

**运行命令**：
```bash
python scripts/update_museum_coordinates.py
```

---

### 2. update_museums_address.py
**用途**：更新博物馆的地址信息

**功能**：
- 从高德POI API获取准确的地址信息
- 补充formatted_address字段

**运行命令**：
```bash
python scripts/update_museums_address.py
```

---

### 3. update_reserve_links.py
**用途**：批量更新博物馆的预约链接和官网信息

**运行命令**：
```bash
python scripts/update_reserve_links.py
```

---

### 4. update_collections_images.py
**用途**：为博物馆文物补充图片URL，更新museums.json

**功能**：
- 根据IMAGE_MAP字典为文物匹配图片链接
- 通过extra_artifacts字典为无文物博物馆添加基础文物

**运行命令**：
```bash
python scripts/update_collections_images.py
```

---

### 5. check_status.py
**用途**：快速查看博物馆文物覆盖情况

**功能**：
- 列出文物较少的博物馆（<5件）
- 列出完全无文物的博物馆

**运行命令**：
```bash
python scripts/check_status.py
```

---

### 6. validate_images.py
**用途**：验证所有文物图片链接的有效性

**运行命令**：
```bash
python scripts/validate_images.py
```

---

## 使用注意事项

1. **运行前备份**：建议在运行任何脚本前备份 `data/museums.json`
2. **API密钥**：坐标和地址脚本需要高德地图API密钥，确保 `.env` 中配置了 `AMAP_KEY`
3. **网络连接**：调用外部API的脚本需要稳定的网络连接

## 依赖环境

```bash
pip install -r requirements.txt
```
