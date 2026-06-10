# scripts/update_news_data.py
"""将从 firecrawl 爬取到的新闻数据写入 museums.json"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSEUMS_FILE = os.path.join(BASE_DIR, 'data', 'museums.json')

# 从 firecrawl 采集到的新闻数据
NEWS_DATA = {
    1: [  # 南京博物院
        {"title": "世界珍宝——印度莫卧儿王朝艺术展", "desc": "2026.5.19 - 2026.8.25，重磅国际特展", "link": "https://www.njmuseum.com/zh/generalDetails?id=1360", "date": "2026-05-19"},
        {"title": "灯影——南京博物院藏陕西皮影艺术展", "desc": "2026年5月15日开幕，精美皮影艺术", "link": "https://www.njmuseum.com/zh/generalDetails?id=1358", "date": "2026-05-15"},
        {"title": "君到姑苏见——明代以来书画中的苏州景观", "desc": "2026年4月4日-6月12日，苏州主题书画展", "link": "https://www.njmuseum.com/zh/generalDetails?id=1356", "date": "2026-04-04"},
        {"title": "邂逅莫卧儿艺术风华之自然诗意", "desc": "2026年6月6日活动", "link": "https://activity.njmuseum.com.cn/reservation/activity/out/activityOutList.do", "date": "2026-06-06"},
        {"title": "遇见——你好，古人的香薰炉", "desc": "2026年6月7日少儿社教活动", "link": "https://activity.njmuseum.com.cn/reservation/activity/out/activityOutList.do", "date": "2026-06-07"},
        {"title": "珍宝奇遇记——馆藏探秘·文物解码", "desc": "2026年6月6日青少年研学活动", "link": "https://activity.njmuseum.com.cn/reservation/activity/out/activityOutList.do", "date": "2026-06-06"},
    ],
    6: [  # 科举博物馆
        {"title": "展览上新丨《秦淮河》特展重磅推出！", "desc": "展示秦淮河相关文物与文化的新特展", "link": "https://www.njiemuseum.com/gongshi_1/277.html", "date": ""},
        {"title": "关于南京中国科举博物馆免费开放日的公告", "desc": "免费开放日活动公告", "link": "https://www.njiemuseum.com/gongshi_1/281.html", "date": ""},
        {"title": "状元大讲堂第121讲——秦淮河：文学艺术的崇高地位", "desc": "秦淮河文学艺术主题讲座", "link": "https://www.njiemuseum.com/gongshi_1/275.html", "date": ""},
        {"title": "邀你赴约！贡院张灯-龙门开启仪式", "desc": "沉浸式体验科举雅韵新年活动", "link": "https://www.njiemuseum.com/newsxq/279.html", "date": ""},
        {"title": "让千年科举文化'活'在当下——2025年度创新实践纪实", "desc": "博物馆2025年度创新实践回顾", "link": "https://www.njiemuseum.com/gongshi_1/272.html", "date": ""},
        {"title": "活动回顾丨新春启序，温情相伴，科举博物馆期待再相逢", "desc": "春节期间活动回顾", "link": "https://www.njiemuseum.com/gongshi_1/278.html", "date": ""},
    ],
    8: [  # 侵华日军南京大屠杀遇难同胞纪念馆
        {"title": "档案在此，容不得日方抵赖", "desc": "最新馆藏档案展陈", "link": "https://www.19371213.com.cn/sylm/xwzx/202606/t20260608_5853270.html", "date": "2026-06-08"},
        {"title": "'三个必胜'主题展览", "desc": "常设主题展览", "link": "https://www.19371213.com.cn", "date": ""},
        {"title": "八十年铁证归来——馆藏东京审判档案文献展", "desc": "正在展出的东京审判档案文献专题展", "link": "https://www.19371213.com.cn/sylm/xwzx/202606/t20260602_5850632.html", "date": "2026-06-02"},
        {"title": "多国学者齐聚沪宁：东京审判正义不可撼动！", "desc": "东京审判开庭80周年国际研讨会报道", "link": "https://www.19371213.com.cn/sylm/xwzx/202606/t20260602_5850631.html", "date": "2026-06-02"},
        {"title": "留言月历丨尽己所能，让越来越多人知晓历史真相", "desc": "观众留言精选展示", "link": "https://www.19371213.com.cn/sylm/xwzx/202606/t20260602_5850634.html", "date": "2026-06-02"},
    ],
    19: [  # 总统府（南京中国近代史遗址博物馆）
        {"title": "孙中山与南京临时政府文物史料展", "desc": "展示孙中山在南京建立临时政府的历史", "link": "https://www.njztf.cn/cn/universal/detail/275.html", "date": ""},
        {"title": "红旗插上总统府", "desc": "展现1949年南京解放的历史瞬间", "link": "https://www.njztf.cn/exhibition_details/978.html", "date": ""},
        {"title": "人间正道是沧桑——近现代史主题展", "desc": "近现代历史变迁主题展览", "link": "https://www.njztf.cn/exhibition_details/1014.html", "date": ""},
        {"title": "洪秀全与天朝宫殿", "desc": "太平天国历史陈列", "link": "https://www.njztf.cn/cn/universal/detail/276.html", "date": ""},
        {"title": "清两江总督与总督署", "desc": "清代两江总督历史陈列", "link": "https://www.njztf.cn/cn/universal/detail/155.html", "date": ""},
        {"title": "以实战演练筑牢文旅安全之基", "desc": "景区安全管理演练新闻", "link": "https://www.njztf.cn/news/detail/1084.html", "date": ""},
    ],
    86: [  # 奥林匹克博物馆
        {"title": "'武动青春·逐梦青奥' 博物馆日主题活动成功举办", "desc": "2026年博物馆日主题活动", "link": "http://www.olympicmuseum-nj.org/NewsCenter/NewsInfo?id=daa995fa-45bd-4163-9e0a-dd86ae10485f&type=1", "date": ""},
        {"title": "联动长三角 逐梦绿茵场——长三角体育文化展", "desc": "长三角体育文化展系列活动", "link": "http://www.olympicmuseum-nj.org/NewsCenter/NewsInfo?id=5c536a7e-ae6f-4a08-a14c-acfa0d163880&type=1", "date": ""},
        {"title": "走进奥博·体育联结世界丨青少年在博物馆乐享运动", "desc": "青少年体育互动体验活动", "link": "http://www.olympicmuseum-nj.org/NewsCenter/NewsInfo?type=1&id=7540a15b-62a3-406d-8827-1948d7690018", "date": ""},
        {"title": "'永恒圣火·共赴未来' 11周年馆庆活动圆满举办", "desc": "博物馆11周年馆庆活动", "link": "http://www.olympicmuseum-nj.org/NewsCenter/NewsInfo?id=4db94769-d5e8-4913-9083-bb36a4a4be51&type=1", "date": ""},
        {"title": "南京奥林匹克博物馆取消预约入馆公告", "desc": "入馆方式调整公告", "link": "http://www.olympicmuseum-nj.org/NewsCenter/NewsInfo?id=f103c0d4-a659-4f41-8cee-95cb4935f26d&type=1", "date": ""},
        {"title": "南京大学终身教育学院与奥博共建实践教学基地", "desc": "馆校合作共建新闻", "link": "http://www.olympicmuseum-nj.org/NewsCenter/NewsInfo?type=1&id=8cd3ab9b-b601-4933-bcbf-cd25968da2cf", "date": ""},
    ],
    17: [  # 德基艺术博物馆
        {"title": "华夏世界现代艺术藏品系列展——动静无尽", "desc": "丰富多彩的现代艺术展", "link": "https://www.dejiart.com/exhibition/huahuashijiexiandangdaiyishudiancangxiliezhandongjingwujin/", "date": ""},
        {"title": "Beeple：来自人造未来的故事", "desc": "数字艺术先驱Beeple作品展", "link": "https://www.dejiart.com/exhibition/beeple-laizirenzaoweilaidegushi/", "date": ""},
        {"title": "奈良美智的玩具屋", "desc": "日本艺术家奈良美智特展", "link": "https://www.dejiart.com/exhibition/nailiangmeizhiluwujuwu/", "date": ""},
        {"title": "金陵图书数字艺术展", "desc": "现代数字艺术与传统书籍的结合", "link": "https://www.dejiart.com/exhibition/jinlingtushuziyishuzhan/", "date": ""},
        {"title": "动静有形艺术展：百年芳珂宝艺术展", "desc": "百年珠宝艺术回顾展", "link": "https://www.dejiart.com/exhibition/dongjingyouxingyishubainianfankeyabaogaojizhubaoyishuzhan/", "date": ""},
        {"title": "飞跃之线：未来可能的世界", "desc": "艺术家的未来视角与构想展", "link": "https://www.dejiart.com/exhibition/feiyuezhixianweilekenengdeshijie/", "date": ""},
    ],
    89: [  # 静海寺纪念馆
        {"title": "中英《南京条约》史实展", "desc": "牢记历史、不忘过去，以史为鉴、开创未来", "link": "https://www.njjhs.cn/smart_community.html", "date": ""},
        {"title": "传承红色基因 厚植家国情怀——总体国家安全观研学", "desc": "全民国家安全教育日研学活动回顾", "link": "https://njjhs.cn/news/495.html", "date": ""},
        {"title": "传承航海精神，点亮科技梦想——郑和下西洋620周年研学活动", "desc": "郑和下西洋620周年纪念暨航海日夏令营", "link": "https://njjhs.cn/news/194.html", "date": ""},
        {"title": "冬韵织暖 春启新章——陈列馆里迎新春", "desc": "春节传统文化活动", "link": "https://njjhs.cn/news/263.html", "date": ""},
    ],
    105: [  # 民间抗日战争博物馆
        {"title": "纪念长征胜利90周年——'一场展览+一场讲座'", "desc": "长征胜利90周年专题活动", "link": "http://www.1937nanjing.org/news/shishiyaowen/2026/0514/5736.html", "date": "2026-05-14"},
        {"title": "2352个名字与980只老兵手印——民间博物馆的抗战记忆", "desc": "博物馆收藏的抗战记忆深度报道", "link": "http://www.1937nanjing.org/news/shishiyaowen/2025/1213/5725.html", "date": "2025-12-13"},
        {"title": "抗战胜利80周年主题展向公众开放，5件展品来自我馆", "desc": "抗战胜利80周年专题展览", "link": "http://www.1937nanjing.org/news/shishiyaowen/2025/0710/5612.html", "date": "2025-07-10"},
        {"title": "《南京大屠杀档案》首次完整入藏日本高校", "desc": "档案海外传播新闻", "link": "http://www.1937nanjing.org/news/shishiyaowen/2025/0729/5613.html", "date": "2025-07-29"},
        {"title": "一个有'声'有'色'的博物馆——我馆这样演绎'红军不怕远征难'", "desc": "创新展陈方式报道", "link": "http://www.1937nanjing.org/news/shishiyaowen/2026/0514/5737.html", "date": "2026-05-14"},
    ],
    47: [  # 兵器博物馆
        {"title": "5.18国际博物馆日——'兵器王国'里精彩纷呈", "desc": "第48个国际博物馆日特色活动", "link": "https://bqbwg.njust.edu.cn/90/11/c3344a364561/page.htm", "date": ""},
        {"title": "纪念人民兵工创建95周年专题讲座", "desc": "在兵器博物馆举行的专题讲座", "link": "https://bqbwg.njust.edu.cn/8e/1e/c3344a364062/page.htm", "date": ""},
        {"title": "关于'5.18国际博物馆日'兵博对公众开放的通知", "desc": "博物馆日开放通知", "link": "https://bqbwg.njust.edu.cn/8e/1f/c3346a364063/page.htm", "date": ""},
        {"title": "关于兵器博物馆'五一节'期间对公众开放公告", "desc": "五一假期开放公告", "link": "https://bqbwg.njust.edu.cn/8a/c9/c3346a363209/page.htm", "date": ""},
        {"title": "首个春假'兵器王国'里娃娃多", "desc": "春假期间亲子参观盛况", "link": "https://bqbwg.njust.edu.cn/87/5b/c3344a362331/page.htm", "date": ""},
    ],
    90: [  # 拉贝与国际安全区纪念馆
        {"title": "德国汉堡市议长费特一行到访拉贝纪念馆", "desc": "国际交流访问活动", "link": "http://rabe.nju.edu.cn/zxdt/zxbd/20260416/i373078.html", "date": "2026-04-16"},
        {"title": "行走读书·跟着《拉贝日记》重走南京安全区", "desc": "主题读书行走活动启动仪式", "link": "http://rabe.nju.edu.cn/zxdt/hdfb/20240331/i263271.html", "date": "2024-03-29"},
        {"title": "牢记历史 珍爱和平——馆院合作共建爱国主义教育基地", "desc": "馆院合作共建活动", "link": "http://rabe.nju.edu.cn/zxdt/hdfb/20210629/i203576.html", "date": ""},
        {"title": "让世界充满爱与和平——拉贝纪念馆主题活动", "desc": "和平主题教育活动", "link": "http://rabe.nju.edu.cn/zxdt/hdfb/20201221/i174840.html", "date": ""},
    ],
}


def main():
    with open(MUSEUMS_FILE, 'r', encoding='utf-8-sig') as f:
        museums = json.load(f)
    
    total = 0
    for museum in museums:
        mid = museum.get('id', 0)
        if mid in NEWS_DATA:
            museum['news'] = NEWS_DATA[mid]
            museum['last_updated'] = '2026-06-09'
            total += len(NEWS_DATA[mid])
            print(f"[{mid}] {museum.get('name', '?')}: {len(NEWS_DATA[mid])} 条新闻")
    
    with open(MUSEUMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(museums, f, ensure_ascii=False, indent=4)
    
    print(f"\n总计: {len(NEWS_DATA)} 个博物馆, {total} 条新闻/展览")

if __name__ == '__main__':
    main()
