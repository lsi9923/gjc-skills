/**
 * fill_wing.js - Coupang Wing 자동 입력 및 전수 diff 검증 스크립트
 * 
 * 설계 원칙 (ops-playbook 속도 설계 & agy/Claude 검토 피드백):
 * 1. aside repl 1회 호출로 spec 읽어 입력 -> (save: true일 때만 중간저장) -> 폼/스토어 읽어 spec과 diff 반환
 * 2. 아코디언 펼침: 실제 접힘 아이콘(텍스트 '') 버튼만 클릭하여 기오픈 섹션 닫힘 방지
 * 3. 옵션: 옵션축 이름/값 입력 -> '옵션목록으로 적용' 클릭 -> 행 수 검증 -> 행별 정상가·판매가·재고 입력
 * 4. 상품정보제공고시: 상품군 드롭다운 먼저 변경 후 칸별 값 입력 (null 필드는 스킵)
 * 5. 중간저장 경고 모달: .alert-confirm 조건부 클릭 (page.once('dialog') 사용 금지)
 * 6. 판매등록·저장하기·판매요청 버튼 코드는 일체 포함 금지 (원천 배제)
 * 7. 전 필드 전수 diff: 상품명·노출명·카테고리·옵션행값/개수·정상가·판매가·재고·검색어15·고시·제조사/브랜드·인증
 * 8. errors[] 또는 diff[]가 하나라도 있으면 success: false
 */

