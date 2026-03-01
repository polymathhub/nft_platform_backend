# 🚀 Developer Quick Reference - GiftedForge Refactored

## Module Import Quick Guide

All modules are auto-initialized. Access them globally:

```javascript
// Telegram Mini App SDK
TelegramSDK.initialize()      // Returns promise
TelegramSDK.getInitData()    // Get Telegram user data

// API calls
ApiService.get('/wallets')
ApiService.post('/auth/telegram/login', data)
ApiService.setToken(token)

// State management
AppState.setUser(user)
AppState.getUser()
AppState.subscribe('user', callback)

// UI updates
UIUtils.switchView('dashboard')
UIUtils.showStatus('Message', 'success')
UIUtils.updateText('elementId', 'New text')

// App initialization
AppBoot.initialize()    // Auto-called, but can be re-called
AppBoot.isInitialized()
```

---

## Common Tasks

### Add a New API Endpoint

```javascript
// In a module or inline code:
const result = await ApiService.get('/my-endpoint');
if (result.ok) {
  console.log('Success:', result.data);
} else {
  UIUtils.showStatus('Error: ' + result.error, 'error');
}
```

### Listen for State Changes

```javascript
// Subscribe to user changes
const unsubscribe = AppState.subscribe('user', (user) => {
  console.log('User changed:', user);
  // Update UI based on new user data
});

// Unsubscribe when done
// unsubscribe();

// Or listen for all state changes
window.addEventListener('state-changed', (event) => {
  const { key, value } = event.detail;
  console.log(`State ${key} changed:`, value);
});
```

### Update UI Elements

```javascript
// Safe text update
UIUtils.updateText('userBalance', '100.50 SOL');

// Safe HTML update (careful with user input!)
UIUtils.updateHTML('userProfile', `<strong>${user.name}</strong>`);

// Show notification
UIUtils.showStatus('Wallet connected!', 'success');

// Switch to different view
UIUtils.switchView('marketplace');
```

### Handle Authentication

```javascript
// Listen for auth expiration
window.addEventListener('auth-required', () => {
  console.log('Need to re-authenticate');
  // Show login prompt
});

// Check if user is authenticated
const user = AppState.getUser();
if (user?.id) {
  console.log('User is authenticated');
} else {
  console.log('User not authenticated');
}
```

---

## File Organization

```
app/static/webapp/
├── index.html                  ← Entry point (HTML only)
├── styles.css                  ← Styling
├── svg-icons.js                ← Icon system
├── logo.svg, icons.svg         ← Assets
└── scripts/                    ← Application modules
    ├── telegram-sdk.js         ← Telegram Mini App init
    ├── api-service.js          ← Backend communication
    ├── app-state.js            ← State management
    ├── ui-utils.js             ← DOM manipulation
    ├── app-init.js             ← App bootstrap
    └── app-compat.js           ← Global functions
```

---

## Debug Checklist

Opening DevTools (F12)?

1. **Check Console for Initialization**
   ```
   ✓ [Boot] Starting initialization sequence
   ✓ [Telegram] SDK... (loaded or "not available - dev mode")
   ✓ [API] Service initialized
   ✓ [State] Initialized
   ✓ [UI] Utilities initialized
   ✓ [Auth] ✅ Authentication successful
   ✓ [Boot] ✅ Initialization complete
   ```

2. **Check Network for API Calls**
   - Should see: `POST /auth/telegram/login` → 200 OK
   - Should see: `GET /dashboard/stats` → 200 OK
   - If getting 404: Backend route might not exist

3. **Check State**
   ```javascript
   console.log('User:', AppState.getUser());
   console.log('Wallets:', AppState.getWallets());
   console.log('Full state:', AppState.getState());
   ```

4. **Check API Base URL**
   ```javascript
   console.log('API URL:', ApiService.getBaseUrl());
   ```

---

## Adding New Features

### Example: Add "Refresh Dashboard" Button

```html
<!-- In index.html -->
<button onclick="refreshDashboard()">Refresh</button>
```

```javascript
// In app-compat.js or a dedicated module
window.refreshDashboard = async () => {
  UIUtils.showLoading(true);
  try {
    const res = await ApiService.get('/dashboard/stats');
    if (res.ok) {
      AppState.setDashboard(res.data);
      UIUtils.updateText('userBalance', res.data.balance);
      UIUtils.showStatus('Dashboard refreshed', 'success');
    }
  } catch (err) {
    UIUtils.showStatus('Refresh failed', 'error');
  } finally {
    UIUtils.showLoading(false);
  }
};
```

