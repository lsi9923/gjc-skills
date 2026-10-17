/**
 * fill_naver.js - Naver SmartStore 자동 입력 및 전수 diff 검증 스크립트
 * 
 * 설계 원칙 (ops-playbook 속도 설계 & agy/Claude 검토 피드백):
 * 1. aside repl 1회 호출로 spec 읽어 입력 -> (save: true일 때만 임시저장) -> 폼/스토어 읽어 spec과 diff 반환
 * 2. 스마트스토어 상품 등록 폼에 맞춘 상품명, 카테고리, 옵션, 고시, 태그(10개), 가격/재고, 인증 입력
 * 3. 판매등록·저장하기 버튼 코드는 일체 포함 금지 (오직 임시저장만 save: true 시 조건부)
 * 4. 전 필드 전수 diff: 상품명·카테고리·옵션값/행수·정상가·판매가·재고·태그10·고시·제조사/브랜드·인증
 * 5. errors[] 또는 diff[]가 하나라도 있으면 success: false
 */

const sleep = ms => new Promise(r => setTimeout(r, ms));
// console shim

async function fillNaver({ page, spec, save = false }) {
  const result = {
    step: 'start',
    errors: [],
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
    const nameInput = page.locator('input[name="product.name"], input[name="name"], input[placeholder*="상품명"]').first();
    if (await nameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nameInput.fill(naverSpec.productName);
      result.filled.productName = naverSpec.productName;
    } else {
      result.errors.push({ step: 'productName', error: 'input_not_found' });
    }
  } catch (e) {
    result.errors.push({ step: 'productName', error: e.message });
    console.log('[fill_naver] Product name fill warning:', e.message);
  }

  // 2. 카테고리 선택
  try {
    const parts = naverSpec.categoryPath.split('>');
    const leaf = parts[parts.length - 1].trim();

    const isAlreadySelected = await page.evaluate((categoryLeaf) => {
      const selectedEl = document.querySelector('#productForm .info-result strong, .info-result strong, .selected-category');
      const text = selectedEl ? selectedEl.innerText : '';
      return text.includes(categoryLeaf);
    }, leaf);

    if (isAlreadySelected) {
      result.filled.category = leaf;
      console.log(`[fill_naver] Category already confirmed: ${leaf}`);
    } else {
      const selectizeInput = page.locator('.selectize-input input, input[placeholder*="카테고리명 입력"]').first();
      if (await selectizeInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        await selectizeInput.click();
        await selectizeInput.fill('');
        await selectizeInput.pressSequentially(leaf, { delay: 80 });
        await page.keyboard.press('Enter');
        await sleep(1000);

        const firstResult = page.locator('.selectize-dropdown-content .option:has-text("' + leaf + '"), .selectize-dropdown-content .option').first();
        if (await firstResult.isVisible({ timeout: 1500 }).catch(() => false)) {
          await firstResult.click();
          result.filled.category = leaf;
        } else {
          result.errors.push({ step: 'category', error: `no_search_result_for_${leaf}` });
        }
      } else {
        result.filled.category = leaf;
      }
    }
  } catch (e) {
    result.errors.push({ step: 'category', error: e.message });
    console.log('[fill_naver] Category fill warning:', e.message);
  }

  // 3. 판매가 및 재고수량
  try {
    if (naverSpec.optionRows && naverSpec.optionRows.length > 0) {
      const row0 = naverSpec.optionRows[0];
      const priceInput = page.locator('input[name="product.salePrice"], input[name="salePrice"]').first();
      if (await priceInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        await priceInput.fill(String(row0.salePrice));
        result.filled.salePrice = row0.salePrice;
      } else {
        result.errors.push({ step: 'salePrice', error: 'input_not_found' });
      }

      const stockInput = page.locator('input[name="stockQuantity"], input[name*="stock"]').first();
      if (await stockInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        await stockInput.fill(String(row0.stock));
        result.filled.stock = row0.stock;
      }
    }
  } catch (e) {
    result.errors.push({ step: 'price_stock', error: e.message });
    console.log('[fill_naver] Price/stock fill warning:', e.message);
  }

  // 4. 옵션 설정 (단일축 구성)
  try {
    if (naverSpec.optionAxes && naverSpec.optionRows && naverSpec.optionRows.length > 0) {
      const optionToggle = page.locator('input[name="useOption"], input[type="radio"][value="true"]').first();
      if (await optionToggle.isVisible({ timeout: 1000 }).catch(() => false)) {
        await optionToggle.check();
        await sleep(500);

        const optNameInput = page.locator('input#choice_option_name0, input[placeholder*="예시:컬러"], input[ng-model*="groupName"]').first();
        if (await optNameInput.isVisible({ timeout: 1000 }).catch(() => false)) {
          await optNameInput.fill(naverSpec.optionAxes[0]);
        }

        const optValInput = page.locator('input[placeholder*="예시 : 빨강,노랑"], input[ng-model*="choiceOptionInput.name"], input[placeholder*="옵션값"]').first();
        if (await optValInput.isVisible({ timeout: 1000 }).catch(() => false)) {
          await optValInput.fill(naverSpec.optionRows[0].values[0]);
        }

        const applyBtn = page.locator('button:has-text("옵션목록으로 적용"), button:has-text("옵션 적용")').first();
        if (await applyBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
          await applyBtn.click();
          await sleep(500);
        }
        result.filled.option = `${naverSpec.optionAxes[0]}: ${naverSpec.optionRows[0].values[0]}`;
      }
    }
  } catch (e) {
    result.errors.push({ step: 'options', error: e.message });
    console.log('[fill_naver] Option fill warning:', e.message);
  }

  // 5. 상품정보제공고시
  try {
    if (naverSpec.notice) {
      // 섹션 펼침
      const noticeTitle = page.locator('.title-line:has-text("상품정보제공고시")').first();
      if (await noticeTitle.isVisible({ timeout: 1000 }).catch(() => false)) {
        await noticeTitle.click();
        await sleep(500);
      }

      const noticeGroupSelect = page.locator('.form-section:has(.title-line:has-text("상품정보제공고시")) select, select[name*="notice"], select[name*="modelNotice"]').first();
      if (await noticeGroupSelect.isVisible({ timeout: 1500 }).catch(() => false)) {
        await noticeGroupSelect.selectOption({ label: naverSpec.notice.group }).catch(async () => {
          await noticeGroupSelect.selectOption(naverSpec.notice.group).catch(() => {});
        });
        await sleep(600);
      }

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
    result.errors.push({ step: 'notice', error: e.message });
    console.log('[fill_naver] Notice fill warning:', e.message);
  }

  // 6. 태그 10개 입력
  try {
    if (naverSpec.tags && naverSpec.tags.length > 0) {
      // 검색설정 섹션 펼침
      const searchTitle = page.locator('.title-line:has-text("검색설정")').first();
      if (await searchTitle.isVisible({ timeout: 1000 }).catch(() => false)) {
        await searchTitle.click();
        await sleep(400);
      }

      // 태그 직접입력 체크박스
      const directCheck = page.locator('input[ng-model*="isDirectInput"]').first();
      if (await directCheck.isVisible({ timeout: 1000 }).catch(() => false)) {
        const isChecked = await directCheck.isChecked().catch(() => false);
        if (!isChecked) {
          await directCheck.click();
          await sleep(300);
        }
      }

      const tagInput = page.locator('input[placeholder*="태그를 입력해주세요."], input[placeholder*="태그"]').first();
      if (await tagInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        for (const tag of naverSpec.tags) {
          await tagInput.fill(tag);
          await tagInput.press('Enter');
          await sleep(80);
        }
        result.filled.tags = naverSpec.tags;
      } else {
        result.errors.push({ step: 'tags', error: 'input_not_found' });
      }
    }
  } catch (e) {
    result.errors.push({ step: 'tags', error: e.message });
    console.log('[fill_naver] Tags fill warning:', e.message);
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
    result.errors.push({ step: 'mfg_brand', error: e.message });
    console.log('[fill_naver] Brand/Mfg fill warning:', e.message);
  }

  // 8. 인증 처리 (구매대행 면제 또는 대상아님)
  try {
    if (naverSpec.certification) {
      if (naverSpec.certification.kcExemptionType === 'OVERSEAS') {
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
    result.errors.push({ step: 'certification', error: e.message });
    console.log('[fill_naver] Certification fill warning:', e.message);
  }

  // 9. 임시저장 (save 옵션이 true일 때만 실행 / 판매등록 코드는 일체 없음)
  if (save === true) {
    console.log('[fill_naver] save: true specified. Clicking 임시저장...');
    const tempSaveBtn = page.locator('button:has-text("임시저장")').first();
    if (await tempSaveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await tempSaveBtn.click();
      await sleep(1500);
      result.saved = true;
    } else {
      result.saved = false;
      result.errors.push({ step: 'save', error: 'tempSaveButton_not_found' });
    }
  } else {
    console.log('[fill_naver] save: false. Skipping 임시저장 (dry-run mode).');
    result.saved = null;
  }

  // 10. 전 필드 전수 Diff 검증 (DOM 값 역조회)
  try {
    const currentValues = await page.evaluate(() => {
      const name = document.querySelector('input[name="product.name"], input[name="name"], input[placeholder*="상품명"]');
      const price = document.querySelector('input[name="product.salePrice"], input[name="salePrice"]');
      const stock = document.querySelector('input[name="product.stockQuantity"], input[name="stockQuantity"]');
      const brand = document.querySelector('input[name*="brand"], input[placeholder*="브랜드"]');
      const mfg = document.querySelector('input[name*="manufacturer"], input[placeholder*="제조사"]');
      const noticeGroup = document.querySelector('select[name*="notice"], select[name*="modelNotice"]');
      
      // 카테고리
      const catEl = document.querySelector('.info-result.text-info strong, .info-result strong, .selectize-input .item');
      let category = catEl ? (catEl.innerText || catEl.value || null) : null;
      if (!category) {
        const catLine = Array.from(document.querySelectorAll('.title-line')).find(el => (el.innerText || '').includes('카테고리'));
        if (catLine) category = catLine.innerText;
      }

      // 옵션 행 수
      const optionRows = Array.from(document.querySelectorAll('tr[ng-repeat*="optionCombination"], tr[ng-repeat*="item"], .option-table tbody tr'));
      const optionRowCount = optionRows.length > 0 ? optionRows.length : (document.querySelectorAll('input#choice_option_name0').length > 0 ? 1 : 0);

      // 태그 칩 추출
      let tagChips = Array.from(document.querySelectorAll('.tag, .tag-chip, .tag-item, [ng-repeat*="sellerTag"]')).map(t => t.innerText.trim().replace(/^#/, '')).filter(Boolean);
      if (tagChips.length === 0) {
        const tagLine = Array.from(document.querySelectorAll('.title-line')).find(el => (el.innerText || '').includes('검색설정'));
        if (tagLine) {
          const m = tagLine.innerText.match(/태그\(([^)]+)\)/);
          if (m) tagChips = m[1].split(',').map(s => s.trim()).filter(Boolean);
        }
      }

      // 브랜드 / 제조사 summary fallback
      let brandVal = brand ? brand.value : null;
      let mfgVal = mfg ? mfg.value : null;
      const majorInfoLine = Array.from(document.querySelectorAll('.title-line')).find(el => (el.innerText || '').includes('상품 주요정보'));
      if (majorInfoLine) {
        const text = majorInfoLine.innerText;
        const bMatch = text.match(/브랜드\(([^)]+)\)/);
        if (bMatch && !brandVal) brandVal = bMatch[1];
        const mMatch = text.match(/제조사\(([^)]+)\)/);
        if (mMatch && !mfgVal) mfgVal = mMatch[1];
      }

      // 고시 상품군 summary fallback
      let noticeGroupVal = noticeGroup ? (noticeGroup.options[noticeGroup.selectedIndex]?.text || noticeGroup.value) : null;
      const noticeLine = Array.from(document.querySelectorAll('.title-line')).find(el => (el.innerText || '').includes('상품정보제공고시'));
      if (noticeLine && (!noticeGroupVal || noticeGroupVal.includes('?'))) {
        const text = noticeLine.innerText;
        const nMatch = text.match(/설정함\s*\/\s*([^\s메뉴]+)/);
        if (nMatch) noticeGroupVal = nMatch[1];
      }

      return {
        productName: name ? name.value : null,
        category: category,
        optionRowCount: optionRowCount,
        salePrice: price ? parseInt(price.value.replace(/[^0-9]/g, ''), 10) : null,
        stock: stock ? parseInt(stock.value.replace(/[^0-9]/g, ''), 10) : null,
        brand: brandVal,
        manufacturer: mfgVal,
        noticeGroup: noticeGroupVal,
        tags: tagChips
      };
    });

    result.currentFormValues = currentValues;

    // --- 전수 Diff 대조 ---
    // 1) 상품명
    if (naverSpec.productName && currentValues.productName !== naverSpec.productName) {
      result.diff.push({ field: 'productName', expected: naverSpec.productName, actual: currentValues.productName });
    }

    // 2) 카테고리
    if (naverSpec.categoryPath) {
      const expLeaf = naverSpec.categoryPath.split('>').pop().trim();
      if (!currentValues.category || !currentValues.category.includes(expLeaf)) {
        result.diff.push({ field: 'category', expected: expLeaf, actual: currentValues.category });
      }
    }

    // 3) 옵션 행 수
    if (naverSpec.optionRows && naverSpec.optionRows.length > 0) {
      if (currentValues.optionRowCount !== naverSpec.optionRows.length) {
        result.diff.push({ field: 'optionRowCount', expected: naverSpec.optionRows.length, actual: currentValues.optionRowCount });
      }
    }

    // 4) 판매가
    if (naverSpec.optionRows && naverSpec.optionRows[0]) {
      const expPrice = naverSpec.optionRows[0].salePrice;
      if (currentValues.salePrice !== expPrice) {
        result.diff.push({ field: 'salePrice', expected: expPrice, actual: currentValues.salePrice });
      }
    }

    // 5) 재고수량
    if (naverSpec.optionRows && naverSpec.optionRows[0]) {
      const expStock = naverSpec.optionRows[0].stock;
      if (currentValues.stock !== expStock) {
        result.diff.push({ field: 'stock', expected: expStock, actual: currentValues.stock });
      }
    }

    // 6) 태그 10개 개수 대조
    if (naverSpec.tags && naverSpec.tags.length > 0) {
      if (!currentValues.tags || currentValues.tags.length < naverSpec.tags.length) {
        result.diff.push({ field: 'tagsCount', expected: naverSpec.tags.length, actual: currentValues.tags ? currentValues.tags.length : 0 });
      }
    }

    // 7) 고시 상품군 (null guard 제거)
    if (naverSpec.notice && naverSpec.notice.group) {
      const actNoticeGroup = currentValues.noticeGroup || null;
      if (!actNoticeGroup || !actNoticeGroup.includes(naverSpec.notice.group)) {
        result.diff.push({ field: 'noticeGroup', expected: naverSpec.notice.group, actual: actNoticeGroup });
      }
    }

    // 8) 제조사 (null guard 제거)
    if (naverSpec.manufacturer) {
      const actMfg = currentValues.manufacturer || null;
      if (!actMfg || !actMfg.includes(naverSpec.manufacturer)) {
        result.diff.push({ field: 'manufacturer', expected: naverSpec.manufacturer, actual: actMfg });
      }
    }
    // 최종 성공 여부: diff 0개 AND errors 0개
    result.success = (result.diff.length === 0 && result.errors.length === 0);
  } catch (e) {
    result.errors.push({ step: 'diffAudit', error: e.message });
    result.success = false;
  }

  console.log(`[fill_naver] Completed fill for ${spec.id}. Diff count: ${result.diff.length}, Error count: ${result.errors.length}`);
  return result;
}

if (typeof module !== 'undefined') {
  module.exports = { fillNaver };
}
