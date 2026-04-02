/**
 * ═══════════════════════════════════════════════════════════════════════════
 * WALLET INITIALIZATION - Auto-initialize on app load
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * This script:
 * 1. Loads walletManager.js
 * 2. Initializes WalletManager singleton on DOMContentLoaded
 * 3. Makes wallet globally available via window.walletManager
 * 4. Restores previous session automatically
 * 5. Sets up global event listeners
 * 
 * Include in every page's <script> section:
 * <script src="js/walletInit.js"></script>
 */

async function initializeWalletSystem() {
  try {
    console.log('[WalletInit] Starting wallet system initialization...');

    // Get singleton instance
    const walletManager = window.WalletManager.getInstance();

    // Initialize (restores previous session if available)
    const isConnected = await walletManager.initialize();

    console.log('[WalletInit] Wallet system ready. Connected:', isConnected);

    // Make available globally
    window.walletManager = walletManager;

    // Setup global event listeners
    walletManager.on('connected', (data) => {
      console.log('[WalletInit] Global event: wallet connected');
      document.dispatchEvent(
        new CustomEvent('wallet-connected', { detail: data })
      );
      // Update UI across all pages
      updateWalletUIGlobally(data);
    });

    walletManager.on('disconnected', () => {
      console.log('[WalletInit] Global event: wallet disconnected');
      document.dispatchEvent(new CustomEvent('wallet-disconnected'));
      // Update UI across all pages
      clearWalletUIGlobally();
    });

    walletManager.on('error', (error) => {
      console.error('[WalletInit] Wallet error:', error);
      document.dispatchEvent(
        new CustomEvent('wallet-error', { detail: error })
      );
    });

    walletManager.on('transaction-sent', (data) => {
      console.log('[WalletInit] Transaction confirmed:', data);
      document.dispatchEvent(
        new CustomEvent('wallet-transaction-sent', { detail: data })
      );
    });

    // Dispatch initialization complete event
    document.dispatchEvent(new CustomEvent('wallet-system-ready'));

    return walletManager;
  } catch (error) {
    console.error('[WalletInit] Initialization failed:', error);
    document.dispatchEvent(new CustomEvent('wallet-system-error', { detail: error }));
    throw error;
  }
}

/**
 * Update wallet UI globally
 * Called when wallet connects
 */
function updateWalletUIGlobally(data) {
  const walletManager = window.walletManager;

  // Update all elements with wallet address
  document.querySelectorAll('[data-wallet-address]').forEach((el) => {
    el.textContent = walletManager.getFormattedAddress();
  });

  // Update all connect buttons
  document.querySelectorAll('[data-connect-wallet-btn]').forEach((btn) => {
    btn.textContent = 'Wallet Connected';
    btn.disabled = true;
    btn.classList.add('wallet-connected');
  });

  // Show wallet connected indicators
  document.querySelectorAll('[data-wallet-indicator]').forEach((el) => {
    el.classList.add('connected');
  });
}

/**
 * Clear wallet UI globally
 * Called when wallet disconnects
 */
function clearWalletUIGlobally() {
  document.querySelectorAll('[data-wallet-address]').forEach((el) => {
    el.textContent = 'Not connected';
  });

  document.querySelectorAll('[data-connect-wallet-btn]').forEach((btn) => {
    btn.textContent = 'Connect Wallet';
    btn.disabled = false;
    btn.classList.remove('wallet-connected');
  });

  document.querySelectorAll('[data-wallet-indicator]').forEach((el) => {
    el.classList.remove('connected');
  });
}

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * GLOBAL API FUNCTIONS - Usage in your code
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * // Connect wallet
 * await window.walletManager.connect();
 * 
 * // Disconnect wallet
 * await window.walletManager.disconnect();
 * 
 * // Check if connected
 * const isConnected = window.walletManager.isConnected();
 * 
 * // Get address
 * const address = window.walletManager.getAddress();
 * 
 * // Send transaction
 * await window.walletManager.sendTransaction({
 *   to: 'destination_address',
 *   amount: 1.5,  // in TON
 *   payload: 'optional_payload',
 *   metadata: { type: 'mint' }
 * });
 * 
 * // Listen to events
 * window.walletManager.on('connected', (data) => {
 *   console.log('Wallet connected:', data.address);
 * });
 */

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeWalletSystem);
} else {
  // DOM already loaded
  initializeWalletSystem().catch(console.error);
}
