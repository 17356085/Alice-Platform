"""调试 thead 行结构"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver(); d = base.open_browser()
try:
    ensure_logged_in(d)
    time.sleep(2)
    d.execute_script("window.location.hash = '#/lab/gas/report';")
    time.sleep(8)

    result = d.execute_script("""
        var rows = document.querySelectorAll('thead tr');
        var info = 'Rows in thead: ' + rows.length;
        for (var r=0; r<rows.length; r++) {
            var ths = rows[r].querySelectorAll('th');
            info += ' | Row' + r + ': ' + ths.length + 'th';
            for (var t=0; t<Math.min(ths.length,6); t++) {
                info += ' ['+t+']=' + ths[t].textContent.trim().substring(0,15);
            }
        }
        var lastRow = document.querySelector('thead tr:last-child');
        var lastThs = lastRow ? lastRow.querySelectorAll('th') : [];
        info += ' | Last row: ' + lastThs.length + 'th';
        for (var t=0; t<Math.min(lastThs.length,3); t++) {
            info += ' ['+t+']=' + lastThs[t].textContent.trim().substring(0,15);
        }
        // Check data cell count in first data row
        var dataRow = document.querySelector('tbody tr');
        if (dataRow) {
            info += ' | Data cells in first row: ' + dataRow.querySelectorAll('td').length;
        }
        return info;
    """)
    print(result.decode('utf-8') if isinstance(result, bytes) else result)
finally:
    base.close_browser()
