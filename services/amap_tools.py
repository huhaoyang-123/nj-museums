# services/amap_tools.py
"""
高德地图 API 工具封装
为 DeepSeek Tool Calls 提供以下工具函数：
  - search_nearby_museums  : 周边博物馆 POI 搜索
  - get_route_info         : 路径规划（驾车 / 步行 / 公交地铁）
  - geocode_address        : 地理编码（地址 → 坐标）
"""

import os
import json
import logging
import re
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

AMAP_KEY = os.environ.get('AMAP_KEY', '')
AMAP_REST_URL = 'https://restapi.amap.com/v3'


# ============================================================
# Tool 定义（JSON Schema，供 DeepSeek API 使用）
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_nearby_museums",
            "description": (
                "搜索南京市内某个位置周边的博物馆。"
                "当用户询问'附近有哪些博物馆'、'XX附近有什么博物馆'、"
                "'周边博物馆'、'离我最近的博物馆'等位置相关问题时必须调用此工具。"
                "location参数可以是地名或经纬度坐标。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "位置描述，如'新街口'、'夫子庙'、'南京站'、"
                            "'南京大学鼓楼校区'等南京市内的地名"
                        )
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_route_info",
            "description": (
                "获取从起点到终点的出行路线信息，包括距离、预计耗时和路线指引。"
                "当用户询问'怎么去XX'、'从XX到XX多远'、'需要多长时间'、"
                "'坐什么车'等交通路线问题时，必须调用此工具获取实时路线数据。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "起点，可以是地名（如'南京站'）或地址"
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点，可以是地名（如'南京博物院'）或地址"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "transit"],
                        "description": "出行方式：transit=公交地铁，driving=驾车，walking=步行。用户未指定时默认transit"
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_address",
            "description": (
                "将地址或地名转换为精确的经纬度坐标和格式化地址。"
                "当需要获取某个地点的精确坐标、验证地址是否存在时调用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "需要查询的地址或地名，如'南京博物院'、'中山陵'"
                    }
                },
                "required": ["address"]
            }
        }
    }
]


# ============================================================
# 核心 API 调用
# ============================================================

def _amap_get(path: str, params: dict) -> Any:
    """通用高德 REST API GET 请求"""
    params['key'] = AMAP_KEY
    try:
        resp = requests.get(f"{AMAP_REST_URL}{path}", params=params, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"高德 API 请求失败: {path} - {e}")
        return {"status": "0", "info": str(e)}


def _geocode(address: str, city: str = "南京") -> Optional[dict]:
    """地理编码：地址 → 坐标"""
    result = _amap_get("/geocode/geo", {"address": address, "city": city})
    if result.get("status") == "1" and result.get("geocodes"):
        geo: dict = result["geocodes"][0]
        lng, lat = geo["location"].split(",")
        return {
            "lng": float(lng),
            "lat": float(lat),
            "formatted_address": geo.get("formatted_address", address)
        }
    return None


def _search_poi_around(lng: float, lat: float, radius: int = 5000) -> list:
    """周边 POI 搜索：查找博物馆类地点"""
    result = _amap_get("/place/around", {
        "location": f"{lng},{lat}",
        "keywords": "博物馆|纪念馆|陈列馆|美术馆|科技馆",
        "types": "060000",               # 科教文化服务大类
        "radius": radius,
        "sortrule": "distance",
        "offset": 15,
        "extensions": "all"
    })
    if result.get("status") == "1" and result.get("pois"):
        return result["pois"]
    return []


def _search_poi_text(keywords: str, city: str = "南京") -> list:
    """文本 POI 搜索"""
    result = _amap_get("/place/text", {
        "keywords": keywords,
        "city": city,
        "types": "060000",
        "offset": 10,
        "extensions": "all"
    })
    if result.get("status") == "1" and result.get("pois"):
        return result["pois"]
    return []


def _get_direction(origin_lng: float, origin_lat: float, dest_lng: float, dest_lat: float, mode: str = "transit") -> Optional[dict]:
    """路径规划"""
    origin = f"{origin_lng},{origin_lat}"
    destination = f"{dest_lng},{dest_lat}"

    if mode == "driving":
        path = "/direction/driving"
    elif mode == "walking":
        path = "/direction/walking"
    else:
        path = "/direction/transit/integrated"

    params = {
        "origin": origin,
        "destination": destination,
        "city": "南京",
        "cityd": "南京",
        "extensions": "all"
    }

    result = _amap_get(path, params)
    if result.get("status") == "1" and result.get("route"):
        return result["route"]
    return None


# ============================================================
# 工具执行入口
# ============================================================

def execute_tool(tool_name, arguments):
    """根据工具名称执行对应功能，返回 JSON 字符串供 AI 阅读"""
    try:
        if tool_name == "search_nearby_museums":
            return _do_search_nearby(arguments)
        elif tool_name == "get_route_info":
            return _do_get_route(arguments)
        elif tool_name == "geocode_address":
            return _do_geocode(arguments)
        else:
            return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"工具执行失败 {tool_name}: {e}")
        return json.dumps({"error": f"工具执行异常: {str(e)}"}, ensure_ascii=False)


# ============================================================
# 各工具具体实现
# ============================================================

