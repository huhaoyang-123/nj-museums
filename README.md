# 博物金陵 - 南京博物馆导览系统

基于 Flask 的南京博物馆信息导览 Web 应用，集成 AI 智能对话与语音识别，提供 151 座博物馆的查询、筛选、地图导航、代表文物浏览与个性化收藏服务。

## 项目结构

```
EL.demo2.0/
├── app.py                              # Flask 主入口（路由、AI 对话、语音识别、Token 用量追踪）
├── requirements.txt                    # Python 依赖（Flask、Flask-CORS、python-dotenv、requests）
├── .env.example                        # 环境变量模板
├── .gitignore                          # Git 忽略规则
├── .gitattributes                      # Git 行尾规范化
│
├── data/                               # 数据层
│   ├── museums.json                    # 151 座博物馆的完整数据（含代表文物、最新动态）
│   └── token_usage.json                # AI Token 累计用量记录（上限 20M）
│
├── services/                           # 服务层
│   └── museum_service.py               # 博物馆数据加载、字段转换、坐标回填、分类映射
│
├── templates/                          # 前端模板（原生 HTML + CSS + JavaScript，无框架依赖）
│   ├── index.html                      # 主页（Hero + 博物馆卡片 + 地图 + 聊天侧边栏 + 收藏面板）
│   ├── collections.html                # 代表文物详情页（骨架屏 + 懒加载 + 淡入动画）
│   └── chat.html                       # AI 导览独立全屏页面
│
├── scripts/                            # 数据维护脚本
│   ├── check_status.py                 # 检查博物馆文物覆盖情况
│   ├── discover_new_museums.py         # 通过高德 POI API 发现新博物馆候选
│   ├── dedup_museums.py                # 去重新博物馆候选名单
│   ├── fill_museum_metadata.py         # 通过百度百科/搜索引擎填充博物馆元数据
│   ├── fill_candidates_address.py      # 为候选博物馆补充地址信息
│   ├── fix_museum_coordinates_poi.py   # 通过高德 POI 搜索修正博物馆坐标
│   ├── crawl_museum_news.py            # 从博物馆官网爬取最新展览/活动/新闻
│   ├── crawl_news_quick.py             # 精简版新闻爬虫（聚焦重点博物馆）
│   ├── update_news_data.py             # 写入精选新闻/展览数据到 museums.json
│   └── README.md                       # 脚本使用说明
│
├── .vscode/                            # VS Code 调试配置
│   └── launch.json                     # Flask debugpy 启动配置
│
├── .trae/                              # Trae IDE 配置
│   ├── rules/
│   │   └── git-commit-message.md       # Git 提交信息规范
│   └── skills/
│       └── museum-artifact-scraper/
│           └── SKILL.md                # 博物馆文物爬取技能定义
```

## 核心功能与实现逻辑

### 1. 博物馆信息展示

**实现位置**：`templates/index.html`（前端） + `app.py`（API） + `services/museum_service.py`（数据层）

- **数据加载**：页面 `window.load` 事件触发 `fetch('/api/museums')` 获取全部博物馆 JSON，存储在全局变量 `museumsData` 中
- **卡片渲染**：`renderMuseumCards(museums, page)` 生成网格卡片，每张卡片展示名称、类型、简介摘要、区域标签，点击卡片弹出详情弹窗
- **搜索**：关键词实时匹配 `name`、`desc`、`address`，300ms 防抖输入
- **三层筛选**：
  - 区域（9 区）—— `data-filter="district"`
  - 分类（历史人文/艺术文化/科学教育/专题特色）—— `data-filter="type"`，对应 `museum.type` 字段
  - 费用（免费/付费）—— `data-filter="ticket"`，`isFree()` 函数解析 `ticket_info` 字段，识别"免费"关键词与金额数字
- **分页**：每页 12 座，`filterMuseums()` → `renderMuseumCards()` → `renderMuseumPagination()` 实现统一切片
- **详情弹窗**：`showMuseumDetail(museum)` 填充正门照片、基本信息（地址、开放时间、门票、电话）、详细介绍、文物轮播、操作按钮
- **数据转换**（`museum_service.py`）：
  - 分类自动映射：`category` → `type`（如"综合类" → `history`，"自然科学类" → `science`）
  - 坐标回填：优先使用精确 `lat/lng`，无精确坐标时用区域坐标 + `hash(name)` 散列偏移避免重叠

### 2. 代表文物浏览

