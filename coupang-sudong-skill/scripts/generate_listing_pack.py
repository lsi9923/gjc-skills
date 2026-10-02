#!/usr/bin/env python3
"""
네이버 스마트스토어 & 쿠팡 윙 통합 상위노출 등록 팩 생성기
1688 소싱 데이터 기반 -> 듀얼 플랫폼 즉시 등록용 데이터 전수 출력 (CLI 및 JSON 내보내기)
"""
import sys
import os
import json
import argparse
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))

from category_dispatcher import resolve_20_category
from coupang_title_composer import compose_coupang_f_pattern_title
from coupang_tags_generator import get_coupang_tags
from genuine_notices_builder import build_20_category_notices
from run_coupang_pipeline import build_coupang_complete_payload

def generate_dual_listing_pack(sourcing_spec: dict) -> dict:
    main_kw = sourcing_spec.get("mainKeyword", "유모차모기장")
    cat = resolve_20_category(main_kw)
    features = sourcing_spec.get("features", ["풀커버 방충망", "중앙 지퍼형", "전차종 호환", "고밀도 미세메쉬"])
    
    # 1. 가격 계산
    base_cny = sourcing_spec.get("cnyPrice", 4.0)
    exchange_rate = 200
    cost_krw = int(base_cny * exchange_rate)
    landed_cost_krw = sourcing_spec.get("landedCostKrw", 4032)
    
    # 판매가: 35% 마진 + 무료배송 기준
    sale_price = int(round(((cost_krw + 3500) / (1 - 0.35)) / 100) * 100)
    if sale_price < 11500 and landed_cost_krw >= 4000:
        sale_price = 19800  # 실측 시장 경쟁가 (1위 24,900원 대비 19,800원)
    original_price = int(round((sale_price * 1.5) / 100) * 100)
    
    # 2. 네이버 등록 데이터 조립
    naver_title = sourcing_spec.get("naverTitle", f"{main_kw} 유모차 방충망 풀커버 지퍼형 접이식")
    naver_tags = [
        "유모차모기장", "유모차방충망", "유모차커버", "유모차모기망", "유모차가리개",
        "휴대용유모차모기장", "디럭스유모차모기장", "절충형유모차모기장", "유모차방충커버", "아기유모차모기장"
    ]
    
    detail_html = f"""<div style="max-width:860px; margin:0 auto; font-family:-apple-system,BlinkMacSystemFont,sans-serif; line-height:1.6; color:#222;">
  <div style="text-align:center; padding:30px 10px; background:#f0fdf4; border-radius:12px; margin-bottom:24px;">
    <h2 style="font-size:24px; font-weight:800; color:#166534; margin:0 0 10px 0;">{main_kw} 여름 외출 필수 안심 풀커버</h2>
    <p style="font-size:15px; color:#15803d; margin:0;">고밀도 미세 벌집 메쉬로 날벌레·미세먼지 완벽 차단! 중앙 지퍼 개폐로 아이 승하차도 간편하게</p>
  </div>
  <div style="margin-bottom:24px;">
    <h3 style="font-size:18px; font-weight:700; border-bottom:2px solid #222; padding-bottom:8px;">📌 핵심 특장점</h3>
    <ul style="padding-left:20px; font-size:14px; color:#444;">
      {"".join(f'<li style="margin-bottom:6px;">{feat}</li>' for feat in features)}
      <li style="margin-bottom:6px;">전 차종 호환 (디럭스 / 절충형 / 휴대용 유모차 99% 완벽 피팅)</li>
      <li style="margin-bottom:6px;">고탄력 밴딩 마감으로 틈새 없는 해충 차단</li>
    </ul>
  </div>
  <div style="margin-bottom:24px;">
    <h3 style="font-size:18px; font-weight:700; border-bottom:2px solid #222; padding-bottom:8px;">📐 제품 상세 스펙</h3>
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
      <tr style="border-bottom:1px solid #e5e7eb;"><th style="width:25%; padding:8px; text-align:left; background:#f9fafb;">품명</th><td style="padding:8px;">유모차 범용 풀커버 모기장</td></tr>
      <tr style="border-bottom:1px solid #e5e7eb;"><th style="padding:8px; text-align:left; background:#f9fafb;">재질</th><td style="padding:8px;">고밀도 미세 벌집 메쉬 (폴리에스터 100%)</td></tr>
      <tr style="border-bottom:1px solid #e5e7eb;"><th style="padding:8px; text-align:left; background:#f9fafb;">치수/무게</th><td style="padding:8px;">70cm ~ 150cm 고탄력 확장 / 약 120g</td></tr>
      <tr style="border-bottom:1px solid #e5e7eb;"><th style="padding:8px; text-align:left; background:#f9fafb;">제조국/원산지</th><td style="padding:8px;">중국 (China) / 해외구매대행 수입</td></tr>
      <tr><th style="padding:8px; text-align:left; background:#f9fafb;">세탁방법</th><td style="padding:8px;">30℃ 미온수 중성세제 손세탁 권장 (열풍건조 금지)</td></tr>
    </table>
  </div>
  <div style="background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:16px; font-size:12px; color:#991b1b;">
    <b>[해외구매대행 안내]</b> 본 상품은 해외 공급처로부터 직접 배송되는 상품으로 주문 시 수령인의 <b>개인통관고유부호(PCC)</b>가 반드시 필요합니다. 평균 배송 소요일은 영업일 기준 7~10일 소요됩니다.
  </div>
</div>"""

    naver_pack = {
        "platform": "NAVER_SMARTSTORE",
        "targetUrl": "https://sell.smartstore.naver.com/#/products/create",
        "category": cat["naver"]["categoryName"],
        "categoryId": cat["naver"]["categoryId"],
        "categoryName": cat["naver"]["categoryName"],
        "productName": naver_title,
        "charCount": len(naver_title),
        "salePrice": sale_price,
        "stockQuantity": 999,
        "pricing": {
            "originalPrice": original_price,
            "salePrice": sale_price,
            "stockQuantity": 999,
            "deliveryChargeType": "FREE",
            "deliveryCharge": 0,
            "returnCharge": 3500,
            "exchangeCharge": 7000
        },
        "shipping": {
            "feeType": "FREE",
            "fee": 0,
            "returnFee": 3500,
            "exchangeFee": 7000,
            "outboundAddress": "인천광역시 검단구 완정로 146 (리더스빌) 2층 208-43c호 (23466)"
        },
        "origin": "중국",
        "brand": "자체제작",
        "manufacturer": "협력업체",
        "tags": naver_tags,
        "detailHtml": detail_html,
        "attributes": {
            "종류": "모기장",
            "커버기능": ["수면차광막", "방충차단", "시력보호창"],
            "호환모델": "전차종 호환 (디럭스/절충형/휴대용)"
        },
        "notices": {
            "noticeType": cat["naver"]["noticeType"],
            "items": {
                "품명 및 모델명": "유모차 범용 풀커버 모기장",
                "재질": "고밀도 미세메쉬 (폴리에스터 100%), 고탄력 밴드",
                "크기/중량": "70cm ~ 150cm / 약 120g",
                "색상": "블랙 / 패턴",
                "제조자/수입자": "협력업체 / 끄롱마켓",
                "제조국": "중국 (China)",
                "취급방법": "미온수 중성세제 손세탁 권장",
                "품질보증기준": "소비자분쟁해결기준에 따름",
                "A/S책임자": "판매자 고객센터 및 톡톡문의"
            }
        },
        "options": sourcing_spec.get("options", []),
        "seo": {
            "pageTitle": f"{naver_title} - 스마트스토어",
            "metaDescription": f"{main_kw} 유모차 방충망 풀커버 지퍼형 접이식 안심 해충 차단 커버"
        }
    }
    
    # 3. 쿠팡 윙 등록 데이터 조립
    features = sourcing_spec.get("features", ["풀커버 방충망", "중앙 지퍼형", "전차종 호환", "고밀도 미세메쉬"])
    coupang_title = compose_coupang_f_pattern_title("", main_kw, features, max_words=8)
    if len(coupang_title) < 50:
        coupang_title = f"{main_kw} 풀커버 방충망 디럭스 절충형 휴대용 전차종 호환 지퍼형 신생아 여름 외출 필수템 고밀도 미세메쉬 해충 차단 안심커버"
        
    coupang_tags = get_coupang_tags(main_kw, cat["matchedCategory"])
    coupang_payload = build_coupang_complete_payload(
        sourcing_spec=sourcing_spec,
        use_free_shipping=True,
        use_make_order_delay=False
    )
    
    coupang_pack = {
        **coupang_payload,
        "platform": "COUPANG_WING",
        "targetUrl": "https://wing.coupang.com/vendor/inventory/registration",
        "categoryName": cat["coupang"]["categoryName"],
        "sellerProductName": coupang_title,
        "displayProductName": f"{coupang_payload.get('brand', '')} {coupang_title}".strip()[:100],
        "charCount": len(coupang_title),
        "searchTags": coupang_tags,
        "pricing": {
            "originalPrice": original_price,
            "salePrice": sale_price,
            "stockQuantity": 999,
            "emptyBarcode": True,
            "emptyBarcodeReason": "해외구매대행 상품으로 바코드가 없습니다."
        },
        "shipping": {
            "deliveryMethod": "AGENT_BUY",
            "pccNeeded": True,
            "outboundShippingTimeDay": 7,
            "deliveryChargeType": "FREE",
            "deliveryCharge": 0,
            "returnCharge": 3500
        }
    }
    return {
        "sourceUrl": sourcing_spec.get("sourceUrl", ""),
        "offerId": sourcing_spec.get("offerId", ""),
        "naver": naver_pack,
        "coupang": coupang_pack
    }

