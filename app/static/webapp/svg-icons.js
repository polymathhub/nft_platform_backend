/**
 * Minimal SvgIconSystem shim
 * Provides a lightweight interface so legacy HTML references won't fail.
 */
(function(){
  class SvgIconSystem {
    constructor() {
      this.loaded = false;
      try {
        this._init();
      } catch (e) {
        console.warn('[SvgIconSystem] init failed:', e && e.message);
      }
    }

    _init() {
      // no-op: keep API surface
      this.loaded = true;
      window.addEventListener('load', () => {
        console.log('[SvgIconSystem] ready');
      });
    }

    get(iconName) {
      // return an inline placeholder SVG string
      return `<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="currentColor"></circle></svg>`;
    }
  }

  // Expose globally
  try {
    window.SvgIconSystem = SvgIconSystem;
    window.svgIcons = new SvgIconSystem();
  } catch (e) {
    console.warn('[SvgIconSystem] could not expose global:', e && e.message);
  }
})();
