#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evidence-led product sourcing classification, ranking and unit-economics guidance."""
import re
import urllib.parse
from brand_cert_expert import enrich_brand_and_cert

# Specific high-confidence names take precedence over the transparent keyword fallback.
KNOWN_MAPPINGS = [
    (r"로펫|눈빛이 오늘의 분위기", "AI 반려로봇 로펫 (감정표현 스마트 데스크 로봇)", "해외구매대행 추천", "AI 반려로봇 데스크 로봇", False, True),
    (r"휴대용 버너.*자리차지.*인덕션", "초슬림 미니 휴대용 인덕션 (컴팩트 핫플레이트)", "해외구매대행 추천", "미니 휴대용 인덕션 1구 핫플레이트", True, True),
    (r"무잉크 감열식|프린터.*잉크 없이", "무잉크 감열식 미니 휴대용 프린터", "해외구매대행 추천", "무잉크 감열식 휴대용 프린터", False, True),
    (r"자동 웍질 냄비", "자동 교반 멀티쿠커", "해외구매대행 추천", "자동 교반 멀티쿠커 냄비", True, True),
    (r"만년연필", "슬림 무한 만년연필", "사입 추천", "무한 만년연필 필기구", False, False),
]

EXCLUDED = re.compile(
    r"강의|수강생|전자책|컨설팅|부업|창업|사업자등록|키워드북|세일|할인쿠폰|이벤트|모집|"
    r"냉동|아이스크림|밀키트|김치|삼겹살|한우|쭈꾸미|불고기|만두피|와사비|로즈마리|"
    r"삼다수|국산생수|굴소스|자연치즈|밀크\s*푸딩|초콜렛|초콜릿|커피캔디|자일리톨|숙식빵|매실청|"
    r"신선\s*대란|바질페스토|파스타소스|홍로사과|햇사과|쿠크다스|꽃송이버섯효소|카라멜\s*넛|"
    r"에스프레소\s*블렌드|인스턴트커피|스페셜\s*블랜드|로이스|매일바이오|구미\s*클리스터|LA갈비|소갈비|"
    r"호박팥차|코카콜라|푸룬\s*자두|호놀룰루\s*쿠키|호밀통밀\s*브레드|치킨파우더|새송이\s*버섯|"
    r"깜빠뉴|치즈쿠키|바사삭닭다리|말차\s*파우더|그릴스모크햄|탑플릇젤리|모짜렐라|미숫가루|목캔디|자스민\s*티|"
    r"네블라이저|팝마트|POPMART|마이멜로디|쿠로미|레고\s*42202|맥너겟|맥도날드|Galaxy\s*Z\s*Fold|사이니지\s*TV|"
    r"입생로랑|산타마리아노벨라|이솝|설화수|맥\s*러스터글래스|백화점정품|"
    r"샤넬|에르메스|루이비통|구찌|디올|프라다|롤렉스|헬로키티|산리오|포켓몬|디즈니|"
    r"BTS|방탄소년단|SHEIN.*유해물질|불법으로 판매",
    re.I,
)
INFO_ONLY = re.compile(r"사업자등록 준비|구매대행.*단계|창업.*방법|강의|수강생|부업|모집|세일이 시작|할인 코드", re.I)
ELECTRICAL = re.compile(
    r"전기|전동|충전|무선|블루투스|배터리|USB|LED|인덕션|프린터|로봇|모터|전자|스마트워치|이어폰|"
    r"가습기|선풍기|실링팬|환풍기|청소기|다리미|믹서|블렌더|블랜더|그라인더|기계식\s*키보드|고데기|매직기|"
    r"전기\s*모기채|멀티탭|전동\s*드릴|디지털\s*저울|현미경|버블건|착즙기|프로젝터|무드등|수유등|전기포트",
    re.I,
)
FOOD_CONTACT = re.compile(
    r"식기|식품용|텀블러|머그|보온병|프라이팬|사각팬|그릴팬|와플팬|계란팬|냄비|포크|수저|젓가락|"
    r"거름망|채반|체망|여과기|슬라이서|채칼|도마|얼음틀|얼음\s*트레이|밀폐용기|실리콘보관|주방용|"
    r"거품기|스쿱|식품\s*분쇄기|접시|보틀|물병|물통|착즙기|빨대|마티니\s*잔|와인\s*잔|칵테일\s*잔|"
    r"쌀통|머핀틀|차\s*여과기|티망|바베큐그릴",
    re.I,
)
COSMETICS = re.compile(
    r"화장품|화장용|메이크업|스킨케어|기초화장|색조|세럼|크림|선크림|립스틱|립밤|쿠션팩트|쿠션파데|"
    r"네일케어|매니큐어|샴푸|바디워시|바디로션|염색약|염색제|토너|컨실러|프라이머|픽서|풋크림|미용액|"
    r"에센스|트리트먼트|블러셔|아이브로우|아이섀도우|마스카라|새치커버|피지\s*연화제",
    re.I,
)