if __name__ == "__main__":
    case_path = os.path.join(os.path.dirname(__file__), "..", "cases", "case_stroller_mosquito_net.json")
    spec = {}
    if os.path.exists(case_path):
        try:
            with open(case_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except Exception:
            pass

    pack = generate_dual_listing_pack({
        "mainKeyword": "유모차모기장",
        "sourceUrl": spec.get("sourceUrl", "https://detail.1688.com/offer/871109274152.html"),
        "offerId": spec.get("offerId", "871109274152"),
        "cnyPrice": spec.get("rawProduct", {}).get("supplyPricesCny", {}).get("base", 4.0),
        "landedCostKrw": spec.get("rawProduct", {}).get("sellerLifeImportLandedCostKrw", 4032),
        "features": spec.get("rawProduct", {}).get("specs", {}).get("features", ["풀커버 방충망", "중앙 지퍼형", "전차종 호환", "고밀도 미세메쉬"]),
        "options": spec.get("rawProduct", {}).get("options", [
            {"name": "[기본형] 클래식 풀커버 블랙", "cny": 4.0, "stock": 196},
            {"name": "[고급형] 프리미엄 중앙지퍼 블랙", "cny": 12.6, "stock": 977}
        ])
    })
    
    print("=" * 70)
    print("🚀 [네이버 스마트스토어 등록 팩]")
    print(f"* 카테고리: {pack['naver']['categoryName']} (ID: {pack['naver']['categoryId']})")
    print(f"* 상품명 ({pack['naver']['charCount']}자): {pack['naver']['productName']}")
    print(f"* 판매가: {pack['naver']['pricing']['salePrice']:,}원 (무료배송)")
    print(f"* 태그 10개: {', '.join(pack['naver']['tags'])}")
    print("=" * 70)
    print("🚀 [쿠팡 윙 등록 팩]")
    print(f"* 카테고리: {pack['coupang']['categoryName']} (코드: {pack['coupang']['displayCategoryCode']})")
    print(f"* 상품명 ({pack['coupang']['charCount']}자): {pack['coupang']['sellerProductName']}")
    print(f"* 배송설정: {pack['coupang']['shipping']['deliveryMethod']} (통관부호 필수, 출고 {pack['coupang']['shipping']['outboundShippingTimeDay']}일)")
    print(f"* 태그 20개: {', '.join(pack['coupang']['searchTags'])}")
    print("=" * 70)
