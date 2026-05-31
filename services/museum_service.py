# services/museum_service.py
import json
import logging
import os

logger = logging.getLogger(__name__)

def get_all_museums():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'museums.json')

    logger.info("读取文件: %s", file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("读取成功，数据条数: %d", len(data))
        return data
    except FileNotFoundError:
        logger.error("文件不存在: %s", file_path)
        return []
    except json.JSONDecodeError as e:
        logger.error("JSON 解析失败: %s", e)
        return []