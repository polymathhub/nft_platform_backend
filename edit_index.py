#!/usr/bin/env python3
"""Edit index.html to remove Telegram auto-login from landing page."""

import re

# Read the file with UTF-16 encoding (BOM)
with open('app/static/webapp/index.html', 'r', encoding='utf-16') as f:
    content = f.read()

# Remove the Telegram auto-login block (Step 3)
# This block tries to auto-authenticate users when they open the page
# We need to remove this because it blocks access to the Browse Marketplace button
pattern = r"        // Step 3: Try Telegram auto-login if inside Telegram\s+if \(tg\?\.initData\).*?(?=\n\n        // Step 4:)"

replacement = """        // Step 3: Telegram auth now tied to wallet connection button
        // Users choose when to authenticate (not forced on page load)"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    print("✓ Successfully removed Telegram auto-login block")
    
    # Write back with same encoding
    with open('app/static/webapp/index.html', 'w', encoding='utf-16') as f:
        f.write(new_content)
    print("✓ File updated successfully")
else:
    print("! Pattern not found - checking content...")
    if "Step 3: Try Telegram auto-login" in content:
        print("! Found Step 3 comment but pattern didn't match")
        print("! Will do manual inspection")
