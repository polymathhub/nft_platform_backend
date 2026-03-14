#!/usr/bin/env python3
"""Update index.html to add wallet selection modal functionality."""

import re

# Read the file with UTF-16 encoding (BOM)
with open('app/static/webapp/index.html', 'r', encoding='utf-16') as f:
    content = f.read()

# Find the setupConnectButton function and replace it
# This is a complex replacement, so let's be very specific

# First, remove the auto-login code if it still exists
if "// Step 3: Try Telegram auto-login if inside Telegram" in content:
    print("Removing Telegram auto-login from Step 3...")
    # Find and remove the entire if block
    pattern = r"        // Step 3: Try Telegram auto-login if inside Telegram\s+if \(tg\?\.initData\) \{[^}]*?\n        \n        // Step 4:"
    replacement = "        // Step 3: Telegram auth handled in wallet modal\n\n        // Step 4:"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Find setupConnectButton function
# Look for "function setupConnectButton()" and replace until "console.log('TON Connect button ready');"

pattern = r"    /\*\*\s+\* Handle TON Wallet connection button[^}]*?console\.log\('.*?TON Connect button ready.*?'\);\s+\}"

# The new function implementation
new_setup = '''    /**
     * Show wallet selection modal
     */
    function showWalletSelectionModal() {
      const modal = document.getElementById('walletSelectionModal');
      const tonWalletBtn = document.getElementById('tonWalletOption');
      const telegramWalletBtn = document.getElementById('telegramWalletOption');
      const closeBtn = document.getElementById('walletModalClose');

      // Show modal
      modal.style.display = 'flex';

      // Close modal handler
      const closeModal = () => {
        modal.style.display = 'none';
      };

      closeBtn.addEventListener('click', closeModal);
      
      // Close on background click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeModal();
        }
      });

      // TON Wallet option
      tonWalletBtn.addEventListener('click', async () => {
        closeModal();
        console.log('User selected TON Wallet');
        await handleTonWalletConnection();
      });

      // Telegram Wallet option
      telegramWalletBtn.addEventListener('click', async () => {
        if (!tg?.initData) {
          Toast.error('Telegram Wallet only available inside Telegram');
          return;
        }
        closeModal();
        console.log('User selected Telegram Wallet');
        await handleTelegramWalletConnection();
      });
    }

    /**
     * Handle TON Wallet connection flow
     */
    async function handleTonWalletConnection() {
      const connectBtn = document.getElementById('connectBtn');
      const originalText = connectBtn.textContent;
      const originalDisabled = connectBtn.disabled;

      try {
        if (!tonConnect.isReady) {
          Toast.error('TonConnect is loading... Please try again in a moment.');
          return;
        }

        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting TON Wallet...';

        // Open TON Connect modal
        const result = await tonConnect.openModal();

        if (!result || !result.account?.address) {
          connectBtn.textContent = originalText;
          connectBtn.disabled = originalDisabled;
          return;
        }

        connectBtn.textContent = 'Saving wallet...';
        Toast.show('Wallet selected. Saving to backend...', 'info', 2000);

        // Send to backend
        const response = await fetch('/api/v1/wallet/ton/callback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            wallet_address: result.account.address,
            tonconnect_session: result,
            init_data: tg?.initData || ''
          })
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Backend error');
        }

        const data = await response.json();
        if (data.success) {
          console.log('TON wallet connected');
          Toast.success('Wallet connected! Redirecting to dashboard...', 2000);
          setTimeout(() => {
            window.location.href = basePath + '/dashboard.html';
          }, 1500);
        } else {
          throw new Error(data.detail || 'Connection failed');
        }
      } catch (error) {
        console.error('TON Connect error:', error);
        
        if (error.message?.includes('cancelled') || error.message?.includes('closed')) {
          console.log('User cancelled connection');
        } else {
          Toast.error(`Connection failed: ${error.message}`);
        }
        
        connectBtn.textContent = originalText;
        connectBtn.disabled = originalDisabled;
      }
    }

    /**
     * Handle Telegram Wallet connection flow
     */
    async function handleTelegramWalletConnection() {
      const connectBtn = document.getElementById('connectBtn');
      const originalText = connectBtn.textContent;
      
      try {
        if (!tg?.initData) {
          Toast.error('Telegram Wallet connection requires Telegram app');
          return;
        }

        connectBtn.disabled = true;
        connectBtn.textContent = 'Authenticating with Telegram...';

        console.log('Authenticating via Telegram...');
        const authResponse = await fetch('/api/v1/auth/telegram/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ init_data: tg.initData })
        });
        
        if (!authResponse.ok) {
          const errorData = await authResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Telegram authentication failed');
        }

        const authData = await authResponse.json();
        if (authData.token) {
          localStorage.setItem('token', authData.token);
          console.log('Authenticated via Telegram');
          Toast.success('Authenticated! Redirecting to dashboard...', 2000);
          setTimeout(() => {
            window.location.href = basePath + '/dashboard.html';
          }, 1500);
        } else {
          throw new Error(authData.detail || 'Authentication failed');
        }
      } catch (error) {
        console.error('Telegram authentication error:', error);
        Toast.error(`Telegram auth failed: ${error.message}`);
        connectBtn.textContent = originalText;
        connectBtn.disabled = false;
      }
    }

    /**
     * Handle Connect Wallet button - shows wallet selection modal
     * Independent from marketplace
     */
    function setupConnectButton() {
      const connectBtn = document.getElementById('connectBtn');
      if (!connectBtn) {
        console.warn('Connect button not found');
        return;
      }

      connectBtn.disabled = false;
      connectBtn.style.opacity = '1';
      connectBtn.title = 'Click to choose your wallet';

      connectBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('User clicked Connect Wallet button');
        showWalletSelectionModal();
      });

      console.log('Connect Wallet button ready');
    }'''

# Try to replace with regex for setupConnectButton
# Look for pattern "function setupConnectButton()" through its closing brace
import re

# Match the entire setupConnectButton function
pattern = r"    /\*\*\s+\* Handle TON Wallet connection button.*?console\.log\('.*?TON Connect button ready.*?'\);\s+\}"

if re.search(pattern, content, re.DOTALL):
    print("Found setupConnectButton function, replacing...")
    content = re.sub(pattern, new_setup, content, flags=re.DOTALL)
    print("Successfully replaced setupConnectButton")
else:
    print("Could not find setupConnectButton function with regex")
    print("File may have different formatting")

# Write back
with open('app/static/webapp/index.html', 'w', encoding='utf-16') as f:
    f.write(content)

print("File updated successfully!")