**实现位置**：`templates/collections.html` + `app.py` 路由 `/museum/<id>/collections`

- **独立页面**：通过 URL 路径参数定位博物馆，`next()` 查找匹配数据
- **骨架屏加载**：页面初始渲染 4 个骨架占位卡片，图片加载后淡入替换
- **懒加载**：前 4 张图片优先加载（`loading="eager"`），后续图片使用 `loading="lazy"` + `decoding="async"` 减少初始加载开销
- **文物卡片**：每张卡片展示文物名称、年代标签、描述，鼠标悬停有金色光晕效果
- **图片占位**：缺失图片时显示类型图标（🏛️/🎨/🔬/✨）替代占位

### 3. 最新动态

**实现位置**：`templates/index.html`（前端）

- **数据来源**：`museums.json` 中 `news` 字段，包含 `title`、`desc`、`link`、`date`
- **展示位置**：博物馆详情弹窗中，介绍文字下方显示"📰 最新动态"区块
- **交互**：每条动态显示图标 + 标题 + 简短描述，点击可在新标签页打开官网链接
- **滚动**：列表最大高度 280px，超出可滚动浏览
- **自动隐藏**：无 `news` 数据的博物馆不显示该区块
- **数据采集**：通过 `crawl_museum_news.py`（静态网站）和 `update_news_data.py`（JS 渲染网站）两种方式维护

### 4. 地图导航

**实现位置**：`templates/index.html`（前端 JS） + `app.py` `/api/amap-config`（动态 Key）

- **SDK 加载**：从 `/api/amap-config` 获取 Web 端 Key 后动态创建 `<script>` 标签加载高德 JS API v2.0，避免 Key 硬编码在前端
- **南京边界**：`AMap.DistrictSearch` 搜索"南京市"，绘制金色描边 `Polygon`，`map.setFitView()` 自动适配视口
- **边界限制**：`checkBoundary()` 监听 `moveend`/`zoomend` 事件，拖拽越界时强制回弹；缩放范围限制在 9-18 级
- **自定义标记**：`createMuseumMarker(museum)` 生成复杂 DOM 标记，包含：
  - 脉冲光环（CSS `@keyframes mkrPulse`）
  - 外发光环（`radial-gradient`）
  - 分类彩色主 pin（金色/古铜/蓝色/红色，对应 4 种分类）
  - 悬停标签（名称 + 等级 + 分类）
  - 点击信息窗口（地址、开放时间、门票、预约按钮、查看详情按钮）
- **地图筛选面板**：右侧浮动面板，支持按类型（多选）和费用（互斥）筛选标记显示/隐藏
- **初始化时序**：加载顺序为"SDK 加载 → 边界绘制 → 数据 fetch → 添加标记"，各环节有兜底，避免数据未就绪导致标记缺失

#### 导航功能（唤起本地地图APP）

- **导航按钮**：详情弹窗中新增「🚗 打开导航」按钮，仅当博物馆有坐标数据时显示
- **平台检测**：`isMobileDevice()` 通过 `navigator.userAgent` 判断运行环境
- **移动端**：显示导航选择弹窗，支持三种地图应用：
  - 高德地图：`amapuri://route/plan?dlat=...&dlng=...&dname=...`
  - 百度地图：`baidumap://map/direction?destination=latlng:...|name:...`
  - Apple Maps：`https://maps.apple.com/?q=...`
- **PC端兼容**：无法唤起本地地图APP时，自动复制博物馆名称和地址到剪贴板，提示用户粘贴到手机导航APP使用
- **导航弹窗样式**：金色边框弹窗，三个地图选项按钮垂直排列，悬停有光晕效果

### 5. AI 智能导览

**实现位置**：`app.py` `/api/ask` + `templates/index.html`（侧边聊天面板）

- **AI 服务**：DeepSeek Chat API（`api.deepseek.com/v1/chat/completions`）
- **系统提示词**：`SYSTEM_PROMPT_BASE` + `build_museum_context()` 拼接全部博物馆概况（名称|类型|区域|门票|预约|简介），每条记录约 120 字符
- **智能动作匹配**：`extract_museum_actions(answer_text, museums)` 解析 AI 回复中的 `【博物馆名称】`、别名、分类关键词，匹配数据库后生成三类操作按钮：
  - "查看详情"：`openMuseumDetailById(id)` 打开详情弹窗
  - "预约"：`openReserveLink()` 打开预约链接或弹窗提示
  - "地图查看"：`navigateToMuseum(lat, lng)` 地图定位 + 自动打开详情
