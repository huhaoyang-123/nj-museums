# 博物金陵 - 南京博物馆导览系统

基于 Flask 的南京博物馆信息导览 Web 应用，集成 AI 智能对话，提供 82 座博物馆的查询、筛选、地图导航与代表文物浏览服务。

## 项目结构

```
EL.demo1.1/
├── app.py                          # Flask 主入口（路由、AI 对话、博物馆数据 API）
├── requirements.txt                # Python 依赖
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略规则
│
├── data/                           # 数据层
│   └── museums.json                # 82 座博物馆的完整数据（含代表文物）
│
├── services/                       # 服务层
│   └── museum_service.py           # 博物馆数据加载与转换
│
├── templates/                      # 前端模板
│   ├── index.html                  # 主页（Hero + 博物馆卡片 + 地图 + 聊天面板）
│   ├── collections.html            # 代表文物详情页（骨架屏 + 懒加载 + 淡入动画）
│   └── chat.html                   # AI 导览独立页面
│
├── scripts/                        # 数据维护脚本
│   ├── add_collections.py          # 添加博物馆代表文物数据
│   ├── update_collections_images.py # 更新文物图片为真实 URL
│   ├── update_museum_coordinates.py # 通过高德 API 更新经纬度坐标
│   ├── update_museums_address.py   # 更新博物馆地址信息
│   ├── update_reserve_links.py     # 更新预约链接与官网
│   ├── reindex_museums.py          # 重新索引博物馆 ID
│   └── README.md                   # 脚本使用说明
│
└── .vscode/                        # VS Code 调试配置
    └── launch.json
```

## 核心功能

### 1. 博物馆信息展示
- **卡片浏览**：82 座博物馆的网格/列表展示，支持搜索与多层筛选
- **筛选维度**：区域（9 区）、分类（历史人文/艺术文化/科学教育/专题特色）、费用（免费/付费）
- **详情弹窗**：博物馆名称、地址、开放时间、门票、联系电话、详细介绍
- **分页浏览**：每页 12 座，支持页码跳转

### 2. 代表文物浏览
- **文物展示**：每个博物馆的镇馆之宝/代表文物，含名称、年代、描述
- **真实图片**：文物图片来自南京博物院官网、人民画报等权威来源
- **独立页面**：`/museum/<id>/collections` 查看完整的文物列表
- **加载优化**：骨架屏动画、淡入过渡、前 4 张优先加载、后续图片懒加载、异步解码

### 3. 地图导航
- **高德地图集成**：南京市行政边界、分类彩色标记、博物馆分布可视化
- **分类筛选**：地图侧面板支持按类型和费用筛选显示
- **边界限制**：地图拖拽和缩放限制在南京市范围内
- **信息窗口**：点击标记弹窗显示博物馆要点及快捷操作

### 4. AI 智能导览
- **AI 模型**：DeepSeek Chat API，基于博物馆数据库回答
- **侧边面板**：主页内的聊天面板，支持快捷提问
- **智能匹配**：AI 回复中自动匹配博物馆名称，生成"查看详情""预约""地图"按钮
- **独立页面**：`/chat` 提供全屏 AI 导览体验

### 5. 页面导航
- **三段式布局**：首页 → 博物馆 → 地图，底部圆点导航
- **平滑滚动**：CSS scroll-behavior + JavaScript 精确控制
- **滚动进度条**：顶部金色渐变进度条

## 技术栈

| 层次     | 技术                         |
| -------- | ---------------------------- |
| 后端框架 | Flask 3.x + Flask-CORS       |
| AI 服务  | DeepSeek Chat API            |
| 地图服务 | 高德地图 JS API v2.0         |
| 前端     | 原生 HTML + CSS + JavaScript |
| 数据存储 | 单一 JSON 文件               |
| 环境管理 | python-dotenv                |

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
```
编辑 `.env` 文件，填写：
```env
AMAP_KEY=你的高德地图Web服务API密钥
GROQ_API_KEY=你的DeepSeek API密钥
PORT=5000
```

### 3. 启动项目
```bash
python app.py
```
访问 http://127.0.0.1:5000

## 数据说明

### museums.json 数据结构

```json
{
  "id": 1,
  "name": "博物馆名称",
  "address": "详细地址",
  "district": "所属区域",
  "intro_short": "简介",
  "open_time": "开放时间",
  "ticket_info": "门票信息",
  "reserve_link": "预约链接",
  "website": "官方网站",
  "phone": "联系电话",
  "level": "博物馆等级",
  "category": "博物馆类型",
  "type": "分类标识（history/art/science/specialty）",
  "lat": 32.04,
  "lng": 118.78,
  "photo_url": "图片URL",
  "collections": [
    {
      "name": "文物名称",
      "era": "年代",
      "desc": "描述",
      "image": "图片URL"
    }
  ],
  "collections_note": "数据来源说明"
}
```

### 数据来源
- 博物馆信息：官方网站、Wikipedia、手动整理
- 坐标：高德地理编码 API
- 预约链接：各博物馆官网
- 文物数据：南京博物院官网、人民画报、知乎专栏等权威来源

## API 接口

| 方法 | 路径                               | 说明                          |
| ---- | ---------------------------------- | ----------------------------- |
| GET  | `/api/museums`                     | 获取全部博物馆列表            |
| GET  | `/api/reserve-info`                | 获取有预约链接的博物馆信息    |
| GET  | `/api/reserve-info?id=<museum_id>` | 获取指定博物馆预约信息        |
| POST | `/api/ask`                         | AI 对话（body: `{question}`） |

## 维护脚本

详见 [scripts/README.md](scripts/README.md)。常用场景：

| 场景              | 脚本                           |
| ----------------- | ------------------------------ |
| 新增/更新文物数据 | `add_collections.py`           |
| 更新文物图片 URL  | `update_collections_images.py` |
| 修正博物馆坐标    | `update_museum_coordinates.py` |
| 补充地址信息      | `update_museums_address.py`    |
| 更新预约链接      | `update_reserve_links.py`      |
| 重新编号博物馆    | `reindex_museums.py`           |

> 运行脚本前请备份 `data/museums.json`，部分脚本需要高德 API 密钥。

## 许可证

本项目仅供学习和研究使用。
