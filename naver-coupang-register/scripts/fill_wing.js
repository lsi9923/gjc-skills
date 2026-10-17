/**
 * fill_wing.js - Coupang Wing 자동 입력 및 diff 검증 스크립트
 * 
 * 설계 원칙 (ops-playbook 속도 설계):
 * 1. aside repl 1회 호출로 spec 읽어 입력 -> (save: true일 때만 중간저장) -> 폼/스토어 읽어 spec과 diff 반환
 * 2. 아코디언 펼침 필수
 * 3. 상품정보제공고시: 상품군 드롭다운 먼저 변경 후 칸별 값 입력
 * 4. 중간저장 경고 모달: .alert-confirm 조건부 클릭 (page.once('dialog') 사용 금지)
 * 5. 판매등록·저장하기·판매요청 버튼 코드는 일체 포함 금지
 */

async function fillWing({ page, spec, save = false }) {
  const result = {
    step: 'start',
    diff: [],
    filled: {},
    success: false
  };

  if (!page || !spec || !spec.wing) {
    throw new Error('page and spec.wing are required');
  }

  const wingSpec = spec.wing;

  console.log(`[fill_wing] Start filling Wing form for ${spec.id} (${spec.name})`);

  // 1. 아코디언 전체 펼침 (접혀 있으면 필드가 DOM에 렌더링되지 않음)
  try {
    await page.evaluate(() => {
      // Wing 아코디언 헤더 또는 토글 버튼들 전체 클릭하여 펼침
      const toggleHeaders = Array.from(document.querySelectorAll('.accordion-header, .collapse-header, .section-header'));
      for (const h of toggleHeaders) {
        if (!h.classList.contains('expanded') && !h.classList.contains('active')) {
          h.click();
        }
      }
      // 또는 fa-chevron-down / fa-chevron-right 등 아이콘이 닫힌 상태면 클릭
      const arrows = Array.from(document.querySelectorAll('.collapse-icon, .arrow-icon, .toggle-icon'));
      for (const a of arrows) {
        a.click();
      }
    });
    await page.waitForTimeout(500);
  } catch (e) {
    console.warn('[fill_wing] Accordion expand warning:', e.message);
  }

  // 2. 등록상품명(판매자관리용) & 노출상품명 입력
  try {
    // 2-1. 등록상품명
    const sellerProdInput = page.locator('input[placeholder*="등록상품명"], input[name*="sellerProductName"]').first();
    if (await sellerProdInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await sellerProdInput.fill(wingSpec.sellerProductName);
      result.filled.sellerProductName = wingSpec.sellerProductName;
    }

    // 2-2. 노출상품명 (비활성 체크)
    const displayProdInput = page.locator('input[placeholder*="노출상품명"], input[name*="displayProductName"]').first();
    if (await displayProdInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      const isDisabled = await displayProdInput.isDisabled().catch(() => false);
      if (!isDisabled && wingSpec.displayProductName) {
        await displayProdInput.fill(wingSpec.displayProductName);
        result.filled.displayProductName = wingSpec.displayProductName;
      } else {
        result.filled.displayProductName = '[DISABLED_OR_EMPTY]';
      }
    }
  } catch (e) {
    console.warn('[fill_wing] Product name fill warning:', e.message);
  }

  // 3. 카테고리 (이미 선택되어 있는지 확인 후 필요시 선택)
  try {
    const categoryInput = page.locator('input[placeholder*="카테고리명 입력"]').first();
    if (await categoryInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      const currentCat = await categoryInput.inputValue().catch(() => '');
      if (!currentCat && wingSpec.categoryPath) {
        // 카테고리 검색창에 마지막 키워드 입력
        const parts = wingSpec.categoryPath.split('>');
        const leaf = parts[parts.length - 1].trim();
        await categoryInput.fill(leaf);
        await categoryInput.press('Enter');
        await page.waitForTimeout(1000);
        // 추천 리스트에서 첫번째 항목 선택
        const firstRec = page.locator('.category-search-result li, .category-list li').first();
        if (await firstRec.isVisible({ timeout: 1500 }).catch(() => false)) {
          await firstRec.click();
        }
      }
    }
  } catch (e) {
    console.warn('[fill_wing] Category fill warning:', e.message);
  }

  // 4. 옵션 및 가격/재고
  try {
    if (wingSpec.optionRows && wingSpec.optionRows.length > 0) {
      const row0 = wingSpec.optionRows[0];
      // 정상가 / 판매가 / 재고 단일 또는 테이블 입력
      const salePriceInputs = page.locator('input[placeholder*="판매가"], input[name*="salePrice"]');
      if (await salePriceInputs.count() > 0) {
        await salePriceInputs.first().fill(String(row0.salePrice));
        result.filled.salePrice = row0.salePrice;
      }
      const origPriceInputs = page.locator('input[placeholder*="정상가"], input[placeholder*="할인율 기준가"], input[name*="originalPrice"]');
      if (await origPriceInputs.count() > 0 && row0.originalPrice) {
        await origPriceInputs.first().fill(String(row0.originalPrice));
        result.filled.originalPrice = row0.originalPrice;
      }
      const stockInputs = page.locator('input[placeholder*="재고"], input[name*="stock"]');
      if (await stockInputs.count() > 0) {
        await stockInputs.first().fill(String(row0.stock));
        result.filled.stock = row0.stock;
      }
    }
  } catch (e) {
    console.warn('[fill_wing] Price/stock fill warning:', e.message);
  }

  // 5. 검색어 (15개) 입력
  try {
    if (wingSpec.searchTerms && wingSpec.searchTerms.length > 0) {
      const tagInput = page.locator('input[placeholder*="검색어를 입력하세요"], .srp-search-input').first();
      if (await tagInput.isVisible({ timeout: 1000 }).catch(() => false)) {
        for (const term of wingSpec.searchTerms) {
          await tagInput.fill(term);
          await tagInput.press('Enter');
          await page.waitForTimeout(100);
        }
        result.filled.searchTermsCount = wingSpec.searchTerms.length;
      }
    }
  } catch (e) {
    console.warn('[fill_wing] Search terms fill warning:', e.message);
  }

  // 6. 상품정보제공고시 (상품군 드롭다운 먼저 변경 필수)
  try {
    if (wingSpec.notice) {
      // 6-1. 고시 상품군 드롭다운 변경
      const noticeGroupSelect = page.locator('.notice-section select, select[name*="noticeGroup"], select.notice-category-select').first();
      if (await noticeGroupSelect.isVisible({ timeout: 1500 }).catch(() => false)) {
        await noticeGroupSelect.selectOption({ label: wingSpec.notice.group }).catch(async () => {
          // label로 못 찾을 시 text 검색
          await noticeGroupSelect.selectOption(wingSpec.notice.group);
        });
        await page.waitForTimeout(1000); // 드롭다운 변경 후 폼 필드 리렌더링 대기
      }

      // 6-2. 고시 칸별 값 입력
      if (wingSpec.notice.fields) {
        for (const [label, val] of Object.entries(wingSpec.notice.fields)) {
          if (val === null) continue; // null인 값은 건너뜀 (지어내기 금지)
          // 라벨 근처의 input/textarea 매핑
          const fieldInput = page.locator(`tr:has-text("${label}") input, tr:has-text("${label}") textarea, div:has-text("${label}") > input, div:has-text("${label}") > textarea`).first();
          if (await fieldInput.isVisible({ timeout: 500 }).catch(() => false)) {
            await fieldInput.fill(val);
          }
        }
      }
      result.filled.noticeGroup = wingSpec.notice.group;
    }
  } catch (e) {
    console.warn('[fill_wing] Notice fill warning:', e.message);
  }

  // 7. 제조사 / 브랜드 / 인증
  try {
    // 제조사: 협력업체
    const mfgInput = page.locator('input[placeholder*="제조사명"], input[name*="manufacturer"]').first();
    if (await mfgInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await mfgInput.fill(wingSpec.manufacturer || '협력업체');
      result.filled.manufacturer = wingSpec.manufacturer;
    }

    // 인증: 상세페이지 별도표기 또는 대상아님
    if (wingSpec.certification && wingSpec.certification.certificationType) {
      const certRadio = page.locator(`input[value*="${wingSpec.certification.certificationType}"]`).first();
      if (await certRadio.isVisible({ timeout: 1000 }).catch(() => false)) {
        await certRadio.check();
      }
    }
  } catch (e) {
    console.warn('[fill_wing] Mfg/Cert fill warning:', e.message);
  }

  // 8. 중간저장 (save 옵션이 true일 때만 실행)
  if (save === true) {
    console.log('[fill_wing] save: true specified. Triggering intermediate save...');
    const saveBtn = page.locator('button:has-text("중간저장")').first();
    if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await saveBtn.click();
      await page.waitForTimeout(500);

      // 조건부 DOM 확인 모달 처리 (.alert-confirm)
      const confirmBtn = page.locator('.alert-confirm');
      if (await confirmBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
        console.log('[fill_wing] .alert-confirm modal detected. Clicking confirm...');
        await confirmBtn.click();
      }
      await page.waitForTimeout(2000);
      result.saved = true;
    } else {
      result.saved = false;
      result.diff.push({ field: 'saveButton', expected: 'visible', actual: 'not_found' });
    }
  } else {
    console.log('[fill_wing] save: false. Skipping intermediate save (dry-run mode).');
    result.saved = null;
  }

  // 9. 폼 입력값 읽기 및 spec 대조 (Diff 계산)
  try {
    const currentValues = await page.evaluate(() => {
      const sellerProd = document.querySelector('input[placeholder*="등록상품명"], input[name*="sellerProductName"]');
      const displayProd = document.querySelector('input[placeholder*="노출상품명"], input[name*="displayProductName"]');
      const salePrice = document.querySelector('input[placeholder*="판매가"], input[name*="salePrice"]');
      
      // Vuex store가 있으면 store의 최신 oSellerProduct도 조회
      const appMain = document.querySelector('.app-main');
      const storeProd = appMain && appMain.__vue__ && appMain.__vue__.$store ? appMain.__vue__.$store.getters.oSellerProduct : null;

      return {
        sellerProductName: sellerProd ? sellerProd.value : (storeProd ? storeProd.sellerProductName : null),
        displayProductName: displayProd ? displayProd.value : (storeProd ? storeProd.displayProductName : null),
        salePrice: salePrice ? parseInt(salePrice.value.replace(/[^0-9]/g, ''), 10) : (storeProd && storeProd.items && storeProd.items[0] ? storeProd.items[0].salePrice : null)
      };
    });

    result.currentFormValues = currentValues;

    // Diff 비교
    if (wingSpec.sellerProductName && currentValues.sellerProductName !== wingSpec.sellerProductName) {
      result.diff.push({
        field: 'sellerProductName',
        expected: wingSpec.sellerProductName,
        actual: currentValues.sellerProductName
      });
    }

    if (wingSpec.optionRows && wingSpec.optionRows[0] && currentValues.salePrice !== wingSpec.optionRows[0].salePrice) {
      result.diff.push({
        field: 'salePrice',
        expected: wingSpec.optionRows[0].salePrice,
        actual: currentValues.salePrice
      });
    }

    result.success = (result.diff.length === 0);
  } catch (e) {
    result.diff.push({ field: 'readBack', error: e.message });
    result.success = false;
  }

  console.log(`[fill_wing] Completed fill for ${spec.id}. Diff count: ${result.diff.length}`);
  return result;
}

if (typeof module !== 'undefined') {
  module.exports = { fillWing };
}
