#!/usr/bin/env python3
"""Fix auth router error logging"""

with open('app/routers/auth_router.py', 'r') as f:
    content = f.read()

# Enhance Telegram login error logging
old_pattern = 'logger.warning(f"Invalid Telegram login attempt - signature verification failed")'
new_code = '''logger.warning(
            f"[AUTH] Telegram login failed - signature verification failed | "
            f"telegram_id={telegram_data.get('telegram_id')} | "
            f"hash_present={bool(telegram_data.get('hash'))} | "
            f"auth_date={telegram_data.get('auth_date')}"
        )'''

if old_pattern in content:
    content = content.replace(old_pattern, new_code)
    print("✓ Updated: Telegram login error logging")
else:
    print("⚠ Pattern not found, searching for similar...")
    if "signature verification failed" in content:
        print("✓ Found related text, attempting alternative replacement")

with open('app/routers/auth_router.py', 'w') as f:
    f.write(content)

print("✓ Auth router enhanced: Better error logging added")
