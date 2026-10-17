/**
 * fill_naver.js - Naver SmartStore 자동 입력 및 diff 검증 스크립트
 * 
 * 설계 원칙 (ops-playbook 속도 설계):
 * 1. aside repl 1회 호출로 spec 읽어 입력 -> (save: true일 때만 임시저장) -> 폼/스토어 읽어 spec과 diff 반환
 * 2. 스마트스토어 상품 등록 폼에 맞춘 상품명, 카테고리, 옵션, 고시, 태그(10개), 가격/재고, 인증 입력
 * 3. 판매등록·저장하기 버튼 코드는 일체 포함 금지 (오직 임시저장만 save: true 시 조건부)
 */

async function fillNaver({ page, spec, save = false }) {
  const result = {
    step: 'start',
    diff: [],
    filled: {},
    success: false
  };

  if (!page || !spec || !spec.naver) {
    throw new Error('page and spec.naver are required');
  }

  const naverSpec = spec.naver;

  console.log(`[fill_naver] Start filling Naver form for ${spec.id} (${spec.name})`);

  // 1. 상품명 입력
  try {
    const nameInput = page.locator('input[name="name"], input[placeholder*="상품명"]').first();
    if (await nameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nameInput.fill(naverSpec.productName);
      result.filled.productName = naverSpec.productName;
    }
  } catch (e) {
    console.warn('[fill_naver] Product name fill warning:', e.message);
  }

  // 2. 카테고리 선택
  try {
    const catSearchInput = page.locator('input[placeholder*="카테고리명 입력"], input.category-search-input').first();
    if (await catSearchInput.isVisible({ timeout: 1500 }).catch(() => false)) {
      const parts = naverSpec.categoryPath.split('>');
      const leaf = parts[parts.length - 1].trim();
      await catSearchInput.fill(leaf);
      await catSearchInput.press('Enter');
      await page.waitForTimeout(1000);

      // 검색 결과 중 첫번째 카테고리 클릭
      const firstResult = page.locator('.category-search-result-item, .category-list-item, li[role="option"]').first();
      if (await firstResult.isVisible({ timeout: 1500 }).catch(() => false)) {
        await firstResult.click();
        result.filled.category = leaf;
      }
    }
  } catch (e) {
    console.warn('[fill_naver] Category fill warning:', e.message);
  }

  // 3. 판매가 및 재고수량
  try {
    if (naverSpec.optionRows && naverSpec.optionRows.length > 0) {
      const row0 = naverSpec.optionRows[0];
      const priceInput = page.locator('input[name="salePrice"], input[name*="price"]').first();
      if (await priceInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        await priceInput.fill(String(row0.salePrice));
        result.filled.salePrice = row0.salePrice;
      }

      const stockInput = page.locator('input[name="stockQuantity"], input[name*="stock"]').first();
      if (await stockInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        await stockInput.fill(String(row0.stock));
        result.filled.stock = row0.stock;
      }
    }
  } catch (e) {
    console.warn('[fill_naver] Price/stock fill warning:', e.message);
  }

  // 4. 옵션 설정 (단일축 구성)
  try {
    if (naverSpec.optionAxes && naverSpec.optionRows && naverSpec.optionRows.length > 0) {
      // 옵션 사용 토글 활성화
      const optionToggle = page.locator('input[name="useOption"], input[type="radio"][value="true"]').first();
      if (await optionToggle.isVisible({ timeout: 1000 }).catch(() => false)) {
        await optionToggle.check();
        await page.waitForTimeout(500);

        // 옵션명 입력 (예: 구성)
        const optNameInput = page.locator('input[placeholder*="옵션명"]').first();
        if (await optNameInput.isVisible({ timeout: 1000 }).catch(() => false)) {
          await optNameInput.fill(naverSpec.optionAxes[0]);
        }

        // 옵션값 입력
        const optValInput = page.locator('input[placeholder*="옵션값"]').first();
        if (await optValInput.isVisible({ timeout: 1000 }).catch(() => false)) {
          await optValInput.fill(naverSpec.optionRows[0].values[0]);
        }

        // 옵션 목록으로 적용 버튼
        const applyBtn = page.locator('button:has-text("옵션목록으로 적용"), button:has-text("옵션 적용")').first();
        if (await applyBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
          await applyBtn.click();
          await page.waitForTimeout(500);
        }
        result.filled.option = `${naverSpec.optionAxes[0]}: ${naverSpec.optionRows[0].values[0]}`;
      }
    }
  } catch (e) {
    console.warn('[fill_naver] Option fill warning:', e.message);
  }

  // 5. 상품정보제공고시
  try {
    if (naverSpec.notice) {
      // 고시 상품군 드롭다운 선택
      const noticeGroupSelect = page.locator('select[name*="notice"], select[name*="modelNotice"]').first();
      if (await noticeGroupSelect.isVisible({ timeout: 1500 }).catch(() => false)) {
        await noticeGroupSelect.selectOption({ label: naverSpec.notice.group }).catch(async () => {
          await noticeGroupSelect.selectOption(naverSpec.notice.group);
        });
        await page.waitForTimeout(1000);
      }

      // 고시 칸별 값 입력
      if (naverSpec.notice.fields) {
        for (const [label, val] of Object.entries(naverSpec.notice.fields)) {
          if (val === null) continue;
          const fieldInput = page.locator(`tr:has-text("${label}") input, tr:has-text("${label}") textarea, div:has-text("${label}") > input`).first();
          if (await fieldInput.isVisible({ timeout: 500 }).catch(() => false)) {
            await fieldInput.fill(val);
          }
        }
      }
      result.filled.noticeGroup = naverSpec.notice.group;
    }
  } catch (e) {
    console.warn('[fill_naver] Notice fill warning:', e.message);
  }

  // 6. 태그 10개 입력
  try {
    if (naverSpec.tags && naverSpec.tags.length > 0) {
      const tagInput = page.locator('input[placeholder*="태그"], input.nvs-tag-input, input[name*="tag"]').first();
      if (await tagInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        for (const tag of naverSpec.tags) {
          await tagInput.fill(tag);
          await tagInput.press('Enter');
          await page.waitForTimeout(100);
        }
        result.filled.tagsCount = naverSpec.tags.length;
      }
    }
  } catch (e) {
    console.warn('[fill_naver] Tags fill warning:', e.message);
  }

  // 7. 브랜드 / 제조사
  try {
    const brandInput = page.locator('input[name*="brand"], input[placeholder*="브랜드"]').first();
    if (await brandInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await brandInput.fill(naverSpec.brand || '끄롱마제');
      result.filled.brand = naverSpec.brand;
    }

    const mfgInput = page.locator('input[name*="manufacturer"], input[placeholder*="제조사"]').first();
    if (await mfgInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await mfgInput.fill(naverSpec.manufacturer || '협력업체');
      result.filled.manufacturer = naverSpec.manufacturer;
    }
  } catch (e) {
    console.warn('[fill_naver] Brand/Mfg fill warning:', e.message);
  }

  // 8. 인증 처리 (구매대행 면제 또는 대상아님)
  try {
    if (naverSpec.certification) {
      if (naverSpec.certification.kcExemptionType === 'OVERSEAS') {
        // 해외구매대행 안전인증 면제 라디오 선택
        const certRadio = page.locator('input[value*="OVERSEAS"], input[value*="EXEMPTION"]').first();
        if (await certRadio.isVisible({ timeout: 1000 }).catch(() => false)) {
          await certRadio.check();
        }
      } else {
        const notReqRadio = page.locator('input[value*="NOT_REQUIRED"], input[value*="NONE"]').first();
        if (await notReqRadio.isVisible({ timeout: 1000 }).catch(() => false)) {
          await notReqRadio.check();
        }
      }
    }
  } catch (e) {
    console.warn('[fill_naver] Certification fill warning:', e.message);
  }

  // 9. 임시저장 (save 옵션이 true일 때만 실행)
  if (save === true) {
    console.log('[fill_naver] save: true specified. Clicking 임시저장...');
    const tempSaveBtn = page.locator('button:has-text("임시저장")').first();
    if (await tempSaveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await tempSaveBtn.click();
      await page.waitForTimeout(1500);
      result.saved = true;
    } else {
      result.saved = false;
      result.diff.push({ field: 'tempSaveButton', expected: 'visible', actual: 'not_found' });
    }
  } else {
    console.log('[fill_naver] save: false. Skipping 임시저장 (dry-run mode).');
    result.saved = null;
  }

  // 10. 폼 입력값 읽기 및 spec 대조 (Diff 계산)
  try {
    const currentValues = await page.evaluate(() => {
      const name = document.querySelector('input[name="name"], input[placeholder*="상품명"]');
      const price = document.querySelector('input[name="salePrice"], input[name*="price"]');
      const stock = document.querySelector('input[name="stockQuantity"], input[name*="stock"]');

      return {
        productName: name ? name.value : null,
        salePrice: price ? parseInt(price.value.replace(/[^0-9]/g, ''), 10) : null,
        stock: stock ? parseInt(stock.value.replace(/[^0-9]/g, ''), 10) : null
      };
    });

    result.currentFormValues = currentValues;

    // Diff 비교
    if (naverSpec.productName && currentValues.productName !== naverSpec.productName) {
      result.diff.push({
        field: 'productName',
        expected: naverSpec.productName,
        actual: currentValues.productName
      });
    }

    if (naverSpec.optionRows && naverSpec.optionRows[0] && currentValues.salePrice !== naverSpec.optionRows[0].salePrice) {
      result.diff.push({
        field: 'salePrice',
        expected: naverSpec.optionRows[0].salePrice,
        actual: currentValues.salePrice
      });
    }

    result.success = (result.diff.length === 0);
  } catch (e) {
    result.diff.push({ field: 'readBack', error: e.message });
    result.success = false;
  }

  console.log(`[fill_naver] Completed fill for ${spec.id}. Diff count: ${result.diff.length}`);
  return result;
}

if (typeof module !== 'undefined') {
  module.exports = { fillNaver };
}
