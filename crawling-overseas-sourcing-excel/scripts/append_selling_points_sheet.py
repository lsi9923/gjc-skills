import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pathlib import Path
import json

EXCEL_PATH = Path(r"C:/Users/imda0/Desktop/해외구매대행_사입_TOP50_상품리뷰_수집분석.xlsx")
JSON_PATH = Path(r"C:/tmp/product_selling_points.json")

def append_selling_points_sheet():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    products = data.get("products", [])

    wb = openpyxl.load_workbook(EXCEL_PATH)
    sheet_title = "상품별 핵심 소구점 및 카피"
    if sheet_title in wb.sheetnames:
        del wb[sheet_title]
    
    ws = wb.create_sheet(title=sheet_title)

    # Styles
    title_font = Font(name="맑은 고딕", size=14, bold=True, color="1F4E79")
    header_font = Font(name="맑은 고딕", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    body_font = Font(name="맑은 고딕", size=9)
    bold_body_font = Font(name="맑은 고딕", size=9, bold=True)
    hook_font = Font(name="맑은 고딕", size=10, bold=True, color="C00000")
    border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    headers = [
        "순번", "추천 순위", "상품명", "카테고리", "근거 신뢰도",
        "킬러 메인 헤드라인 (클릭 유발)", "서브 설명 카피 (실질 혜택)",
        "고객 핵심 결핍 (Pain Point)", "제품 핵심 해결책 (Solution)",
        "3대 핵심 소구점 (Appeal Points)", "구매 전환 트리거 (결제 결심 이유)",
        "실구매 고객 리얼 인용구", "표시광고 주의사항 (과장 방지)"
    ]

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(1, col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28

    cat_map = {
        "MERAKA만능 채칼": "주방용품",
        "동물 자석 커플 키링": "팬시/잡화",
        "27리빙 여행용 깔끔한 소분": "여행/생활",
        "비비돔 무선 미니 고데기": "디지털/이미용",
        "의자 커버": "홈/인테리어",
        "파스텔펫 강아지": "반려동물",
        "Zeekr 차량용": "차량용품",
        "베베데코 고탄력": "홈/인테리어"
    }

    for idx, p in enumerate(products, start=1):
        p_name = p.get("product", "")
        cat_val = "생활잡화"
        for k, v in cat_map.items():
            if k in p_name:
                cat_val = v
                break

        # Refined headlines by Antigravity recommendations
        hl = p.get("headline", "")
        if "손 다칠 걱정 끝" in hl: hl = "푸드홀더로 안전하게, 균일한 채썰기"
        elif "뜬 앞머리 10초 만에" in hl: hl = "바쁜 아침 뜬 앞머리 간편 정돈"
        elif "여행 짐 부피 반으로" in hl: hl = "짐 부피를 쏙 줄이는 소분 파우치"
        elif "소파 새로 사지 말고" in hl: hl = "소파에 씌워 새것처럼 분위기 전환"

        appeal_text = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(p.get("appeal_points", [])))
        quotes_text = "\n".join(f'"{q}"' for q in p.get("evidence_quotes", []))
        avoid_text = "\n".join(f"• {a}" for a in p.get("avoid_claims", []))

        row_vals = [
            idx,
            f"{idx}위",
            p_name,
            cat_val,
            p.get("evidence_confidence", "보통"),
            hl,
            p.get("sub_copy", ""),
            p.get("pain_point", ""),
            p.get("solution", ""),
            appeal_text,
            p.get("purchase_trigger", ""),
            quotes_text,
            avoid_text
        ]
        ws.append(row_vals)
        r_num = idx + 1
        ws.row_dimensions[r_num].height = 85

        for c_idx in range(1, len(row_vals) + 1):
            cell = ws.cell(r_num, c_idx)
            cell.border = border
            if c_idx == 6:
                cell.font = hook_font
            elif c_idx in (2, 5):
                cell.font = bold_body_font
            else:
                cell.font = body_font

            align_h = "center" if c_idx in (1, 2, 4, 5) else "left"
            cell.alignment = Alignment(horizontal=align_h, vertical="center", wrap_text=True)

    # Column widths
    ws.column_dimensions["A"].width = 7
    ws.column_dimensions["B"].width = 11
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 14
    ws.column_dimensions["F"].width = 32
    ws.column_dimensions["G"].width = 34
    ws.column_dimensions["H"].width = 38
    ws.column_dimensions["I"].width = 38
    ws.column_dimensions["J"].width = 45
    ws.column_dimensions["K"].width = 38
    ws.column_dimensions["L"].width = 40
    ws.column_dimensions["M"].width = 35

    try:
        wb.save(EXCEL_PATH)
        print(f"SUCCESS: Saved sheet to {EXCEL_PATH}")
    except PermissionError:
        import time
        alt_path = EXCEL_PATH.with_name(f"{EXCEL_PATH.stem}_{time.strftime('%H%M%S')}{EXCEL_PATH.suffix}")
        wb.save(alt_path)
        print(f"SUCCESS: Saved sheet to alt path {alt_path}")

if __name__ == "__main__":
    append_selling_points_sheet()