- **Token 用量追踪**：每次 API 调用累加 `total_tokens` 至 `data/token_usage.json`，超过 20M 上限返回 503
- **聊天面板**：
  - 首页浮动按钮：右下角 💬 按钮，`toggleChatPanel()` 控制侧边面板滑入/滑出
  - 快捷提问：4 个快捷芯片（必去推荐、免费参观、如何预约、亲子游玩）
  - 对话历史：用户消息红色气泡、AI 回复金色边框气泡，自动滚底
- **独立页面**：`/chat` 提供全屏沉浸式 AI 导览，设计语言与首页一致

### 6. 语音识别

**实现位置**：`app.py` `/api/speech-to-text` + `templates/index.html`（录音逻辑）

- **语音采集**：浏览器 `MediaRecorder API` → `AudioContext` → `ScriptProcessor` → 16kHz PCM，前端手动编码 WAV 格式（44 字节 RIFF 头 + PCM 数据）
- **后端识别**：`base64` 编码音频 → 百度语音识别 API（`vop.baidu.com/server_api`），`dev_pid=1537`（普通话）
- **Token 管理**：`get_baidu_access_token()` 使用 OAuth2 客户端凭证模式获取 access_token，带缓存（到期前 5 分钟刷新）
- **双入口**：
  - 搜索栏 🎤 按钮：录音后自动填写搜索框并触发搜索
  - 聊天面板 🎤 按钮：录音后自动填写输入框（需手动发送）
- **状态提示**：录音中红色脉冲动画（`@keyframes mic-pulse`），处理中转圈动画

### 7. 个性化功能（localStorage）

**实现位置**：`templates/index.html`（localStorage 模块 + UI）

- **收藏（⭐）**：`bwj_favorites` 存储 ID 数组
  - 卡片右上角星标按钮
  - 详情弹窗收藏按钮
  - 右侧收藏面板：列出所有收藏博物馆、支持移除
  - 收藏面板统计：总收藏数、已打卡数、有笔记数
- **打卡记录（✅）**：`bwj_visited` 存储 `{museum_id: "YYYY-MM-DD"}`
  - 点击"标记已参观"自动记录当天日期
  - 卡片左上角绿色"已参观"标签
- **个人笔记（📝）**：`bwj_notes` 存储 `{museum_id: "笔记内容"}`
  - 详情弹窗底部笔记文本框
  - 保存后按钮变绿提示"已保存"

### 8. 页面设计

**实现位置**：`templates/index.html`（HTML 结构 + CSS 样式 + JS 交互）

- **三段式布局**：Hero 首页 → 博物馆卡片区 → 地图区
- **滚动导航**：滚动超过 Hero 区域后顶部 Nav 滑入显示；底部滚动进度条（金色渐变）
- **滚动动画**：`IntersectionObserver` 监听 `.fade-up` 元素，进入视口时触发透明→可见、上移 30px 的淡入动画
- **视觉风格**：深色背景（`#0a0505`）+ 金色（`#d4af37`）主题色 + 朱红（`#c7000a`）点缀 + SVG 噪点纹理叠加层 + 角落装饰线条
- **字体**：标题用宋体/楷体，正文用无衬线，统一 `letter-spacing` 增强古典感
- **响应式**：卡片网格 `auto-fit, minmax(280px, 1fr)`，移动端单列

## 技术栈

| 层次       | 技术                                    |
| ---------- | --------------------------------------- |
| 后端框架   | Flask 3.x + Flask-CORS                  |
| AI 服务    | DeepSeek Chat API（deepseek-chat 模型） |
| 语音识别   | 百度语音识别 API（dev_pid=1537）        |
| 地图服务   | 高德地图 JS API v2.0 + DistrictSearch   |
| 前端       | 原生 HTML + CSS + JavaScript（零框架）  |
| 客户端存储 | localStorage（收藏/打卡/笔记）          |
| 数据存储   | 单一 JSON 文件（museums.json）          |
| 环境管理   | python-dotenv                           |

## API 接口

| 方法 | 路径                               | 说明                                                        |
| ---- | ---------------------------------- | ----------------------------------------------------------- |
| GET  | `/api/museums`                     | 获取全部博物馆列表（含转换后字段）                          |
| GET  | `/api/reserve-info`                | 获取所有有预约链接的博物馆信息                              |
| GET  | `/api/reserve-info?id=<museum_id>` | 获取指定博物馆预约信息                                      |
| POST | `/api/ask`                         | AI 对话（body: `{"question": "..."}`）返回 answer + actions |
| POST | `/api/speech-to-text`              | 语音识别（multipart: audio=wav）                            |
| GET  | `/api/amap-config`                 | 获取高德 Web 端 Key（动态提供）                             |

