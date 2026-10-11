#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIPRIS 상표권 판정, 내 브랜드(택갈이) 클린 상품명, 쿠팡·국내 실측 스펙/재질/성분 요약,
저비용 KC·식약처·생활화학 인증 돌파 가이드 및 1688 중국 공장 문의 메시지(중문+한글) 생성 엔진.
"""
import re
import urllib.parse

GLOBAL_BRANDS = [
    ("스탠리", r"스탠리|stanley"),
    ("이케아", r"이케아|ikea|nordli|홀메루드"),
    ("나비엔매직", r"나비엔매직|나비엔"),
    ("아식스", r"아식스|asics"),
    ("호카", r"호카|hoka"),
    ("룰루레몬", r"룰루레몬|lululemon"),
    ("무인양품", r"무인\s*양품|muji"),
    ("님봇", r"님봇|niimbot"),
    ("AULA 독거미", r"\baula\b|독거미"),
    ("필립스", r"필립스|philips"),
    ("릴리바이레드", r"릴리바이레드|lilybyred"),
    ("마녀공장", r"마녀공장"),
    ("메디필", r"메디필|medipeel"),
    ("브이티(VT)", r"브이티코스메틱|브이티|\bvt\b"),
    ("셀퓨전씨", r"셀퓨전씨"),
    ("밀크바오밥", r"밀크바오밥"),
    ("에스트라", r"에스트라|aestura"),
    ("비플레인", r"비플레인|beplain"),
    ("도브", r"\bdove\b|도브"),
    ("콜게이트", r"콜게이트|colgate"),
    ("올라플렉스", r"올라플렉스|olaplex"),
    ("츠바키", r"츠바키|tsubaki"),
    ("고바야시", r"고바야시"),
    ("휴족시간", r"휴족시간"),
    ("라이온(LION)", r"라이온|\blion\b|나녹스|nanox"),
    ("홈스타", r"홈스타"),
    ("미세스마이어스", r"미세스\s*마이어스"),
    ("란도린", r"란도린"),
    ("록타이트", r"록타이트|loctite"),
    ("에너자이저", r"에너자이저|energizer"),
    ("WORX", r"\bworx\b"),
    ("야마자키실업", r"야마자키실업"),
    ("인제뉴어티", r"인제뉴어티|ingenuity"),
    ("몽벨", r"몽벨|mont-bell"),
    ("레노바", r"레노바|renova"),
    ("스빈또", r"스빈또|svinto"),
    ("핑크스터프", r"핑크스터프"),
    ("키스뉴욕", r"키스뉴욕"),
    ("클라뷰", r"클라뷰"),
    ("언리시아", r"언리시아"),
    ("본셉", r"본셉"),
    ("투에딧", r"투에딧"),
    ("클리덤", r"클리덤"),
    ("라비오뜨", r"라비오뜨"),
    ("아이메디아", r"아이메디아"),
    ("보다나", r"보다나|vodana"),
    ("호유(시엘로)", r"호유|시엘로"),
    ("사이오스", r"사이오스|syoss"),
    ("샤넬", r"샤넬|chanel"),
    ("디올", r"디올|dior"),
    ("구찌", r"구찌|gucci"),
    ("프라다", r"프라다|prada"),
    ("에르메스", r"에르메스|hermes"),
    ("루이비통", r"루이비통|louis\s*vuitton"),
    ("롤렉스", r"롤렉스|rolex"),
    ("이솝", r"이솝|aesop"),
    ("산타마리아노벨라", r"산타마리아노벨라"),
    ("설화수", r"설화수"),
    ("나이키", r"나이키|nike"),
    ("아디다스", r"아디다스|adidas"),
]

COMPAT_BRANDS = [
    ("아크테릭스", r"아크테릭스"),
    ("테슬라", r"테슬라"),
    ("맥세이프", r"맥세이프|magsafe"),
    ("갤럭시워치/버즈", r"갤럭시워치|갤럭시\s*버즈"),
    ("에어팟", r"에어팟"),
    ("몽벨", r"몽벨|mont-bell"),
]

SELLER_BRANDS = [
    "틈브릭", "투데이리빙", "안심구매단", "센토바", "27리빙", "개과천선", "브리즈문", "룸앤무드",
    "아이작큐브", "모더너리", "마켓피아", "여우소리", "인플리바타", "윰스모르", "더벨라", "쥬얼",
    "엔플로", "오코로", "데일리픽", "페어토", "코어밸런", "귀월미", "그루홈", "이플스토리",
    "젊은이마켓", "러블리컬", "파스텔펫", "스콩", "푸르미", "맥도도", "키젤로", "홈플래닛",
    "슬라이드스트로우", "르멘트", "루아르모", "와이엔", "넛토", "다다", "달미컴", "러블리씨씨",
    "원이네", "미츠케", "엘이씨", "디클펫", "몽리코", "락톡마켓", "호인트", "카템", "트래블이지",
    "비공구오", "라임리빙", "깔끔더하기", "오엔리빙", "이글웨이", "아띠래빗", "퀸즈앤킹스",
    "딩동펫", "우이지아", "몬스터팜", "토요요", "알보우", "키들", "럭키썸", "스코라", "무식이네",
    "도블레", "티핏", "디스톤", "지티스", "조앤제이", "오즈토이", "아이젠베르그", "라라홀릭",
    "유키", "홈비", "솔리드", "콴텀", "블럭마트", "아이한코", "툴콘", "공간백서", "하이하",
    "플라워치", "파이어립", "리빙글로리", "코너팩토리", "다알리아", "존글로벌", "에테르코",
    "레인보우플라워", "굿라이프", "딜리버룸", "실버카우", "리브나인", "KOGEL", "독일 코겔",
    "루베이", "DlyEase", "MERAKA", "DSAZ", "KIFFJOIT", "yeyes-22", "Aimeen", "CYLIFE",
    "Kleeno", "Mankiw맨큐", "Mankiw", "SAHINER", "Tiger Pavilion", "DelightZone",
    "Richmagic", "KEFEYA", "HanilElectric", "4-ZIP", "소르벨라", "얼띵스", "보아스", "SNUG",
    "브리센스", "폴메디슨", "브레인코스모스", "아이숲", "연하", "Arbe", "NY20", "다우몰",
    "굿픽샵", "K : with", "RON", "GOSS", "GSDF-7012", "걸리쥬", "아웃플레이스", "리빙베이직",
    "어반라이프", "네이처하이크", "올리빙", "소소일소", "바겐슈타이거", "코멧", "자주", "모던하우스",
]

CN_ITEM_MAP = [
    # 1. 고특정 복합/단일 제품 (최우선 매칭)
    (r"창문.*로봇|로봇.*청소기|유리창.*청소기", "智能双向喷水擦窗机器人/全自动擦玻璃神器"),
    (r"티슈.*케이스|각티슈|휴지케이스|냅킨.*케이스", "创意多功能纸巾盒/桌面抽纸收纳盒"),
    (r"칫솔.*살균기|살균.*칫솔|칫솔.*소독기", "智能UVC紫外线牙刷消毒器/壁挂烘干置物架"),
    (r"공구함|토르.*망치|망치.*공구", "雷神之锤多功能五金工具箱套装/家用维修工具组"),
    (r"캐리어.*바퀴.*커버|바퀴.*보호.*커버", "行李箱轮子硅胶保护套/静音防磨耐磨套"),
    (r"캐리어.*선반|선반.*캐리어|접이식.*캐리어", "多功能可折叠带置物架行李箱/便携登机箱"),
    (r"돌잔치.*신발|아기.*신발|보행기화|유아.*덧신", "婴儿学步鞋/宝宝抓周软底鞋"),
    (r"이불.*옷걸이|원형.*옷걸이|나선형.*옷걸이", "螺旋式床单被套晾衣架/大件被褥晾晒架"),
    (r"사이드미러.*스퀴지|백미러.*스퀴지", "汽车后视镜伸缩刮水器/迷你便携除水刷"),
    (r"잔손.*젓가락|연습용.*젓가락|교정.*젓가락", "儿童学习练习筷/辅助训练筷"),
    (r"침대커버.*고정|침대시트.*고정|시트.*클립", "床单固定器扣件/床笠防滑防跑固定夹"),
    (r"세제.*수세미|수세미", "自带清洁剂百洁布/清洁海绵擦"),
    (r"토일렛|고양이.*화장실", "猫砂盆套装(含猫砂铲)"),
    (r"흔들침대|해먹.*침대|반려견.*침대", "宠物透气网布摇摇床/狗行军床"),
    (r"캘리그라피|수채화.*펜|브러쉬.*펜", "双头水彩毛笔/软头水彩笔套装"),
    (r"멀티쿠커|자동.*냄비|교반.*쿠커", "全自动搅拌炒菜机/多功能料理锅"),
    (r"텀블러|보온보냉|스트로우.*텀블러", "磁吸手机支架保温杯/不锈钢随行杯"),
    (r"분쇄기|그라인더|원두.*그라인더", "多功能电动研磨机/粉碎机"),
    (r"부스터.*캠핑의자|유아.*캠핑의자", "儿童便携折叠露营椅(带遮阳伞)"),
    (r"사다리.*행거|사다리.*옷걸이|원목.*행거", "实木梯形衣帽架/落地挂衣架"),
    (r"스팀청소기|고온.*스팀", "手持高温高压蒸汽清洁机"),
    (r"빵\s*슬라이서|토스트.*슬라이서", "手摇面包切片机(厚度可调)"),
    (r"요리용핀셋|호네누끼|생선.*가시.*제거", "不锈钢拔刺镊子/厨房去鱼刺夹"),
    (r"청소솔|틈새.*브러쉬|세탁기.*브러쉬", "滚筒洗衣机烘干机缝隙清洁刷套装"),
    (r"리드줄|산책줄|자동.*리드줄", "宠物360度防缠绕双头牵引绳"),
    (r"신발.*지우개|스웨이드.*클리너", "鞋用去污橡皮擦/绒面鞋清洁块"),
    (r"맥세이프.*거치대|마그네틱.*거치대", "超强磁吸MagSafe便携手机支架"),
    (r"소분\s*파우치|여행용.*파우치|워시백", "旅行收纳分装袋/洗漱包"),
    (r"동전지갑|하트.*파우치|키링.*파우치", "心形迷你零钱包/耳机收纳包"),
    (r"프린터|라벨프린터|감열식.*프린터", "迷你便携无墨热敏打印机"),
    (r"만년연필|영구.*연필", "永恒铅笔/免削无墨金属铅笔"),
    (r"로봇|반려로봇|데스크.*로봇", "AI智能桌面陪伴机器人"),
    (r"인덕션|핫플레이트|1구.*인덕션", "超薄迷你便携电磁炉"),
    (r"믹서기|블렌더|주서기", "无线便携榨汁杯/迷你搅拌机"),
    (r"착즙기|레몬.*착즙기", "无线电动水果榨汁机"),
    (r"실링팬|천장선풍기|캠핑.*팬", "LED带灯吊扇/露营帐篷吊扇"),
    (r"환풍기|배기팬|창문.*환풍기", "窗式静音排气扇/换气扇"),
    (r"고데기|매직기|헤어아이론", "USB无线便携直发梳/电热直卷发棒"),
    (r"뷰러|속눈썹.*고데기", "电热睫毛夹/便携睫毛卷翘器"),
    (r"케이블|충전선|고속.*케이블", "磁吸防缠绕Type-C快充数据线"),
    (r"요가블럭|폼롤러|보수볼|요가용품", "高密度EVA瑜伽砖/泡沫轴/波速球"),
    (r"머그|도자기.*컵|유리잔|찻잔", "创意陶瓷马克杯/玻璃水杯"),
    (r"도마|향균.*도마|스텐.*도마", "抗菌防霉厨房切菜板"),
    (r"채칼|슬라이서|만능.*채칼", "多功能不锈钢切菜器/刨丝器"),
    (r"거름망|여과기|티망|차망", "不锈钢厨房沥水篮/滤茶器"),
    (r"얼음틀|얼음\s*트레이|아이스.*몰드", "按压式硅胶冰格/储冰盒"),
    (r"쌀통|계량.*쌀통|잡곡통", "按压式防虫分格米桶"),
    (r"스퀴지|밀대|유리창.*닦이", "浴室刮水器/迷你海绵拖把"),
    (r"선반|정리대|트롤리|수납장", "免打孔置物架/移动收纳推车"),
    (r"바퀴|캐스터|이동받침|만능바퀴", "360度粘贴式万向轮/家电移动底座"),
    (r"우산|우비|레인코트|방수\s*커버", "晴雨伞/儿童雨衣/防雨鞋套"),
    (r"무드등|수유등|프로젝터|취침등", "LED氛围小夜灯/星空投影灯"),
    (r"이어워머|귀마개|방한.*귀마개", "发热保暖耳罩/防冻耳套"),
    (r"소방패치|소화.*패치|스티커.*소화", "配电箱自动灭火贴片/灭火胶囊"),
    (r"모기채|전기.*모기채|파리채", "折叠式电蚊拍/灭蚊灯二合一"),
    (r"모니터|휴대용.*모니터|보조.*모니터", "便携式高清扩展显示屏"),
    (r"현미경|디지털.*현미경", "高倍率便携数码显微镜"),
    (r"피지.*연화제|블랙헤드.*클리너", "黑头导出液/毛孔清洁浮出水"),
    (r"치약|구강.*청결|미백.*치약", "按压式果香美白去渍牙膏"),
    (r"혀\s*커버|구강.*보호대", "一次性舌苔清洁套/护齿套"),
    (r"섬유탈취제|룸스프레이|드레스퍼퓸", "衣物除味香氛喷雾/织物除菌液"),
    (r"순간접착제|강력.*접착제", "高强度耐水多功能快干强力胶"),
    (r"비데.*노즐.*세정|변기.*클리너", "智能马桶喷嘴清洁剂/泡沫除垢剂"),
    (r"쿨링시트|냉각.*패치|휴족.*시트", "舒缓足贴/清凉降温凝胶贴"),
    (r"새치커버|염색.*스틱|헤어.*마스카라", "一次性遮白发棒/快速补染笔"),
    (r"아이섀도우|무드키보드|메이크업.*팔레트", "多色眼影盘/高光修容彩妆盘"),
    (r"양말|쿠션.*양말|스포츠.*양말", "加厚毛圈减震运动袜/跑步毛巾底袜"),
    (r"어항.*장식|수족관.*조경", "鱼缸水族造景骷髅装饰摆件"),
    (r"서랍.*매트|싱크대.*매트|방수.*시트", "橱柜抽屉防潮防滑垫/加厚EVA垫"),
    (r"모래액자|샌드아트|무빙샌드", "3D流沙画摆件/减压沙漏创意夜灯"),
    (r"슬러시.*메이커|스무디.*컵", "自制DIY捏捏冰沙杯/雪糕机制冷杯"),
    (r"송장.*지우개|개인정보.*보호", "热敏纸涂改液/快递单信息消除滚轮"),
    (r"옷\s*접기|빨래.*접기.*판", "懒人家用叠衣板/衣服收纳折叠神器"),
    (r"바람막이|방풍.*자켓", "轻薄防风防泼水户外皮肤风衣"),
    (r"골프티|자석.*골프티", "磁吸高尔夫球钉/限位发球座"),
    (r"도어스텝|차량.*발판", "汽车车门锁扣脚踏板/车顶行李辅助踏板"),
    (r"디스펜서|물비누.*펌프", "按压式自动定量皂液器/洗洁精盒"),
    (r"빨대|스트로우|실리콘.*빨대", "可拆卸易清洗硅胶吸管套装"),
    (r"밀봉기|비닐.*접착기|실링기", "迷你便携家用封口机/零食保鲜机"),
    (r"안전가위|유아.*가위|공예.*가위", "儿童安全手工剪刀/弹簧省力剪"),
    (r"키보드.*키캡|키캡.*스티커", "个性机械键盘键帽/卡通键帽贴纸"),
    (r"안대|수면.*안대|온열.*안대", "3D立体遮光透气真丝睡眠眼罩"),
    (r"슬리퍼|욕실화|지압.*슬리퍼", "居家静音防滑漏水EVA浴室拖鞋"),
    (r"샤워기|필터.*샤워기", "增压过滤花洒喷头/除氯净水喷头"),
    (r"치실|치간.*칫솔", "高拉力超细便携牙线棒家庭装"),
    (r"목욕장갑|때타올|샤워.*타올", "加厚双面磨砂去角质搓澡巾"),
    (r"넥마운트|목걸이.*거치대", "第一人称视角挂脖手机支架"),
]

PROMO_BRACKET_RE = re.compile(
    r"^\s*(?:\[(?:국내배송|국내매장정품|일본정품|본사직배송|당일\s*출고|안전인증|안심소재|1\+1할인|재구매1위|180도\s*원터치\s*회전|로켓프레시|무상\s*A/S\s*\d*년?|사은품\s*증정|특가\s*세일|한정\s*수량|초특가)\]\s*)+",
    re.I,
)
LEADING_BRACKET_BRAND_RE = re.compile(r"^\s*\[([^\]]+)\]\s*")
CHEMICAL_RE = re.compile(r"세정제|클리너|세제|탈취제|방향제|접착제|록타이트|얼룩\s*제거|때밀이|물때|녹\s*제거|비데\s*노즐|페이스트|광택제", re.I)
BABY_RE = re.compile(r"유아|아기|신생아|어린이|아동|키즈|장난감|완구|보행기|붕붕카|워터건|버블|비눗방울|욕조", re.I)
QUASI_DRUG_RE = re.compile(r"치약|구강\s*보호대|혀\s*커버|구강\s*청결|살충제|소독제", re.I)
SANITARY_RE = re.compile(r"롤화장지|휴지|물티슈|일회용\s*타월|종이냅킨|칫솔|치간칫솔", re.I)


def _strip_seller_from_title(title: str, brand_to_strip: str | None = None) -> str:
    s = PROMO_BRACKET_RE.sub("", title or "").strip()
    s = re.sub(r"^본사정품\s+", "", s).strip()
    m_br = LEADING_BRACKET_BRAND_RE.match(s)
    if m_br:
        s = s[m_br.end():].strip()
    if brand_to_strip:
        pat = re.compile(r"^(?:" + re.escape(brand_to_strip) + r"|독일\s*코겔|MERAKA만능|Mankiw맨큐)\s*", re.I)
        s = pat.sub("", s).strip()
    for sb in sorted(SELLER_BRANDS, key=len, reverse=True):
        if s.lower().startswith(sb.lower()):
            rest = s[len(sb):].lstrip(" :-_/")
            if len(rest) >= 4:
                s = rest
                break
    # Strip trailing option tags (e.g. , 핑크, , 1개, , 9ml, 내추럴블랙 등)
    s = re.sub(r"\s*,\s*(?:[가-힣A-Za-z0-9/·& ]+|\d+(?:ml|g|kg|L|cm|mm|mAh|W|V|구|종|색|개입|매|켤레|팩|p|pcs|개|set|세트).*)$", "", s, flags=re.I).strip()
    # Strip trailing category suffixes (- 운동화, - 침대/쇼파 등)
    s = re.sub(r"\s*[-–]\s*[가-힣A-Za-z0-9/·& ]+$", "", s).strip()
    return s or title.strip()

NOUN_EXTRACT_PATTERNS = [
    r"창문.*로봇|로봇.*청소기", r"티슈.*케이스|휴지.*케이스", r"칫솔.*살균기|살균기",
    r"공구함|토르.*망치", r"바퀴.*커버", r"이불.*옷걸이", r"스퀴지", r"연습용.*젓가락|젓가락",
    r"침대.*고정|시트.*클립", r"수세미", r"토일렛|고양이\s*화장실", r"흔들침대|해먹",
    r"프린터|라벨기", r"인덕션", r"멀티쿠커|자동\s*냄비", r"텀블러|보온병",
    r"그라인더|분쇄기", r"캠핑의자|부스터의자", r"사다리행거|옷걸이|행거",
    r"스팀청소기|청소기", r"슬라이서|채칼", r"핀셋|호네누끼", r"청소솔|틈새브러쉬|브러쉬",
    r"리드줄|산책줄", r"신발지우개|클리너", r"거치대|스탠드", r"파우치|수납백",
    r"동전지갑|지갑", r"실링팬|환풍기|선풍기", r"고데기|매직기", r"뷰러",
    r"케이블|충전기", r"요가블럭|폼롤러|보수볼", r"머그|유리잔|컵", r"도마",
    r"거름망|티망|차망", r"얼음틀|아이스몰드", r"쌀통", r"밀대", r"선반|트롤리",
    r"바퀴|캐스터", r"우산|양산|우비", r"무드등|수유등|조명", r"이어워머|귀마개",
    r"소방패치", r"모기채", r"모니터", r"현미경", r"치약", r"탈취제|방향제",
    r"접착제", r"쿨링시트|냉각패치", r"새치커버|염색스틱", r"아이섀도우|팔레트",
    r"양말", r"서랍매트|식탁매트", r"모래액자", r"슬러시메이커", r"송장지우개",
    r"바람막이|자켓", r"골프티", r"도어스텝", r"디스펜서", r"빨대|스트로우",
    r"밀봉기|실링기", r"가위", r"키캡", r"안대", r"슬리퍼|욕실화", r"샤워기",
    r"치실", r"목욕장갑|때타올", r"만년연필", r"캘리그라피펜",
]

STOP_TOKENS = {
    "세제가", "귀여운", "새로운", "전용", "2개", "3D", "14Fl", "국내배송", "초슬림", "원터치",
    "미니", "휴대용", "대용량", "스마트", "자동", "다기능", "초강력", "고급", "실리콘", "스테인리스",
    "올스텐", "무선", "전기", "충전식", "가성비", "추천", "인기", "신상품", "1위", "세트",
    "특가", "할인", "신형", "2026", "2025", "1개", "3개", "4개", "5종", "10종", "종", "개",
}


def _extract_clean_noun(text: str) -> str:
    for pat in NOUN_EXTRACT_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            matched = m.group(0)
            return re.sub(r"\s+", "", matched)
    words = re.findall(r"[가-힣A-Za-z0-9]+", text)
    valid_nouns = []
    for w in words:
        if w in STOP_TOKENS:
            continue
        if len(w) < 2:
            continue
        if re.search(r"^(?:초|초미니|극세|고탄성|친환경|무독성|다용도|가정용|업소용)", w):
            w = re.sub(r"^(?:초|초미니|극세|고탄성|친환경|무독성|다용도|가정용|업소용)", "", w)
        if re.search(r"(?:용|형|식|한|스런|스러운|색|종|개|입|팩|매|세트)$", w) and len(w) > 3:
            w = re.sub(r"(?:용|형|식|한|스런|스러운|색|종|개|입|팩|매|세트)$", "", w)
        if len(w) >= 2 and w not in STOP_TOKENS:
            valid_nouns.append(w)
    return valid_nouns[0] if valid_nouns else (words[0] if words else text[:8])


def _detect_materials_and_specs(title_and_surface: str, category: str, food: bool, electric: bool, cosmetics: bool, chemical: bool) -> str:
    mats = []
    checks = [
        ("304 스테인리스 스틸(SUS304) 내병/본체", r"304|올스텐|스테인리스|스테인레스|스텐|텀블러|보온보냉|핀셋|호네누끼"),
        ("식품용/고탄성 실리콘(패킹·바디)", r"실리콘|텀블러|보온보냉"),
        ("세라믹/도자기재", r"세라믹|도자기|머그|찻잔"),
        ("폴리프로필렌(PP)/ABS 합성수지", r"\bpp\b|\babs\b|폴리프로필렌|플라스틱|탄성\s*소재|토일렛|모래삽|쌀통|트레이|보관함|청소기|선반"),
        ("TPU/EVA 방수·완충 엘라스토머", r"\btpu\b|\beva\b|방수\s*커버|폼롤러|슬리퍼|요가블럭|서랍\s*매트"),
        ("원목/우드(참나무·삼나무)", r"우드|원목|목제|목각|시더|참나무|사다리행거"),
        ("코튼/극세사/메쉬 패브릭", r"코튼|크레이프|가제|극세사|메쉬|폴리에스텔|나일론|패브릭|섬유|파우치|양말|흔들침대"),
        ("강화유리/내열유리", r"유리컵|유리\s*텀블러|내열유리|(?<!유리)유리(?!창)"),
        ("네오디뮴 자석(마그네틱)", r"마그네틱|자석|맥세이프"),
        ("계면활성제·세정 화학성분", r"세정제|세제|클리너|얼룩\s*제거|비데\s*노즐|페이스트"),
        ("기능성 화장품 원료(콜라겐/PDRN/레티놀/비타민C)", r"콜라겐|pdrn|레티놀|비타민c|세럼|토너|크림|선크림|컨실러|쿠션|립밤"),
    ]
    for label, pat in checks:
        # Chemical products shouldn't be tagged as pure ceramic or fabric just because of context words
        if chemical and label in ("세라믹/도자기재", "코튼/극세사/메쉬 패브릭"):
            continue
        if re.search(pat, title_and_surface, re.I):
            mats.append(label)
    if not mats:
        fallback_map = {
            "kitchen": "PP/ABS 및 스테인리스·실리콘 복합재(상세 재질 확인)",
            "home": "ABS/PP 합성수지 및 금속·패브릭 복합재",
            "beauty": "화장품 전성분 또는 ABS/실리콘 미용도구 재질",
            "fashion": "폴리에스터/나일론/합성피혁·고무 소재",
            "baby": "무독성 PP/실리콘/코튼 유아용 소재",
            "pet": "PP/ABS/메쉬 패브릭 반려동물용 소재",
            "automotive": "ABS/PC 내열 합성수지 및 알루미늄 합금",
            "stationery": "종이/수성잉크/ABS 문구 소재",
            "outdoor": "방수 폴리에스터/알루미늄/강화 합성수지",
            "mobile": "ABS/PC/알루미늄/네오디뮴 마그네틱",
        }
        mats.append(fallback_map.get(category, "일반 합성수지(PP/ABS) 및 금속 복합소재"))

    specs = re.findall(r"\b\d+(?:\.\d+)?\s*(?:ml|g|kg|L|cm|mm|mAh|W|V|인치|구|종|색|개입|매|켤레|팩|p|pcs)\b", title_and_surface, re.I)
    spec_str = ", ".join(dict.fromkeys(specs[:4])) if specs else "단품 표준 규격(상세페이지 참조)"

    if electric:
        if re.search(r"무선|충전|usb|배터리|c타입|리튬|모니터|현미경|모기채|프린터", title_and_surface, re.I):
            pwr = "USB 충전식(DC 5V 저전압/내장 리튬배터리)"
        else:
            pwr = "교류 전원(AC 220V) 또는 건전지식"
    else:
        pwr = "무전원(비전기 수동식)"

    if cosmetics:
        notice = "화장품법 전성분·제조판매업자·사용기한·기능성 여부 필수 표기"
    elif chemical:
        notice = "안전확인대상 생활화학제품 신고번호·주요물질·계면활성제·보존제 표기 필수"
    elif food and electric:
        notice = "식약처 식품용 기구 수입신고(재질) + KC 전기안전/전자파 적합성 표기 필수"
    elif food:
        notice = "식품위생법 한글표시사항(식품용 기구 도안·재질명·내열/내냉온도·제조원) 필수"
    elif electric:
        notice = "전안법/전파법 KC인증번호·정격전압/소비전력·모델명·제조국 표기 필수"
    else:
        notice = "품질경영 및 공산품안전관리법 한글표시(품명·재질·제조년월·제조자·수입자·원산지 Made in China) 표기"

    return f"• 검출 재질/성분: {', '.join(mats[:3])}\n• 규격/전원: {spec_str} / {pwr}\n• 법정 고시 요건: {notice}"

def _build_cert_guide(is_global: bool, food: bool, electric: bool, cosmetics: bool, chemical: bool, baby: bool, title: str = "") -> str:
    prefix = "⚠️ [원천 브랜드 주의] 타사 원천 상표·디자인권 제품이므로 택갈이(OEM) 사입 금지, 해외 정품 구매대행으로만 취급 권장.\n" if is_global else ""
    if QUASI_DRUG_RE.search(title):
        return prefix + (
            "① [의약외품/구강용품] 치약·구강보호대·살충제는 약사법상 의약외품으로 수입 시 식약처 품목허가 및 품질검사 필수\n"
            "② [저비용 우회 및 검증] 초기에는 해외구매대행(개인 자가사용 1인 면세 범위)으로 선등록하여 시장 수요를 먼저 검증하고, 사입 시에는 의약외품 제조업/수입업 허가 대행업체를 통해 규격기준 검토 진행"
        )
    if SANITARY_RE.search(title):
        return prefix + (
            "① [위생용품관리법] 롤화장지·물티슈·일회용 타월·칫솔 등은 위생용품 수입업 신고 및 통관 전 정밀검사(형광증백제/포름알데히드 시험) 대상\n"
            "② [비용 절감 돌파] 중국 원제조업체에 공인 시험기관(SGS/TUV) 무독성·무형광 성적서를 요구하고, 단일 규격·화이트 무지 제품 1종으로 최초 수입하여 검사 수수료를 최소화"
        )
    if cosmetics:
        return prefix + (
            "① [구매대행] 개인 자가사용 1인 면세 범위 내 무재고 테스트 가능(단 기능성·의약외품 허위표시 주의)\n"
            "② [사입 전환 시] 화장품책임판매업 등록 필수 + 중국 공장에서 CGMP/ISO22716 인증서·100% 전성분표(INCI/CAS)·BSE Free·COA(성적서) 수령 후 한국의약품수출입협회(KPTA) 표준통관예정보고 및 품질검사로 비용 최소화"
        )
    if chemical:
        return prefix + (
            "① [쿠팡 기등록 활용] 쿠팡 상세페이지 고시에서 '안전확인대상 생활화학제품 신고번호(제CB...-....호)'를 확인해 초록누리(ecolife.me.go.kr)에서 품목 구분·성분 조회\n"
            "② [저비용 돌파] 1688 공장에서 100% 전성분표(CAS 번호 포함) 및 MSDS(물질안전보건자료)를 먼저 받아 시험기관 사전검토 진행. 초기에는 세제 액체 제외 본체만 사입하거나 구매대행으로 시장성 검증 후 단일 제형만 신고해 검사비 절감"
        )
    if food and electric:
        return prefix + (
            "① [무재고 테스트] 구매대행(개인통관고유부호 PCC)으로 1인 1대 전파법·전기안전 면제 및 자가사용 식품기구 면제로 인증비 0원 수요 검증\n"
            "② [쿠팡 기등록 역추적] 쿠팡 고시의 KC인증번호(XU/HU/R-R)를 제품안전정보센터(safetykorea.kr)·국립전파연구원에 조회해 중국 원제조사(Factory) 확인 → 동일 공장 소싱 시 CB/CE/RoHS 성적서 활용 및 식약처(impfood.mfds.go.kr) 기등록 해외제조업소 코드·단일 색상 통관으로 정밀검사비 50% 이상 절감"
        )
    if food:
        return prefix + (
            "① [쿠팡 기등록 재질·코드 활용] 쿠팡 고시표에서 정확한 재질(예: SUS304, PP, 실리콘) 확인 후 식약처 수입식품정보마루(impfood.mfds.go.kr)에서 중국 제조공장의 '해외제조업소 코드' 및 기수입 정밀검사 이력 조회\n"
            "② [식약처 검사비 절감 핵심] 기등록 해외제조업소와 동일 공장·동일 재질로 수입하거나, 신규 정밀검사 시 1688 공장에서 '100% 재질 성분비율표(Material Composition Table) + 제조공정도(Process Flow)'를 무료 수령해 제출. 반드시 '단일 색상·단일 재질(예: 무도장 스텐/화이트 1종)'로 먼저 통관해야 색상별 중복 검사비(건당 25~50만원) 폭탄을 피함"
        )
    if electric:
        return prefix + (
            "① [구매대행 0원 테스트] 개인통관고유부호(PCC) 1인 1대 면제 규정을 활용해 인증비 0원으로 구매대행 선등록·판매 검증\n"
            "② [쿠팡 기등록 KC 역추적 & 저비용 인증] 쿠팡 상세하단 KC인증번호(R-R-... / XU10...)를 안전코리아(safetykorea.kr)·전파연구원(rra.go.kr)에 검색하면 '중국 원제조공장 영문명·원모델명'이 노출됨 → 1688에서 해당 원공장을 찾아 기존 회로도·부품표(BOM)·CE/FCC/UN38.3(배터리) 성적서를 무료 확보하고, 직류(USB 5V) 저전압 구조 선택 및 국내 KC 기인증 어댑터 동봉 방식으로 전기안전 시험비를 대폭 절감(전자파 적합등록 단독 진행)"
        )
    if baby:
        return prefix + (
            "① [쿠팡 기등록 KC 확인] 만 13세 이하 어린이제품은 안전코리아(safetykorea.kr)에서 쿠팡 기등록 KC번호로 원제조사 및 시험항목(프탈레이트·중금속) 확인\n"
            "② [저비용 돌파] 1688 공장에 EN71/ASTM/RoHS 무독성 시험성적서 및 재질표를 요청하고 부속품 색상/재질 수를 최소화해 건당 시험비 절감(성인 키덜트·인테리어 소품인 경우 '만 14세 이상 사용 대상' 명확 표기로 어린이제품 중복 규제 회피)"
        )
    return prefix + (
        "① [비규제 일반 공산품 — 인증비 0원] 전기·식품접촉·어린이·화학에 해당하지 않는 일반 공산품으로 별도 KC 시험이나 식약처 정밀검사 없이 즉시 사입 통관 가능\n"
        "② [통관·브랜드화 실무] 1688 공장에 제품/포장 'Made in China' 원산지 표기 및 공용금형(公模) 여부만 확인 후, 타셀러 상표를 뗀 무지 패키지(中性包装)에 내 브랜드 한글표시 스티커만 부착해 쿠팡 로켓그로스·스마트스토어 즉시 입고"
    )


def _cn_product_term(core_name: str, category: str) -> str:
    for pat, cn_term in CN_ITEM_MAP:
        if re.search(pat, core_name, re.I):
            return f"{cn_term} ({core_name})"
    cat_cn = {
        "kitchen": "厨房日用百货", "home": "家居收纳日用品", "beauty": "美妆个护工具",
        "fashion": "服饰箱包配件", "baby": "母婴儿童用品", "pet": "宠物用品",
        "automotive": "汽车车载用品", "stationery": "文具办公用品", "outdoor": "户外露营运动用品",
        "mobile": "手机数码配件",
    }.get(category, "日用百货产品")
    return f"{cat_cn} ({core_name})"


def _build_1688_message(core_name: str, category: str, food: bool, electric: bool, cosmetics: bool, chemical: bool) -> str:
    cn_item = _cn_product_term(core_name, category)
    if food and electric:
        cn_doc = "1) 食品接触部分的100%材质成分表(如SUS304/PP/硅胶)及生产工艺流程图；2) 电器部分的CE/RoHS/FCC检测报告、电路图及电池UN38.3报告(如有)。请问这款之前有出过韩国Coupang或有韩国KC/KFDA认证记录吗？"
        ko_doc = "1) 식품 접촉 부위의 100% 재질 성분비율표(예: SUS304/PP/실리콘) 및 제조공정도, 2) 전기 파트의 CE/RoHS/FCC 성적서, 회로도 및 배터리 UN38.3 성적서(해당 시) 제공 가능한가요? 이 모델 한국 쿠팡 수출 이력이나 한국 KC/식약처 인증 이력이 있는지도 확인 부탁드립니다."
    elif food:
        cn_doc = "1) 100%材质成分比例表(Material Composition Table，需注明具体材质如SUS304/PP/食品级硅胶)；2) 生产工艺流程图(Manufacturing Process Chart)；3) 食品级检测报告(FDA/LFGB或韩国KFDA记录)。"
        ko_doc = "1) 100% 재질 성분비율표(SUS304/PP/식품용 실리콘 등 정확한 재질 비율 명시), 2) 제조공정도(Manufacturing Process Chart), 3) 식품등급 시험성적서(FDA/LFGB 또는 한국 식약처 통관 이력)를 제공해 주실 수 있나요?"
    elif electric:
        cn_doc = "1) 产品规格书、电路图、BOM表及CE/FCC/RoHS检测报告(带锂电池需提供UN38.3及MSDS报告)；2) 请问贵司这款产品之前有出口过韩国(如Coupang)或办过韩国KC认证吗？"
        ko_doc = "1) 제품 사양서, 회로도, 부품표(BOM) 및 CE/FCC/RoHS 시험성적서(리튬배터리 내장 시 UN38.3 및 MSDS 포함), 2) 혹시 이 제품을 한국(쿠팡 등)에 수출했거나 한국 KC인증을 진행한 이력이 있나요?"
    elif chemical or cosmetics:
        cn_doc = "1) 100%全成分表(Full Ingredient List，包含CAS号码及各成分占比%)；2) 英文或韩文MSDS(化学品安全技术说明书)及COA检测报告。"
        ko_doc = "1) 100% 전성분표(CAS 번호 및 각 성분 함유량 % 포함), 2) 영문 또는 국문 MSDS(물질안전보건자료) 및 COA 시험성적서를 보내주실 수 있나요?"
    else:
        cn_doc = "1) 产品的具体材质组成(如PP/ABS/不锈钢等)及尺寸重量规格表；2) 如表面有涂层或配件，请确认环保无毒(RoHS)。"
        ko_doc = "1) 제품의 정확한 재질 구성비(PP/ABS/스테인리스 등) 및 상세 사이즈·중량 스펙표, 2) 코팅이나 부속품 관련 유해물질 무독성(RoHS 등) 여부를 확인 부탁드립니다."

    cn = (
        f"您好！我是韩国电商卖家，正在采购贵司的【{cn_item}】。\n"
        f"请问：1) 这款是公模(Public Mold)现货，没有外观专利或品牌侵权风险吧？\n"
        f"2) 韩国清关及认证需要：{cn_doc}\n"
        f"3) 可以发无品牌中性包装(Neutral Packaging，带Made in China标)吗？如果贴我们自己的韩国品牌Logo(OEM)，起订量(MOQ)和单价是多少？先拿5~10个样品可以吗？谢谢！"
    )
    ko = (
        f"안녕하세요! 한국 이커머스 셀러이며 귀사의 【{cn_item}】 소싱 검토 중입니다.\n"
        f"1) 이 제품은 디자인 특허나 상표권 침해 문제가 없는 공용 금형(公模) 제품이 맞나요?\n"
        f"2) 한국 통관·인증을 위해 {ko_doc}\n"
        f"3) 타사 로고 없는 무지 포장(Made in China 표기 포함) 출고가 가능한가요? 저희 한국 자체 브랜드 로고 OEM(택갈이) 작업 시 최소수량(MOQ)과 단가, 그리고 샘플 5~10개 선발주 가능 여부 알려주세요!"
    )
    return f"[중문 원문 — 1688 왕왕/위챗 복붙용]\n{cn}\n\n[한국어 해석]\n{ko}"


def enrich_brand_and_cert(cand: dict, clean_name: str, surface: str, category: str, food: bool, electric: bool, cosmetics: bool) -> dict:
    cp = cand.get("cp_info") or {}
    title_text = " ".join(str(x or "") for x in (clean_name, cand.get("sibling_title"), cp.get("official_product_name"))).strip()
    check_text = title_text or surface

    chemical = bool(CHEMICAL_RE.search(check_text))
    baby = bool(category == "baby" or BABY_RE.search(check_text))

    # 1. Check compatible accessory first when explicit compatibility token exists
    compat_hit = None
    if re.search(r"호환|전용|맥세이프|magsafe|에어팟|갤럭시워치", check_text, re.I):
        for b_label, b_pat in COMPAT_BRANDS:
            if re.search(b_pat, check_text, re.I):
                if b_label in ("아크테릭스", "몽벨") and not re.search(r"호환|이너백", check_text, re.I):
                    continue
                compat_hit = b_label
                break

    # 2. Check Global / Original IP brands
    global_hit = None
    if not compat_hit:
        for b_label, b_pat in GLOBAL_BRANDS:
            if re.search(b_pat, check_text, re.I):
                global_hit = b_label
                break

    # 3. Check Domestic Seller Private-Label brands
    seller_hit = None
    stripped_promo = PROMO_BRACKET_RE.sub("", clean_name).strip()
    m_br = LEADING_BRACKET_BRAND_RE.match(stripped_promo)
    if m_br:
        br_inside = m_br.group(1).strip()
        if not re.search(r"할인|출고|배송|인증|소재|정품|회전|프레시", br_inside):
            seller_hit = br_inside
    if not seller_hit:
        for sb in sorted(SELLER_BRANDS, key=len, reverse=True):
            if stripped_promo.lower().startswith(sb.lower()):
                seller_hit = sb
                break

    core_clean = _strip_seller_from_title(clean_name, seller_hit)

    if compat_hit:
        kipris_status = f"🔵 호환용 액세서리 [{compat_hit} 호환] ('호환용' 표기 시 내 브랜드 소싱 가능)"
        if "호환" not in core_clean:
            rebrand_clean_name = f"[내브랜드] {core_clean} ({compat_hit} 호환용)"
        else:
            rebrand_clean_name = f"[내브랜드] {core_clean}"
        query_term = compat_hit
    elif global_hit:
        kipris_status = f"⚠️ 원천/글로벌 브랜드 [{global_hit}] (택갈이 금지 · 정품 구매대행만 가능)"
        rebrand_clean_name = f"[정품구매대행 전용] {clean_name}"
        query_term = global_hit
    elif seller_hit:
        kipris_status = f"✅ 국내셀러 상표 [{seller_hit}] (상표 제거 후 내 브랜드 소싱 가능)"
        rebrand_clean_name = f"[내브랜드] {core_clean}"
        query_term = seller_hit
    else:
        kipris_status = "🟢 무브랜드 공용상품 (내 브랜드 즉시 등록 가능)"
        rebrand_clean_name = f"[내브랜드] {core_clean}"
        # Extract clean core noun rather than adjectives/numbers/particles
        query_term = _extract_clean_noun(core_clean)

    # KIPRIS 공식 웹사이트 상표(TM) 다이렉트 검색 URL (네이버 검색 완전 배제)
    q_enc = urllib.parse.quote(query_term)
    kipris_search_url = (
        f"http://www.kipris.or.kr/khome/search/searchResult.do"
        f"?searchKind=totalSearch&searchRight=trademark"
        f"&queryText={q_enc}&queryTextTop={q_enc}&expression={q_enc}"
    )

    spec_material_summary = _detect_materials_and_specs(
        f"{clean_name} {surface}", category, food, electric, cosmetics, chemical
    )
    cert_cost_saving_guide = _build_cert_guide(
        bool(global_hit), food, electric, cosmetics, chemical, baby, title_text
    )
    china_1688_message = _build_1688_message(
        core_clean[:40], category, food, electric, cosmetics, chemical
    )

    return {
        "kipris_status": kipris_status,
        "rebrand_clean_name": rebrand_clean_name,
        "spec_material_summary": spec_material_summary,
        "cert_cost_saving_guide": cert_cost_saving_guide,
        "china_1688_message": china_1688_message,
        "kipris_search_url": kipris_search_url,
        "is_global_brand": bool(global_hit),
    }
