"""批量插入合同 — 索引JS填值 + 键盘选Select（最简化）"""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in
from page.sales_page.ContractPage import ContractPage
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# 索引映射: 0:合同名称 1:客户(select) 2:产品类型(select) 3:合同总量 4:单价
# 5:总价(auto) 6:签订日期 7:有效期限 8:结算方式(select) 9:税率 10:备注

CONTRACTS = [
    ("分页-01", "贵州能源集团有限公司", "LNG",  50, 3.2, "2026-06-01", "2026-12-31"),
    ("分页-02", "四川化工股份有限公司", "LNG",  80, 3.5, "2026-07-01", "2027-06-30"),
    ("分页-03", "贵州能源集团有限公司", "焦油", 30, 2.8, "2026-05-01", "2026-11-30"),
    ("分页-04", "四川化工股份有限公司", "焦油", 60, 3.0, "2026-08-01", "2027-01-31"),
    ("分页-05", "贵州能源集团有限公司", "LNG", 100, 3.1, "2026-09-01", "2027-08-31"),
    ("分页-06", "四川化工股份有限公司", "LNG",  45, 3.3, "2026-04-01", "2026-10-30"),
    ("分页-07", "贵州能源集团有限公司", "焦油", 75, 2.9, "2026-10-01", "2027-09-30"),
]

base = BaseDriver(); driver = base.open_browser(); created = 0

def js_set(idx, val):
    """JS设置form-item[idx]的input值"""
    return driver.execute_script(f"""
        var items=document.querySelector('.el-dialog:not([style*="display: none"])').querySelectorAll('.el-form-item');
        var inp=items[{idx}].querySelector('input:not([type="hidden"]):not([disabled])');
        var ta=items[{idx}].querySelector('textarea');
        var el=inp||ta; if(!el)return'no_el';
        el.focus();el.value='{val}';
        el.dispatchEvent(new Event('input',{{bubbles:true}}));
        el.dispatchEvent(new Event('change',{{bubbles:true}}));
        el.dispatchEvent(new Event('blur',{{bubbles:true}}));
        return el.value;
    """)

def js_select(idx, option_text):
    """JS: 点击Select→等下拉→点击选项→关闭"""
    # 点击Select wrapper（不是隐藏的input）
    r1 = driver.execute_script(f"""
        var items=document.querySelector('.el-dialog:not([style*="display: none"])').querySelectorAll('.el-form-item');
        var sel=items[{idx}].querySelector('.el-select');
        if(!sel) return 'no_select';
        sel.click();
        return 'clicked';
    """)
    time.sleep(0.5)
    # 点选项 — 派发完整鼠标事件链（Vue/Element Plus需要mousedown→mouseup→click）
    r2 = driver.execute_script(f"""
        var dds=document.querySelectorAll('.el-select-dropdown:not([style*="display: none"])');
        for(var i=0;i<dds.length;i++){{
            var opts=dds[i].querySelectorAll('li:not(.is-disabled)');
            for(var j=0;j<opts.length;j++){{
                if((opts[j].textContent||'').trim().indexOf('{option_text}')!==-1){{
                    var evtOpts={{bubbles:true,cancelable:true,view:window}};
                    opts[j].dispatchEvent(new MouseEvent('mousedown',evtOpts));
                    opts[j].dispatchEvent(new MouseEvent('mouseup',evtOpts));
                    opts[j].dispatchEvent(new MouseEvent('click',evtOpts));
                    return 'picked:'+opts[j].textContent.trim();
                }}
            }}
        }}
        return 'not_found';
    """)
    # 关闭残留下拉
    driver.execute_script("document.body.click()")
    time.sleep(0.3)
    return f"{r1},{r2}"

try:
    ensure_logged_in(driver)
    page = ContractPage(driver); page.navigate()

    deadline = time.time() + 30
    while time.time() < deadline:
        rows = driver.execute_script('return document.querySelectorAll("tr.el-table__row").length')
        if rows > 0: logger.info("%d行", rows); break
        time.sleep(1)

    before = page.get_total_count()
    logger.info("当前:%d", before)

    if before >= 11:
        logger.info("已充足")
    else:
        need = min(len(CONTRACTS), 12 - max(before, 0))

        for i, (suffix, customer, product, qty, price,
                sign_date, valid_to) in enumerate(CONTRACTS):
            if i >= need: break
            cname = f"分页测试_{suffix}"
            logger.info("[%d/%d] %s", i+1, need, cname)

            # 点新增
            driver.execute_script("""var b=document.querySelectorAll('button');
                for(var i=0;i<b.length;i++){if((b[i].textContent||'').indexOf('新增合同')!==-1){b[i].click();return;}}""")
            time.sleep(1.5)

            # JS填充文本/数字/日期字段
            js_set(0, cname)        # 合同名称
            js_set(3, str(qty))     # 总量
            js_set(4, str(price))   # 单价
            js_set(6, sign_date)    # 签订日期
            js_set(7, valid_to)     # 有效期限
            js_set(9, "13")         # 税率
            js_set(10, "自动化测试") # 备注
            time.sleep(0.3)

            # Select下拉 — JS点击
            s1 = js_select(1, customer)  # 客户
            logger.info("  客户:%s", s1)
            s2 = js_select(2, product)   # 产品类型
            logger.info("  产品:%s", s2)
            s8 = js_select(8, "货到付款") # 结算方式
            logger.info("  结算:%s", s8)
            time.sleep(0.3)

            # 保存
            sv = driver.execute_script("""
                var dlg=document.querySelector('.el-dialog:not([style*="display: none"])');
                var btns=dlg.querySelectorAll('button.el-button--primary');
                for(var i=0;i<btns.length;i++){btns[i].click();return'ok';}
                return'no_btn';
            """)
            time.sleep(2.5)

            # 检查
            still_open = driver.execute_script(
                'return !!document.querySelector(".el-dialog:not([style*=\\"display: none\\"])")')
            errs = driver.execute_script("""var es=document.querySelectorAll('.el-form-item__error');
                var m=[];es.forEach(function(e){var t=e.textContent.trim();if(t)m.push(t);});return m;""")

            if not still_open:
                created += 1; logger.info("  ✅")
            elif errs:
                logger.warning("  ❌ %s", errs)
                driver.execute_script("var d=document.querySelector('.el-dialog__headerbtn');if(d)d.click();")
            else:
                logger.warning("  ❌ 未关")
                driver.execute_script("var d=document.querySelector('.el-dialog__headerbtn');if(d)d.click();")
            time.sleep(0.5)

    page.click_reset(); time.sleep(2)
    after = page.get_total_count()
    logger.info("========================")
    logger.info("%d→%d (新增%d)", before, after, created)
    logger.info("✅ 可分页!" if after >= 11 else f"⚠️ {after}")

finally:
    base.close_browser()
