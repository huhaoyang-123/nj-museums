import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(base_dir, 'data', 'museums.json')

with open(file_path, 'r', encoding='utf-8') as f:
    museums = json.load(f)

for idx, museum in enumerate(museums, start=1):
    museum['id'] = idx

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(museums, f, ensure_ascii=False, indent=2)

print(f"重新编号完成！共 {len(museums)} 个博物馆")
