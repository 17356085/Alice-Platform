# Code Consistency Check — sales/contract

**Time**: 2026-06-17 16:01:33
**Module**: sales
**Page**: contract
**Issues**: 14

FAIL: 代码合规检查发现 14 个问题:
  - test_contract.py:61: print 调试（禁止模式: @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feat）
  - test_contract.py:106: print 调试（禁止模式: customer = self._pick_existing_customer(page)
            CO）
  - test_contract.py:115: print 调试（禁止模式: page.fill_contract_form(
                name=CREATED_CONTRA）
  - test_contract.py:192: print 调试（禁止模式: status = page.get_contract_status(contract_name)
           ）
  - test_contract.py:209: print 调试（禁止模式: page.click_reset_search()
            page.search(name=new_n）
  - test_contract.py:363: print 调试（禁止模式: errors = page.try_save_with_invalid_dates(
                s）
  - test_contract.py:371: print 调试（禁止模式: try:
                page.click_dialog_cancel()
            ）
  - test_contract.py:397: print 调试（禁止模式: page.click_add()
            customer = self._pick_existing_）
  - test_contract.py:412: print 调试（禁止模式: page.click_reset_search()
            page.search(name=lifec）
  - test_contract.py:420: print 调试（禁止模式: toast = page.start_contract(lifecycle_name)
            prin）
  - test_contract.py:431: print 调试（禁止模式: toast = page.complete_contract(lifecycle_name)
            p）
  - test_contract.py:462: print 调试（禁止模式: page.click_add()
            customer = self._pick_existing_）
  - test_contract.py:483: print 调试（禁止模式: page.click_delete_by_name(delete_name)

            try:
   ）
  - test_contract.py:507: print 调试（禁止模式: page.click_reset_search()
            page.search(name=delet）
