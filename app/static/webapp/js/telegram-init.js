/**
 * TELEGRAM INITIALIZATION SYSTEM
 * 
 * This module ensures proper Telegram WebApp initialization BEFORE any other code.
 * It must be loaded as the FIRST script on every page.
 * 
 * Purpose:
 * - Detect Telegram context early
 * - Call Telegram.WebApp.ready() at the right time
 * - Ensure initData is available
 * - Provide status to downstream modules
 */

// ============================================================================
// PHASE 1: TELEGRAM CONTEXT DETECTION
// ============================================================================

/**
 * Detect if running in Telegram Mini App context
 * @returns {boolean} true if in Telegram, false otherwise
 */
function isTelegramContext() {
  try {
    return (
      typeof window !== 'undefined' &&
      typeof window.Telegram !== 'undefined' &&
      typeof window.Telegram.WebApp !== 'undefined'
    );
  } catch (e) {
    return false;
  }
}

/**
 * Get Telegram info for debugging
 */
function getTelegramInfo() {
  try {
    if (!isTelegramContext()) {
      return { context: 'NOT_TELEGRAM' };
    }
    
    const tg = window.Telegram.WebApp;
    return {
      context: 'TELEGRAM_MINI_APP',
      hasInitData: !!tg.initData,
      hasUser: !!tg.initDataUnsafe?.user,
      userId: tg.initDataUnsafe?.user?.id || null,
      isDark: tg.isDarkMode,
      platform: tg.platform,
      version: tg.version,
    };
  } catch (e) {
    return { context: 'TELEGRAM_ERROR', error: e.message };
  }
}

// ============================================================================
// PHASE 2: TELEGRAM.WEBAPP.READY() INITIALIZATION
// ============================================================================

/**
 * Call Telegram.WebApp.ready() at the appropriate time
 * This signals to Telegram that the Mini App is ready to receive updates
 */
function initializeTelegramWebApp() {
  if (!isTelegramContext()) {
    console.log('[Telegram Init] Not in Telegram context, skipping WebApp.ready()');
    return false;
  }

  try {
    const tg = window.Telegram.WebApp;
    
    // Check if ready() exists and is a function
    if (typeof tg.ready !== 'function') {
      console.warn('[Telegram Init] Telegram.WebApp.ready() is not a function');
      return false;
    }

    // Call ready() to signal to Telegram that we're initialized
    tg.ready();
    console.log('[Telegram Init] ✅ Telegram.WebApp.ready() called successfully');
    
    // Telegram is now ready - we can access initData
    const initData = tg.initData || '';
    if (initData) {
      console.log('[Telegram Init] ✅ Telegram.WebApp.initData is available (length: ' + initData.length + ')');
    } else {
      console.warn('[Telegram Init] ⚠️ Telegram.WebApp.initData is empty - may not be in mini app');
    }

    return true;
  } catch (error) {
    console.error('[Telegram Init] ❌ Error calling Telegram.WebApp.ready():', error.message);
    return false;
  }
}

// ============================================================================
// PHASE 3: GLOBAL STATE AND EVENT SYSTEM
// ============================================================================

// Create global Telegram state object
window._telegramState = {
  isInitialized: false,
  inTelegramContext: isTelegramContext(),
  readyCalled: false,
  initData: null,
  error: null,
};

/**
 * Custom event dispatcher for Telegram initialization events
 */
function dispatchTelegramEvent(eventName, detail = {}) {
  try {
    const event = new CustomEvent(`telegram:${eventName}`, {
      detail: {
        timestamp: Date.now(),
        info: getTelegramInfo(),
        ...detail
      }
    });
    window.dispatchEvent(event);
    console.log(`[Telegram Init] Event dispatched: telegram:${eventName}`);
  } catch (e) {
    console.warn('[Telegram Init] Failed to dispatch event:', e.message);
  }
}

// ============================================================================
// PHASE 4: MAIN INITIALIZATION SEQUENCE
// ============================================================================

/**
 * Main initialization function - orchestrates the entire Telegram setup
 */
async function initTelegram() {
  console.group('[Telegram Init] Starting Telegram initialization sequence');
  
  try {
    // Step 1: Detect context
    const inTelegram = isTelegramContext();
    console.log(`[Telegram Init] Step 1: Context detection = ${inTelegram ? '✅ TELEGRAM' : '⚠️ NOT_TELEGRAM'}`);
    
    // Step 2: Set up error handling for Telegram SDK
    if (inTelegram) {
      const tg = window.Telegram.WebApp;
      
      // Setup error handler
      if (typeof tg.onEvent === 'function') {
        tg.onEvent('themeChanged', () => {
          console.log('[Telegram Init] Theme changed');
        });
      }
    }
    
    // Step 3: Call ready() to initialize Telegram
    console.log('[Telegram Init] Step 3: Calling Telegram.WebApp.ready()...');
    const readySuccess = initializeTelegramWebApp();
    window._telegramState.readyCalled = readySuccess;
    
    if (!readySuccess && inTelegram) {
      console.warn('[Telegram Init] ⚠️ Telegram.WebApp.ready() failed but we are in Telegram context');
    }
    
    // Step 4: Wait for initData to be available if in Telegram
    if (inTelegram) {
      console.log('[Telegram Init] Step 4: Waiting for initData...');
      let attempts = 0;
      const maxAttempts = 20;
      
      while (!window.Telegram.WebApp.initData && attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 100));
        attempts++;
      }
      
      if (window.Telegram.WebApp.initData) {
        window._telegramState.initData = window.Telegram.WebApp.initData;
        console.log('[Telegram Init] Step 4: ✅ initData available after ' + attempts + ' attempts');
      } else {
        console.warn('[Telegram Init] Step 4: ⚠️ initData not available after ' + maxAttempts + ' attempts');
      }
    }
    
    // Step 5: Finalize and dispatch event
    window._telegramState.isInitialized = true;
    dispatchTelegramEvent('initialized', {
      success: true,
      inTelegram,
      readyCalled: readySuccess,
      info: getTelegramInfo()
    });
    
    console.log('[Telegram Init] ✅ Telegram initialization complete');
    console.log('[Telegram Init] Info:', getTelegramInfo());
    
  } catch (error) {
    console.error('[Telegram Init] ❌ Fatal error during initialization:', error);
    window._telegramState.error = error.message;
    window._telegramState.isInitialized = false;
    
    dispatchTelegramEvent('error', {
      error: error.message,
      stack: error.stack
    });
  } finally {
    console.groupEnd();
  }
}

// ============================================================================
// PHASE 5: AUTO-INITIALIZATION ON SCRIPT LOAD
// ============================================================================

// Determine optimal time to initialize based on document state
if (document.readyState === 'loading') {
  // DOM is still loading, initialize when document is ready
  document.addEventListener('DOMContentLoaded', () => {
    initTelegram();
  });
} else {
  // DOM is already Ready, initialize immediately
  initTelegram();
}

// Also expose initialization for manual triggering if needed
window._initTelegram = initTelegram;
window._getTelegramInfo = getTelegramInfo;
window._isTelegramContext = isTelegramContext;

// Export for ES6 modules
export { initTelegram, getTelegramInfo, isTelegramContext };
