#!/usr/bin/env python3
"""
쿠팡 카테고리 매처 및 고시/속성 표준화 엔진 (스월백 & 대디갓재 실전 규칙 반영)
1. 옵션명 표준화: 색상 입력 시 쿠팡 표준 명칭 강제 변환 (흰색 -> 화이트, 회색 -> 그레이 등)
2. 고시정보 '품명 및 모델명': [브랜드명 + 메인키워드]로 명시하여 검색 알고리즘 가중치 획득
3. 검색필터(속성): 쿠팡 실제 좌측 사이드바 필터와 1:1로 일치하는 핵심 항목만 엄선
"""

# 쿠팡 공식 표준 색상 매핑 테이블
COUPANG_COLOR_STANDARDS = {
    "흰색": "화이트",
    "하얀색": "화이트",
    "아이보리": "아이보리",
    "검정": "블랙",
    "검정색": "블랙",
    "까만색": "블랙",
    "회색": "그레이",
    "쥐색": "그레이",
    "차콜": "차콜",
    "먹색": "차콜",
    "빨강": "레드",
    "빨간색": "레드",
    "파랑": "블루",
    "파란색": "블루",
    "남색": "네이비",
    "노랑": "옐로우",
    "노란색": "옐로우",
    "초록": "그린",
    "녹색": "그린",
    "카키": "카키",
    "분홍": "핑크",
    "분홍색": "핑크",
    "갈색": "브라운",
    "밤색": "브라운",
    "베이지": "베이지"
}

def normalize_coupang_color(raw_color: str) -> str:
    """쿠팡 필터 연동을 위한 색상 표준화"""
    clean = raw_color.strip()
    for k, v in COUPANG_COLOR_STANDARDS.items():
        if k in clean:
            # 예: '더블 스펠 블랙 그레이' -> '블랙 그레이'
            # 단순 '회색' -> '그레이'
            clean = clean.replace(k, v)
    return clean

CATEGORY_PRESETS = {
    "자전거장갑": {
        "displayCategoryCode": 58974,
        "categoryName": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
        "noticeCategoryName": "패션잡화 (모자/벨트/액세서리)",
        "defaultNotices": [
            {"name": "종류", "value": "자전거 방한 라이딩 장갑"},
            {"name": "소재", "value": "폴리에스테르, 벨벳 기모, 실리콘"},
            {"name": "치수", "value": "상세페이지 참조"},
            {"name": "제조자/수입자", "value": "협력업체 / 판매자"},
            {"name": "제조국", "value": "중국"},
            {"name": "취급시 주의사항", "value": "미온수 중성세제 손세탁 권장"},
            {"name": "품질보증기준", "value": "관련법 및 소비자분쟁해결기준에 따름"},
            {"name": "A/S 책임자와 전화번호", "value": "판매자 고객센터 문의"}
        ],
        "sidebarFilters": [
            {"attributeTypeName": "사용대상", "attributeValueName": "남녀공용"},
            {"attributeTypeName": "계절", "attributeValueName": "겨울"},
            {"attributeTypeName": "장갑 형태", "attributeValueName": "손가락장갑"},
            {"attributeTypeName": "주요기능", "attributeValueName": "방한/방풍"},
            {"attributeTypeName": "스마트폰 터치 가능여부", "attributeValueName": "터치가능"}
        ]
    },
    "보온텀블러": {
        "displayCategoryCode": 71822,
        "categoryName": "주방용품 > 잔/컵/보온병 > 텀블러/보온병",
        "noticeCategoryName": "주방용품",
        "defaultNotices": [
            {"name": "재질", "value": "스테인리스 304, 실리콘, PP"},
            {"name": "구성품", "value": "본품, 빨대, 뚜껑"},
            {"name": "크기", "value": "상세페이지 참조"},
            {"name": "동일모델의 출시년월", "value": "상세페이지 참조"},
            {"name": "제조자/수입자", "value": "협력업체 / 판매자"},
            {"name": "제조국", "value": "중국"},
            {"name": "수입식품안전관리특별법에 따른 수입신고 확인", "value": "수입식품안전관리특별법에 따른 수입신고를 필함"},
            {"name": "품질보증기준", "value": "관련법 및 소비자분쟁해결기준에 따름"},
            {"name": "A/S 책임자와 전화번호", "value": "판매자 고객센터 문의"}
        ],
        "sidebarFilters": [
            {"attributeTypeName": "사용대상", "attributeValueName": "남녀공용"},
            {"attributeTypeName": "보온/보냉 여부", "attributeValueName": "보온/보냉겸용"},
            {"attributeTypeName": "손잡이 유무", "attributeValueName": "손잡이있음"}
        ]
    }
}

def match_coupang_category_and_notices(keyword: str, brand: str = "자체제작") -> dict:
    meta = None
    for k, v in CATEGORY_PRESETS.items():
        if k in keyword or keyword in k:
            meta = v
            break
            
    if meta is None:
        meta = {
            "displayCategoryCode": 58974,
            "categoryName": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
            "noticeCategoryName": "기타 재화",
            "defaultNotices": [
                {"name": "제조자/수입자", "value": "협력업체 / 판매자"},
                {"name": "제조국", "value": "중국"},
                {"name": "품질보증기준", "value": "관련법 및 소비자분쟁해결기준에 따름"},
                {"name": "A/S 책임자와 전화번호", "value": "판매자 고객센터 문의"}
            ],
            "sidebarFilters": [
                {"attributeTypeName": "사용대상", "attributeValueName": "남녀공용"}
            ]
        }
        
    # [핵심] 품명 및 모델명에 [브랜드명 + 메인키워드] 주입 (검색 알고리즘 가중치 부여)
    full_model_name = f"{brand} {keyword}".strip()
    notices = [{"name": "품명 및 모델명", "value": full_model_name}] + meta["defaultNotices"]
    
    return {
        "displayCategoryCode": meta["displayCategoryCode"],
        "categoryName": meta["categoryName"],
        "noticeCategoryName": meta["noticeCategoryName"],
        "notices": notices,
        "attributes": meta["sidebarFilters"]
    }

if __name__ == "__main__":
    res = match_coupang_category_and_notices("자전거장갑", "G-SPORT")
    print(f"카테고리: {res['categoryName']}")
    print(f"품명및모델명: {res['notices'][0]['value']}")
    print("색상 표준화 테스트:", normalize_coupang_color("검정색 / 회색 / 흰색"))