PRODUCT_TERMS = re.compile(
    r"가방|백팩|이너백|에코백|파우치|거치대|홀더|후크|정리함|정리대|수납|우산|우비|레인코트|브러시|브러쉬|"
    r"청소|세척|건조대|랙|선반|트롤리|매트|클립|집게|가위|칼|채칼|펜|연필|케이스|커버|쿠션|의자|조명|램프|무드등|수유등|"
    r"디퓨저|방향제|수건|손수건|양말|신발|운동화|스니커즈|구두|슬리퍼|옷걸이|행거|슬라이서|주걱|디스펜서|용기|보관함|"
    r"시계|안경|수경|고글|필통|프린터|로봇|가습기|선풍기|실링팬|환풍기|청소기|믹서|블렌더|블랜더|그라인더|인덕션|"
    r"충전기|케이블|이어폰|키보드|키캡|마우스|모니터|부스터|발판|도어스텝|스퀴지|밀대|수세미|스펀지|필터|패드|"
    r"장난감|퍼즐|게임|체스|룰렛|피젯토이|워터건|버블|비눗방울|오르골|인형|피규어|펫|반려동물|강아지|고양이|어항|수족관|"
    r"캠핑|차량용|생활용품|거품기|스쿱|발톱|견인기|거꾸리|햇빛가리개|고데기|매직기|뷰러|갈이|접시|요가블럭|폼롤러|"
    r"슬라이드보드|보수볼|머그|텀블러|보틀|물병|물통|스트랩|타이머|모기채|다리미|멀티탭|드릴|그릴|화로대|쌀통|저울|"
    r"현미경|복싱|먼지털이|비누트레이|뜨개질|공병|쇼핑카트|카트|용돈박스|소방패치|대야|각도기|커터기|치실|칫솔|치약|"
    r"트리머|미용기|바리깡|스탬프|스프레이건|분사기|촛대|캔들|테이블|책상|서랍장|욕조|요가팬츠|레깅스|바람막이|조끼|"
    r"헤어밴드|머리띠|썬캡|모자|동전지갑|키링|다이어리|착즙기|안전문|고체향수|흔들말|붕붕카|킥보드|얼음|벨크로|테이프|"
    r"전기포트|차\s*여과기|티망|공구함|망치|접착제|때타올|때밀이|샤워|푸셔|잔|세정제|클리너|세제|탈취제|세럼|크림|토너|"
    r"바디워시|바디로션|선크림|립밤|컨실러|프라이머|펜슬|네일|이어워머|쿨링시트|바퀴|캐스터|핑거가드|실꿰기|혀\s*커버|옷\s*접기|머핀틀",
    re.I,
)

