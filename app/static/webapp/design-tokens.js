/**
 * DESIGN TOKENS
 * Premium fintech NFT Telegram Mini App
 * Based on reference design (GiftedForge)
 */

export const DESIGN_TOKENS = {
  // ==================== COLOR SYSTEM ====================
  colors: {
    // Primary gradients
    primary: {
      start: '#6B5B95',      // Deep purple
      end: '#8B5CF6',        // Vibrant purple
      rgb: 'rgb(139, 92, 246)',
    },
    
    // Backgrounds
    background: {
      base: '#0F172A',       // Dark navy
      elevated: '#1E293B',   // Slightly lighter
      card: '#1A1F31',       // Card background
    },
    
    // Surfaces
    surface: {
      primary: '#4F46E5',    // Purple action
      secondary: '#8B5CF6',  // Light purple
      tertiary: '#EC4899',   // Pink accent
    },
    
    // Semantic colors
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    
    // Text
    text: {
      primary: '#FFFFFF',
      secondary: '#A0AEC0',
      tertiary: '#718096',
    },
    
    // Borders & Dividers
    border: {
      light: 'rgba(255, 255, 255, 0.05)',
      medium: 'rgba(255, 255, 255, 0.10)',
      dark: 'rgba(0, 0, 0, 0.2)',
    },
  },

  // ==================== SPACING SCALE ====================
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '28px',
    '4xl': '32px',
    '6xl': '48px',
  },

  // ==================== BORDER RADIUS ====================
  radius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '28px',
    full: '9999px',
  },

  // ==================== SHADOWS ====================
  shadows: {
    none: 'none',
    soft: '0 4px 12px rgba(0, 0, 0, 0.15)',
    medium: '0 8px 24px rgba(0, 0, 0, 0.2)',
    elevated: '0 12px 32px rgba(0, 0, 0, 0.3)',
    inner: 'inset 0 2px 4px rgba(0, 0, 0, 0.1)',
  },

  // ==================== TYPOGRAPHY ====================
  typography: {
    // Display sizes
    display: {
      large: {
        size: '32px',
        weight: 700,
        lineHeight: '1.2',
      },
      medium: {
        size: '28px',
        weight: 700,
        lineHeight: '1.2',
      },
      small: {
        size: '24px',
        weight: 700,
        lineHeight: '1.3',
      },
    },
    
    // Heading sizes
    heading: {
      1: {
        size: '24px',
        weight: 700,
        lineHeight: '1.3',
      },
      2: {
        size: '20px',
        weight: 600,
        lineHeight: '1.4',
      },
      3: {
        size: '18px',
        weight: 600,
        lineHeight: '1.4',
      },
    },
    
    // Body text
    body: {
      large: {
        size: '16px',
        weight: 500,
        lineHeight: '1.5',
      },
      normal: {
        size: '14px',
        weight: 400,
        lineHeight: '1.6',
      },
      small: {
        size: '12px',
        weight: 400,
        lineHeight: '1.5',
      },
    },
    
    // Label/caption
    label: {
      size: '12px',
      weight: 600,
      lineHeight: '1.4',
      letterSpacing: '0.5px',
    },
  },

  // ==================== ELEVATION SYSTEM ====================
  zIndex: {
    base: 0,
    dropdown: 100,
    sticky: 200,
    fixed: 300,
    offcanvas: 400,
    modal: 500,
    tooltip: 600,
    notification: 700,
  },

  // ==================== TRANSITIONS ====================
  transitions: {
    fast: '150ms ease-out',
    base: '200ms ease-out',
    slow: '300ms ease-out',
  },

  // ==================== BREAKPOINTS ====================
  breakpoints: {
    phone: '320px',
    tablet: '768px',
    desktop: '1024px',
  },

  // ==================== CONTAINER ====================
  container: {
    maxWidth: '100%',
    padding: '16px',
    mobilePadding: '16px',
  },

  // ==================== CARD SYSTEM ====================
  card: {
    padding: '20px',
    radius: '20px',
    shadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    borderRadius: '20px',
  },

  // ==================== BUTTON SYSTEM ====================
  button: {
    height: {
      sm: '32px',
      md: '40px',
      lg: '48px',
    },
    padding: {
      sm: '8px 16px',
      md: '12px 24px',
      lg: '16px 32px',
    },
    radius: {
      sm: '8px',
      md: '12px',
      lg: '16px',
      pill: '9999px',
    },
  },

  // ==================== INPUT SYSTEM ====================
  input: {
    height: '44px',
    padding: '12px 16px',
    radius: '12px',
    fontSize: '14px',
    focusRing: '0 0 0 3px rgba(139, 92, 246, 0.3)',
  },

  // ==================== NAVIGATION ====================
  navigation: {
    bottomHeight: '64px',
    pillRadius: '28px',
    iconSize: '24px',
    labelSize: '12px',
  },
};

export const GRADIENTS = {
  primary: 'linear-gradient(135deg, #6B5B95 0%, #8B5CF6 100%)',
  primaryWeak: 'linear-gradient(135deg, rgba(107, 91, 149, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
  dark: 'linear-gradient(180deg, #0F172A 0%, #1A1F31 100%)',
  darkElevated: 'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)',
};

export default DESIGN_TOKENS;
