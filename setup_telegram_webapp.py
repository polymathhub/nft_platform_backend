#!/usr/bin/env python3
"""
Setup Telegram Bot with Web App Menu Button
This script configures the Telegram bot to show a "Web App" button in the bot menu.
"""

import asyncio
import aiohttp
import sys
import os
from pathlib import Path

async def setup_telegram_menu_button(bot_token, webapp_url):
    """Set up the Telegram bot menu button for web app."""
    
    if not bot_token:
        print("❌ Telegram bot token not configured")
        return False
    
    print(f"🤖 Setting up Telegram Bot Menu Button")
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"Web App URL: {webapp_url}")
    # Telegram API endpoint
    api_url = f"https://api.telegram.org/bot{bot_token}/setChatMenuButton"
    
    # Menu button configuration - shows "Web App" button
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": "Web App",
            "web_app": {
                "url": webapp_url
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                result = await response.json()
                
                if result.get("ok"):
                    print(f"✅ Menu button set successfully!")
                    print(f"   Button text: Web App")
                    print(f"   Opens URL: {webapp_url}")
                    return True
                else:
                    print(f"❌ Failed to set menu button: {result.get('description')}")
                    return False
    
    except Exception as e:
        print(f"❌ Error setting menu button: {e}")
        return False


async def set_webhook(bot_token, webhook_url, webhook_secret):
    """Set up the Telegram webhook."""
    
    if not bot_token:
        print("❌ Telegram bot token not configured")
        return False
    
    print(f"\n🔗 Setting up Telegram Webhook")
    print(f"Webhook URL: {webhook_url}")
    
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "secret_token": webhook_secret or "your-secret-token",
        "allowed_updates": ["message", "callback_query", "web_app_data"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                result = await response.json()
                
                if result.get("ok"):
                    print(f"✅ Webhook set successfully!")
                    print(f"   Webhook URL: {webhook_url}")
                    return True
                else:
                    print(f"❌ Failed to set webhook: {result.get('description')}")
                    print(f"   Make sure your webhook URL is publicly accessible!")
                    return False
    
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False


async def get_bot_info(bot_token):
    """Get bot information."""
    
    if not bot_token:
        print("❌ Telegram bot token not configured")
        return False
    
    print(f"\n📱 Getting Bot Information")
    
    api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                result = await response.json()
                
                if result.get("ok"):
                    bot = result.get("result", {})
                    print(f"✅ Bot Information:")
                    print(f"   ID: {bot.get('id')}")
                    print(f"   Name: {bot.get('first_name')}")
                    print(f"   Username: @{bot.get('username')}")
                    print(f"   Can use Web App: {bot.get('can_join_groups')}")
                    return True
                else:
                    print(f"❌ Failed to get bot info: {result.get('description')}")
                    return False
    
    except Exception as e:
        print(f"❌ Error getting bot info: {e}")
        return False


async def main():
    """Main setup function."""
    print("\n" + "=" * 70)
    print("🚀 Telegram Bot Web App Setup")
    print("=" * 70)
    
    # Get configuration from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    webapp_url = os.getenv("TELEGRAM_WEBAPP_URL", "https://nftplatformbackend-production-b67d.up.railway.app/web-app/")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "https://nftplatformbackend-production-b67d.up.railway.app/api/v1/telegram/webhook")
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    
    if not bot_token:
        print("\n❌ TELEGRAM_BOT_TOKEN not set in environment!")
        print("\nTo set it, run one of:")
        print("  Windows (PowerShell): $env:TELEGRAM_BOT_TOKEN = 'your_token_here'")
        print("  Windows (CMD): set TELEGRAM_BOT_TOKEN=your_token_here")
        print("  Linux/Mac: export TELEGRAM_BOT_TOKEN=your_token_here")
        print("\nOr create .env file with: TELEGRAM_BOT_TOKEN=your_token_here")
        return False
    
    # Get bot info first
    bot_ok = await get_bot_info(bot_token)
    if not bot_ok:
        print("\n❌ Could not connect to Telegram bot. Check your token!")
        return False
    
    # Set up menu button
    menu_ok = await setup_telegram_menu_button(bot_token, webapp_url)
    if not menu_ok:
        print("\n⚠️  Menu button setup failed, continuing...")
    
    # Set up webhook
    webhook_ok = await set_webhook(bot_token, webhook_url, webhook_secret)
    if not webhook_ok:
        print("\n⚠️  Webhook setup failed")
    
    print("\n" + "=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print(f"""
📋 Next Steps:

1. Open Telegram and find your bot
2. You should see a "Web App" button at the bottom
3. Click the button to open the web app
4. The app will authenticate you and load your data

🧪 For Testing:
- If the button doesn't appear, try the /start command
- The bot may take a few seconds to update
- Make sure the webhook URL is publicly accessible (HTTPS)

⚙️ Configuration:
- Bot Token: {bot_token[:20]}...
- Web App URL: {webapp_url}
- Webhook URL: {webhook_url}

📚 Documentation:
- Web App URL must be HTTPS
- Bot must be able to reach the webhook URL
- Webhook requires valid HTTPS certificate
    """)
    
    return menu_ok and webhook_ok


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