CATEGORY_TERMS = {
    "kitchen": re.compile(r"주방|식기|컵|텀블러|머그|보틀|냄비|팬|도마|거름망|수저|젓가락|식품|주먹밥|얼음|주방용|거품기|스쿱|채칼|슬라이서|착즙기|갈이|쌀통|머핀틀|차\s*여과기|티망|전기포트", re.I),
    "home": re.compile(r"수납|정리|욕실|청소|세탁|매트|선반|트롤리|행거|조명|무드등|디퓨저|방향제|침실|침대|가구|바퀴|생활용품|실링팬|환풍기|스퀴지|밀대|수세미|걸레|비누|대야|세정제|클리너|세제|탈취제|멀티탭|공구|접착제|모기채", re.I),
    "beauty": re.compile(r"화장|뷰티|메이크업|세럼|크림|파우더|브러시|브러쉬|미용|네일|큐티클|헤어|고데기|매직기|뷰러|선크림|립밤|컨실러|프라이머|토너|바디워시|바디로션|샴푸|트리트먼트|향수|발톱|때타올|때밀이|치실|칫솔|치약|트리머", re.I),
    "fashion": re.compile(r"의류|신발|운동화|스니커즈|구두|슬리퍼|가방|백팩|이너백|에코백|양말|옷걸이|패션|우산|우비|레인코트|파우치|동전지갑|키링|모자|썬캡|헤어밴드|머리띠|바람막이|조끼|레깅스|요가팬츠", re.I),
    "baby": re.compile(r"유아|아기|신생아|키즈|어린이|아동|부스터|붕붕카|흔들말|보행기|장난감|완구|욕조|버블|비눗방울|워터건", re.I),
    "pet": re.compile(r"강아지|고양이|반려동물|반려견|펫|애견|애묘|리드줄|산책줄|토일렛|모래삽|어항|수족관", re.I),
    "automotive": re.compile(r"차량|자동차|세차|차량용|도어스텝|사이드미러|햇빛가리개|컵홀더|헤드레스트", re.I),
    "stationery": re.compile(r"문구|연필|펜|캘리그라피|노트|다이어리|필통|가위|송장|각도기|드로잉", re.I),
    "outdoor": re.compile(r"캠핑|등산|여행|낚시|야외|피크닉|랜턴|수영|수경|고글|요가블럭|폼롤러|슬라이드보드|보수볼|복싱|그릴|화로대", re.I),
    "mobile": re.compile(r"스마트폰|휴대폰|태블릿|충전|케이블|이어폰|키보드|키캡|마우스|맥세이프|넥마운트|모니터", re.I),
}

REFERENCE_PRICE = {
    "kitchen": 14900, "home": 15900, "beauty": 12900, "fashion": 16900,
    "baby": 19900, "pet": 17900, "automotive": 18900, "stationery": 8900,
    "outdoor": 19900, "mobile": 24900, "general": 14900,
}


def _finite(value, default=0.0):
    try:
        n = float(value)
        return n if n == n and abs(n) != float("inf") else default
    except (TypeError, ValueError):
        return default


def _product_name(cand, surface):
    cp = cand.get("cp_info") or {}
    sibling = (cand.get("sibling_title") or "").strip()
    official = str(cp.get("official_product_name") or "").strip()
    raw_title = str(cand.get("title") or "").strip()
    query = str(cp.get("query") or "").strip()

    chosen = official or sibling or ""
    if not chosen and query and 4 <= len(query) <= 60 and not re.search(r"할인|쿠폰|추천|모음|후기|특가", query):
        chosen = query
    if not chosen and raw_title:
        # Filter out social hooks, narrative complaints, or affiliate boilerplate
        is_hook = bool(re.search(
            r"하\.\.\.|헛구역질|스멀스멀|해버림|올라와서|파트너스|활동의\s*일환|일정액의\s*수수료|"
            r"꿀템|치트키|공유합니다|소개합니다|모음집|사용해보니|내돈내산|솔직후기|대박|실화냐|"
            r"너무\s*좋|진짜\s*좋|알려드|알려 드|보여드|보여 드|추천템|살\s*수\s*밖에|미쳤다",
            raw_title,
            re.I,
        ))
        if not is_hook and " - " in raw_title:
            chosen = raw_title
        elif not is_hook and len(raw_title) <= 50:
            chosen = raw_title

    if chosen:
        chosen = re.sub(r"^\s*(?:\[(?:[^\]]+)\]\s*)+", "", chosen).strip()
        chosen = re.sub(r"\s*,\s*(?:[가-힣A-Za-z0-9/·& ]+|\d+(?:ml|g|kg|L|cm|mm|mAh|W|V|구|종|색|개입|매|켤레|팩|p|pcs|개|set|세트).*)$", "", chosen, flags=re.I).strip()
        chosen = re.sub(r"\s*[-–]\s*[가-힣A-Za-z0-9/·& ]+$", "", chosen).strip()
        if 3 <= len(chosen) <= 85 and not INFO_ONLY.search(chosen):
            return chosen
    return ""


