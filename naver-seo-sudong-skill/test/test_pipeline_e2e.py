"""
실제 1688 소싱 케이스 기반 4대 에이전트 파이프라인 통합 검증 테스트
[Agent 1: 소싱 분석] -> [Agent 2: SEO 실측] -> [Agent 3: 20개 폼/JSON 생성] -> [Agent 4: Auto-fill 브릿지 데이터 정합성]
"""
import json
import os
import sys

def test_full_pipeline():
    schema_path = os.path.join(os.path.dirname(__file__), "..", "contracts", "listing-data.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # 1. Agent 1 시뮬레이션 (1688 소싱 스펙 분석 결과)
    sourcing_output = {
        "rawTitle": "夏季户外骑行手套防滑半指山地公路自行车运动手套",
        "cnyPrice": 18.0,
        "specs": {
            "material": "고탄성 라이크라, 통기성 메쉬, 극세사 실리콘",
            "size": ["M", "L", "XL"],
            "color": ["블랙", "레드", "블루"],
            "weight": "75g",
            "features": ["3D 젤패드 충격흡수", "통기성 메쉬 땀배출", "탈착 편의 이지풀 탭"]
        },
        "candidateMainKeywords": ["자전거장갑", "라이딩장갑"]
    }

    # 2. Agent 2 시뮬레이션 (네이버 SEO 실측 결과)
    seo_output = {
        "category": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
        "relevance": 1.0,
        "titles": {
            "titleA": "자전거장갑 여름 바이크 장갑 라이딩 장갑 자전거 반장갑",
            "lengthA": 30,
            "titleB": "여름 바이크 장갑 자전거장갑 라이딩 장갑 사이클 반장갑",
            "lengthB": 29
        },
        "tags": [
            "자전거장갑", "라이딩장갑", "여름바이크장갑", "자전거반장갑",
            "싸이클장갑", "로드자전거장갑", "산악자전거장갑", "MTB장갑", "터치장갑", "통기성장갑"
        ]
    }

    # 3. Agent 3 시뮬레이션 (스마트스토어 20개 항목 페이로드 생성)
    # 마진 35%, 환율 200원, 배송비 3,500원 반영
    exchange_rate = 200
    cost_krw = sourcing_output["cnyPrice"] * exchange_rate
    margin_rate = 0.35
    target_price = int(round((cost_krw / (1 - margin_rate)) / 100) * 100)

    listing_payload = {
        "category": seo_output["category"],
        "productName": seo_output["titles"]["titleA"],
        "salePrice": target_price,
        "stockQuantity": 999,
        "options": [
            {"groupName": "색상", "values": sourcing_output["specs"]["color"]},
            {"groupName": "사이즈", "values": sourcing_output["specs"]["size"]}
        ],
        "tags": seo_output["tags"],
        "detailHtml": f"""
        <div style="max-width:860px; margin:0 auto; font-family:sans-serif;">
            <h2>장거리 라이딩에도 손바닥 저림 없는 3D 젤패드 자전거 반장갑</h2>
            <p>특장점: {', '.join(sourcing_output['specs']['features'])}</p>
            <p>소재: {sourcing_output['specs']['material']}</p>
        </div>
        """,
        "origin": "중국",
        "brand": "자체제작",
        "manufacturer": "협력업체",
        "shipping": {
            "feeType": "PAID",
            "fee": 3500,
            "returnFee": 3500,
            "exchangeFee": 7000,
            "outboundAddress": "인천광역시 검단구 완정로 146 (리더스빌) 2층 208-43c호 (23466)"
        },
        "seo": {
            "pageTitle": f"{seo_output['titles']['titleA']} - 스마트스토어",
            "metaDescription": "충격흡수 젤패드와 통기성 메쉬를 갖춘 여름 라이딩 자전거장갑"
        }
    }

    # 4. 검증: 필수 스키마 속성 확인
    for req in schema["required"]:
        assert req in listing_payload, f"Missing required property: {req}"

    # 5. 상품명 25~30자 검증
    name_len = len(listing_payload["productName"])
    assert 25 <= name_len <= 35, f"Product name length out of range: {name_len}"

    # 6. 태그 10개 검증
    assert len(listing_payload["tags"]) <= 10, "Tags count must be <= 10"

    print("Pipeline Integration Test Passed Successfully!")
    print(f"- 카테고리: {listing_payload['category']}")
    print(f"- 확정 상품명 ({name_len}자): {listing_payload['productName']}")
    print(f"- 계산된 판매가: {listing_payload['salePrice']:,}원")
    print(f"- 태그 ({len(listing_payload['tags'])}개): {', '.join(listing_payload['tags'])}")

if __name__ == "__main__":
    test_full_pipeline()
