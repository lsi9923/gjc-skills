#!/usr/bin/env python3
"""
쿠팡/네이버 20대 전수 핵심 카테고리 동적 디스패처 (오탐 방지 정밀 매칭)
"""

CATEGORY_20_REGISTRY = {
    # 1. 원예 / 가드닝
    "원예가드닝": {
        "keywords": ["자동급수화분", "저면관수", "화분", "원예키트", "식물영양제", "물주개", "분무기", "가드닝", "재배키트"],
        "naver": {
            "categoryId": "50001254",
            "categoryName": "생활/건강 > 원예/식물 > 원예소품 > 화분",
            "noticeType": "GARDEN",
            "noticeTypeName": "원예용품",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 83450,
            "categoryName": "생활용품 > 원예/가드닝 > 화분/받침 > 저면관수화분",
            "noticeCategoryName": "원예용품",
            "mandatoryAttributes": ["화분 형태", "재질", "급수 방식", "배수구 유무", "직경/높이"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 2. 완구 / 취미
    "완구취미": {
        "keywords": ["3D퍼즐", "입체퍼즐", "메탈퍼즐", "프라모델", "피규어", "보드게임", "조립키트", "조립블록"],
        "naver": {
            "categoryId": "50001633",
            "categoryName": "출산/육아 > 완구/매트 > 퍼즐/블록 > 3D/입체퍼즐",
            "noticeType": "HOBBY",
            "noticeTypeName": "완구/취미용품 (성인용 조립키트)",
            "kcType": "EXEMPT"
        },
        "coupang": {
            "displayCategoryCode": 89120,
            "categoryName": "완구/취미 > 프라모델/피규어 > 메탈/3D퍼즐 > 조립키트",
            "noticeCategoryName": "완구/취미용품",
            "mandatoryAttributes": ["사용연령", "재질", "난이도", "조립 도구 포함여부", "피스 수"],
            "certificationType": "EXEMPT"
        }
    },

    # 3. 청소 / 생활가전
    "청소생활가전": {
        "keywords": ["초음파세척기", "안경세척기", "보풀제거기", "무선청소기", "물걸레", "스팀다리미"],
        "naver": {
            "categoryId": "50001588",
            "categoryName": "디지털/가전 > 생활가전 > 청소기 > 초음파세척기",
            "noticeType": "CLEAN",
            "noticeTypeName": "소형전자제품 (세척/청소)",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 78450,
            "categoryName": "가전디지털 > 생활가전 > 세척/살균기 > 초음파세척기",
            "noticeCategoryName": "소형전자제품 (음향기기/소형가전)",
            "mandatoryAttributes": ["초음파 주파수", "수조 용량", "전원 방식", "타이머 설정", "소재"],
            "certificationType": "TARGET"
        }
    },

    # 4. 여행 / 레저
    "여행레저": {
        "keywords": ["캐리어", "여행용캐리어", "기내용캐리어", "하드캐리어", "레디백", "여권케이스"],
        "naver": {
            "categoryId": "50000646",
            "categoryName": "패션잡화 > 여행용가방/소품 > 캐리어 > 하드캐리어",
            "noticeType": "BAG",
            "noticeTypeName": "가방 (여행가방/캐리어)",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 57420,
            "categoryName": "패션의류/잡화 > 여행가방 > 하드캐리어 > 20인치",
            "noticeCategoryName": "가방",
            "mandatoryAttributes": ["캐리어 인치", "바디 재질", "잠금장치(TSA)", "바퀴 수", "확장 가능여부"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 5. 공구 / DIY
    "공구DIY": {
        "keywords": ["전동드라이버", "전동드릴", "비트세트", "정밀드라이버", "렌치", "스패너"],
        "naver": {
            "categoryId": "50001301",
            "categoryName": "생활/건강 > 공구 > 전동공구 > 전동드라이버",
            "noticeType": "TOOL",
            "noticeTypeName": "전동공구",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 85110,
            "categoryName": "산업/공구 > 전동공구 > 드라이버/렌치 > 무선드라이버",
            "noticeCategoryName": "전동공구",
            "mandatoryAttributes": ["전압(V)", "최대 토크", "배터리 용량", "정역회전 기능", "비트 구성수"],
            "certificationType": "TARGET"
        }
    },

    # 6. 조명 / 인테리어
    "조명인테리어": {
        "keywords": ["무드등", "센서등", "수면등", "취침등", "간접조명", "스탠드조명"],
        "naver": {
            "categoryId": "50001083",
            "categoryName": "가구/인테리어 > 인테리어소품 > 조명 > 무드등",
            "noticeType": "LIGHT",
            "noticeTypeName": "조명기구",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 62450,
            "categoryName": "홈인테리어 > 조명/스탠드 > 무드등/취침등 > 터치센서등",
            "noticeCategoryName": "조명기구",
            "mandatoryAttributes": ["전원방식", "색온도 조절", "밝기 조절", "충전단자", "타이머 기능"],
            "certificationType": "TARGET"
        }
    },

    # 7. 문구 / 사무용품
    "문구사무": {
        "keywords": ["버티컬마우스", "무선마우스", "키보드", "마우스패드", "독서대", "데스크매트"],
        "naver": {
            "categoryId": "50001554",
            "categoryName": "디지털/가전 > PC주변기기 > 마우스 > 무선마우스",
            "noticeType": "OFFICE",
            "noticeTypeName": "사무용기기 (컴퓨터주변기기)",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 79150,
            "categoryName": "가전디지털 > 컴퓨터/주변기기 > 마우스 > 무선마우스",
            "noticeCategoryName": "사무용기기 (컴퓨터/노트북/주변기기)",
            "mandatoryAttributes": ["연결방식", "DPI 조절", "버튼 수", "배터리 종류", "인체공학 디자인"],
            "certificationType": "TARGET"
        }
    },

    # 8. 디지털 / PC주변기기
    "PC주변기기": {
        "keywords": ["멀티허브", "C타입허브", "도킹스테이션", "USB허브", "젠더", "카드리어"],
        "naver": {
            "categoryId": "50001553",
            "categoryName": "디지털/가전 > PC주변기기 > 케이블/젠더 > USB허브",
            "noticeType": "DIGITAL",
            "noticeTypeName": "소형전자제품",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 79240,
            "categoryName": "가전디지털 > 컴퓨터/주변기기 > PC주변기기 > USB허브",
            "noticeCategoryName": "소형전자제품 (음향기기/소형가전)",
            "mandatoryAttributes": ["포트 수", "HDMI 해상도", "PD 충전 전력", "본체 인터페이스", "재질"],
            "certificationType": "TARGET"
        }
    },

    # 9. 유아 / 아동용품
    "유아용품": {
        "keywords": ["흡착식판", "유아식판", "턱받이", "치발기", "유모차", "카시트", "아기띠", "이유식기"],
        "naver": {
            "categoryId": "50000139",
            "categoryName": "출산/육아 > 수유용품 > 이유식용품 > 이유식기/식판",
            "noticeType": "BABY",
            "noticeTypeName": "영유아용품",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 88410,
            "categoryName": "출산/유아동 > 이유식용품 > 식판/볼 > 흡착식판",
            "noticeCategoryName": "영유아용품",
            "mandatoryAttributes": ["사용연령", "BPA 프리 여부", "식기세척기 가능", "열탕소독 가능", "소재"],
            "certificationType": "TARGET"
        }
    },
    # 9-1. 유모차 방충/모기장 액세서리
    "유모차방충망": {
        "keywords": ["유모차모기장", "유모차방충망", "유모차모기망", "유모차커버", "유모차가리개", "유모차방충커버", "방충망", "모기망", "유모차"],
        "naver": {
            "categoryId": "50000624",
            "categoryName": "출산/육아 > 유모차 > 유모차용품 > 유모차커버",
            "noticeType": "BABY",
            "noticeTypeName": "영유아용품",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 77108,
            "categoryName": "출산/유아동 > 외출용품 > 유모차액세서리 > 유모차방충막/모기장",
            "noticeCategoryName": "영유아용품",
            "mandatoryAttributes": ["호환 유모차", "재질", "개폐 방식", "신축 조절 범위", "차단 기능"],
            "certificationType": "TARGET"
        }
    },

    # 10. 식품 / 가공식품
    "가공식품": {
        "keywords": ["동결건조", "과일칩", "간식", "스낵", "견과류", "초콜릿", "원두", "건어물"],
        "naver": {
            "categoryId": "50000026",
            "categoryName": "식품 > 과자/베이커리 > 스낵/과자 > 기타스낵",
            "noticeType": "FOOD",
            "noticeTypeName": "가공식품",
            "kcType": "FOOD_SAFETY"
        },
        "coupang": {
            "displayCategoryCode": 91200,
            "categoryName": "식품 > 스낵/간식 > 과자/스낵 > 건조스낵",
            "noticeCategoryName": "가공식품",
            "mandatoryAttributes": ["보관방법", "총 수량", "포장형태", "원재료", "유통기한"],
            "certificationType": "EXEMPT"
        }
    },

    # 11. 반려동물
    "반려동물": {
        "keywords": ["강아지식기", "노즈워크", "급식기", "사료그릇", "고양이장난감", "하네스", "배변패드", "반려동물", "강아지", "고양이"],
        "naver": {
            "categoryId": "50001648",
            "categoryName": "생활/건강 > 반려동물 > 강아지 식기/급수기 > 식기/식탁",
            "noticeType": "PET",
            "noticeTypeName": "반려동물용품",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 74512,
            "categoryName": "반려동물용품 > 강아지 식기/급수기 > 식기/급식기",
            "noticeCategoryName": "반려동물용품",
            "mandatoryAttributes": ["반려동물 크기", "식기 종류", "용량", "미끄럼방지 유무", "소재"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 12. 차량용품
    "차량용품": {
        "keywords": ["차량용거치대", "맥세이프거치대", "차량용충전기", "차량용", "맥세이프", "트렁크매트", "시트커버", "송풍구거치대"],
        "naver": {
            "categoryId": "50001053",
            "categoryName": "디지털/가전 > 휴대폰액세서리 > 거치대 > 차량용거치대",
            "noticeType": "CAR",
            "noticeTypeName": "자동차용품 (네비게이션/블랙박스/액세서리)",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 63980,
            "categoryName": "자동차용품 > 인테리어소품 > 휴대폰거치대 > 무선충전거치대",
            "noticeCategoryName": "자동차용품",
            "mandatoryAttributes": ["고정방식", "충전방식", "최대출력", "맥세이프 호환여부", "회전 여부"],
            "certificationType": "TARGET"
        }
    },

    # 13. 소형가전
    "소형가전": {
        "keywords": ["이어폰", "블루투스", "무선이어폰", "선풍기", "미니선풍기", "보조배터리", "가습기", "헤드셋", "스피커", "충전기"],
        "naver": {
            "categoryId": "50001597",
            "categoryName": "디지털/가전 > 음향가전 > 블루투스셋 > 블루투스이어폰",
            "noticeType": "DIGITAL",
            "noticeTypeName": "소형전자제품 (소형가전/음향/디지털)",
            "kcType": "TARGET"
        },
        "coupang": {
            "displayCategoryCode": 77892,
            "categoryName": "가전디지털 > 음향가전 > 이어폰/헤드폰 > 무선이어폰",
            "noticeCategoryName": "소형전자제품 (음향기기/소형가전)",
            "mandatoryAttributes": ["무선연결방식", "충전단자", "블루투스 버전", "배터리용량", "노이즈캔슬링 여부"],
            "certificationType": "TARGET"
        }
    },

    # 14. 스포츠/헬스
    "스포츠헬스": {
        "keywords": ["튜빙밴드", "저항밴드", "요가매트", "폼롤러", "덤벨", "아령", "악력기", "피트니스", "홈트"],
        "naver": {
            "categoryId": "50001428",
            "categoryName": "스포츠/레저 > 헬스/피트니스 > 웨이트기구 > 튜빙/스트레칭밴드",
            "noticeType": "SPORTS",
            "noticeTypeName": "체육용품",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 59120,
            "categoryName": "스포츠/레저 > 헬스/피트니스 > 피트니스소품 > 밴드/스트랩",
            "noticeCategoryName": "체육용품",
            "mandatoryAttributes": ["강도", "재질", "제품구성", "길이", "사용부위"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 15. 가구/캠핑
    "가구캠핑": {
        "keywords": ["캠핑체어", "캠핑의자", "캠핑테이블", "릴렉스체어", "접이식의자", "텐트"],
        "naver": {
            "categoryId": "50001402",
            "categoryName": "스포츠/레저 > 캠핑 > 캠핑가구 > 캠핑의자",
            "noticeType": "FURNITURE",
            "noticeTypeName": "가구 (침대/소파/테이블/체어)",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 61240,
            "categoryName": "스포츠/레저 > 캠핑 > 캠핑가구 > 캠핑의자",
            "noticeCategoryName": "가구",
            "mandatoryAttributes": ["종류", "프레임재질", "내하중", "접이식 여부", "중량"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 16. 화장품/뷰티
    "화장품": {
        "keywords": ["수분크림", "에센스", "세럼", "로션", "앰플", "립스틱", "클렌저", "선크림", "크림"],
        "naver": {
            "categoryId": "50000190",
            "categoryName": "화장품/미용 > 스킨케어 > 크림",
            "noticeType": "COSMETIC",
            "noticeTypeName": "화장품",
            "kcType": "COSMETIC_REG"
        },
        "coupang": {
            "displayCategoryCode": 67890,
            "categoryName": "뷰티 > 스킨케어 > 크림/올인원 > 수분크림",
            "noticeCategoryName": "화장품",
            "mandatoryAttributes": ["피부타입", "피부고민", "용량", "주요제품특징", "사용부위"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 17. 생활/욕실
    "생활욕실": {
        "keywords": ["샤워헤드", "필터샤워기", "샤워기", "수전", "배수구", "칫솔살균기"],
        "naver": {
            "categoryId": "50001099",
            "categoryName": "생활/건강 > 욕실용품 > 샤워기/수전용품 > 샤워기헤드",
            "noticeType": "BATH",
            "noticeTypeName": "생활위생용품",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 81245,
            "categoryName": "생활용품 > 욕실용품 > 샤워기/호스 > 샤워헤드",
            "noticeCategoryName": "생활위생용품",
            "mandatoryAttributes": ["샤워헤드 기능", "절수 기능 유무", "필터 포함 여부", "헤드 직경", "연결 규격"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 18. 주방용품
    "주방용품": {
        "keywords": ["텀블러", "보온병", "물병", "냄비", "프라이팬", "수저세트", "밀폐용기", "조리도구"],
        "naver": {
            "categoryId": "50000155",
            "categoryName": "주방용품 > 잔/컵/보온병 > 텀블러/보온병",
            "noticeType": "KITCHEN",
            "noticeTypeName": "주방용품",
            "kcType": "FOOD_SAFETY"
        },
        "coupang": {
            "displayCategoryCode": 71822,
            "categoryName": "주방용품 > 잔/컵/보온병 > 텀블러/보온병",
            "noticeCategoryName": "주방용품",
            "mandatoryAttributes": ["용량", "보온/보냉 여부", "손잡이 유무", "빨대 포함여부", "식기세척기 사용가능여부"],
            "certificationType": "EXEMPT"
        }
    },

    # 19. 패션의류
    "패션의류": {
        "keywords": ["후드티", "맨투맨", "팬츠", "바지", "티셔츠", "자켓", "패딩", "조거팬츠", "원피스", "청바지"],
        "naver": {
            "categoryId": "50000803",
            "categoryName": "패션의류 > 남성의류 > 티셔츠",
            "noticeType": "CLOTHES",
            "noticeTypeName": "의류",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 56123,
            "categoryName": "패션의류 > 남성의류 > 상의 > 티셔츠/후드",
            "noticeCategoryName": "의류",
            "mandatoryAttributes": ["상의 사이즈", "핏", "기장", "소재", "계절"],
            "certificationType": "NOT_TARGET"
        }
    },

    # 20. 패션잡화
    "패션잡화": {
        "keywords": ["장갑", "방한장갑", "자전거장갑", "라이딩장갑", "모자", "벨트", "양말", "머플러", "넥워머", "스카프"],
        "naver": {
            "categoryId": "50001476",
            "categoryName": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
            "noticeType": "WEAR",
            "noticeTypeName": "패션잡화 (모자/벨트/액세서리/가방/장갑)",
            "kcType": "NOT_TARGET"
        },
        "coupang": {
            "displayCategoryCode": 58974,
            "categoryName": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
            "noticeCategoryName": "패션잡화 (모자/벨트/액세서리)",
            "mandatoryAttributes": ["사용대상", "계절", "장갑 형태", "주요기능", "스마트폰 터치 가능여부"],
            "certificationType": "NOT_TARGET"
        }
    }
}

def resolve_20_category(keyword: str) -> dict:
    clean = keyword.replace(" ", "")
    # 키워드 길이 내림차순 정렬 (더 구체적인 키워드 우선 매칭)
    all_kws = []
    for cat_name, cat_data in CATEGORY_20_REGISTRY.items():
        for kw in cat_data["keywords"]:
            all_kws.append((len(kw), kw, cat_name, cat_data))
    all_kws.sort(key=lambda x: x[0], reverse=True)

    for _, kw, cat_name, cat_data in all_kws:
        if kw in keyword or kw in clean:
            return {"matchedCategory": cat_name, **cat_data}
            
    return {"matchedCategory": "패션잡화", **CATEGORY_20_REGISTRY["패션잡화"]}
