# NFT Image Protection System

## Overview
This document describes the security measures implemented to prevent NFT images from being copied, downloaded, or saved by users.

## Implementation Components

### 1. Backend Image Endpoint (`app/routers/image_router.py`)

**Purpose**: Provide authenticated image serving with security headers.

**Endpoints**:

#### GET `/api/v1/images/nft/{nft_id}`
Serves NFT images with full access control and security headers.
- **Authentication**: Required (validates logged-in user)
- **Authorization**: Validates user has permission to view the NFT
- **Security Headers**:
  - `Cache-Control: no-cache, no-store, must-revalidate` - Prevents caching
  - `X-Frame-Options: DENY` - Prevents embedding in iframes
  - `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
  - `Content-Security-Policy: default-src 'none'` - Strict security policy

#### GET `/api/v1/images/proxy?url={image_url}`
Proxies external image URLs with authentication and security headers.
- **Authentication**: Required
- **URL Validation**: Verifies the image URL is accessible and valid
- **Security Headers**: Same as above

### 2. Frontend Image Protection (JavaScript)

**File**: `app/static/webapp/app.js`

#### Core Protection Functions

##### `protectImage(element)`
Applies protection to individual image elements:
- Disables right-click context menu
- Prevents drag and drop
- Disables text selection
- Sets `pointer-events: none` to prevent browser save dialogs

##### `protectAllImages()`
Scans the DOM and protects all NFT images:
- Finds all `<img>` tags with NFT-related attributes
- Finds all elements with CSS background images
- Applies protection to each element

##### `protectKeyboardShortcuts()`
Blocks common keyboard shortcuts on image elements:
- **Ctrl+S**: Save page/image
- **Ctrl+C**: Copy
- **Print Screen**: Screen capture
- Detects if focus is on image element before blocking

##### `applyImageProtectionStyles()`
Injects CSS rules to prevent:
- Text selection on NFT images
- User dragging images
- Touch callout menus on mobile
- Image drag-and-drop on all browsers

#### CSS Protection Rules

```css
/* Prevents selection and dragging */
img[alt*="NFT"], [style*="background-image"] {
  user-select: none !important;
  pointer-events: none !important;
  -webkit-user-drag: none !important;
  -webkit-touch-callout: none !important;
}

/* Disables browser drag functionality */
img {
  -webkit-user-drag: none;
  -khtml-user-drag: none;
  -moz-user-drag: none;
  -o-user-drag: none;
}
```

## Protection Methods

### User-Side Prevention

| Method | Implementation | Blocks |
|--------|---------------|--------|
| **Right-Click** | `contextmenu` event listener | Context menu → Save Image |
| **Drag-and-Drop** | `dragstart` event listener | Dragging image to desktop |
| **Keyboard Shortcuts** | `keydown` event listener | Ctrl+S, Ctrl+C, Print Screen |
| **Selection** | CSS `user-select: none` | Text/image selection |
| **Pointer Events** | CSS `pointer-events: none` | Browser save dialogs |
| **Touch Callout** | CSS `-webkit-touch-callout` | Mobile context menus |

### Backend Prevention

| Method | Implementation | Prevents |
|--------|---------------|----------|
| **Authentication** | JWT token validation | Unauthorized access |
| **Authorization** | User ownership check | Viewing others' NFTs |
| **Cache Busting** | `Cache-Control` headers | Offline image access |
| **CSP Headers** | Content Security Policy | Embedding/framing images |
| **MIME Sniffing** | `X-Content-Type-Options` | Browser type guessing |

## Security Layers

### Layer 1: Backend Authentication
```python
@router.get("/images/proxy")
async def proxy_image(url: str, current_user = Depends(get_current_user)):
    # 1. Validates JWT token
    # 2. Checks user exists and is authorized
    # 3. Validates image URL
    # 4. Returns image with security headers
