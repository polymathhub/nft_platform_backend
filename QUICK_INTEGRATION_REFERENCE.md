# Quick Integration Reference

## Three Core Pillars

### 1. API Service (`window.api`)
**Purpose:** All HTTP requests to backend

```javascript
// Auth
const user = await api.login(email, password);

// Data
const wallets = await api.getUserWallets();
const nfts = await api.getUserNFTs();
const listings = await api.getActiveListings();

// Actions
await api.mintNFT(walletId, name, desc, imageUrl);
await api.buyNow(listingId);
```

### 2. State Management (`window.appState`)
**Purpose:** Single source of truth for all data

```javascript
// Get data
const user = appState.currentUser;
const summary = appState.getSummary();

// Set data
appState.setCurrentUser(user);
appState.setWallets(wallets);

// Listen to changes
appState.subscribe('user', (user) => {
  console.log('User changed:', user);
});
```

### 3. UI Utilities (`UIUtils` & `StateBinder`)
**Purpose:** Reusable UI patterns and state binding

```javascript
// Show feedback
UIUtils.showToast('Success!', 'success');
UIUtils.showErrorModal('Error', message);

// Format data
UIUtils.formatCurrency(100);
UIUtils.formatAddress('0x...');

// Bind state to UI
StateBinder.bindText(element, 'user', u => u.first_name);
StateBinder.bindClass(element, 'user', 'authenticated');
```

## Common Patterns

### Pattern 1: Load & Display Data

```javascript
async function loadAndDisplay() {
  try {
    // 1. Show loading
    UIUtils.showLoadingSkeleton(container);
    
    // 2. Fetch data
    const data = await api.getUserNFTs();
    
    // 3. Store in state
    appState.setUserNFTs(data);
    
    // 4. Display
    container.innerHTML = data.map(nft => `
      <div>${nft.name}</div>
    `).join('');
  } catch (error) {
    // 5. Handle error
    UIUtils.showError(container, 'Error', error.message);
  }
}
```

### Pattern 2: Handle User Action

```javascript
button.addEventListener('click', async () => {
  try {
    // Show loading
    UIUtils.setButtonLoading(button, true);
    
    // Call API
    await api.someAction(params);
    
    // Reload data
    await loadDashboardData();
    
    // Show success
    UIUtils.showToast('Done!', 'success');
  } catch (error) {
    UIUtils.showToast(error.message, 'error');
  } finally {
    UIUtils.setButtonLoading(button, false);
  }
});
```

### Pattern 3: Real-time Updates

```javascript
// Subscribe to state changes
appState.subscribe('notifications', (notifications) => {
  // Update badge count
  badge.textContent = appState.unreadCount;
});

// When receiving new data
const result = await api.getNotifications();
appState.setNotifications(result);
// Automatically triggers subscribers
```

## API Quick Reference

### Most Used Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Login | POST | `/auth/login` |
| Get Current User | GET | `/auth/me` |
| Get Wallets | GET | `/wallets` |
| Create Wallet | POST | `/wallets/create` |
| Get My NFTs | GET | `/nfts/user` |
| Mint NFT | POST | `/nfts/mint` |
| Get Listings | GET | `/marketplace/listings` |
| Buy NFT | POST | `/marketplace/listings/{id}/buy` |

## State Structure Quick View

```javascript
appState = {
  // Auth
  currentUser: { id, email, username, first_name, last_name, ... }
  isAuthenticated: boolean
  
  // Wallets
  wallets: [{ id, address, blockchain, is_primary }, ...]
  selectedWalletId: string
  
  // NFTs
  userNFTs: [{ id, name, image_url, description, ... }, ...]
  
  // Marketplace
  activeListings: [{ id, nft, price, seller, ... }, ...]
  
  // Notifications
  notifications: [{ id, title, message, read }, ...]
  unreadCount: number
}
```

## Event Handler Template

```javascript
// Template for any event handler
async function handleAction(actionName) {
  const button = document.getElementById(`${actionName}Btn`);
  
  if (!button) return;
  
  button.addEventListener('click', async () => {
    try {
      // 1. Validate
      if (!appState.currentUser) {
        UIUtils.showToast('Please log in first', 'error');
        return;
      }
      
      // 2. Load
      UIUtils.setButtonLoading(button, true);
      
      // 3. Execute
      const result = await api[actionName](params);
      
      // 4. Update
      appState.set...(result);
      
      // 5. Feedback
      UIUtils.showToast('Success!', 'success');
    } catch (error) {
      UIUtils.showErrorModal('Error', error.message);
    } finally {
      UIUtils.setButtonLoading(button, false);
    }
  });
}
```

## Debugging Tips

```javascript
// Check if API is working
console.log(window.api.accessToken);

// Check current state
console.log(appState.getSummary());

// Test API call
await api.getUserWallets();

// Listen to state changes
appState.subscribe('all', (change) => {
  console.log('State changed:', change);
});
```

## Common Tasks

### Display User Name
```javascript
const userName = document.getElementById('userName');
userName.textContent = appState.currentUser.first_name;
```

### Show/Hide Based on Auth
```javascript
const content = document.getElementById('content');
content.style.display = appState.isAuthenticated ? 'block' : 'none';
```

### Count NFTs
```javascript
const nftCount = appState.getUserNFTs().length;
document.getElementById('nftCount').textContent = nftCount;
```

### Format Currency
```javascript
const price = UIUtils.formatCurrency(100.50); // "$100.50"
```

### Show Error
```javascript
UIUtils.showErrorModal(
  'Operation Failed',
  'Something went wrong',
  () => window.location.reload() // retry handler
);
```

## Data Binding Shortcuts

```javascript
// Auto-sync element with state
StateBinder.bindText(
  document.getElementById('userName'),
  'user',
  (user) => user?.first_name || 'Guest'
);

// Show/hide based on state
StateBinder.bindClass(
  document.getElementById('menu'),
  'user',
  'visible'
);

// Update element HTML
StateBinder.bindHTML(
  document.getElementById('stats'),
  'nfts',
  (nfts) => `You have ${nfts.length} NFTs`
);
```

## Error Handling Pattern

```javascript
try {
  const result = await api.someEndpoint(data);
  // Success
  UIUtils.showToast('Success!', 'success');
} catch (error) {
  // Error object structure:
  // { status: 400, message: "...", data: {...} }
  
  if (error.status === 401) {
    // Unauthorized - redirect to login
  } else if (error.status === 400) {
    // Bad request - show form error
  } else {
    // Other error
  }
  
  UIUtils.showToast(error.message, 'error');
}
```

## Testing Checklist

- [ ] app.js loaded and api/appState initialized
- [ ] Console shows no errors
- [ ] User can log in
- [ ] Dashboard data loads
- [ ] UI updates when state changes
- [ ] Errors show properly
- [ ] Navigation works
- [ ] Buttons work without errors

---

**Remember:** Everything flows through:
1. API calls → api service
2. Results → appState
3. State changes → UI updates via subscribers
