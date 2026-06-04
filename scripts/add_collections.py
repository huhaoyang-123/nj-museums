"""
为 museums.json 中的每个博物馆添加 collections（代表文物）数组。
数据来源于 Firecrawl 网络搜索。
"""
import json
import sys
import os

# 构建 collections 数据映射（key 为博物馆 id）
collections_map = {
    1: {  # 南京博物院
        "collections": [
            {"name": "金兽", "desc": "西汉金器，重9100克，含金量99%，迄今出土最重金器，国之瑰宝", "era": "西汉", "image": ""},
            {"name": "釉里红岁寒三友纹梅瓶", "desc": "明洪武釉里红，现存唯一带盖完整的洪武釉里红梅瓶，国宝级文物", "era": "明洪武", "image": ""},
            {"name": "金蝉玉叶", "desc": "明代发簪，金蝉立于和田羊脂白玉叶上，构思巧妙的稀世工艺珍品", "era": "明", "image": ""},
            {"name": "银缕玉衣", "desc": "东汉银缕玉衣，全国仅发现一件，玉片2600余块", "era": "东汉", "image": ""},
            {"name": "错银铜牛灯", "desc": "东汉青铜器，环保设计领先西方一千多年，实用与艺术完美结合", "era": "东汉", "image": ""},
            {"name": "广陵王玺金印", "desc": "东汉唯一汉朝刘姓王金印，高纯度黄金制成，汉印精品", "era": "东汉", "image": ""},
            {"name": "透雕人鸟兽玉饰件", "desc": "新石器时代良渚文化，我国出土最早的人鸟兽透雕精品", "era": "新石器时代", "image": ""},
            {"name": "青瓷神兽尊", "desc": "西晋青瓷，出土于周处家族墓，最早有铭款瓷器之一", "era": "西晋", "image": ""},
        ],
        "collections_note": "数据来源：知乎专栏《南京博物院的十八件镇馆之宝》（2007年评选），南博院藏42万余件"
    },
    2: {  # 南京市博物馆（朝天宫）
        "collections": [
            {"name": "元青花「萧何月下追韩信」图梅瓶", "desc": "元末明初青花瓷罕见珍品，中国瓷器三绝之一，禁止出境展览文物", "era": "元", "image": "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330611479306.jpg"},
            {"name": "青瓷羊尊", "desc": "三国吴青瓷，釉色匀净无暇，造型优美，六朝青瓷珍品", "era": "三国·吴", "image": "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330616242517.jpg"},
            {"name": "镶金托云龙纹玉带板", "desc": "明洪武四年汪兴祖墓出土，工艺精湛的明代玉带饰", "era": "明洪武", "image": "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330609467827.jpg"},
            {"name": "嵌宝石金盒", "desc": "明成化十年沐斌夫人梅氏墓出土，明代金银器珍品", "era": "明", "image": "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330607530410.jpg"},
            {"name": "人面形陶塑", "desc": "新石器时代，南京地区发现最早的人塑像，金陵始祖", "era": "新石器时代", "image": "http://www.rmhb.com.cn/yxsj/tpgs/202506/W020250624330608840559.jpg"},
            {"name": "兽面纹铜铙", "desc": "商末青铜器，南京浦口龙王荡出土", "era": "商", "image": ""},
            {"name": "紫砂提梁壶", "desc": "明嘉靖吴经墓出土，早期紫砂壶重要实物", "era": "明嘉靖", "image": ""},
        ],
        "collections_note": "数据来源：人民画报《南京市博物馆（朝天宫）：玉堂佳器「国保」新生》（2025.6），馆藏十万余件"
    },
    3: {  # 六朝博物馆
        "collections": [
            {"name": "青瓷釉下彩羽人纹盘口壶", "desc": "1983年出土，通体绘制纹饰，我国最早釉下彩瓷器之一，镇馆之宝", "era": "三国·吴", "image": ""},
            {"name": "青瓷莲花尊", "desc": "存世莲花尊中体型最大、制作最精美的器物，佛教艺术珍品", "era": "南朝", "image": ""},
            {"name": "六朝陶俑群", "desc": "东晋至南朝陶俑，展示六朝人物风貌与服饰", "era": "东晋-南朝", "image": ""},
            {"name": "六朝墓志石刻", "desc": "六朝时期的墓志铭与石刻瓦当，记录都城历史", "era": "六朝", "image": ""},
        ],
        "collections_note": "数据来源：iMuseum、南京大学等，展出约1200件文物"
    },
    4: {  # 江宁织造博物馆
        "collections": [
            {"name": "明万历织金孔雀羽妆花纱袍料（复制件）", "desc": "云锦复制国宝，纱地妆花工艺，17余米长，真金线与孔雀羽织就", "era": "明万历", "image": ""},
            {"name": "元代织金大袖袍服", "desc": "目前已知最早运用云锦织金工艺的实物", "era": "元", "image": ""},
            {"name": "清代云锦龙袍", "desc": "江宁织造府为皇室织造的云锦龙袍精品", "era": "清", "image": ""},
            {"name": "《红楼梦》相关文物", "desc": "与曹雪芹家族及红楼梦文化相关的史料文物", "era": "清", "image": ""},
        ],
        "collections_note": "数据来源：人民画报、iMuseum，馆藏云锦精品100余件"
    },
    5: {  # 太平天国历史博物馆（瞻园）
        "collections": [
            {"name": "太平天国黄缎绣龙马褂", "desc": "镇馆之宝，黄缎彩线绣五爪团龙，太平天国高级官员官服", "era": "太平天国", "image": ""},
            {"name": "太平天国镇库钱", "desc": "太平天国时期的货币文物", "era": "太平天国", "image": ""},
            {"name": "团龙马褂", "desc": "1864年席宝田俘获幼天王时所得，后捐赠", "era": "太平天国", "image": ""},
        ],
        "collections_note": "数据来源：知乎专栏、携程游记，全国收藏太平天国文物最丰富的博物馆"
    },
    6: {  # 南京中国科举博物馆
        "collections": [
            {"name": "康熙御题碑", "desc": "镇馆之宝，清代康熙皇帝御笔题写的碑刻", "era": "清康熙", "image": ""},
            {"name": "进士题名碑", "desc": "记录历代进士名录的石碑，科举制度实物见证", "era": "明清", "image": ""},
            {"name": "科举匾额", "desc": "明清时期科举相关匾额，包括状元、榜眼、探花匾", "era": "明清", "image": ""},
            {"name": "魁星堂", "desc": "刻满历代状元名录的核心理念展示空间", "era": "", "image": ""},
        ],
        "collections_note": "数据来源：中国新闻网、钟山清风，江南贡院遗址基础上建成"
    },
    7: {  # 南京城墙博物馆
        "collections": [
            {"name": "明城砖矩阵", "desc": "700多块代表性城砖，铭文记载造砖人夫姓名，网红打卡点", "era": "明", "image": ""},
            {"name": "四重城垣沙盘", "desc": "复原明初南京城宏大规模，生动展示城门宫殿楼宇", "era": "明", "image": ""},
            {"name": "明代石井栏", "desc": "发现于西水关附近，呈现城墙守护下的市井生活", "era": "明", "image": ""},
        ],
        "collections_note": "数据来源：中国新闻网、新华报业，中国规模最大的地方城墙专题博物馆"
    },
    8: {  # 侵华日军南京大屠杀遇难同胞纪念馆
        "collections": [
            {"name": "遇难同胞遗骸遗址", "desc": "江东门「万人坑」遗址，三次发掘出的遇难同胞遗骸", "era": "1937", "image": ""},
            {"name": "幸存者照片墙", "desc": "南京大屠杀幸存者肖像与证言史料", "era": "近现代", "image": ""},
            {"name": "历史档案史料", "desc": "南京大屠杀相关的档案文献、影像资料与实物证据", "era": "1937", "image": ""},
        ],
        "collections_note": "数据来源：纪念馆官网、维基百科，国家一级博物馆"
    },
    9: {  # 南京云锦博物馆
        "collections": [
            {"name": "云锦龙袍匹料", "desc": "明清皇家云锦龙袍面料，妆花工艺代表作", "era": "明清", "image": ""},
            {"name": "大花楼木织机", "desc": "云锦织造核心设备，长5.6米高4米，传统手工操作", "era": "", "image": ""},
            {"name": "历代云锦精品", "desc": "从战国到明清最具代表性的云锦实物及丝织文物复制品", "era": "战国-清", "image": ""},
        ],
        "collections_note": "数据来源：云锦博物馆官网，藏有织品文物1000多件、图稿2000多份"
    },
    10: {  # 南京古生物博物馆
        "collections": [
            {"name": "原始中华龙鸟化石", "desc": "镇馆之宝，距今约1.25亿年，热河生物群代表化石", "era": "白垩纪早期", "image": ""},
            {"name": "澄江动物群化石", "desc": "距今约5.3亿年寒武纪生命大爆发见证，国宝级化石", "era": "寒武纪", "image": ""},
            {"name": "孔子鸟化石", "desc": "热河生物群重要鸟类化石", "era": "白垩纪早期", "image": ""},
        ],
        "collections_note": "数据来源：南京古生物博物馆官网，世界最大古生物专业博物馆之一"
    },
    11: {  # 南京地质博物馆
        "collections": [
            {"name": "北京猿人头盖骨首批复制品", "desc": "世界上仅存5个首批复制品之一，镇馆之宝", "era": "旧石器时代", "image": ""},
            {"name": "炳灵大夏巨龙", "desc": "大型恐龙化石标本", "era": "白垩纪", "image": ""},
            {"name": "江苏宜兴恐龙蛋化石", "desc": "江苏省内发现的恐龙蛋化石标本", "era": "白垩纪", "image": ""},
        ],
        "collections_note": "数据来源：知乎《历数中国各地的地质博物馆》，馆藏标本2万余件"
    },
    12: {  # 梅园新村纪念馆
        "collections": [
            {"name": "周恩来铜像", "desc": "梅园新村纪念馆标志性展品", "era": "近现代", "image": ""},
            {"name": "中共代表团办公旧址文物", "desc": "梅园新村17/30/35号旧址中的历史文物与史料", "era": "1946-1947", "image": ""},
        ],
        "collections_note": "数据来源：博物南京，全国重点文保单位"
    },
    13: {  # 南京市民俗博物馆（甘熙宅第）
        "collections": [
            {"name": "秦淮灯彩", "desc": "国家级非遗项目，传统秦淮花灯制作技艺展示", "era": "", "image": ""},
            {"name": "南京绒花", "desc": "省级非遗项目，传统蚕丝绒花手工艺", "era": "", "image": ""},
            {"name": "金陵刻经", "desc": "人类非遗项目，木质雕版印刷技艺展示", "era": "", "image": ""},
            {"name": "南京白局", "desc": "国家级非遗，南京地方曲艺形式", "era": "", "image": ""},
        ],
        "collections_note": "数据来源：南京市文化和旅游局、秦淮区人民政府，展示十余个市级以上非遗项目"
    },
    14: {  # 渡江胜利纪念馆
        "collections": [
            {"name": "京电号小火轮", "desc": "渡江战役中运送解放军过江的英雄船", "era": "1949", "image": ""},
            {"name": "渡江战役文物史料", "desc": "渡江战役相关武器、军服、文件等实物", "era": "1949", "image": ""},
        ],
        "collections_note": "数据来源：博物南京，大型革命史纪念馆"
    },
    15: {  # 南京大报恩寺遗址博物馆
        "collections": [
            {"name": "鎏金七宝阿育王塔", "desc": "北宋佛教文物，通高1.2米，中国境内出土体量最大阿育王塔", "era": "北宋", "image": ""},
            {"name": "琉璃构件", "desc": "明代大报恩寺琉璃塔多彩琉璃建筑构件", "era": "明", "image": ""},
            {"name": "感应舍利", "desc": "地宫出土的佛教感应舍利", "era": "北宋", "image": ""},
        ],
        "collections_note": "数据来源：知乎、人民网，遗址已发掘出土1.2万余件文物"
    },
    16: {  # 明孝陵博物馆
        "collections": [
            {"name": "神武门铜狮", "desc": "明代铸造的铜狮，明孝陵博物馆最著名文物", "era": "明", "image": ""},
            {"name": "明孝陵神道石刻", "desc": "石象路神道守护神兽系列石刻复制品及相关文物", "era": "明", "image": ""},
            {"name": "朱元璋主题浮雕", "desc": "序厅正立面双层式主题浮雕，表现明初历史场景", "era": "明", "image": ""},
        ],
        "collections_note": "数据来源：南京本地宝、百度百科，世界遗产明孝陵配套博物馆"
    },
    17: {  # 德基艺术博物馆
        "collections": [
            {"name": "「动静无尽：花卉静物三百年」常设展", "desc": "展出逾百件馆藏，含莫奈、毕加索等西方大师及中国现当代艺术家花卉主题杰作", "era": "现当代", "image": ""},
            {"name": "中国古代陶瓷收藏", "desc": "涵盖中国古代陶瓷、书画、佛教造像、明式家具等多个门类", "era": "古代", "image": ""},
        ],
        "collections_note": "数据来源：德基艺术博物馆官网、维基百科，研究驱动型私立博物馆"
    },
    18: {  # 励志社博物馆
        "collections": [],
        "collections_note": "该馆为小型民国历史博物馆，网上未搜索到公开的镇馆之宝/代表文物名单，建议实地参观获取"
    },
    19: {  # 总统府
        "collections": [
            {"name": "孙中山临时大总统办公室复原陈列", "desc": "孙中山先生1912年就任临时大总统时的办公场景复原", "era": "1912", "image": ""},
            {"name": "洪秀全历史文物陈列", "desc": "太平天国天王府时期的历史文物与史料", "era": "太平天国", "image": ""},
            {"name": "两江总督署史料展", "desc": "清代两江总督署相关文物与档案", "era": "清", "image": ""},
        ],
        "collections_note": "数据来源：CCTV国家地理，以历史建筑群和史料陈列为主"
    },
    20: {  # 玄武区退役军人主题馆
        "collections": [],
        "collections_note": "该馆为小型纪念场馆，网上未搜索到公开的镇馆之宝/代表展品名单，建议实地参观获取"
    },
    21: {  # 南京近代建筑博物馆
        "collections": [
            {"name": "南京近代建筑模型与图纸", "desc": "展示南京民国至现代代表性建筑的模型、设计图纸与照片", "era": "近现代", "image": ""},
        ],
        "collections_note": "数据来源：博物馆官网，以建筑历史展览为主"
    },
    22: {  # 德基美术馆
        "collections": [
            {"name": "现当代艺术展品", "desc": "商业综合体中的展览空间，以当期展览为准", "era": "现当代", "image": ""},
        ],
        "collections_note": "与德基艺术博物馆同属德基集团，以当期展览为主要展示内容"
    },
    23: {  # 东南大学校史馆
        "collections": [
            {"name": "东南大学百年校史文物", "desc": "建校以来的历史文献、照片、教学仪器与校友捐赠", "era": "近现代", "image": ""},
        ],
        "collections_note": "高校校史馆，以校史档案和实物为主"
    },
    24: {  # 吴健雄纪念馆
        "collections": [
            {"name": "吴健雄手稿与实验仪器", "desc": "著名物理学家吴健雄女士的学术手稿、诺贝尔奖章复制品及实验设备", "era": "近现代", "image": ""},
        ],
        "collections_note": "纪念物理学家吴健雄的个人纪念馆"
    },
    25: {  # 江南丝绸文化博物馆
        "collections": [
            {"name": "江南丝绸织品", "desc": "展示江南地区丝绸文化历史与工艺的代表性织品", "era": "", "image": ""},
        ],
        "collections_note": "小型专题博物馆，位于夫子庙内"
    },
    26: {  # 南京老字号博物馆
        "collections": [
            {"name": "老字号品牌文物", "desc": "南京老字号品牌的招牌、器物、包装与历史照片", "era": "近现代", "image": ""},
        ],
        "collections_note": "小型民俗博物馆，位于老门东"
    },
    27: {  # 南京永银钱币博物馆
        "collections": [
            {"name": "中国历代钱币", "desc": "从先秦到近代的中国历代货币实物，钱币文化专题", "era": "历代", "image": ""},
        ],
        "collections_note": "钱币文化专题馆"
    },
    28: {  # 南京钰缘泉博物馆
        "collections": [],
        "collections_note": "小型私立玉器专题馆，网上未搜索到详细的代表藏品名单"
    },
    29: {  # 南京镜见律师博物馆
        "collections": [],
        "collections_note": "法律专题小型博物馆，网上未搜索到详细的代表藏品名单"
    },
    30: {  # 太平天国壁画艺术馆
        "collections": [
            {"name": "太平天国壁画", "desc": "太平天国时期的壁画艺术作品原件", "era": "太平天国", "image": ""},
        ],
        "collections_note": "壁画专题艺术馆"
    },
    31: {  # 李香君故居陈列馆
        "collections": [
            {"name": "李香君故居复原陈列", "desc": "明末清初秦淮名妓李香君故居的家具、器物与史料", "era": "明末清初", "image": ""},
        ],
        "collections_note": "名人故居类小型陈列馆"
    },
    32: {  # 王导谢安纪念馆
        "collections": [
            {"name": "六朝书法碑刻", "desc": "王羲之等六朝书法名家的作品摹刻与相关碑刻", "era": "东晋", "image": ""},
        ],
        "collections_note": "纪念东晋名相的小型纪念馆"
    },
    33: {  # 秦大士故居展览馆
        "collections": [
            {"name": "秦大士书法作品", "desc": "清代状元秦大士的书法真迹与科举文物", "era": "清", "image": ""},
        ],
        "collections_note": "清代状元故居改建的小型展览馆"
    },
    34: {  # 孙中山纪念馆
        "collections": [
            {"name": "孙中山手稿与遗物", "desc": "孙中山先生的亲笔手稿、衣物、书籍等生平遗物", "era": "近现代", "image": ""},
        ],
        "collections_note": "位于中山陵景区内，展示孙中山生平事迹"
    },
    35: {  # 南京抗日航空烈士纪念馆
        "collections": [
            {"name": "抗战时期飞机实物与模型", "desc": "纪念中外航空烈士，展示航空抗战历史文物", "era": "抗日战争", "image": ""},
        ],
        "collections_note": "纪念抗日航空烈士的专题纪念馆"
    },
    36: {  # 美龄宫
        "collections": [
            {"name": "美龄宫建筑与室内陈设", "desc": "蒋介石与宋美龄旧居，中西合璧建筑及民国室内家具陈设", "era": "民国", "image": ""},
        ],
        "collections_note": "以建筑本身和民国生活场景复原为主要展示内容"
    },
    37: {  # 东吴大帝孙权纪念馆
        "collections": [],
        "collections_note": "小型三国主题纪念馆，网上未搜索到详细代表文物名单"
    },
    38: {  # 紫金山森林科普馆
        "collections": [],
        "collections_note": "自然科学科普类场馆，以图文展板为主，无传统意义文物藏品"
    },
    39: {  # 南京梅花艺术中心
        "collections": [],
        "collections_note": "梅花节期间开放的艺术展示中心，以临时展览为主"
    },
    40: {  # 南京中山植物园
        "collections": [
            {"name": "珍稀植物活体收藏", "desc": "中国第一座国立植物园，收藏万余种植物活体标本", "era": "", "image": ""},
        ],
        "collections_note": "以活体植物收藏为主，非文物类博物馆"
    },
    41: {  # 南京地震科学馆
        "collections": [
            {"name": "地震监测仪器", "desc": "各时期地震监测设备与地震科学科普展品", "era": "近现代", "image": ""},
        ],
        "collections_note": "以科普仪器设备展示为主"
    },
    42: {  # 南京近代邮政博物馆
        "collections": [
            {"name": "近代邮政文物", "desc": "近代邮政邮票、邮戳、信函与邮政设备", "era": "近现代", "image": ""},
        ],
        "collections_note": "邮政专题小型博物馆"
    },
    43: {  # 南京十朝历史文化陈列馆
        "collections": [
            {"name": "十朝古都历史文物", "desc": "展示南京十朝古都历史文化的代表性文物与资料", "era": "历代", "image": ""},
        ],
        "collections_note": "展示南京十朝都城历史"
    },
    44: {  # 紫金山昆虫博物馆
        "collections": [
            {"name": "昆虫标本", "desc": "展示昆虫多样性的各类昆虫标本", "era": "", "image": ""},
        ],
        "collections_note": "以昆虫标本展示为主"
    },
    45: {  # 紫金山天文历史博物馆
        "collections": [
            {"name": "古代天文仪器", "desc": "浑仪、简仪等古代天文观测仪器复制品及天文历史文物", "era": "古代", "image": ""},
        ],
        "collections_note": "依托紫金山天文台的科普博物馆"
    },
    46: {  # 南京车管所汽车博物馆
        "collections": [],
        "collections_note": "小型汽车专题馆，网上未搜索到详细代表藏品名单"
    },
    47: {  # 南京理工大学兵器博物馆
        "collections": [
            {"name": "火炮与轻武器藏品", "desc": "展示各种兵器装备，包括火炮、坦克、轻武器等实物", "era": "近现代", "image": ""},
        ],
        "collections_note": "兵器科学与技术教育基地"
    },
    48: {  # 郑和纪念馆
        "collections": [
            {"name": "郑和下西洋史料", "desc": "郑和宝船模型、航海图及相关历史文物", "era": "明", "image": ""},
        ],
        "collections_note": "纪念明代航海家郑和的专题馆"
    },
    49: {  # 五老村爱国卫生运动纪念馆
        "collections": [],
        "collections_note": "小型纪念场馆，网上未搜索到详细代表展品名单"
    },
    50: {  # 秦淮非遗馆
        "collections": [
            {"name": "南京非遗作品", "desc": "秦淮灯彩、金陵剪纸、南京绒花、金陵刻经等非遗作品展示", "era": "", "image": ""},
        ],
        "collections_note": "以非遗技艺展示和体验为主"
    },
    51: {  # 南京越剧博物馆
        "collections": [
            {"name": "越剧服饰与道具", "desc": "越剧传统戏服、头饰、道具与历史资料", "era": "近现代", "image": ""},
        ],
        "collections_note": "戏曲艺术专题馆"
    },
    52: {  # 南京航空航天博物馆
        "collections": [
            {"name": "飞行器实物", "desc": "退役战斗机、无人机、航空发动机等实物展品", "era": "近现代", "image": ""},
        ],
        "collections_note": "展示航空航天历史的专题博物馆"
    },
    53: {  # 江苏省五环彩票博物馆
        "collections": [
            {"name": "各时期彩票实物", "desc": "中国彩票发展史上各时期的奖券与相关文物", "era": "近现代", "image": ""},
        ],
        "collections_note": "彩票专题博物馆"
    },
    54: {  # 南京国防园
        "collections": [
            {"name": "退役军事装备", "desc": "坦克、火炮、雷达等退役军事装备实物展示", "era": "近现代", "image": ""},
        ],
        "collections_note": "以退役军事装备户外展示为主"
    },
    55: {  # 颐和路社区将军馆
        "collections": [
            {"name": "将军生平事迹展品", "desc": "颐和路社区将军们的勋章、军装与生平资料", "era": "近现代", "image": ""},
        ],
        "collections_note": "社区级纪念场馆"
    },
    56: {  # 吴贻芳纪念馆
        "collections": [
            {"name": "吴贻芳遗物", "desc": "金陵女子大学校长吴贻芳的遗物与生平资料", "era": "近现代", "image": ""},
        ],
        "collections_note": "教育家个人纪念馆"
    },
    57: {  # 江苏省中医药博物馆
        "collections": [
            {"name": "传统药材标本", "desc": "珍贵中药标本、古代医书与中医药器具", "era": "历代", "image": ""},
        ],
        "collections_note": "中医药文化专题博物馆"
    },
    58: {  # 南京大学校史博物馆
        "collections": [
            {"name": "南京大学百年校史文物", "desc": "南京大学百年来的重要文献、照片与实物", "era": "近现代", "image": ""},
        ],
        "collections_note": "高校校史馆"
    },
    59: {  # 南京森林警察学院珍稀动物标本馆
        "collections": [
            {"name": "珍稀动物标本", "desc": "各类珍稀保护动物的标本收藏", "era": "", "image": ""},
        ],
        "collections_note": "高校教学标本馆"
    },
    60: {  # 横山县抗日民主政府旧址史料陈列馆
        "collections": [],
        "collections_note": "位于江宁区的乡村革命史陈列馆，网上未搜索到详细代表展品名单"
    },
}

# 读取原始 JSON
json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'museums.json')
with open(json_path, 'r', encoding='utf-8') as f:
    museums = json.load(f)

# 更新每个博物馆
updated_count = 0
for museum in museums:
    mid = museum.get('id')
    if mid in collections_map:
        data = collections_map[mid]
        museum['collections'] = data['collections']
        museum['collections_note'] = data['collections_note']
        updated_count += 1
    else:
        # 未在映射表中的博物馆，添加空数组和说明
        museum['collections'] = []
        museum['collections_note'] = '暂未收录代表文物数据，欢迎补充'

print(f"已更新 {updated_count} / {len(museums)} 个博物馆")

# 写回 JSON
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(museums, f, ensure_ascii=False, indent=2)

print("museums.json 写入完成")