def _category(cand, surface):
    cat = str(cand.get("cat") or "general").lower()
    if cat in CATEGORY_TERMS and cat != "general":
        return cat
    for name, rx in CATEGORY_TERMS.items():
        if rx.search(surface):
            return name
    return "general"


def _recommendation_reason(cand, category):
    text = " ".join(str(cand.get(k) or "") for k in ("text", "summary_ko"))
    text = re.sub(r"https?://\S+|@[\w.]+|#[\w가-힣]+", " ", text)
    sentences = [re.sub(r"\s+", " ", s).strip(" \t-•") for s in re.split(r"[.!?\n。]+", text)]
    pain = re.compile(r"불편|귀찮|힘들|번거|정리|공간|손목|냄새|보관|세척|간편|편하|휴대|무겁|엉키|새지|걸리|흘러|흘리", re.I)
    cta = re.compile(r"댓글|팔로우|DM|프로필|링크 남기|구매 링크|광고|협찬|최저가", re.I)
    candidates = [s for s in sentences if 18 <= len(s) <= 150 and pain.search(s) and not cta.search(s)]
    if candidates:
        evidence = max(candidates, key=lambda s: (len(pain.findall(s)), min(len(s), 100)))[:105]
        return f"원문에서 확인된 사용 맥락: {evidence} / {category} 문제해결형 상품으로 소량 샘플 검수 후 수요 확인"
    return f"{category} 카테고리의 실물 상품. 원문 반응과 확인 가능한 상품·가격 증거를 바탕으로 소량 샘플 검수 후 수요 확인"


