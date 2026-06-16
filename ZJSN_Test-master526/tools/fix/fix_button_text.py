"""Fix all xpaths that match button text to handle whitespace in '确 定' (with space)"""
import re

path = r'D:\ZJSN_Test-master\page\person_page\TrainPlanPage.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

# Fix 1: SAVE_BUTTON — use normalize-space for "确定" matching
old = "contains(text(),\"保存\") or contains(text(),\"确定\")"
new = "contains(text(),\"保存\") or normalize-space()=\"确定\""
content = content.replace(old, new)
print(f'SAVE_BUTTON text matching fixed: {content.count(new)} occurrence(s)')

# Fix 2: Same pattern in click_save fallback xpaths that use contains(text(),"确定")
old2 = "contains(text(),\"确定\")"
new2 = "normalize-space()=\"确定\""
# But don't replace in non-button contexts - be specific
count = content.count(old2)
content = content.replace(old2, new2)
print(f'contains(text(),"确定") -> normalize-space()="确定": {count - content.count(new2)} occurrences')

# Fix 3: confirm_course_selection - has text()="确定选择" and text()="确定"
old3 = 'text()="确定选择"'
new3 = 'normalize-space()="确定选择"'
content = content.replace(old3, new3)
print(f'text()="确定选择" fixed: {content.count(new3)} occurrence(s)')

old3b = 'text()="确定"'
new3b = 'normalize-space()="确定"'
content = content.replace(old3b, new3b)
print(f'text()="确定" fixed: {content.count(new3b)} occurrence(s)')

# Fix 4: Any remaining contains(text(),"确")
old4 = 'contains(text(),"确")'
new4 = 'contains(normalize-space(),"确")'
content = content.replace(old4, new4)
print(f'contains(text(),"确") fixed: {content.count(new4)} occurrence(s)')

# Fix 5: _click_dialog_confirm_button already uses normalize-space, but check for footer buttons
# Also check COURSE_SELECT_CONFIRM
old5 = 'text()="确定选择"'
new5 = 'normalize-space()="确定选择"'
print(f'text()="确定选择" in COURSE_SELECT_CONFIRM: already handled')

# Write back
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nWritten {len(content)} bytes (was {original_len})')
print('All button text fixes applied!')
