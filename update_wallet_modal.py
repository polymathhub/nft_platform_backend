import re
with open('app/static/webapp/dashboard.html', 'r', encoding='utf-16') as f:
    content = f.read()
if "// Step 3: Try Telegram auto-login if inside Telegram" in content:
    print("Removing Telegram auto-login from Step 3...")
    pattern = r"        // Step 3: Try Telegram auto-login if inside Telegram\s+if \(tg\?\.initData\) \{[^}]*?\n        \n        // Step 4:"
    replacement = "        // Step 3: Telegram auth handled in wallet modal\n\n        // Step 4:"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
pattern = r"    /\*\*\s+\* Handle TON Wallet connection button[^}]*?console\.log\('.*?TON Connect button ready.*?'\);\s+\}"
import re
pattern = r"    /\*\*\s+\* Handle TON Wallet connection button.*?console\.log\('.*?TON Connect button ready.*?'\);\s+\}"
if re.search(pattern, content, re.DOTALL):
    print("Found setupConnectButton function, replacing...")
    content = re.sub(pattern, new_setup, content, flags=re.DOTALL)
    print("Successfully replaced setupConnectButton")
else:
    print("Could not find setupConnectButton function with regex")
    print("File may have different formatting")
with open('app/static/webapp/dashboard.html', 'w', encoding='utf-16') as f:
    f.write(content)
print("File updated successfully!")