def score_and_classify_candidate(cand: dict) -> dict | None:
    entry = cand.get("entry") or {}
    item = cand.get("item") or {}
    raw = cand.get("raw") or {}
    cp = cand.get("cp_info") or {}
    surface = " ".join(str(x or "") for x in (
        cand.get("sibling_title"), cp.get("official_product_name"), cand.get("title"),
        cand.get("text"), cand.get("summary_ko"), cp.get("query"),
    ))
    if EXCLUDED.search(surface) or INFO_ONLY.search(surface) and not PRODUCT_TERMS.search(surface):
        return None

    matched = next((m for m in KNOWN_MAPPINGS if re.search(m[0], surface, re.I)), None)
    name = matched[1] if matched else _product_name(cand, surface)
    if not name or len(name) < 3 or not PRODUCT_TERMS.search(surface):
        return None

    category = _category(cand, surface)
    food = matched[4] if matched else bool(FOOD_CONTACT.search(surface))
    electric = matched[5] if matched else bool(ELECTRICAL.search(surface))
    cosmetics = bool(COSMETICS.search(surface))
    price = _finite(cp.get("price"), 0)
    if not (cand.get("store_url") or price or matched):
        return None

    expert_info = enrich_brand_and_cert(cand, name, surface, category, food, electric, cosmetics)
    is_global = expert_info.get("is_global_brand", False)

    # Global IP brands, electrical, food-contact, cosmetics, or >=35,000 KRW items go to purchasing agency
    agency = bool(is_global or electric or food or cosmetics or price >= 35000 or (matched and matched[2] == "해외구매대행 추천"))
    sourcing_type = "해외구매대행 추천" if agency else "사입 추천"
    # Extract clean keyword stripped of domestic seller brands for clean search URLs
    clean_kw = expert_info["rebrand_clean_name"].replace("[내브랜드]", "").replace("[정품구매대행 전용]", "").strip()
    kw = (matched[3] if matched else (clean_kw or name))
    encoded = urllib.parse.quote(kw)
    hyphen = urllib.parse.quote(kw.replace(" ", "-"))
    ali_url = f"https://ko.aliexpress.com/w/wholesale-{hyphen}.html"
    s1688_url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}"
    naver_url = f"https://search.naver.com/search.naver?query={encoded}+%EA%B0%80%EA%B2%A9%EB%B9%84%EA%B5%90"
    store_url = cand.get("store_url") or ""
    link_tier = int(cand.get("link_tier") or 3)

    vir = _finite(entry.get("virality_score"))
    nov = _finite(entry.get("novelty_score"))
    market = _finite(entry.get("market_score"))
    likes = _finite((item.get("metrics") or {}).get("likes"))
    comments = _finite((item.get("metrics") or {}).get("comments"))
    bait = 0.78 if likes > 0 and comments > likes * 1.8 else 1.0
    overlap = _finite(raw.get("post_product_overlap"), 0.55)
    overlap = 0.55 if overlap < 0.12 else 0.8 if overlap < 0.25 else 1.0
    v_norm = min(25, max(0, vir / 7.5 * 25 * bait))
    n_norm = min(25, max(0, nov / 6.8 * 25 * overlap))
    l_bonus = 20 if link_tier == 1 and price else 16.5 if cand.get("store_url") else 12
    f_sourcing = min(30, max(0, market / 9.5 * 24 + (5 if not agency else 3)))
    findings = (raw.get("import_regulation") or {}).get("findings") or []
    high_reg = any(isinstance(f, dict) and str(f.get("applicability", "")).lower() == "high" for f in findings)
    ip = raw.get("ip_risk") or {}
    ip_grade = str(ip.get("grade") or "").lower() if isinstance(ip, dict) else ""
    risk = high_reg or ip_grade in {"high", "critical"}
    if cosmetics:
        badge = "🟠 화장품: 책임판매업·성분/표시·수입 요건 확인 필수"
        factor = 0.84
    elif food and electric:
        badge = "🟠 식품접촉·전기/KC 가능성: 사전 확인 필수"
        factor = 0.88
    elif food:
        badge = "🟠 식품접촉 제품: 재질·식약처 요건 확인 필수"
        factor = 0.92
    elif electric:
        badge = "🟡 전기·무선 제품: KC/전파 인증 대상 여부 확인"
        factor = 0.93
    elif risk or is_global:
        badge = "🟡 원천브랜드·지재권 확인: 정품 구매대행 전용 (택갈이 금지)"
        factor = 0.90
    else:
        badge = "🟢 상대적 저규제 일반 공산품 (품목별 통관 확인)"
        factor = 1.0

    s_v3 = round(max(0, min(100, (v_norm + n_norm + l_bonus + f_sourcing) * factor)), 1)
    grade = "S급 (최우선)" if s_v3 >= 82 else "A급 (우수)" if s_v3 >= 74 else "B급 (유망)" if s_v3 >= 62 else "C급 (탐색)"
    retail = int(price) if price else REFERENCE_PRICE.get(category, REFERENCE_PRICE["general"])
    source_key = str(cp.get("price_source") or "")
    source_labels = {"caption_verified": "원문 가격표기", "naver_smartstore": "네이버 상품정보", "NAVER_LIVE": "네이버 실시간 시세"}
    price_source = source_labels.get(source_key, "쿠팡 실측" if price else "카테고리 기준 계획 추정")
    price_str = f"{price_source} {retail:,}원" if price else f"국내 기준 판매가 계획 추정 {retail:,}원 (실측 전 가정)"

    if sourcing_type == "해외구매대행 추천":
        if retail < 12000:
            bundle_price = max(22000, retail * 3)
            cost_bundle = max(6000, int(round(bundle_price * 0.35, -2)))
            profit_bundle = int(bundle_price * 0.9 - cost_bundle - 5500)
            margin_pct = max(25, int(profit_bundle / bundle_price * 100))
            margin_guide = f"단품(판매가 {retail:,}원) 해외배송비 고려 시 단독 마진 낮음 / 2~3개 묶음세트({bundle_price:,}원) 구성 시 예상 기여이익 ~{profit_bundle:,}원 ({margin_pct}% 마진 극대화)"
        else:
            cost = max(4000, int(round(retail * 0.38, -2)))
            shipping = 5500 if retail < 40000 else 8500
            profit = max(0, int(retail * 0.9 - cost - shipping))
            margin = max(0, int(profit / retail * 100)) if retail else 0
            margin_guide = f"계획 추정: 상품원가 ~{cost:,}원 + 배송/수수료 ~{shipping:,}원, 판매가 기준 기여이익 ~{profit:,}원 ({margin}%); 공급가·광고비·반품비 확인 전 확정 마진 아님"
        strategy = "1단계: 판매자·모델·배송비와 인증요건 확인 후 무재고 테스트 → 판매 데이터 확인 → 반복판매 시 정식수입·인증 검토"
    else:
        cost = max(1000, int(round(retail * 0.22, -2)))
        shipping = 1800
        profit = max(0, int(retail * 0.88 - cost - shipping - 3000))
        margin = max(0, int(profit / retail * 100)) if retail else 0
        cny = max(5, round(cost / 195, 1))
        margin_guide = f"계획 추정: 1688 목표 도매가 ¥{cny} (~{cost:,}원) + 입고/플랫폼비 ~{shipping+3000:,}원, 기여이익 ~{profit:,}원 ({margin}%); 견적·운임·세금·광고비 확인 전 확정 마진 아님"
        strategy = "1단계: 공급처 2곳 이상 비교·샘플 5~10개 품질검수 → 2단계: 전량원가와 반품률 산출 후 소량 사입 → 재주문은 판매 검증 후"
    reason = _recommendation_reason(cand, category)
    if food or electric:
        reason += "; 인증·재질 검증 후 진행"
    cat_ko_map = {
        "kitchen": "주방용품", "home": "생활용품", "beauty": "뷰티미용", "fashion": "패션잡화",
        "baby": "유아동용품", "pet": "반려동물용품", "automotive": "차량용품", "stationery": "문구사무",
        "outdoor": "캠핑레저", "mobile": "디지털모바일", "general": "생활잡화",
    }
    cat_ko = cat_ko_map.get(category, "생활용품")
    seo = " ".join(dict.fromkeys([kw, name, cat_ko, "아이디어상품"]))
    url = str(cand.get("url") or "")
    if link_tier == 1:
        link_status = "✅ 구매처/가격 캐시 확인"
    elif cand.get("store_url"):
        link_status = "🔗 상점 링크 확보 (상품·가격 추가 확인)"
    else:
        link_status = "🔍 소싱 검색 링크 제공 (원 판매처 미확보)"
    excerpt = re.sub(r"\s+", " ", str(cand.get("title") or cand.get("text") or ""))[:130]
    confidence = min(0.95, 0.35 + (0.2 if cand.get("store_url") else 0) + (0.2 if price else 0) + (0.15 if matched else 0))

    return {
        "clean_name": name[:80], "sourcing_type": sourcing_type, "search_kw": kw,
        "seo_keywords": seo, "recommend_reason": reason, "selling_point": reason,
        "grade": grade, "s_v3": s_v3, "v_norm": round(v_norm, 1), "n_norm": round(n_norm, 1),
        "l_bonus": round(l_bonus, 1), "f_sourcing": round(f_sourcing, 1),
        "reg_badge": badge, "price_str": price_str, "margin_guide": margin_guide,
        "channel_strategy": strategy, "category": category,
        "primary_image_url": cand.get("prod_img") or "", "purchase_url": store_url,
        "ali_sourcing_url": ali_url, "s1688_url": s1688_url, "naver_check_url": naver_url,
        "link_status": link_status, "post_url": url,
        "merchant": raw.get("commerce_merchant") or item.get("platform") or "",
        "engagement": f"좋아요 {int(likes):,} / 댓글 {int(comments):,}", "raw_excerpt": excerpt,
        "price_status": "EXACT" if price else "ESTIMATE", "has_exact_price": bool(price),
        "decision_status": "TEST_ONLY", "evidence_confidence": round(confidence, 2),
        "kipris_status": expert_info["kipris_status"],
        "rebrand_clean_name": expert_info["rebrand_clean_name"],
        "spec_material_summary": expert_info["spec_material_summary"],
        "cert_cost_saving_guide": expert_info["cert_cost_saving_guide"],
        "china_1688_message": expert_info["china_1688_message"],
        "kipris_search_url": expert_info["kipris_search_url"],
    }