### AI 对话返回值格式

```json
{
  "answer": "AI 回复文本...",
  "actions": [
    {
      "museum_name": "南京博物院",
      "museum_id": 1,
      "category": "综合类",
      "district": "玄武区",
      "reserve_link": "https://...",
      "lat": 32.04,
      "lng": 118.78
    }
  ]
}
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
```
编辑 `.env` 文件，填写所需配置：

| 环境变量               | 说明                                  | 是否必填 |
| ---------------------- | ------------------------------------- | -------- |
| `AMAP_KEY`             | 高德地图 Web服务端Key（用于地理编码） | 是       |
| `AMAP_WEB_KEY`         | 高德地图 Web端Key（用于前端地图渲染） | 是       |
| `AMAP_WEB_SECRET_KEY`  | Web端安全密钥（可选）                 | 否       |
| `GROQ_API_KEY`         | DeepSeek AI API密钥                   | 是       |
| `BAIDU_ASR_API_KEY`    | 百度语音识别 API Key                  | 否       |
| `BAIDU_ASR_SECRET_KEY` | 百度语音识别 Secret Key               | 否       |
| `PORT`                 | 服务器端口（默认5000）                | 否       |

> **重要说明**：高德地图的 Web端Key 和 Web服务端Key 是两种不同类型，需分别在[高德开发者平台](https://console.amap.com/)申请：
> - **Web端Key**：用于浏览器端地图渲染
> - **Web服务端Key**：用于服务器端地理编码API

```env
# 示例配置
AMAP_KEY=your_amap_web_service_key_here
AMAP_WEB_KEY=your_amap_web_key_here
GROQ_API_KEY=sk-your-deepseek-api-key-here
BAIDU_ASR_API_KEY=your_baidu_asr_api_key_here
BAIDU_ASR_SECRET_KEY=your_baidu_asr_secret_key_here
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
  "collections_note": "数据来源说明",
  "news": [
    {
      "title": "展览/活动/新闻标题",
      "desc": "简短描述",
      "link": "https://官网链接",
      "date": "2026-06-09"
    }
  ]
}
```

### 数据加载管线

1. `museum_service.py` 读取 `data/museums.json`
2. 遍历每条记录，执行字段转换：
   - `category` → `type` 映射（`CATEGORY_TYPE_MAP`）
   - `district` → 坐标回填（优先精确坐标，回退到区域坐标 + hash 散列）
   - 补充 `intro_short`、`news`、`collections` 等字段
3. 返回标准化的博物馆列表供 API 和模板使用

### 数据来源
- 博物馆基本信息：官方网站、Wikipedia、手动整理
- 坐标：高德地理编码 API
- 预约链接：各博物馆官网
- 文物数据：南京博物院官网、人民画报、知乎专栏等权威来源

## 维护脚本

详见 [scripts/README.md](scripts/README.md)。常用场景：

| 场景             | 脚本                            | 依赖       |
| ---------------- | ------------------------------- | ---------- |
| 发现新博物馆候选 | `discover_new_museums.py`       | `AMAP_KEY` |
| 去重候选名单     | `dedup_museums.py`              | —          |
| 填充博物馆元数据 | `fill_museum_metadata.py`       | 网络       |
| 补充候选地址信息 | `fill_candidates_address.py`    | `AMAP_KEY` |
| 修正博物馆坐标   | `fix_museum_coordinates_poi.py` | `AMAP_KEY` |
| 检查文物覆盖     | `check_status.py`               | —          |
| 爬取官网新闻     | `crawl_museum_news.py`          | 网络       |
| 快速爬取新闻     | `crawl_news_quick.py`           | 网络       |
| 写入精选新闻     | `update_news_data.py`           | —          |

> 运行脚本前请备份 `data/museums.json`，部分脚本需要高德 API 密钥。

## 浏览器兼容性说明

- 语音识别功能需要 HTTPS 或 localhost 环境（`getUserMedia` 安全策略）
- 高德地图需浏览器支持 ES6
- localStorage 需浏览器启用 Cookie/存储

## 许可证

本项目仅供学习和研究使用。
