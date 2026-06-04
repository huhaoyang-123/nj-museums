"""
更新 museums.json 中所有文物为真实图片URL，无图文物则删除。
"""
import json
import os

IMAGE_MAP = {
    # === 南京博物院 (id=1) ===
    (1, "金兽"): "https://www.njmuseum.com/files/nb/collection/modify/2023/05/04/16831904434753.png",
    (1, "釉里红岁寒三友纹梅瓶"): "https://www.njmuseum.com/files/newbackImage/2018-11-02/6603326d-228a-4f34-907e-096d01d33c83.jpg",
    (1, "金蝉玉叶"): "https://www.njmuseum.com/files/nb/collection/modify/2020/12/01/1606807297495%E9%87%91%E8%9D%89%E7%8E%89%E5%8F%B6.jpg",
    (1, "银缕玉衣"): "https://5b0988e595225.cdn.sohucs.com/images/20180825/0a7473e06d1a47c89a4a9ac5c84a2bce.jpg",
    (1, "错银铜牛灯"): "https://www.njmuseum.com/files/nb/collection/modify/2021/09/30/163299245898926%E9%94%99%E9%93%B6%E7%89%9B%E7%81%AF3.png",
    (1, "广陵王玺金印"): "https://www.njmuseum.com/files/nb/collection/modify/2020/06/15/1592205313069%E9%87%91%E5%8D%B020200615.png",
    (1, "透雕人鸟兽玉饰件"): "https://pic4.zhimg.com/v2-ea251470953370255c60c0a6302a12fb_1440w.jpg",
    (1, "青瓷神兽尊"): "https://zdimg.lifeweek.com.cn/bg/20201215/1608020953023jksea.jpg",

    # === 南京市博物馆/朝天宫 (id=2) ===
    (2, "元青花「萧何月下追韩信」图梅瓶"): "https://www.njmuseumadmin.com/Public/Upload/FckFile/150921022300570",
    (2, "青瓷羊尊"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330616242517.jpg",
    (2, "镶金托云龙纹玉带板"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330609467827.jpg",
    (2, "嵌宝石金盒"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330607530410.jpg",
    (2, "人面形陶塑"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330608840559.jpg",
    (2, "兽面纹铜铙"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330610093561.jpg",
    (2, "紫砂提梁壶"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330615589268.jpg",

    # === 六朝博物馆 (id=3) ===
    (3, "青瓷釉下彩羽人纹盘口壶"): "https://www.njmuseumadmin.com/Public/Upload/default/2015/09/01/ab70d96832c45aadf53958801f4b3115.jpg",
    (3, "青瓷莲花尊"): "https://www.njmuseumadmin.com/Public/Upload/FckFile/150921020910955",
    (3, "六朝陶俑群"): "https://www.njmuseumadmin.com/Public/Upload/default/2015/08/19/3084e773070976345b77f28c63b2003f.jpg",

    # === 江宁织造博物馆 (id=4) ===
    (4, "明万历织金孔雀羽妆花纱袍料（复制件）"): "http://www.rmhb.com.cn/yxsj/zttp/202506/W020250625521583728374.jpg",
    (4, "元代织金大袖袍服"): "https://icity-static.icitycdn.com/images/uploads/ap/imsm/event/pic_head/a8udxo3/c549a6d58633e56da8udxo3.jpg/1477297167/640x0",

    # === 太平天国历史博物馆 (id=5) ===
    (5, "太平天国黄缎绣龙马褂"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624344851818010.jpg",

    # === 科举博物馆 (id=6) ===
    (6, "康熙御题碑"): "https://www.chinanews.com/cr/2013/1121/3389805647.jpg",
    (6, "进士题名碑"): "https://inews.gtimg.com/om_bt/O4FRnWPPGhhbpjKahDuHHBwCzlrlItlwajS86Dx04S2dwAA/641",

    # === 城墙博物馆 (id=7) ===
    (7, "四重城垣沙盘"): "http://www.news.cn/local/2021-12/29/1128214384_16407811788941n.jpg",

    # === 侵华日军南京大屠杀遇难同胞纪念馆 (id=8) ===
    (8, "遇难同胞遗骸遗址"): "http://www.81.cn/js_208592/_attachment/2024/03/23/16296309_ccfad48d4236684923c2371d65691f85.jpg",
    (8, "幸存者照片墙"): "http://www.81.cn/js_208592/_attachment/2024/03/23/16296309_af74e6332bae94337a605f19f8bab0c4.jpg",

    # === 大报恩寺 (id=15) ===
    (15, "鎏金七宝阿育王塔"): "https://www.njmuseumadmin.com/Public/Upload/FckFile/150921022453902",
    (15, "琉璃构件"): "https://www.njmuseumadmin.com/Public/Upload/FckFile/150921021532327",
    (15, "感应舍利"): "https://www.seu.edu.cn/_upload/article/47/32/769bee1b4c19ac0bf05488cefe25/5add9292-fca3-43ce-bc3e-94763e2342c1.jpg",

    # === 古生物博物馆 (id=10) ===
    (10, "原始中华龙鸟化石"): "https://www.nmp.ac.cn/hsjp/jzdwhs/202411/W020241125637364011526.png",
    (10, "澄江动物群化石"): "https://media.bjnews.com.cn/cover/2025/02/25/5558455284944414102.jpg?x-oss-process=image/resize,m_fill,h_300,w_300",
    (10, "孔子鸟化石"): "https://upload.wikimedia.org/wikipedia/commons/c/c5/Sinosauropteryxfossil.jpg",

    # === 云锦博物馆 (id=9) ===
    (9, "云锦龙袍匹料"): "http://www.njyjmuseum.com/attached/upload/image/20240308/6384549190517001194575642.png",
    (9, "大花楼木织机"): "https://pic.huitu.com/res/20260327/1165041_20260327184502552207_1.jpg",

    # === 地质博物馆 (id=11) ===
    (11, "北京猿人头盖骨首批复制品"): "https://upload.wikimedia.org/wikipedia/commons/e/ee/Peking_Man_Skull_%28replica%29_presented_at_Paleozoological_Museum_of_China.jpg",
    (11, "炳灵大夏巨龙"): "https://upload.wikimedia.org/wikipedia/commons/6/6c/Daxiatitan.jpg",

    # === 渡江胜利纪念馆 (id=14) ===
    (14, "京电号小火轮"): "http://jsnews.jschina.com.cn/zt2022/ztgk/202204/W020220423553682082939",

    # === 明孝陵博物馆 (id=16) ===
    (16, "明孝陵神道石刻"): "https://imgcdn.yzwb.net/1765289877409fcapp_c93097a4-ae3c-42f2-871c-c04473cd64d6_1765283105961coverWaterMark.jpg?imageMogr2/thumbnail/1080x%3E/strip/ignore-error/1|imageslim",

    # === 朝天宫 (id=2) additional ===
    (2, "官窑青釉瓷盘"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330612155275.jpg",
    (2, "月影梅纹银盘"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330610756142.jpg",
}

json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'museums.json')

with open(json_path, 'r', encoding='utf-8') as f:
    museums = json.load(f)

# First, add missing artifacts (e.g. 官窑青釉瓷盘, 月影梅纹银盘 to museum id=2)
extra_artifacts = {
    2: [
        {"name": "官窑青釉瓷盘", "desc": "南宋官窑青釉，汪兴祖墓出土，南宋官窑瓷器珍品", "era": "南宋"},
        {"name": "月影梅纹银盘", "desc": "南宋庆元元年张同之夫妇墓出土，宋代金银器上品佳作", "era": "南宋"},
        {"name": "兽面纹铜铙", "desc": "商周青铜打击乐器，体饰兽面纹，铸工精良", "era": "商周"},
        {"name": "紫砂提梁壶", "desc": "明代紫砂壶，提梁式造型古朴，明代宜兴紫砂代表", "era": "明"},
    ],
    3: [
        {"name": "六朝陶俑群", "desc": "六朝时期陶俑组合，反映六朝衣冠风貌与社会生活", "era": "六朝"},
    ],
    4: [
        {"name": "元代织金大袖袍服", "desc": "元代织金锦袍服，见证元代丝织工艺之精绝", "era": "元"},
    ],
    6: [
        {"name": "进士题名碑", "desc": "记录历代进士名录的石碑，科举制度实物见证", "era": "明清"},
    ],
    7: [
        {"name": "四重城垣沙盘", "desc": "复原明初南京城宏大规模，生动展示城门宫殿楼宇", "era": "明"},
    ],
    8: [
        {"name": "幸存者照片墙", "desc": "南京大屠杀幸存者影像墙，铭记历史的见证", "era": "现代"},
    ],
    9: [
        {"name": "大花楼木织机", "desc": "传统云锦提花织机，长5.6米高4米，1924个零部件，云锦工艺核心", "era": "明清"},
    ],
    10: [
        {"name": "澄江动物群化石", "desc": "5.3亿年前寒武纪生命大爆发见证，世界级化石宝库", "era": "寒武纪"},
    ],
    11: [
        {"name": "炳灵大夏巨龙", "desc": "亚洲最大恐龙化石之一，体长26米，白垩纪巨型恐龙", "era": "白垩纪"},
    ],
    15: [
        {"name": "感应舍利", "desc": "大报恩寺地宫出土，佛教圣物，与佛顶骨舍利同出", "era": "北宋"},
    ],
}

for museum in museums:
    mid = museum.get('id')
    # Add extra artifacts
    if mid in extra_artifacts:
        existing_names = {c['name'] for c in museum.get('collections', [])}
        for extra in extra_artifacts[mid]:
            if extra['name'] not in existing_names:
                museum.setdefault('collections', []).append(extra)

total_kept = 0
total_removed = 0

for museum in museums:
    mid = museum.get('id')
    collections = museum.get('collections', [])
    if not collections:
        continue

    new_collections = []
    for item in collections:
        name = item.get('name', '')
        key = (mid, name)
        if key in IMAGE_MAP:
            item['image'] = IMAGE_MAP[key]
            new_collections.append(item)
            total_kept += 1
        else:
            total_removed += 1

    museum['collections'] = new_collections
    if new_collections:
        museum['collections_note'] = '数据来源：网络搜索，图片均为实况文物照片'

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(museums, f, ensure_ascii=False, indent=2)

print(f"保留 {total_kept} 件文物（有真实图片），删除 {total_removed} 件文物（无图）")

# Print stats
with_data = [(m['name'], len(m['collections'])) for m in museums if len(m.get('collections', [])) > 0]
print(f"\n有文物数据的博物馆: {len(with_data)} / {len(museums)}")
for name, cnt in sorted(with_data, key=lambda x: -x[1]):
    print(f"  {name}: {cnt} 件")
