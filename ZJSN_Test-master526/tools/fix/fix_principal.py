"""Fix select_principal dialog detection"""
with open(r'D:\ZJSN_Test-master\page\person_page\TrainPlanPage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the pattern - look for 'for d in dialogs:' near '排除已有的弹窗'
idx = content.find('for d in dialogs:')
if idx < 0:
    print("ERROR: could not find 'for d in dialogs:'")
    exit(1)

# Find the next 'if principal_dialog is None:' after this
end_marker = 'if principal_dialog is None:'
end_idx = content.find(end_marker, idx)
if end_idx < 0:
    print("ERROR: could not find 'if principal_dialog is None:'")
    exit(1)

# Extract the block to replace (from 'for d in dialogs:' to just before 'if principal_dialog is None:')
block = content[idx:end_idx]
print(f"Block found at {idx}-{end_idx}")
print(f"Block starts with: {repr(block[:80])}")
print(f"Block ends with: {repr(block[-80:])}")

replacement = '''        for d in reversed(dialogs):
            try:
                title_els = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
                if not title_els:
                    continue
                title = title_els[0].text.strip()
                if not title or title == "添加培训计划":
                    continue
                principal_dialog = d
                break
            except Exception:
                continue

        '''

content = content[:idx] + replacement + content[end_idx:]

with open(r'D:\ZJSN_Test-master\page\person_page\TrainPlanPage.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fix 2 applied successfully!")
