import re
with open('app/static/webapp/dashboard.html', 'r', encoding='utf-16') as f:
    content = f.read()
pattern = r"        // Step 3: Try Telegram auto-login if inside Telegram\s+if \(tg\?\.initData\).*?(?=\n\n        // Step 4:)"
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
if new_content != content:
    print("✓ Successfully removed Telegram auto-login block")
    with open('app/static/webapp/dashboard.html', 'w', encoding='utf-16') as f:
        f.write(new_content)
    print("✓ File updated successfully")
else:
    print("! Pattern not found - checking content...")
    if "Step 3: Try Telegram auto-login" in content:
        print("! Found Step 3 comment but pattern didn't match")
        print("! Will do manual inspection")
