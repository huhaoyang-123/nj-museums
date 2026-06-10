import json, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(BASE, 'data', 'museums.json'), 'r', encoding='utf-8'))

PRIORITY = {'中山陵','明孝陵','总统府','夫子庙','南京博物院',
    '侵华日军南京大屠杀遇难同胞纪念馆','南京中国科举博物馆','南京城墙博物馆',
    '南京云锦博物馆','南京古生物博物馆','南京大报恩寺遗址博物馆','郑和纪念馆',
    '南京市博物馆','南京六朝博物馆','南京民俗博物馆','江宁织造博物馆',
    '太平天国历史博物馆','南京奥林匹克博物馆','南京抗日航空烈士纪念馆',
    '南京紫金山昆虫博物馆','高淳陶瓷博物馆'}

for m in data:
    name = m.get('name','')
    if name in PRIORITY:
        c = m.get('collections',[])
        imgs = sum(1 for x in c if x.get('image',''))
        tag = 'OK' if imgs >= 3 else ('FEW' if c else 'NONE')
        print(f'  [{tag:>4}] id={m["id"]:>3} {name}: {len(c)} items ({imgs} images)')

total_with = sum(1 for m in data if m.get('collections'))
print(f'\nWith collections: {total_with}/151')
print(f'Without: {151 - total_with}')
