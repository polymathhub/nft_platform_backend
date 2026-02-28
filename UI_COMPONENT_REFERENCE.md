# GiftedForge Marketplace - Component Reference

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER (Fixed)                       │
│  GiftedForge          [Bell Icon] [Avatar]                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  DASHBOARD / MARKETPLACE CONTENT                            │
│  (Scrollable)                                               │
│                                                              │
│  [When on Dashboard]                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Welcome back, John                                  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │     Total Balance: $12,450.5         [+ Deposit]    │   │
│  │     No wallet connected                             │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  NFTs Owned    │  Active Listings                   │   │
│  │      16        │       03                           │   │
│  │  Wallet Bal.   │  Total Profit                      │   │
│  │    1.24 ETH    │      $450                          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Quick Actions:  [Create Wallet] [Mint NFT]          │   │
│  │                 [Browse Market]                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Your Collection                              View All│   │
│  │ ┌─────────────────┐  ┌─────────────────┐           │   │
│  │ │ LQ    [Liquid   │  │ ND    [Neon     │           │   │
│  │ │       Oil]      │  │       Dreams]   │           │   │
│  │ │ Owner           │  │ Owner           │           │   │
│  │ │ 2.5 ETH         │  │ 1.8 ETH         │           │   │
│  │ │ [View Item]     │  │ [View Item]     │           │   │
│  │ └─────────────────┘  └─────────────────┘           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Recent Activity                                     │   │
│  │ [Icon] Minted Genesis Cube    3 hours ago  +450 USD│   │
│  │ [Icon] Sale Aborted #22       2 days ago   -250 USD│   │
│  │ [Icon] Bought Fresh Flash     Pending      -250 USD│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  [When on Marketplace]                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Marketplace    [Sort] [Filter] [Grid|List]          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  ┌──────────┐  ┌──────────┐                         │   │
│  │  │ [Image]  │  │ [Image]  │  ← 2 Column Grid      │   │
│  │  │ NEW      │  │ EPIC     │                         │   │
│  │  │ Title    │  │ Title    │                         │   │
│  │  │ Creator  │  │ Creator  │                         │   │
│  │  │ 👁️ 250  │  │ 👁️ 450  │                         │   │
│  │  │ 📈 5     │  │ 📈 12    │                         │   │
│  │  ├──────────┤  ├──────────┤                         │   │
│  │  │100 ⭐│  │ │150 ⭐│  │                         │   │
│  │  │ [Buy]  │  │ [Buy]  │                         │   │
│  │  └──────────┘  └──────────┘                         │   │
│  │  ┌──────────┐  ┌──────────┐                         │   │
│  │  │ [Image]  │  │ [Image]  │                         │   │
│  │  │          │  │          │                         │   │
│  │  │ [card]   │  │ [card]   │                         │   │
│  │  │          │  │          │                         │   │
│  │  └──────────┘  └──────────┘                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  [Spacing for bottom nav]                                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                     DARK FLOATING NAVBAR                    │
│  [Home] [Wallet] [Mint] [Market] [Profile]                 │
│  Dark background, blur effect, rounded corners              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Header
- **Position:** Fixed top
- **Height:** 56px (16px padding)
- **Background:** White (#ffffff)
- **Border:** 1px solid #e2e8f0
- **Content:**
  - Left: Logo text "GiftedForge" (20px, bold)
  - Right: Notification bell + Avatar circle

### Dark Floating Navbar
- **Position:** Fixed bottom (16px from edges)
- **Height:** Auto + safe area
- **Background:** `rgba(26, 31, 40, 0.95)` - dark with transparency
- **Backdrop:** blur(10px)
- **Border:** `rgba(255, 255, 255, 0.1)` - subtle light border
- **Border Radius:** 40px (pill shape)
- **Box Shadow:** `0 -8px 32px rgba(0, 0, 0, 0.25)` - dark shadow
- **Z-Index:** 1000
- **Content:** 5 nav items

**Nav Item States:**
- **Default:** `color: rgba(255, 255, 255, 0.6)` - muted light
- **Hover:** `color: white; background: rgba(255, 255, 255, 0.1)`
- **Active:** 
  - Background: gradient (primary to primary-light)
  - Color: white
  - Box shadow: `0 4px 12px rgba(91, 75, 219, 0.25)`

### Marketplace Header
- **Display:** Flex, space-between
- **Content:**
  - Left: "Marketplace" title
  - Right: 3 control buttons + toggle group

### Control Buttons
- **Size:** 36x36px
- **Background:** var(--bg-secondary) #f8fafc
- **Border:** 1px solid var(--border) #e2e8f0
- **Border Radius:** 8px
- **Icon:** 18x20px, stroke-based SVG, currentColor

**States:**
- **Default:** Light background
- **Hover:** Light gray bg, primary color border
- **Active:** Primary background, white icon

### Control Button Group (Grid/List Toggle)
- **Display:** Inline flex, gap 4px
- **Background:** Slightly dark (surface color)
- **Border:** Grouped border
- **Buttons:** Transparent, toggle active state
- **Active Button:** Primary background

### Marketplace Grid
- **Default:** 2 columns, 12px gap
- **List View:** 1 column, cards horizontal
- **Responsive:**
  - 480px: 12px gap, adjust padding
  - 380px: 8px gap, smaller elements

### Marketplace Card
- **Background:** var(--bg-secondary) #f8fafc
- **Border:** 1px solid var(--border)
- **Border Radius:** 8px
- **Transition:** All 200ms ease

**Structure:**
```
┌─ Card (flex column) ─────────┐
│ ┌─ Image Container ───────┐  │
│ │ [Image]                 │  │
│ │ [Badge: NEW/EPIC/etc]   │  │
│ └─────────────────────────┘  │
│ ┌─ Card Content ──────────┐  │
│ │ Title (2 lines max)     │  │
│ │ Creator                 │  │
│ │ 👁️ 250 views  📈 5 sales│  │
│ └─────────────────────────┘  │
│ ┌─ Card Footer ───────────┐  │
│ │ 100 ⭐  │  [Buy Button] │  │
│ └─────────────────────────┘  │
└──────────────────────────────┘
```

**Card States:**
- **Default:** Light gray
- **Hover:** Primary border, subtle shadow, lift up (translateY -2px)
- **Active (Click):** White background, primary border, strong glow

### Filter Panel (Bottom Sheet Modal)
- **Position:** Fixed bottom, full width
- **Background:** White (#ffffff)
- **Border:** 1px solid #e2e8f0 at top
- **Border Radius:** 16px 16px 0 0
- **Z-Index:** 1501
- **Transform:** Slide up animation
- **Content:**
  - Header: "Filters" title + close button
  - Content: Price range, Availability, Creator filters
  - Actions: Reset + Apply buttons

**Filter Section:**
- Price Range: 2-column number inputs
- Availability: 2 checkboxes (Available, Sold Out)
- Creator: Dynamic list from data

### Sort Menu (Dropdown)
- **Position:** Absolute, top of sort button
- **Background:** White with subtle border
- **Options:** 4 sort modes
- **Display:** Flex column
- **Selected:** Show checkmark (✓) in primary color

### Item Details Modal (Click Card)
- **Position:** Fixed, centered overlay
- **Background:** White (#ffffff)
- **Border Radius:** 8px
- **Content:**
  - Image (square, aspect 1:1)
  - Title
  - Details grid (Price, Views, Sales)
  - Purchase button (gradient primary)

---

## Color Reference

### Backgrounds
```
Primary     #ffffff (white)
Secondary   #f8fafc (light gray)
Tertiary    #f0f2f5 (lighter gray)
Surface     #e8ecf1 (cool gray)
Dark Navbar rgba(26, 31, 40, 0.95)
```

### Text
```
Primary     #1a1a1a (dark)
Secondary   #64748b (gray)
Tertiary    #94a3b8 (light gray)
Muted       #cbd5e1 (very light)
White (nav) rgba(255, 255, 255, 0.6 - 1.0)
```

### Accents
```
Primary     #5b4bdb (purple)
Primary Lt  #7c6ff9 (light purple)
Primary Dk  #3d2f91 (dark purple)
Success     #10b981 (green)
Warning     #f59e0b (orange)
Error       #ef4444 (red)
```

### Borders
```
Light       #e2e8f0
Dark        #f1f5f9
Nav         rgba(255, 255, 255, 0.1)
```

---

## Typography

### Font Family
```
-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif
```

### Sizes
- **Large:** 22px (Welcome greeting)
- **Section Title:** 15px (bold)
- **Card Title:** 13px (bold, 2 lines)
- **Body:** 13px
- **Small:** 12px (labels, badges)
- **Tiny:** 11px (stats, secondary)
- **Micro:** 10px (tertiary labels)

### Weights
- Regular: 400
- Medium: 600
- Bold: 700

---

## Spacing System (4px Base)

```
1 unit  = 4px
2 unit  = 8px  (default gaps)
3 unit  = 12px (card internals)
4 unit  = 16px (section padding)
5 unit  = 20px (large padding)
6 unit  = 24px (extra large)
8 unit  = 32px (sections)
```

---

## Transitions

```
Fast    150ms ease
Normal  200ms ease
```

---

## Border Radius

```
Small   4px  (inputs, small badges)
Medium  6px  (buttons, toggles)
Large   8px  (cards, modals)
2XL     16px (modal header)
Round   40px (nav pill shape)
```

---

## Shadows

```
Small   0 1px 2px 0 rgba(0, 0, 0, 0.05)
Medium  0 4px 6px -1px rgba(0, 0, 0, 0.1)
Large   0 10px 15px -3px rgba(0, 0, 0, 0.1)
Dark    0 -8px 32px rgba(0, 0, 0, 0.25) [Navbar]
Card H  0 8px 20px rgba(91, 75, 219, 0.1)
```

---

## Responsive Breakpoints

```
Desktop     >= 600px
Tablet      480px - 600px
Mobile      380px - 480px
Small App   < 380px
```

---

## Accessibility

- All buttons have `aria-label`
- Icons use `currentColor` for contrast
- Form inputs are properly labeled
- Navigation has semantic structure
- Focus states follow WCAG guidelines
- Safe area support for notched devices

---

## Browser Support

- ✅ Modern Chromium (Edge, Chrome)
- ✅ Safari (iOS 12+)
- ✅ Firefox (modern)
- ✅ Telegram WebView
- ✅ Mobile browsers

---

## Performance Notes

- CSS custom properties for theming
- Hardware-accelerated transforms
- Optimized shadows and gradients
- Minimal repaints on state changes
- Efficient grid layout
- SVG icons (scalable, sharp)

---

## Known Limitations

- No pagination (loads all items)
- No infinite scroll
- Sort/filter client-side only
- No offline support
- Requires active network connection
- Telegram WebView integration required for full features

---

**Last Updated:** February 27, 2026  
**Status:** Production Ready  
**Maintained By:** Principal Frontend Engineer