### Example: Add New View

1. **Add HTML structure** to index.html:
   ```html
   <div data-view="mynewview" style="display: none;">
     <h1>My New View</h1>
     <!-- content -->
   </div>
   ```

2. **Add navigation button**:
   ```html
   <button onclick="window.switchPage('mynewview')">New View</button>
   ```

3. **Add data loading** to app-init.js:
   ```javascript
   async function loadMyNewViewData() {
     const res = await ApiService.get('/my-endpoint');
     if (res.ok) {
       AppState.setMyData(res.data);  // Add to AppState
       UIUtils.updateHTML('myViewContent', renderData(res.data));
     }
   }
   ```

---

## Testing in Telegram vs Localhost

### Localhost (Development)
- Telegram SDK NOT available (dev mode)
- All other features work normally
- Good for quick iteration

### Telegram Mini App (Production)
- Telegram SDK available
- Safe area insets applied
- Keyboard handling different
- Always test here before deploying

---

## Performance Tips

1. **Lazy-load data** - Don't load all dashboard data upfront
   ```javascript
   async function loadViewData(viewName) {
     if (viewName === 'marketplace') {
       const res = await ApiService.get('/marketplace');
       // Process...
     }
   }
   ```

2. **Cache user state** - Use AppState subscriptions instead of re-fetching
   ```javascript
   // Bad: Re-fetch every time
   const user = await ApiService.get('/auth/me');
   
   // Good: Use cached state
   const user = AppState.getUser();
   ```

3. **Debounce rapid requests** - Don't spam the backend
   ```javascript
   let debounceTimer;
   function onSearchInput(query) {
     clearTimeout(debounceTimer);
     debounceTimer = setTimeout(async () => {
       const res = await ApiService.get('/search?q=' + query);
       // Process results
     }, 300);
   }
   ```

---

## Deployment Checklist

Before deploying to Railway:

- [ ] Local testing complete (no console errors)
- [ ] Tested on actual Telegram Mini App
- [ ] No hardcoded URLs (using ApiService.getBaseUrl())
- [ ] Environment variables configured if needed
- [ ] Backend is deployed and running
- [ ] `/auth/telegram/login` endpoint returns valid JWT
- [ ] All expected API endpoints exist
- [ ] CORS configured in backend if needed

---

## Useful Backend Routes

```
Auth:
  POST   /auth/register                 → Register new user
  POST   /auth/login                    → Traditional login
  POST   /auth/telegram/login           → Telegram Mini App login ⭐
  POST   /auth/refresh                  → Refresh JWT token
  GET    /auth/me                       → Get current user

Wallets:
  GET    /wallets                       → List user wallets
  GET    /wallets/connected             → Get connected wallet
  POST   /wallets/connect               → Connect new wallet
  
Dashboard:
  GET    /dashboard/stats               → Get user stats

Collections:
  GET    /collections                   → List all collections
  GET    /collections/{id}              → Get collection details

NFTs:
  GET    /nft                           → List NFTs
  POST   /nft/mint                      → Mint new NFT

Marketplace:
  GET    /marketplace/listings          → Get marketplace listings
  POST   /marketplace/listings          → Create listing
```

---

## Common Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: Cannot read property 'getUser' of undefined` | AppState not initialized | Wait for script to load (use defer attribute) |
| `404 Not Found` on API call | Endpoint doesn't exist | Check backend routers are all included |
| `401 Unauthorized` | JWT invalid or expired | Re-authenticate via `/auth/telegram/login` |
| `CORS error` | Frontend origin not allowed | Add origin to backend CORS config |
| `Telegram SDK not detected` | Running outside Telegram app | This is OK - dev mode works without it |
| `AppInitializer is not defined` | Script load order issue | Check all scripts have `defer` attribute |

---

## Getting Help

1. **Check console logs** - Look for `[Boot]`, `[API]`, `[Auth]` prefixes
2. **Check network tab** - See actual API requests/responses
3. **Read module documentation** - Each `.js` file has detailed comments
4. **Check SYSTEM_REFACTOR_COMPLETE.md** - Full architecture guide
5. **Test individually** - Use browser console to test modules:
   ```javascript
   await ApiService.get('/dashboard/stats')
   UIUtils.switchView('wallet')
   AppState.getUser()
   ```

---

**Happy coding! 🎉**

The modular architecture makes it easy to:
- ✅ Add new features
- ✅ Debug issues
- ✅ Test components
- ✅ Deploy safely
- ✅ Maintain code

Remember: Each module is independent. Change one without breaking others.
