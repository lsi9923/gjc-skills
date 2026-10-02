#!/usr/bin/env python3
"""
쿠팡 전용 고관여 F자 패턴 상품명 조합기 (스월백 & 대디갓재 실전 전략 반영)
공식: [브랜드명] + [고관여 소구점/특장점 서브키워드] + [메인 키워드]
원리:
  - 소비자는 이미 검색 후 진입하므로 메인 키워드는 3열(뒤)에 배치.
  - 사람의 시선 이동(F자 패턴)에 맞춰 시선을 사로잡는 고관여 특장점을 전면에 배치하여 CTR(클릭률) 극대화.
  - 단어 수 5~6개 내외로 제한하여 가독성과 알고리즘 품질 점수 극대화.
  - 특수기호(+, [], (), / 등) 및 옵션에 들어갈 색상/사이즈/수량 단어는 자동 정제/제거.
"""
import re

# 옵션으로 들어가야 할 단어 (상품명 중복 방지 및 감점 방지)
OPTION_WORDS = [
    "블랙", "화이트", "그레이", "레드", "블루", "그린", "옐로우", "핑크", "베이지", "네이비",
    "검정", "흰색", "회색", "빨강", "파랑", "노랑",
    "S", "M", "L", "XL", "2XL", "3XL", "FREE", "프리", "프리사이즈",
    "1개", "2개", "3개", "1+1", "1세트", "2세트", "세트"
]

SPECIAL_CHARS = re.compile(r"[\+\[\]\(\)\{\}\<\>/\,\!\@\#\$\%\^\&\*\~]")

def clean_word(w: str) -> str:
    cleaned = SPECIAL_CHARS.sub("", w).strip()
    return cleaned

def compose_coupang_f_pattern_title(
    brand: str,
    main_keyword: str,
    hook_features: list[str],
    max_words: int = 6
) -> str:
    """
    [브랜드] + [고관여 소구점 2~3개] + [메인 키워드]
    예: "자체제작 무선 충전 대용량 보온 텀블러"
    """
    tokens = []
    
    # 1. 브랜드 (브랜드 없으면 생략 가능)
    if brand and brand not in ["자체제작", "노브랜드", "협력업체", "브랜드없음"]:
        b_clean = clean_word(brand)
        if b_clean:
            tokens.append(b_clean)
            
    # 2. 고관여 소구점 (F자 패턴 앞단)
    feature_words = []
    for f in hook_features:
        for w in f.split():
            cw = clean_word(w)
            if cw and cw not in OPTION_WORDS and cw != main_keyword and cw not in feature_words and cw not in tokens:
                feature_words.append(cw)
                
    # 앞단에 배치할 소구점 2~4개 선택
    # 남은 자리: max_words - (1 if brand else 0) - len(main_keyword.split())
    main_words = [clean_word(w) for w in main_keyword.split() if clean_word(w)]
    available_feature_slots = max(1, max_words - len(tokens) - len(main_words))
    
    selected_features = feature_words[:available_feature_slots]
    tokens.extend(selected_features)
    
    # 3. 메인 키워드 (F자 패턴 3열/뒷단)
    for mw in main_words:
        if mw not in tokens:
            tokens.append(mw)
            
    title = " ".join(tokens)
    return title

if __name__ == "__main__":
    t1 = compose_coupang_f_pattern_title(
        brand="G-SPORT",
        main_keyword="자전거 장갑",
        hook_features=["겨울 방한", "방풍 기모", "터치스크린", "충격흡수"]
    )
    print(f"[예시 1] {t1} (단어수: {len(t1.split())})")

    t2 = compose_coupang_f_pattern_title(
        brand="",
        main_keyword="보온 텀블러",
        hook_features=["차량용 무선", "대용량 빨대형", "스테인리스 손잡이"]
    )
    print(f"[예시 2] {t2} (단어수: {len(t2.split())})")