def _do_search_nearby(arguments):
    """搜索周边博物馆"""
    location = arguments.get("location", "")

    geo = _geocode(location)
    if not geo:
        geo = _geocode(location, city="")

    if not geo:
        return json.dumps({
            "error": f"未能在南京市找到「{location}」，请尝试更具体的地名（如'新街口地铁站'）",
            "pois": []
        }, ensure_ascii=False)

    pois = _search_poi_around(geo["lng"], geo["lat"])

    if not pois:
        return json.dumps({
            "searched_location": geo["formatted_address"],
            "coords": f"{geo['lng']},{geo['lat']}",
            "pois": [],
            "message": f"在「{geo['formatted_address']}」周边 5 公里内未找到博物馆"
        }, ensure_ascii=False)

    simplified = []
    for p in pois[:10]:
        item = {
            "name": p.get("name", ""),
            "address": p.get("address", ""),
            "distance": p.get("distance", "未知"),
            "type": p.get("type", ""),
        }
        if p.get("tel"):
            item["tel"] = p["tel"]
        biz_ext = p.get("biz_ext")
        if biz_ext and biz_ext.get("rating"):
            item["rating"] = biz_ext["rating"]
        simplified.append(item)

    return json.dumps({
        "searched_location": geo["formatted_address"],
        "coords": f"{geo['lng']},{geo['lat']}",
        "count": len(simplified),
        "pois": simplified
    }, ensure_ascii=False)


def _do_get_route(arguments):
    """获取路线信息"""
    origin = arguments.get("origin", "")
    destination = arguments.get("destination", "")
    mode = arguments.get("mode", "transit")

    geo_origin = _geocode(origin) or _geocode(origin, city="")
    geo_dest = _geocode(destination) or _geocode(destination, city="")

    if not geo_origin:
        return json.dumps({"error": f"无法找到起点「{origin}」，请提供更具体的地名"}, ensure_ascii=False)
    if not geo_dest:
        return json.dumps({"error": f"无法找到终点「{destination}」，请提供更具体的地名"}, ensure_ascii=False)

    route = _get_direction(
        geo_origin["lng"], geo_origin["lat"],
        geo_dest["lng"], geo_dest["lat"], mode
    )

    if not route:
        return json.dumps({
            "error": "未能获取路线信息，请检查起终点是否在南京市范围内",
            "origin": geo_origin["formatted_address"],
            "destination": geo_dest["formatted_address"]
        }, ensure_ascii=False)

    mode_label = {"transit": "公交/地铁", "driving": "驾车", "walking": "步行"}.get(mode, mode)

    result = {
        "mode": mode_label,
        "origin": geo_origin["formatted_address"],
        "destination": geo_dest["formatted_address"],
    }

    if mode == "driving":
        paths = route.get("paths", [])
        if paths:
            p = paths[0]
            result.update({
                "distance": p.get("distance", "未知"),
                "duration": p.get("duration", "未知"),
                "toll": p.get("tolls", "0"),
                "steps_summary": _fmt_driving_steps(p.get("steps", []))
            })
    elif mode == "walking":
        paths = route.get("paths", [])
        if paths:
            p = paths[0]
            result.update({
                "distance": p.get("distance", "未知"),
                "duration": p.get("duration", "未知"),
                "steps_summary": _fmt_walking_steps(p.get("steps", []))
            })
    else:
        transits = route.get("transits", [])
        if transits:
            t = transits[0]
            result.update({
                "distance": t.get("distance", "未知"),
                "duration": t.get("duration", "未知"),
                "cost": t.get("cost", "0"),
                "walking_distance": t.get("walking_distance", "0"),
                "segments": _fmt_transit_segments(t.get("segments", []))
            })
        else:
            result["message"] = "未找到公交/地铁方案"

    return json.dumps(result, ensure_ascii=False)


def _do_geocode(arguments):
    """地理编码"""
    address = arguments.get("address", "")
    geo = _geocode(address) or _geocode(address, city="")
    if not geo:
        return json.dumps({"error": f"未找到「{address}」的地理坐标"}, ensure_ascii=False)
    return json.dumps(geo, ensure_ascii=False)


# ============================================================
# 路线格式化辅助函数
# ============================================================

def _strip_html(text):
    """去除 HTML 标签"""
    return re.sub(r'<[^>]+>', '', text)


def _fmt_walking_steps(steps):
    """格式化步行步骤"""
    if not steps:
        return ""
    lines = []
    for s in steps[:5]:
        instruction = _strip_html(s.get("instruction", ""))
        road = s.get("road", "")
        dist = s.get("distance", "?")
        segment = f"{instruction}（{road}，约{dist}米）" if road else f"{instruction}（约{dist}米）"
        lines.append(segment)
    return "; ".join(lines)


def _fmt_driving_steps(steps):
    """格式化驾车步骤"""
    return _fmt_walking_steps(steps)


def _fmt_transit_segments(segments):
    """格式化公交 / 地铁换乘段"""
    if not segments:
        return ""
    parts = []
    for seg in segments:
        bus = seg.get("bus", {})
        walking = seg.get("walking", {})

        if bus and bus.get("buslines"):
            bl = bus["buslines"][0]
            line_type = bl.get("type", "公交")
            line_name = bl.get("name", "未知线路")
            start_stop = (bl.get("departure_stop") or {}).get("name", "?")
            end_stop = (bl.get("arrival_stop") or {}).get("name", "?")
            station_count = bl.get("station_num", "?")
            parts.append(
                f"乘坐{line_type}{line_name}：{start_stop} → {end_stop}（{station_count}站）"
            )

        if walking:
            dist = walking.get("distance", "?")
            parts.append(f"步行约{dist}米")

    return "; ".join(parts)