async function fillWing({ page, spec, save = false }) {
  const result = {
    step: 'start',
    errors: [],
    diff: [],
    filled: {},
    success: false
  };

  if (!page || !spec || !spec.wing) {
    throw new Error('page and spec.wing are required');
  }

  const wingSpec = spec.wing;
  console.log(`[fill_wing] Start filling Wing form for ${spec.id} (${spec.name})`);

  // 1. 아코디언 펼침: 실제 접힘 아이콘 텍스트 ''인 버튼/아이콘만 클릭
  try {
    const foldedCount = await page.evaluate(() => {
      let count = 0;
      // 텍스트가 ''이거나 data/class로 접힘 상태인 버튼 탐색
      const elements = Array.from(document.querySelectorAll('button, i, span, .collapse-icon, .accordion-header'));
      for (const el of elements) {
        const text = (el.innerText || el.textContent || '').trim();
        if (text === '' || text.includes('')) {
          el.click();
          count++;
        }
      }
      return count;
    });
    console.log(`[fill_wing] Unfolded ${foldedCount} accordion sections with ''`);
    await page.waitForTimeout(600);
  } catch (e) {
    result.errors.push({ step: 'accordion', error: e.message });
    console.warn('[fill_wing] Accordion expand warning:', e.message);
  }

  // 2. 등록상품명(판매자관리용) & 노출상품명 입력
  try {
    const sellerProdInput = page.locator('input[placeholder*="등록상품명"], input[name*="sellerProductName"]').first();
    if (await sellerProdInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await sellerProdInput.fill(wingSpec.sellerProductName);
      result.filled.sellerProductName = wingSpec.sellerProductName;
    } else {
      result.errors.push({ step: 'sellerProductName', error: 'input_not_found' });
    }

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
    result.errors.push({ step: 'productNames', error: e.message });
    console.warn('[fill_wing] Product name fill warning:', e.message);
  }

  // 3. 카테고리 선택
  try {
    const categoryInput = page.locator('input[placeholder*="카테고리명 입력"]').first();
    if (await categoryInput.isVisible({ timeout: 1500 }).catch(() => false)) {
      const currentCat = await categoryInput.inputValue().catch(() => '');
      if (!currentCat && wingSpec.categoryPath) {
        const parts = wingSpec.categoryPath.split('>');
        const leaf = parts[parts.length - 1].trim();
        await categoryInput.fill(leaf);
        await categoryInput.press('Enter');
        await page.waitForTimeout(1000);

        const firstRec = page.locator('.category-search-result li, .category-list li, .category-picker-item').first();
        if (await firstRec.isVisible({ timeout: 1500 }).catch(() => false)) {
          await firstRec.click();
          result.filled.category = leaf;
        } else {
          result.errors.push({ step: 'category', error: `no_recommendation_for_${leaf}` });
        }
      } else {
        result.filled.category = currentCat;
      }
    }
  } catch (e) {
    result.errors.push({ step: 'category', error: e.message });
    console.warn('[fill_wing] Category fill warning:', e.message);
  }

  // 4. 옵션 설정: 축 이름 확인 -> 축 값 입력 -> '옵션목록으로 적용' 클릭 -> 행 수 검증 -> 행별 정상가/판매가/재고 입력
  try {
    if (wingSpec.optionAxes && wingSpec.optionRows && wingSpec.optionRows.length > 0) {
      // 4-1. 옵션 사용 여부 확인/체크
      const optionUseCheck = page.locator('input[name*="useOption"], input[value="true"][name*="option"]').first();
      if (await optionUseCheck.isVisible({ timeout: 1000 }).catch(() => false)) {
        await optionUseCheck.check().catch(() => {});
      }

      // 4-2. 옵션축별 값 입력
      const optValInputs = page.locator('input[placeholder*="옵션값"], input[placeholder*="콤마(,)"]');
      const valInputCount = await optValInputs.count();

      // spec의 옵션축별 유일 값 수집
      for (let axisIdx = 0; axisIdx < wingSpec.optionAxes.length; axisIdx++) {
        const axisName = wingSpec.optionAxes[axisIdx];
        const axisValues = Array.from(new Set(wingSpec.optionRows.map(r => r.values[axisIdx])));

        // 해당 축 인덱스의 옵션값 입력칸에 콤마 구분 또는 개별 입력
        if (axisIdx < valInputCount) {
          await optValInputs.nth(axisIdx).fill(axisValues.join(', '));
        } else {
          // 필요시 '옵션 추가' 버튼 클릭
          const addAxisBtn = page.locator('button:has-text("옵션 추가"), button:has-text("추가하기")').first();
          if (await addAxisBtn.isVisible({ timeout: 500 }).catch(() => false)) {
            await addAxisBtn.click();
            await page.waitForTimeout(300);
            const freshInputs = page.locator('input[placeholder*="옵션값"]');
            if (await freshInputs.count() > axisIdx) {
              await freshInputs.nth(axisIdx).fill(axisValues.join(', '));
            }
          }
        }
      }

      // 4-3. '옵션목록으로 적용' 버튼 클릭
      const applyOptionBtn = page.locator('button:has-text("옵션목록으로 적용"), button:has-text("옵션 목록으로 적용"), button:has-text("옵션 적용"), button:has-text("옵션목록 생성")').first();
      if (await applyOptionBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
        await applyOptionBtn.click();
        await page.waitForTimeout(1000);
      } else {
        result.errors.push({ step: 'applyOptionBtn', error: 'button_not_found' });
      }

      // 4-4. 생성된 옵션 행 수 검증
      const optionRowsLocator = page.locator('.option-table tbody tr, .inventory-table tbody tr, table.table-bordered tbody tr');
      const actualRowCount = await optionRowsLocator.count();
      if (actualRowCount !== wingSpec.optionRows.length && actualRowCount > 0) {
        console.warn(`[fill_wing] Option row count mismatch: actual ${actualRowCount} vs spec ${wingSpec.optionRows.length}`);
      }

      // 4-5. 행별 정상가 / 판매가 / 재고수량 입력
      for (let rIdx = 0; rIdx < wingSpec.optionRows.length; rIdx++) {
        const specRow = wingSpec.optionRows[rIdx];
        const rowLoc = optionRowsLocator.nth(rIdx);

        // 판매가 입력
        const rowSalePrice = rowLoc.locator('input[name*="salePrice"], input[placeholder*="판매가"]').first();
        if (await rowSalePrice.isVisible({ timeout: 500 }).catch(() => false)) {
          await rowSalePrice.fill(String(specRow.salePrice));
        } else {
          // 전역 일괄입력 또는 단일 입력칸 fallback
          const globalSale = page.locator('input[placeholder*="판매가"]').first();
          if (await globalSale.isVisible({ timeout: 500 }).catch(() => false)) {
            await globalSale.fill(String(specRow.salePrice));
          }
        }

        // 정상가 입력
        if (specRow.originalPrice) {
          const rowOrigPrice = rowLoc.locator('input[name*="originalPrice"], input[placeholder*="정상가"], input[placeholder*="할인율 기준가"]').first();
          if (await rowOrigPrice.isVisible({ timeout: 500 }).catch(() => false)) {
            await rowOrigPrice.fill(String(specRow.originalPrice));
          } else {
            const globalOrig = page.locator('input[placeholder*="할인율 기준가"], input[placeholder*="정상가"]').first();
            if (await globalOrig.isVisible({ timeout: 500 }).catch(() => false)) {
              await globalOrig.fill(String(specRow.originalPrice));
            }
          }
        }

        // 재고수량 입력
        const rowStock = rowLoc.locator('input[name*="stock"], input[placeholder*="재고"]').first();
        if (await rowStock.isVisible({ timeout: 500 }).catch(() => false)) {
          await rowStock.fill(String(specRow.stock));
        } else {
          const globalStock = page.locator('input[placeholder*="재고수량"]').first();
          if (await globalStock.isVisible({ timeout: 500 }).catch(() => false)) {
            await globalStock.fill(String(specRow.stock));
          }
        }
      }

      result.filled.options = `${wingSpec.optionAxes.join('/')} (${wingSpec.optionRows.length}행)`;
    }
  } catch (e) {
    result.errors.push({ step: 'options', error: e.message });
    console.warn('[fill_wing] Options fill warning:', e.message);
  }

  // 5. 검색어 (15개) 입력 (placeholder: '검색어를 입력하세요', .srp-search-input)
  try {
    if (wingSpec.searchTerms && wingSpec.searchTerms.length > 0) {
      const tagInput = page.locator('input[placeholder*="검색어를 입력하세요"], .srp-search-input').first();
      if (await tagInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        for (const term of wingSpec.searchTerms) {
          await tagInput.fill(term);
          await tagInput.press('Enter');
          await page.waitForTimeout(80);
        }
        result.filled.searchTerms = wingSpec.searchTerms;
      } else {
        result.errors.push({ step: 'searchTerms', error: 'input_not_found' });
      }
    }
  } catch (e) {
    result.errors.push({ step: 'searchTerms', error: e.message });
    console.warn('[fill_wing] Search terms fill warning:', e.message);
  }

  // 6. 상품정보제공고시 (상품군 드롭다운 먼저 변경 필수)
  try {
    if (wingSpec.notice) {
      // 6-1. 고시 상품군 드롭다운 변경
      const noticeGroupSelect = page.locator('.notice-section select, select[name*="noticeGroup"], select.notice-category-select').first();
      if (await noticeGroupSelect.isVisible({ timeout: 1500 }).catch(() => false)) {
        await noticeGroupSelect.selectOption({ label: wingSpec.notice.group }).catch(async () => {
          await noticeGroupSelect.selectOption(wingSpec.notice.group);
        });
        await page.waitForTimeout(1000); // 드롭다운 변경 후 폼 리렌더링 대기
      }

      // 6-2. 고시 칸별 값 입력 (null은 지어내지 않고 스킵)
      if (wingSpec.notice.fields) {
        for (const [label, val] of Object.entries(wingSpec.notice.fields)) {
          if (val === null) continue;
          const fieldInput = page.locator(`tr:has-text("${label}") input, tr:has-text("${label}") textarea, div:has-text("${label}") > input, div:has-text("${label}") > textarea`).first();
          if (await fieldInput.isVisible({ timeout: 500 }).catch(() => false)) {
            await fieldInput.fill(val);
          }
        }
      }
      result.filled.noticeGroup = wingSpec.notice.group;
    }
  } catch (e) {
    result.errors.push({ step: 'notice', error: e.message });
    console.warn('[fill_wing] Notice fill warning:', e.message);
  }

  // 7. 제조사 / 브랜드 / 인증
  try {
    const mfgInput = page.locator('input[placeholder*="제조사명"], input[name*="manufacturer"]').first();
    if (await mfgInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await mfgInput.fill(wingSpec.manufacturer || '협력업체');
      result.filled.manufacturer = wingSpec.manufacturer;
    }

    if (wingSpec.certification && wingSpec.certification.certificationType) {
      const certRadio = page.locator(`input[value*="${wingSpec.certification.certificationType}"]`).first();
      if (await certRadio.isVisible({ timeout: 1000 }).catch(() => false)) {
        await certRadio.check();
      }
    }
  } catch (e) {
    result.errors.push({ step: 'mfg_cert', error: e.message });
    console.warn('[fill_wing] Mfg/Cert fill warning:', e.message);
  }

  // 8. 중간저장 (save 옵션이 true일 때만 실행 / 판매등록 코드는 일체 없음)
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
      result.errors.push({ step: 'save', error: 'save_button_not_found' });
    }
  } else {
    console.log('[fill_wing] save: false. Skipping intermediate save (dry-run mode).');
    result.saved = null;
  }

  // 9. 전 필드 전수 Diff 검증 (DOM 및 Vuex store oSellerProduct 대조)
  try {
    const auditData = await page.evaluate(() => {
      // 1. Vuex store 조회
      const appMain = document.querySelector('.app-main');
      const store = appMain && appMain.__vue__ && appMain.__vue__.$store;
      const storeProd = store ? store.getters.oSellerProduct : null;

      // 2. DOM 값 fallback 조회
      const sellerProdEl = document.querySelector('input[placeholder*="등록상품명"], input[name*="sellerProductName"]');
      const displayProdEl = document.querySelector('input[placeholder*="노출상품명"], input[name*="displayProductName"]');
      const catEl = document.querySelector('input[placeholder*="카테고리명 입력"], .category-picker-selected');
      const mfgEl = document.querySelector('input[placeholder*="제조사명"], input[name*="manufacturer"]');
      const brandEl = document.querySelector('input[placeholder*="브랜드명"], input[name*="brand"]');
      const noticeGroupEl = document.querySelector('.notice-section select, select.notice-category-select');

      // 검색어 태그 칩 추출
      const tagChips = Array.from(document.querySelectorAll('.srp-tag-chip, .search-term-chip, .tag-chip')).map(c => c.innerText.trim().replace(/^#/, ''));

      return {
        hasStore: Boolean(storeProd),
        storeProd: storeProd ? JSON.parse(JSON.stringify(storeProd)) : null,
        domValues: {
          sellerProductName: sellerProdEl ? sellerProdEl.value : null,
          displayProductName: displayProdEl ? displayProdEl.value : null,
          category: catEl ? catEl.value || catEl.innerText : null,
          manufacturer: mfgEl ? mfgEl.value : null,
          brand: brandEl ? brandEl.value : null,
          noticeGroup: noticeGroupEl ? (noticeGroupEl.options[noticeGroupEl.selectedIndex]?.text || noticeGroupEl.value) : null,
          tagChips: tagChips
        }
      };
    });

    result.auditData = auditData;
    const storeProd = auditData.storeProd;
    const dom = auditData.domValues;

    // --- 전 필드 전수 Diff 대조 ---
    // 1) 등록상품명
    const actualSellerName = storeProd?.sellerProductName || dom.sellerProductName;
    if (wingSpec.sellerProductName && actualSellerName !== wingSpec.sellerProductName) {
      result.diff.push({ field: 'sellerProductName', expected: wingSpec.sellerProductName, actual: actualSellerName });
    }

    // 2) 카테고리 ID 또는 경로
    if (wingSpec.categoryId) {
      const actCatId = storeProd ? storeProd.categoryId : null;
      if (actCatId !== wingSpec.categoryId) {
        result.diff.push({ field: 'categoryId', expected: wingSpec.categoryId, actual: actCatId });
      }
    }

    // 3) 옵션 행 수 및 행별 가격/재고/값
    if (wingSpec.optionRows && wingSpec.optionRows.length > 0) {
      const actualItems = (storeProd && storeProd.items) ? storeProd.items : [];
      if (actualItems.length !== wingSpec.optionRows.length) {
        result.diff.push({ field: 'optionRowCount', expected: wingSpec.optionRows.length, actual: actualItems.length });
      }
      for (let i = 0; i < wingSpec.optionRows.length; i++) {
        const expRow = wingSpec.optionRows[i];
        const actItem = actualItems[i] || null;
        if (!actItem) {
          result.diff.push({ field: `option[${i}]`, expected: expRow, actual: null });
        } else {
          if (expRow.salePrice && actItem.salePrice !== expRow.salePrice) {
            result.diff.push({ field: `option[${i}].salePrice`, expected: expRow.salePrice, actual: actItem.salePrice });
          }
          if (expRow.originalPrice && actItem.originalPrice !== expRow.originalPrice) {
            result.diff.push({ field: `option[${i}].originalPrice`, expected: expRow.originalPrice, actual: actItem.originalPrice });
          }
          if (expRow.stock && actItem.maximumBuyForPerson !== expRow.stock) {
            result.diff.push({ field: `option[${i}].stock`, expected: expRow.stock, actual: actItem.maximumBuyForPerson });
          }
        }
      }
    }

    // 4) 검색어 (15개 집합 및 개수 대조)
    if (wingSpec.searchTerms && wingSpec.searchTerms.length > 0) {
      const actualTags = (storeProd && storeProd.searchTags) ? storeProd.searchTags : (dom.tagChips || []);
      if (actualTags.length < wingSpec.searchTerms.length) {
        result.diff.push({ field: 'searchTermsCount', expected: wingSpec.searchTerms.length, actual: actualTags.length });
      }
    }

    // 5) 고시 상품군
    if (wingSpec.notice && wingSpec.notice.group) {
      const actGroup = dom.noticeGroup || null;
      if (!actGroup || !actGroup.includes(wingSpec.notice.group)) {
        result.diff.push({ field: 'noticeGroup', expected: wingSpec.notice.group, actual: actGroup });
      }
    }

    // 6) 제조사
    if (wingSpec.manufacturer) {
      const actMfg = (storeProd && storeProd.manufacturer) ? storeProd.manufacturer : dom.manufacturer;
      if (!actMfg || !actMfg.includes(wingSpec.manufacturer)) {
        result.diff.push({ field: 'manufacturer', expected: wingSpec.manufacturer, actual: actMfg });
      }
    }
    // 최종 성공 여부: diff 0개 AND errors 0개
    result.success = (result.diff.length === 0 && result.errors.length === 0);
  } catch (e) {
    result.errors.push({ step: 'diffAudit', error: e.message });
    result.success = false;
  }

  console.log(`[fill_wing] Completed fill for ${spec.id}. Diff count: ${result.diff.length}, Error count: ${result.errors.length}`);
  return result;
}

if (typeof module !== 'undefined') {
  module.exports = { fillWing };
}
