import json
with open(r'c:\Users\haoyang hu\Desktop\EL.demo 3.0\data\museums.json', 'r', encoding='utf-8') as f:
    museums = json.load(f)
print(f'总博物馆数: {len(museums)}')
with_collections = [(m['id'], m['name'], len(m.get("collections", []))) for m in museums]
with_collections.sort(key=lambda x: x[2])
print(f'有文物的博物馆: {sum(1 for x in with_collections if x[2] > 0)} / {len(museums)}')
print()
print('=== 文物较少的博物馆（<5件）===')
for mid, name, cnt in with_collections:
    if 0 < cnt < 5:
        print(f'  id={mid} [{cnt}件] {name}')
print()
print('=== 完全无文物的博物馆 ===')
for mid, name, cnt in with_collections:
    if cnt == 0:
        print(f'  id={mid} {name}')
