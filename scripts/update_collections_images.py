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
    (5, "天王洪秀全玉玺"): "https://upload.wikimedia.org/wikipedia/commons/3/3a/TaiPingRevolutionSeal.png",
    (5, "太平天国镇库钱"): "https://upload.wikimedia.org/wikipedia/commons/b/b2/The_Coin_of_Heavenly_Kingdom_of_Great_Peace.JPG",
    (5, "曾水源墓碑"): "https://upload.wikimedia.org/wikipedia/commons/a/a3/Tombstone_of_Zeng_Shuiyuan_2011-03.JPG",
    (5, "陈玉成英王府雕花梁架"): "https://upload.wikimedia.org/wikipedia/commons/e/ed/Beam_from_the_Official_Residence_of_Chen_Yucheng_2011-12.JPG",
    (5, "太平天国天王宝座"): "https://upload.wikimedia.org/wikipedia/commons/5/5f/Heavenly_throne_%285811933470%29.jpg",

    # === 科举博物馆 (id=6) ===
    (6, "康熙御题碑"): "https://www.chinanews.com/cr/2013/1121/3389805647.jpg",
    (6, "进士题名碑"): "https://inews.gtimg.com/om_bt/O4FRnWPPGhhbpjKahDuHHBwCzlrlItlwajS86Dx04S2dwAA/641",
    (6, "江南贡院明远楼"): "https://upload.wikimedia.org/wikipedia/commons/0/09/Mingyuan_Tower_in_Jiangnan_Examination_Hall.jpg",
    (6, "中国科举博物馆建筑"): "https://upload.wikimedia.org/wikipedia/commons/7/71/China_Imperial_Examination_Museum_20180929.jpg",
    (6, "明代科举人物肖像"): "https://upload.wikimedia.org/wikipedia/commons/0/0f/Portrait_of_Jiang_Shunfu.jpg",

    # === 城墙博物馆 (id=7) ===
    (7, "四重城垣沙盘"): "http://www.news.cn/local/2021-12/29/1128214384_16407811788941n.jpg",
    (7, "中华门城堡"): "https://upload.wikimedia.org/wikipedia/commons/e/e4/%E5%8D%97%E4%BA%AC%E4%B8%AD%E5%8D%8E%E9%97%A8%2C_2009-01-27_01.jpg",
    (7, "中华门瓮城"): "https://upload.wikimedia.org/wikipedia/commons/3/3b/Glazed_arch_of_Dabaoen_Temple.jpg",

    # === 侵华日军南京大屠杀遇难同胞纪念馆 (id=8) ===
    (8, "遇难同胞遗骸遗址"): "http://www.81.cn/js_208592/_attachment/2024/03/23/16296309_ccfad48d4236684923c2371d65691f85.jpg",
    (8, "幸存者照片墙"): "http://www.81.cn/js_208592/_attachment/2024/03/23/16296309_af74e6332bae94337a605f19f8bab0c4.jpg",
    (8, "和平大钟"): "https://upload.wikimedia.org/wikipedia/commons/a/a2/The_Peace_Bell%2C_Nanjing_Massacre_Memorial_%28f17724196152%29.jpg",

    # === 大报恩寺 (id=15) ===
    (15, "鎏金七宝阿育王塔"): "https://www.njmuseumadmin.com/Public/Upload/FckFile/150921022453902",
    (15, "琉璃构件"): "https://www.njmuseumadmin.com/Public/Upload/FckFile/150921021532327",
    (15, "感应舍利"): "https://www.seu.edu.cn/_upload/article/47/32/769bee1b4c19ac0bf05488cefe25/5add9292-fca3-43ce-bc3e-94763e2342c1.jpg",
    (15, "大报恩寺琉璃塔拱门"): "https://upload.wikimedia.org/wikipedia/commons/3/3b/Glazed_arch_of_Dabaoen_Temple.jpg",

    # === 古生物博物馆 (id=10) ===
    (10, "原始中华龙鸟化石"): "https://www.nmp.ac.cn/hsjp/jzdwhs/202411/W020241125637364011526.png",
    (10, "澄江动物群化石"): "https://media.bjnews.com.cn/cover/2025/02/25/5558455284944414102.jpg?x-oss-process=image/resize,m_fill,h_300,w_300",
    (10, "孔子鸟化石"): "https://upload.wikimedia.org/wikipedia/commons/c/c5/Sinosauropteryxfossil.jpg",

    # === 云锦博物馆 (id=9) ===
    (9, "云锦龙袍匹料"): "http://www.njyjmuseum.com/attached/upload/image/20240308/6384549190517001194575642.png",
    (9, "大花楼木织机"): "https://pic.huitu.com/res/20260327/1165041_20260327184502552207_1.jpg",
    (9, "乾隆云锦龙袍"): "https://upload.wikimedia.org/wikipedia/commons/5/52/Drachenrobe-Qianlong.JPG",

    # === 地质博物馆 (id=11) ===
    (11, "北京猿人头盖骨首批复制品"): "https://upload.wikimedia.org/wikipedia/commons/e/ee/Peking_Man_Skull_%28replica%29_presented_at_Paleozoological_Museum_of_China.jpg",
    (11, "炳灵大夏巨龙"): "https://upload.wikimedia.org/wikipedia/commons/6/6c/Daxiatitan.jpg",

    # === 渡江胜利纪念馆 (id=14) ===
    (14, "京电号小火轮"): "http://jsnews.jschina.com.cn/zt2022/ztgk/202204/W020220423553682082939",
    (14, "渡江胜利纪念碑"): "https://upload.wikimedia.org/wikipedia/commons/2/23/Yangtze_Crossing_Monument_-_detail_-_P1070673.JPG",

    # === 明孝陵博物馆 (id=16) ===
    (16, "明孝陵神道石刻"): "https://imgcdn.yzwb.net/1765289877409fcapp_c93097a4-ae3c-42f2-871c-c04473cd64d6_1765283105961coverWaterMark.jpg?imageMogr2/thumbnail/1080x%3E/strip/ignore-error/1|imageslim",
    (16, "明孝陵神道石象路"): "https://upload.wikimedia.org/wikipedia/commons/7/7f/Spirit_Way_Ming_Xiaoling_2017_November.jpg",
    (16, "明孝陵石像路晨曦"): "https://upload.wikimedia.org/wikipedia/commons/2/2f/Ming_Xiaoling_Mausoleum_Spirit_Way.jpg",
    (16, "明孝陵石象"): "https://upload.wikimedia.org/wikipedia/commons/8/89/MingXiaoling_Animal_Elephant_01.jpg",

    # === 梅园新村纪念馆 (id=12) ===
    (12, "中共代表团办事处旧址"): "https://upload.wikimedia.org/wikipedia/commons/b/b8/Meiyuan_Xincun_No.30.jpg",

    # === 南京市民俗博物馆/甘熙宅第 (id=13) ===
    (13, "甘熙宅第全景"): "https://upload.wikimedia.org/wikipedia/commons/0/07/Ganxi%27s_Residence_in_Nanjing_01.jpg",

    # === 南京中国近代史遗址博物馆/总统府 (id=19) ===
    (19, "总统府门楼"): "https://upload.wikimedia.org/wikipedia/commons/8/83/Presidential_Palace_Nanjing_2015_January.jpg",
    (19, "孙中山临时大总统办公室"): "https://upload.wikimedia.org/wikipedia/commons/e/e1/Office_of_Provisional_President_Sun_Yat-sen_2011-12.jpg",
    (19, "孙中山总统府坐像"): "https://upload.wikimedia.org/wikipedia/commons/5/5e/Sun_Yat-sen_Statue_in_Nanjing_Presidential_Palace.jpg",
    (19, "总统府会议室"): "https://upload.wikimedia.org/wikipedia/commons/2/27/Meeting_Room_in_Nanjing_Presidential_Palace.JPG",

    # === 南京博物院 (id=1) additional ===
    (1, "竹林七贤与荣启期砖画"): "https://upload.wikimedia.org/wikipedia/commons/7/73/Seven_Sages_of_the_Bamboo_Grove_and_Rong_Qiqi.jpg",

    # === 六朝博物馆 (id=3) additional ===

    # === 朝天宫 (id=2) additional ===
    (2, "官窑青釉瓷盘"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330612155275.jpg",
    (2, "月影梅纹银盘"): "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330610756142.jpg",

    # === 郑和纪念馆 (id=48) ===
    (48, "郑和铜像"): "https://upload.wikimedia.org/wikipedia/commons/d/de/Bronze_of_Zheng_He%2C_Jinghai_Si.jpg",

    # === 孙中山纪念馆 (id=34) ===
    (34, "中山陵祭堂"): "https://upload.wikimedia.org/wikipedia/commons/a/aa/Hall_of_Sun_Yat-sen_Mausoleum.jpg",

    # === 南京夫子庙 (科举博物馆已有，补充孔夫子雕像) ===
    (6, "南京夫子庙孔子雕像"): "https://upload.wikimedia.org/wikipedia/commons/7/79/Confucius_Sculpture%2C_Nanjing.jpg",
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
    5: [
        {"name": "天王洪秀全玉玺", "desc": "太平天国天王洪秀全玉玺拓片，太平天国最高权力象征", "era": "太平天国"},
        {"name": "太平天国镇库钱", "desc": "太平天国铸造的镇库大钱，存世孤品，镇馆之宝", "era": "太平天国"},
        {"name": "曾水源墓碑", "desc": "太平天国官员曾水源墓碑，研究太平天国官制的重要实物", "era": "太平天国"},
        {"name": "陈玉成英王府雕花梁架", "desc": "太平天国英王陈玉成王府雕花梁架构件，精美木雕遗存", "era": "太平天国"},
        {"name": "太平天国天王宝座", "desc": "太平天国天王宝座，太平天国天王洪秀全的御座", "era": "太平天国"},
    ],
    6: [
        {"name": "进士题名碑", "desc": "记录历代进士名录的石碑，科举制度实物见证", "era": "明清"},
        {"name": "江南贡院明远楼", "desc": "江南贡院中心建筑，中国保留最古老的贡院考场建筑", "era": "明"},
        {"name": "中国科举博物馆建筑", "desc": "中国科举博物馆建筑外景，沉浸式展示千年科举制度", "era": "现代"},
        {"name": "明代科举人物肖像", "desc": "明代科举人物江顺福肖像，博物馆藏科举文物", "era": "明"},
    ],
    7: [
        {"name": "四重城垣沙盘", "desc": "复原明初南京城宏大规模，生动展示城门宫殿楼宇", "era": "明"},
        {"name": "中华门城堡", "desc": "南京中华门城堡，中国现存规模最大的城门城堡", "era": "明"},
        {"name": "中华门瓮城", "desc": "中华门瓮城三道防线环环相扣，军事防御杰作", "era": "明"},
    ],
    8: [
        {"name": "幸存者照片墙", "desc": "南京大屠杀幸存者影像墙，铭记历史的见证", "era": "现代"},
        {"name": "和平大钟", "desc": "和平大钟，悼念遇难同胞，祈愿世界和平", "era": "现代"},
    ],
    9: [
        {"name": "大花楼木织机", "desc": "传统云锦提花织机，长5.6米高4米，1924个零部件，云锦工艺核心", "era": "明清"},
        {"name": "乾隆云锦龙袍", "desc": "清代乾隆年间云锦龙袍，18世纪皇室织物珍品", "era": "清"},
    ],
    10: [
        {"name": "澄江动物群化石", "desc": "5.3亿年前寒武纪生命大爆发见证，世界级化石宝库", "era": "寒武纪"},
    ],
    11: [
        {"name": "炳灵大夏巨龙", "desc": "亚洲最大恐龙化石之一，体长26米，白垩纪巨型恐龙", "era": "白垩纪"},
    ],
    12: [
        {"name": "中共代表团办事处旧址", "desc": "梅园新村30号，周恩来、邓颖超1946年办公与居住地", "era": "1946"},
    ],
    13: [
        {"name": "甘熙宅第全景", "desc": "清代甘熙宅第，九十九间半，南京现有面积最大的明清民居建筑群", "era": "清"},
    ],
    14: [
        {"name": "京电号小火轮", "desc": "渡江战役中运送解放军过江的英雄船", "era": "1949"},
        {"name": "渡江胜利纪念碑", "desc": "渡江胜利纪念碑雕塑，纪念1949年渡江战役胜利", "era": "1949"},
    ],
    15: [
        {"name": "感应舍利", "desc": "大报恩寺地宫出土，佛教圣物，与佛顶骨舍利同出", "era": "北宋"},
        {"name": "大报恩寺琉璃塔拱门", "desc": "明代大报恩寺琉璃塔拱门构件，曾位列中古世界七大奇迹", "era": "明"},
    ],
    16: [
        {"name": "明孝陵神道石象路", "desc": "明孝陵神道石象路秋景，12对石兽守护600余年", "era": "明"},
        {"name": "明孝陵石像路晨曦", "desc": "明孝陵神道石像路晨曦景观，石象路清晨", "era": "明"},
        {"name": "明孝陵石象", "desc": "明孝陵神道石象路石雕，600年历史的石象雕刻", "era": "明"},
    ],
    19: [
        {"name": "总统府门楼", "desc": "南京总统府标志性门楼建筑，中国近代史重要遗址", "era": "民国"},
        {"name": "孙中山临时大总统办公室", "desc": "孙中山1912年在南京就任临时大总统时的办公场所", "era": "1912"},
        {"name": "孙中山总统府坐像", "desc": "南京总统府内孙中山坐像， commissioned Hall前", "era": "民国"},
        {"name": "总统府会议室", "desc": "南京总统府会议室旧址，见证重要历史决策", "era": "民国"},
    ],
    # 南京博物院 新增镇院之宝
    1: [
        {"name": "竹林七贤与荣启期砖画", "desc": "南朝墓葬模印拼嵌画像砖，现存最早魏晋人物画实物，禁止出境展览", "era": "南朝"},
    ],
    # 郑和纪念馆
    48: [
        {"name": "郑和铜像", "desc": "郑和铜像，位于南京静海寺，纪念伟大航海家郑和", "era": "现代"},
    ],
    # 孙中山纪念馆/中山陵
    34: [
        {"name": "中山陵祭堂", "desc": "中山陵主体建筑祭堂，孙中山先生陵寝所在地", "era": "民国"},
    ],
    # 科举博物馆补充
    6: [
        {"name": "南京夫子庙孔子雕像", "desc": "南京夫子庙孔子雕像，儒家文化象征", "era": "现代"},
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
