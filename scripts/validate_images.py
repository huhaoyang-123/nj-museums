import json

# Load museums.json
with open('data/museums.json', encoding='utf-8') as f:
    museums = json.load(f)

total_count = 0
museum_count = 0

print("=== Museum Collections Summary ===")
for museum in museums:
    collections = museum.get('collections', [])
    if collections:
        museum_count += 1
        total_count += len(collections)
        print(f"{museum['name']}: {len(collections)} 件文物")

print(f"\n=== Statistics ===")
print(f"有文物数据的博物馆: {museum_count} / {len(museums)}")
print(f"文物总数: {total_count}")

# Check for missing images
print("\n=== Checking for missing images ===")
missing_images = []
for museum in museums:
    collections = museum.get('collections', [])
    for item in collections:
        if not item.get('image'):
            missing_images.append((museum['name'], item['name']))

if missing_images:
    print("发现缺少图片的文物:")
    for museum_name, item_name in missing_images:
        print(f"- {museum_name}: {item_name}")
else:
    print("所有文物都有图片链接")