```

### Layer 2: Frontend Event Prevention
```javascript
// Prevents standard browser actions
element.addEventListener('contextmenu', e => e.preventDefault());
element.addEventListener('dragstart', e => e.preventDefault());
element.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'c')) {
    e.preventDefault();
  }
});
```

### Layer 3: CSS Protections
```css
/* Makes images non-interactive and unselectable */
img {
  pointer-events: none;
  user-select: none;
  -webkit-user-drag: none;
}
```

## Implementation Stages

**Stage 1** ✅ (Current) - Frontend Protection
- HTML/CSS makes images unselectable and non-draggable
- JavaScript prevents context menu, keyboard shortcuts
- Works on all modern browsers

**Stage 2** (Optional) - Backend Image Serving
- Replace direct image URLs with protected endpoints
- Requires user authentication for each image view
- Provides additional security layer

**Stage 3** (Advanced) - Image Watermarking
- Add transparent watermark overlays to images
- Embed user-specific identifiers
- Deters unauthorized distribution

**Stage 4** (Advanced) - Canvas Rendering
- Render images to canvas instead of `<img>` tags
- Prevents right-click on canvas elements
- Add dynamic watermarks and protection overlays

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Event Prevention | ✅ | ✅ | ✅ | ✅ |
| CSS user-select | ✅ | ✅ | ✅ | ✅ |
| pointer-events | ✅ | ✅ | ✅ | ✅ |
| -webkit-user-drag | ✅ | ✅ | ✅ | ✅ |
| CSP Headers | ✅ | ✅ | ✅ | ✅ |

## Limitations & Caveats

### What This Prevents
✅ Right-click → Save Image
✅ Drag images to desktop
✅ Ctrl+S, Ctrl+C keyboard shortcuts
✅ Browser save dialogs
✅ Standard image selection

### What This Does NOT Prevent
⚠️ Browser developer tools (F12)
⚠️ Browser inspector/screenshot tools
⚠️ Operating system screen capture tools
⚠️ Network traffic inspection (image URL visible in network tab)
⚠️ Determined technical users with advanced tools

**Note**: Complete image protection is impossible on client-side. These measures work against casual copying but not determined attackers. **If you need absolute image protection, consider:**
- Serving images on-demand with time-limited tokens
- Using DRM (Digital Rights Management) solutions
- Storing NFT images server-side with access logs

## Usage Example

The image protection is **automatically enabled** on all NFT display pages:

```javascript
// Images are protected automatically on:
- Dashboard (NFT preview cards)
- My NFTs page (NFT gallery)
- Marketplace (Listing images)
- NFT Detail view

// Manual protection can be applied to new elements:
protectImage(document.getElementById('my-nft-image'));
protectAllImages(); // Protect all NFT images on current page
```

## Testing Image Protection

To verify protections are working:

1. **Right-Click Test**: Right-click on any NFT image → Context menu should not appear
2. **Drag Test**: Try to drag an NFT image → Should not be draggable
3. **Keyboard Test**: Press Ctrl+S or Ctrl+C while hovering over image → Should be blocked
4. **Selection Test**: Try to select image or text → Should not be selectable
5. **DevTools Test**: Open Developer Tools (F12) → Image URL still visible in Network tab (expected)
6. **Screenshot Test**: Still possible using OS screenshot tools (expected - cannot prevent)

## Future Enhancements

1. **Implement Backend Image Serving**
   - Update NFT schema to serve images through protected endpoints
   - Add image access logging for audit trails

2. **Add Watermarking**
   - Embed user-specific identifiers in images
   - Deter unauthorized distribution
   - Add visible/invisible watermarks

3. **Canvas-Based Rendering**
   - Render high-value NFT images on canvas
   - Add animated protection overlays
   - Combine with watermarking

4. **Access Logging**
   - Log each image view attempt
   - Track IP addresses and timestamps
   - Alert on suspicious activity patterns

## Configuration

Current image protection is enabled by default. No configuration needed.

To customize protection levels:

```javascript
// In app.js init() function:
applyImageProtectionStyles();      // Apply CSS protections
protectKeyboardShortcuts();        // Block keyboard shortcuts
protectAllImages();                // Protect all images
```

## Support & Questions

For issues or questions about image protection:
1. Check browser compatibility above
2. Enable DevTools console to see any errors
3. Verify image elements have correct class names/attributes
4. Check that protectAllImages() is called after DOM updates

---

**Last Updated**: February 18, 2026
**Status**: Production Ready (Frontend Protection)
