/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SIMPLE WALLET PAGE INTEGRATION
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Simple integration of SimpleTonConnect with wallet.html
 * No complex state management, just straightforward wallet connection.
 * 
 * Usage:
 *   <script type="module">
 *     import { initWalletConnect } from './js/wallet-connect-simple.js';
 *     initWalletConnect();
 *   </script>
 * ═══════════════════════════════════════════════════════════════════════════
 */

import SimpleTonConnect from './simple-tonconnect.js';

// Initialize wallet connect
export async function initWalletConnect() {
  console.log('[WalletConnect] Initializing...');

  // Create TON Connect instance
  const tonConnect = new SimpleTonConnect('tonconnect-button');

  try {
    // Initialize (will restore previous session if available)
    await tonConnect.init();
    console.log('[WalletConnect] Ready');
  } catch (error) {
    console.error('[WalletConnect] Initialization error:', error);
    return;
  }

  // Update UI based on connection state
  function updateUI() {
    const connectBtn = document.getElementById('connectBtn');
    const walletAddress = document.getElementById('walletAddress');
    const status = document.getElementById('status');

    if (tonConnect.isConnected()) {
      const address = tonConnect.getAddress();
      connectBtn.textContent = 'Disconnect Wallet';
      connectBtn.className = 'balance-action disconnect-btn';
      walletAddress.textContent = formatAddress(address);
      walletAddress.style.display = 'block';
      status.textContent = 'Connected ✅';
      status.className = 'status connected';
    } else {
      connectBtn.textContent = 'Connect TON Wallet';
      connectBtn.className = 'balance-action';
      walletAddress.style.display = 'none';
      status.textContent = 'Not connected';
      status.className = 'status disconnected';
    }
  }

  // Format address for display
  function formatAddress(address) {
    if (!address) return '';
    return address.slice(0, 6) + '...' + address.slice(-6);
  }

  // Handle button click
  const connectBtn = document.getElementById('connectBtn');
  if (connectBtn) {
    connectBtn.addEventListener('click', async (e) => {
      e.preventDefault();

      if (tonConnect.isConnected()) {
        // Disconnect
        await tonConnect.disconnectWallet();
        updateUI();
      } else {
        // Connect
        try {
          await tonConnect.connectWallet();
          // UI will update via 'connected' event
        } catch (error) {
          console.error('[WalletConnect] Connection error:', error);
          alert('Failed to connect wallet: ' + error.message);
        }
      }
    });
  }

  // Listen for connection events
  tonConnect.on('connected', (account) => {
    console.log('[WalletConnect] Wallet connected:', account.address);
    updateUI();

    // Optional: Show notification
    const notification = document.querySelector('.notification');
    if (notification) {
      showNotification('Success', `Connected: ${formatAddress(account.address)}`, 'success');
    }
  });

  tonConnect.on('disconnected', () => {
    console.log('[WalletConnect] Wallet disconnected');
    updateUI();
  });

  tonConnect.on('error', (error) => {
    console.error('[WalletConnect] Error:', error);
    showNotification('Error', 'Connection failed: ' + error.message, 'error');
  });

  tonConnect.on('synced', (data) => {
    console.log('[WalletConnect] Backend synced:', data);
  });

  // Initial UI update
  updateUI();
}

// Helper: Show notification
function showNotification(title, message, type = 'info') {
  // If you have a notification system, use it here
  // Otherwise just use alert
  console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initWalletConnect);
} else {
  initWalletConnect();
}
